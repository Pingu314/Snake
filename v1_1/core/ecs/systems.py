#ECS Systems

import math
from types import SimpleNamespace

from v1_1.config import layout
from v1_1.config.achievement_config import COMBO_GOD_PRESETS, LENGTH_THRESHOLDS, ACHIEVEMENTS, \
    PERFECT_RUN_MIN_FOOD, GREEDY_GOLDEN, NERVOUS_PAUSES, INSANE_SURVIVOR_SECONDS, PATIENCE_SECONDS, MARATHON_SECONDS, \
    ON_FIRE_COMBO, TOURIST_WRAPS, QUICK_DRAW_SECONDS, HIGH_ROLLER_SCORE
from v1_1.core.game_state import GameState
from v1_1.core.ecs.components import Position, SnakeHead, SnakeSegment, \
    PreviousPosition, Velocity, RenderRequest, NameEntry, ComboGlow, ComboCounter, \
    Obstacle, GameEvent, AchievementPopup, RunModifier, ScoreEvent, Food, TurnBuffer, ObstacleMover, \
    Countdown
from v1_1.core.ecs.factories import spawn_achievement_popup
from v1_1.core.ecs.ui_components import UILabel, UIStateTag


def cache_previous_positions(world):
    """Remember where every snake segment was, so snake_follow_system can move the body after the head."""
    positions = world.get(Position)
    prev = world.get(PreviousPosition)

    for e in world.get(SnakeSegment):
        pos = positions[e]
        if e not in prev:
            world.add_component(e,PreviousPosition(pos.x, pos.y))
        else:
            prev[e].x = pos.x
            prev[e].y = pos.y

def snake_follow_system(world):
    segments = world.get(SnakeSegment)
    prevs = world.get(PreviousPosition)
    positions = world.get(Position)

    ordered = sorted(segments.items(),key=lambda x: x[1].index)

    for i in range(1, len(ordered)):
        e, _ = ordered[i]
        lead, _ = ordered[i-1]
        positions[e].x = prevs[lead].x
        positions[e].y = prevs[lead].y

def steering_system(world):
    """Apply one buffered turn per tick. Turns that reverse into the neck or change nothing are dropped."""
    velocities = world.get(Velocity)

    for e, buffer in world.get(TurnBuffer).items():
        vel = velocities[e]
        while buffer.turns:
            dx, dy = buffer.turns.pop(0)
            if (dx, dy) in ((vel.dx, vel.dy), (-vel.dx, -vel.dy)):
                continue
            vel.dx, vel.dy = dx, dy
            break

def movement_system(world):
    positions = world.get(Position)

    for e, vel in world.get(Velocity).items():
        pos = positions.get(e)
        if pos:
            pos.x += vel.dx
            pos.y += vel.dy

def obstacle_movement_system(world):
    """Slide moving obstacle blocks sideways one cell every OBSTACLE_STEP_SECONDS (each block keeps its own time).

    Blocks bounce off the walls, the snake and the food, so a block never moves into
    the snake (only the head driving into a block kills) and never hides the food.
    Run it after collision_system.
    """
    settings = world.settings
    min_x, max_x, _, _ = settings.bounds()
    positions = world.get(Position)
    solid = {(positions[e].x, positions[e].y)
             for e in list(world.get(SnakeSegment)) + list(world.get(Food))}

    def can_move(cells, step):
        return all(min_x <= p.x + step <= max_x and (p.x + step, p.y) not in solid for p in cells)

    blocks = {}
    for e, mover in world.get(ObstacleMover).items():
        blocks.setdefault(id(mover), (mover, []))[1].append(positions[e])

    for mover, cells in blocks.values():
        mover.elapsed += settings.speed()
        if mover.elapsed < settings.OBSTACLE_STEP_SECONDS * 1000:
            continue
        mover.elapsed = 0
        if not can_move(cells, mover.step):
            mover.step = -mover.step
            if not can_move(cells, mover.step):
                continue        # boxed in on both sides: wait
        for pos in cells:
            pos.x += mover.step

def collision_system(world):
    positions = world.get(Position)
    foods = world.get(Food)
    heads = world.get(SnakeHead)
    segments = world.get(SnakeSegment)
    obstacles = world.get(Obstacle)
    grid = world.settings.grid_size

    def touching(a, b, reach):
        return abs(a.x - b.x) < reach and abs(a.y - b.y) < reach

    for head in heads:
        h_pos = positions[head]

        #-------Food--------
        for food_entity in foods:
            if touching(h_pos, positions[food_entity], grid / 2):
                world.add_component(world.create_entity(),
                                    GameEvent("FOOD_HIT", food_entity))

        #--------Self--------
        for entity, seg in segments.items():
            if entity == head or seg.index <= 1:
                continue
            if touching(h_pos, positions[entity], grid):
                world.add_component(world.create_entity(),
                                    GameEvent("DEATH"))

        #------Obstacle-----
        for obs in obstacles:
            if touching(h_pos, positions[obs], grid):
                world.add_component(world.create_entity(),
                                    GameEvent("DEATH"))

def field_frame_system(world, pen):
    """Mark the playfield so its edge can't be misjudged.

    Everything outside the field (side margins, bottom band, HUD band) is filled in the
    frame colour, so no empty-looking space is left that is actually wall. The edge itself
    is a thick line in the warning colour when the walls kill, a thin one when the snake wraps.
    The line sits completely outside the outermost cells, exactly where the collision happens.
    """
    settings, theme = world.settings, world.theme
    fw, fh, far = settings.FIELD_HALF_WIDTH, settings.FIELD_HALF_HEIGHT, layout.FRAME_FAR

    pen.clear()
    pen.penup()
    pen.color(theme.get("frame"))
    for x0, y0, x1, y1 in ((-far, fh, far, far),        # top band (HUD)
                           (-far, -far, far, -fh),      # bottom band
                           (-far, -fh, -fw, fh),        # left margin
                           (fw, -fh, far, fh)):         # right margin
        pen.goto(x0, y0)
        pen.begin_fill()
        for corner in ((x1, y0), (x1, y1), (x0, y1), (x0, y0)):
            pen.goto(corner)
        pen.end_fill()

    deadly = not settings.get_wrap_mode()
    width = layout.WALL_LINE_WIDTH if deadly else layout.BORDER_LINE_WIDTH
    pen.pensize(width)
    pen.color(theme.get("wall" if deadly else "border"))
    ex, ey = fw + width / 2, fh + width / 2
    pen.goto(-ex, -ey)
    pen.pendown()
    for corner in ((ex, -ey), (ex, ey), (-ex, ey), (-ex, -ey)):
        pen.goto(corner)
    pen.penup()

class BoardRenderer:
    """Draws the board: snake, obstacles, food and the pause overlay.

    Tk repaints every canvas item in the changed area, so the cost grows with the number of
    items, not with what changed. Therefore:
      - the snake's body is one thick line per run (a new run starts where it wraps), drawn
        straight on the canvas: one item, however long the snake is
      - head, obstacles and food are turtle stamps (one per cell); only cells whose look
        changed are restamped
    `pens` maps "snake", "food" and "overlay" to turtles; `canvas` is the turtle canvas.
    """

    def __init__(self, pens, canvas):
        self.pens = pens
        self.canvas = canvas
        self.stamps = {}        # (pen name, x, y) -> (stamp id, look)
        self.body_lines = []    # canvas line items, one per run of the body
        self.body_drawn = None  # (cells, colour) last drawn

    def reset(self):
        for pen in self.pens.values():
            pen.clearstamps()
        self.stamps.clear()
        for item in self.body_lines:
            self.canvas.delete(item)
        self.body_lines.clear()
        self.body_drawn = None

    def draw(self, world):
        state = world.state.current
        if state not in (GameState.PLAYING, GameState.PAUSED):
            return
        if state == GameState.PAUSED:
            # the board stands still under the overlay: keep it, only add the overlay on top
            wanted = {key: look for key, (_, look) in self.stamps.items() if key[0] != "overlay"}
            wanted.update(self._overlay(world))      # stamped last, so it lies on top
        else:
            wanted = self._board(world)
            self._draw_body(world)

        for key in [k for k in self.stamps if k not in wanted]:
            self.pens[key[0]].clearstamp(self.stamps.pop(key)[0])
        for key, look in wanted.items():
            old = self.stamps.get(key)
            if old and old[1] == look:
                continue
            pen = self.pens[key[0]]
            if old:
                pen.clearstamp(old[0])
            color, size = look
            pen.color(color)
            pen.shapesize(*size)
            pen.goto(key[1], key[2])
            self.stamps[key] = (pen.stamp(), look)

    @staticmethod
    def _board(world):
        """What every board cell should look like now: {(pen, x, y): (colour, (stretch_wid, stretch_len))}."""
        theme = world.theme
        positions = world.get(Position)
        glows = world.get(ComboGlow)
        pulse = 1 + math.sin(world.state.ms / 720) * 0.1        # food breathes
        wanted = {}
        for e, r in world.get(RenderRequest).items():          # the body has none: see _draw_body
            pos = positions[e]
            if r.kind == "food":
                wanted[("food", pos.x, pos.y)] = (theme.get(r.color_key), (pulse, pulse))
            elif r.kind in ("snake", "obstacle"):
                glow = glows.get(e)
                if glow:
                    strength = glow.ms / glow.max_ms
                    size = 1 + math.sin(glow.ms / 360) * 0.15 * strength
                    color = theme.get("combo_glow_strong" if strength > 0.6 else "combo_glow")
                    wanted[("snake", pos.x, pos.y)] = (color, (size, size))
                else:
                    wanted.setdefault(("snake", pos.x, pos.y), (theme.get(r.color_key), (1, 1)))
        return wanted

    def _draw_body(self, world):
        """The body (everything behind the head) as straight thick lines through the cell centres.

        Projecting caps and mitred corners make the line look exactly like adjacent squares.
        """
        g = world.settings.grid_size
        positions = world.get(Position)
        segments = sorted(world.get(SnakeSegment).items(), key=lambda kv: kv[1].index)
        cells = [(positions[e].x, positions[e].y) for e, _ in segments[1:]]
        color = world.theme.get("snake_body")
        if self.body_drawn == (cells, color):
            return
        self.body_drawn = (cells, color)

        runs, run = [], []
        for cell in cells:
            if run and abs(cell[0] - run[-1][0]) + abs(cell[1] - run[-1][1]) > g:   # wrapped
                runs.append(run)
                run = []
            run.append(cell)
        if run:
            runs.append(run)

        while len(self.body_lines) < len(runs):
            self.body_lines.append(self.canvas.create_line(0, 0, 0, 0, width=g,
                                                           capstyle="projecting", joinstyle="miter"))
        while len(self.body_lines) > len(runs):
            self.canvas.delete(self.body_lines.pop())
        for item, run in zip(self.body_lines, runs):
            if len(run) == 1:
                run = run + [(run[0][0] + 0.01, run[0][1])]     # a line needs two points
            # turtle and canvas share x; the canvas y axis points down
            self.canvas.coords(item, *[v for x, y in run for v in (x, -y)])
            self.canvas.itemconfigure(item, fill=color)

    def _overlay(self, world):
        """The pause overlay covers the whole window, even after the player resized it (+1 cell against gaps)."""
        screen = self.pens["overlay"].getscreen()
        g = world.settings.grid_size        # turtle's built-in square is one cell (20 px) big
        size = (screen.window_height() / g + 1, screen.window_width() / g + 1)
        positions = world.get(Position)
        return {("overlay", positions[e].x, positions[e].y): (layout.OVERLAY_COLOR, size)
                for e, r in world.get(RenderRequest).items() if r.kind == "overlay"}

def ui_render_system(world, pen):
    state = world.state.current
    pen.clear()

    labels = world.get(UILabel)
    states = world.get(UIStateTag)

    if state == GameState.TITLE:
        for label in labels.values():
            if label.text == "SNAKE":
                label.y = layout.TITLE_Y + math.sin(world.state.ms / 1200) * layout.TITLE_BOB

    text_color = world.theme.get("hud_text")
    for e, label in labels.items():
        if e not in states or states[e].state != state:
            continue
        pen.color(world.theme.get(label.color) if label.color else text_color)
        pen.goto(label.x, label.y)
        pen.write(label.text, align=label.align, font=label.font)
    pen.color(text_color)

    if state == GameState.NAME_ENTRY:
        for entry in world.get(NameEntry).values():
            show_cursor = (world.state.ms // (layout.CURSOR_BLINK_SECONDS * 1000)) % 2 == 0
            pen.goto(0, layout.NAME_PROMPT_Y)
            pen.write("ENTER YOUR INITIALS", align="center", font=layout.FONT_PROMPT)
            pen.goto(0, layout.NAME_TEXT_Y)
            pen.write(entry.text + ("_" if show_cursor else " "), align="center", font=layout.FONT_TEXT)

    countdown = next(iter(world.get(Countdown).values()), None)
    if state == GameState.PLAYING and countdown:
        pen.goto(0, layout.COUNTDOWN_Y)
        pen.color(world.theme.get("message"))
        pen.write(str(math.ceil(countdown.ms / countdown.step)), align="center", font=layout.FONT_COUNTDOWN)
        pen.color(world.theme.get("hud_text"))

    combo = next(iter(world.get(ComboCounter).values()), None)
    if state == GameState.PLAYING and combo and combo.value > 1:
        pen.goto(layout.COMBO_X, layout.HUD_Y)
        pen.color(world.theme.get("message"))
        pen.write(f"COMBO x{combo.value}", align="right", font=layout.FONT_TEXT)
        pen.color(world.theme.get("hud_text"))

def score_render_system(world, score_pen, score, best):
    """Arcade HUD: SCORE on the left, HI in the middle in its own colour.
    HI is the best score of this difficulty and climbs along live once you beat it.
    With custom walls the run doesn't count, so the middle says UNRANKED instead."""
    score_pen.clear()
    score_pen.color(world.theme.get("hud_text"))
    score_pen.goto(layout.SCORE_X, layout.HUD_Y)
    score_pen.write(f"SCORE {score}", align="left", font=layout.FONT_TEXT)
    score_pen.goto(0, layout.HUD_Y)
    score_pen.color(world.theme.get("message"))
    middle = f"HI {max(best, score)}" if world.settings.is_ranked() else "UNRANKED"
    score_pen.write(middle, align="center", font=layout.FONT_TEXT)

def countdown_system(world):
    """Count the 3-2-1 down. Returns True while it is still running (the snake waits)."""
    for e, countdown in list(world.get(Countdown).items()):
        countdown.ms -= world.settings.speed()
        if countdown.ms <= 0:
            world.remove_entity(e)
    return bool(world.get(Countdown))

def boundary_system(world):
    """Wrap or kill the snake at the edges. Returns True when the head left the field."""
    wrap = world.settings.get_wrap_mode()
    min_x, max_x, min_y, max_y = world.settings.bounds()
    positions = world.get(Position)

    for e in world.get(SnakeHead):
        pos = positions.get(e)

        if wrap:
            before = (pos.x, pos.y)
            if pos.x > max_x : pos.x = min_x
            elif pos.x < min_x : pos.x = max_x
            if pos.y > max_y : pos.y = min_y
            elif pos.y < min_y : pos.y = max_y
            if (pos.x, pos.y) != before:
                for rm in world.get(RunModifier).values():
                    rm.wraps += 1
        else:
            if pos.x > max_x or pos.x < min_x or pos.y > max_y or pos.y < min_y :
                return True

    return False

def compute_multiplier(world):
    mul = 1.0
    for rm in world.get(RunModifier).values():
        if rm.perfect:
            mul *= world.settings.perfect_multiplier()
    return mul

def scoring_system(world, scoring):
    scoring.set_multiplier(compute_multiplier(world))

    for e, event in list(world.get(ScoreEvent).items()):
        scoring.apply(event)
        world.remove_entity(e)

def combo_glow_system(world):
    glows = world.get(ComboGlow)

    for e, glow in list(glows.items()):
        glow.ms -= world.settings.speed()
        if glow.ms <= 0:
            world.remove_component(e, ComboGlow)

def combo_god(world):
    """COMBO GOD's bonuses for this difficulty once it is earned in this run, else None."""
    if any("COMBO_GOD" in rm.earned for rm in world.get(RunModifier).values()):
        return COMBO_GOD_PRESETS[world.settings.difficulty]
    return None

def combo_decay_system(world):
    god = combo_god(world)
    decay = god["decay_mul"] if god else 1
    for combo in world.get(ComboCounter).values():
        combo.timer -= world.settings.speed() * decay
        if combo.timer <= 0:
            combo.value = 1

def combo_window_system(world):
    window = world.settings.combo_window()
    god = combo_god(world)
    if god:
        window *= god["window_mul"]
    for combo in world.get(ComboCounter).values():
        combo.timer = window * 1000

#---------------ACHIEVEMENTS---------------
# Each check gets (world, run modifier, tick context) and returns True once its goal is met.

def _combo_god(world, rm, ctx):
    return ctx.combo is not None and ctx.combo.value >= COMBO_GOD_PRESETS[ctx.difficulty]["threshold"]

def _tiny_death(world, rm, ctx):
    return ctx.died and ctx.length <= world.settings.START_LENGTH

def _nervous(world, rm, ctx):
    return len(rm.pause_times) >= NERVOUS_PAUSES

def _insane_survivor(world, rm, ctx):
    return ctx.difficulty == "insane" and rm.play_ms >= INSANE_SURVIVOR_SECONDS * 1000

def _long_snake(world, rm, ctx):
    return ctx.length >= LENGTH_THRESHOLDS[ctx.difficulty]

def _perfect_run(world, rm, ctx):
    return ctx.died and rm.perfect and rm.foods_eaten >= PERFECT_RUN_MIN_FOOD

def _greedy(world, rm, ctx):
    return rm.golden_eaten >= GREEDY_GOLDEN

def _lucky_bite(world, rm, ctx):
    # golden food eaten while no combo was running
    return ctx.golden_hits > 0 and ctx.combo is not None and ctx.combo.timer <= 0

def _gold_rush(world, rm, ctx):
    return ctx.gold_rush

def _patience(world, rm, ctx):
    return ctx.patient_bite

def _marathon(world, rm, ctx):
    return rm.play_ms >= MARATHON_SECONDS * 1000

def _on_the_edge(world, rm, ctx):
    return ctx.edge_bite

def _speed_demon(world, rm, ctx):
    return world.settings.speed() <= world.settings.difficulty_config()["min_speed"]

def _on_fire(world, rm, ctx):
    return ctx.combo is not None and ctx.combo.value >= ON_FIRE_COMBO

def _tourist(world, rm, ctx):
    return rm.wraps >= TOURIST_WRAPS

def _quick_draw(world, rm, ctx):
    return ctx.quick_draw

def _high_roller(world, rm, ctx):
    return ctx.score >= HIGH_ROLLER_SCORE

def _snake_eyes(world, rm, ctx):
    return ctx.died and ctx.score % 100 == 11

ACHIEVEMENT_CHECKS = {"COMBO_GOD": _combo_god,
                      "TINY_DEATH": _tiny_death,
                      "NERVOUS": _nervous,
                      "INSANE_SURVIVOR": _insane_survivor,
                      "LONG_SNAKE": _long_snake,
                      "PERFECT_RUN": _perfect_run,
                      "GREEDY": _greedy,
                      "LUCKY_BITE": _lucky_bite,
                      "GOLD_RUSH": _gold_rush,
                      "PATIENCE": _patience,
                      "MARATHON": _marathon,
                      "ON_THE_EDGE": _on_the_edge,
                      "SPEED_DEMON": _speed_demon,
                      "ON_FIRE": _on_fire,
                      "TOURIST": _tourist,
                      "QUICK_DRAW": _quick_draw,
                      "HIGH_ROLLER": _high_roller,
                      "SNAKE_EYES": _snake_eyes}

def achievement_score(achievement_id, difficulty):
    """Points for an achievement; None if it gives no points or isn't offered on this difficulty."""
    score = ACHIEVEMENTS[achievement_id]["score"]
    return score.get(difficulty) if isinstance(score, dict) else score

def achievement_available(achievement_id, difficulty):
    score = ACHIEVEMENTS[achievement_id]["score"]
    return not isinstance(score, dict) or difficulty in score

def award_achievement(world, rm, achievement_id):
    rm.earned.add(achievement_id)
    points = achievement_score(achievement_id, world.settings.difficulty)
    if points:
        world.add_component(world.create_entity(), ScoreEvent(points))
    spawn_achievement_popup(world, achievement_id)

def achievement_system(world, score=0):
    """Award achievements. Must run before the tick's GameEvents are consumed,
    because several achievements look at FOOD_HIT and DEATH events. `score` is the run's score so far."""
    events = world.get(GameEvent).values()
    foods = world.get(Food)
    food_hits = [ev for ev in events if ev.kind == "FOOD_HIT" and ev.entity in foods]

    positions = world.get(Position)
    min_x, max_x, min_y, max_y = world.settings.bounds()

    ctx = SimpleNamespace(
        difficulty=world.settings.difficulty,
        died=any(ev.kind == "DEATH" for ev in events),
        golden_hits=sum(1 for ev in food_hits if foods[ev.entity].golden),
        edge_bite=any(positions[ev.entity].x in (min_x, max_x) or positions[ev.entity].y in (min_y, max_y)
                      for ev in food_hits),
        combo=next(iter(world.get(ComboCounter).values()), None),
        length=len(world.get(SnakeSegment)),
        score=score)

    tick_ms = world.settings.speed()
    for rm in world.get(RunModifier).values():
        rm.play_ms += tick_ms
        rm.ms_since_food += tick_ms
        # judged on the state before this bite
        ctx.gold_rush = ctx.golden_hits > 0 and rm.last_food_golden
        ctx.patient_bite = bool(food_hits) and rm.ms_since_food >= PATIENCE_SECONDS * 1000
        ctx.quick_draw = bool(food_hits) and rm.foods_eaten == 0 and rm.play_ms <= QUICK_DRAW_SECONDS * 1000

        rm.foods_eaten += len(food_hits)
        rm.golden_eaten += ctx.golden_hits
        if food_hits:
            rm.ms_since_food = 0
            rm.last_food_golden = ctx.golden_hits > 0

        for achievement_id, check in ACHIEVEMENT_CHECKS.items():
            if achievement_id in rm.earned or not achievement_available(achievement_id, ctx.difficulty):
                continue
            if check(world, rm, ctx):
                award_achievement(world, rm, achievement_id)

def achievement_popup_system(world):
    for e, popup in list(world.get(AchievementPopup).items()):
        popup.ms -= world.settings.speed()
        if popup.ms <= 0:
            world.remove_entity(e)


def game_over_system(world):
    """Return True when the run ends this tick: a DEATH, or BOARD_FULL (no room left for food).

    All pending GameEvents are cleared in that case so they don't
    linger into the next state.
    """
    events = world.get(GameEvent)
    if not any(event.kind in ("DEATH", "BOARD_FULL") for event in events.values()):
        return False

    for ev_entity in list(events.keys()):
        world.remove_entity(ev_entity)
    return True
