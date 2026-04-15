#ECS Systems

import math

from v1_1.config.AchievementConfig import COMBO_GOD_PRESETS, LENGTH_THRESHOLDS, ACHIEVEMENTS
from v1_1.config.Settings import Settings
from v1_1.config.Themes import Themes
from v1_1.core.Gamestate import Gamestate, GameStateManager
from v1_1.core.ecs.Components import Position, Collider, FoodTag, SnakeHead, SnakeSegment, \
    PreviousPosition, Velocity, Facing, RenderRequest, NameEntry, ComboGlow, UIFade, ComboCounter, \
    Obstacle, GameEvent, AchievementPopup, RunModifier, ScoreEvent, Score, Food
from v1_1.core.ecs.Factories import spawn_achievement_popup
from v1_1.core.ecs.UiComponents import UILabel, UIStateTag




def cache_previous_positions(world):
    positions = world.get(Position)
    prev = world.get(PreviousPosition)

    for e,pos in positions.items():
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

def movement_system(world):
    positions = world.get(Position)
    velocities = world.get(Velocity)

    speed_mul = 1.0
    if Settings.difficulty == "insane":
        speed_mul = 1.25

    for e, vel in velocities.items():
        pos = positions.get(e)
        if pos:
            pos.x += int(vel.dx * speed_mul)
            pos.y += int(vel.dy * speed_mul)

def facing_system(world):
    velocities = world.get(Velocity)
    facings =world.get(Facing)

    for e, vel in velocities.items():
        facing = facings.get(e)
        if not facing:
            continue

        if vel.dx > 0 : facing.angle = 0
        elif vel.dy > 0 : facing.angle = 90
        elif vel.dx < 0 : facing.angle = 180
        elif vel.dy < 0 : facing.angle = 270


def collision_system(world):
    positions = world.get(Position)
    colliders = world.get(Collider)
    foods = world.get(FoodTag)
    heads = world.get(SnakeHead)
    segments = world.get(SnakeSegment)
    obstacles = world.get(Obstacle)

    self_hit = False
    obstacle_hit = False

    for head in heads:
        h_pos = positions[head]
        h_col = colliders[head]

        #-------Food--------
        for food_entity in foods:
            f_pos = positions[food_entity]

            dx = h_pos.x - f_pos.x
            dy = h_pos.y - f_pos.y

            if abs(dx) < Settings.grid_size / 2 and abs(dy) < Settings.grid_size / 2:
                world.add_component(world.create_entity(),
                                    GameEvent("FOOD_HIT", food_entity))

        #--------Self--------
        for entity, seg in segments.items():
            if entity == head or seg.index <= 1:
                continue

            s_pos = positions[entity]

            dx = h_pos.x - s_pos.x
            dy = h_pos.y - s_pos.y

            if abs(dx) < Settings.grid_size and abs(dy) < Settings.grid_size:
                self_hit = True
                world.add_component(world.create_entity(),
                                    GameEvent("DEATH", head))

        #------Obstacle-----
        for obs in obstacles:
            o_pos = positions[obs]
            o_col = colliders[obs]

            dx = h_pos.x - o_pos.x
            dy = h_pos.y - o_pos.y

            if abs(dx) < Settings.grid_size and abs(dy) < Settings.grid_size:
                obstacle_hit = True
                world.add_component(world.create_entity(),
                                    GameEvent("DEATH", head))

    #--------Perfect Run--------
    if obstacle_hit or self_hit:
        for rm in world.get(RunModifier).values():
            rm.perfect = False

def render_system(world, snake_pen, food_turtle, state):
    if state not in (Gamestate.PLAYING, Gamestate.PAUSED):
        return

    renders = world.get(RenderRequest)
    positions = world.get(Position)
    facings = world.get(Facing)
    glows = world.get(ComboGlow)

    snake_pen.clear()
    snake_pen.clearstamps()
    snake_pen.penup()
    snake_pen.showturtle()

    # food pulse
    food_pulse = 1 + math.sin(GameStateManager.ticks() / 6) * 0.1
    food_turtle.shapesize(food_pulse, food_pulse)

    for e, r in renders.items():
        pos = positions[e]

        # ---------- SNAKE ----------
        if r.kind == "snake":
            if e in facings:
                snake_pen.setheading(facings[e].angle)

            # combo glow
            if e in glows:
                glow = glows[e]
                strength = glow.ticks / glow.max_ticks
                pulse = 1 + math.sin(glow.ticks / 3) * 0.15 * strength
                snake_pen.shapesize(pulse, pulse)

                color = (Themes.get("combo_glow_strong")
                    if strength > 0.6
                    else Themes.get("combo_glow"))
                snake_pen.color(color)
            else:
                snake_pen.shapesize(1, 1)
                snake_pen.color(r.color)

            snake_pen.goto(pos.x, pos.y)
            snake_pen.stamp()

        # ---------- FOOD ----------
        elif r.kind == "food":
            food_turtle.goto(pos.x, pos.y)
            food_turtle.color(r.color)
            food_turtle.showturtle()

        # ----------Obstacles--------
        elif r.kind == "obstacle":
            snake_pen.goto(pos.x, pos.y)
            snake_pen.color(r.color)
            snake_pen.shapesize(1, 1)
            snake_pen.stamp()

        #----------Pause Overlay-------
        elif r.kind == "overlay":
            overlay_pen.penup()
            overlay_pen.goto(pos.x, pos.y)
            overlay_pen.color("dim gray")
            overlay_pen.shapesize(40,30)
            overlay_pen.stamp()
            overlay_pen.shapesize(1, 1)

def ui_render_system(world, pen, state):
    pen.clear()
    pen.hideturtle()
    pen.penup()

    labels = world.get(UILabel)
    states = world.get(UIStateTag)

    for e, label in labels.items():
        if e not in states or states[e].state != state:
            continue

        if label.alpha < 1.0:
            label.alpha = min(1.0, label.alpha + label.fade_speed)

        pen.goto(label.x, label.y)
        pen.write(label.text, align=label.align, font=label.font)

    if state == Gamestate.NAME_ENTRY:
        entries = world.get(NameEntry)
        for entry in entries.values():
            entry.blink_timer += 1
            show_cursor = (entry.blink_timer // 20) % 2 == 0
            pen.goto(0, 40)
            pen.write("ENTER YOUR NAME", align="center", font=("Arial", 18, "bold"))
            pen.goto(0, 0)
            pen.write(entry.text + ("_" if show_cursor else " "),
                      align="center",
                      font=("Arial", 16, "normal"))

    if state == Gamestate.TITLE:
        for label in labels.values():
            if label.text == "SNAKE":
                label.y = 120 + math.sin(GameStateManager.ticks() / 10) * 6

    combos = world.get(ComboCounter)
    if combos:
        combo = next(iter(combos.values())).value
        if combo > 1:
            pen.goto(0, 230)
            pen.color(Themes.get("message"))
            pen.write(f"COMBO x{combo}", align="center", font=("Arial", 12, "normal"))

def score_render_system(world, score_pen):
    score = next(iter(world.get(Score).values())).value
    score_pen.clear()
    score_pen.goto(0,260)
    score_pen.write(f"Score: {score}",
                    align="center",
                    font=("Arial", 16, "normal"))

def boundary_system(world, wrap = True):
    min_x, max_x, min_y, max_y = Settings.bounds()
    positions = world.get(Position)

    for e in world.get(SnakeHead):
        pos = positions.get(e)

        if wrap:
            if pos.x > max_x : pos.x = min_x
            elif pos.x < min_x : pos.x = max_x
            if pos.y > max_y : pos.y = min_y
            elif pos.y < min_y : pos.y = max_y
        else:
            if pos.x > max_x or pos.x < min_x or pos.y > max_y or pos.y < min_y :
                return True

    for e in world.get(Obstacle):
        pos = positions[e]
        if pos.x > max_x or pos.x < min_x:
            world.remove_entity(e)

    return False

def snap_to_grid_system(world, grid_size = 20):
    positions = world.get(Position)
    heads = world.get(SnakeHead)

    for e in heads:
        pos = positions[e]
        pos.x = round(pos.x / grid_size) * grid_size
        pos.y = round(pos.y / grid_size) * grid_size

def compute_multiplier(world):
    mul = 1.0
    for rm in world.get(RunModifier).values():
        if rm.perfect:
            mul *= Settings.perfect_multiplier()
    return mul

def scoring_system(world, scoring):
    score_comp = next(iter(world.get(Score).values()), None)

    scoring.set_multiplier(compute_multiplier(world))

    for e, event in list(world.get(ScoreEvent).items()):
        scoring.apply(event)

        if score_comp:
            score_comp.value = scoring.score

        world.remove_entity(e)

def combo_glow_system(world):
    glows = world.get(ComboGlow)

    for e, glow in list(glows.items()):
        glow.ticks -= 1
        if glow.ticks <= 0:
            world.remove_component(e, ComboGlow)

def combo_decay_system(world):
    combos = world.get(ComboCounter)
    mods = world.get(RunModifier)
    for combo in combos.values():
        decay = 1
        for rm in mods.values():
            if rm.combo_god:
                decay  *= COMBO_GOD_PRESETS[Settings.difficulty]["decay_mul"]

        combo.timer -= decay
        if combo.timer <= 0:
            combo.value = 1

def combo_window_system(world):
    combos = world.get(ComboCounter)
    mods = world.get(RunModifier)
    for combo in combos.values():
        window = Settings.combo_window()
        for rm in mods.values():
            if rm.combo_god:
                window *= COMBO_GOD_PRESETS[Settings.difficulty]["window_mul"]
            combo.timer = int(window * 60)

def ui_fade_system(world, state):
    fades = world.get(UIFade)
    labels = world.get(UILabel)
    states = world.get(UIStateTag)

    for e, fade in fades.items():
        if e not in states or e not in labels:
            continue

        if states[e].state != state:
            continue

        fade.alpha = min(1.0, fade.alpha + fade.fade_speed)
        labels[e].alpha = fade.alpha

def achievement_system(world):
    mods = world.get(RunModifier)
    combos = world.get(ComboCounter)
    segments = world.get(SnakeSegment)
    events = world.get(GameEvent)

    for rm in mods.values():
        difficulty = Settings.difficulty
        # ---- COMBO GOD ----
        if combos:
            combo = next(iter(combos.values()))
            preset = COMBO_GOD_PRESETS[Settings.difficulty]

            if combo.value >= preset["threshold"] and not rm.combo_god:
                rm.combo_god = True
                spawn_achievement_popup(world, "COMBO_GOD")

        # ---- DIE AT LENGTH 1 ----
        score_cfg = ACHIEVEMENTS["TINY_DEATH"]["score"]
        value = score_cfg.get(difficulty)
        for _, event in events.items():
            if event.kind == "DEATH" and len(segments) == 1 and not rm.tiny_death:
                rm.tiny_death = True
                if value:
                    world.add_component(world.create_entity(),
                                        ScoreEvent("TINY_DEATH", value))
                    spawn_achievement_popup(world, "TINY_DEATH")
                    break

        # ---- PAUSE SPAM ----
        if len(rm.pause_ticks) >= 10 and not rm.nervous:
            rm.nervous = True
            world.add_component(world.create_entity(),
                                ScoreEvent("NERVOUS",
                                           ACHIEVEMENTS["NERVOUS"]["score"]))
            spawn_achievement_popup(world, "NERVOUS")

        #------Insane Survivor----
        if difficulty == "insane":
            if GameStateManager.current() == Gamestate.PLAYING:
                rm.insane_ticks += 1
                if rm.insane_ticks >= 3600 and not rm.insane_survivor:
                    rm.insane_survivor = True
                    world.add_component(world.create_entity(),
                                        ScoreEvent("INSANE_SURVIVOR",
                                                    ACHIEVEMENTS["INSANE_SURVIVOR"]["score"]))
                    spawn_achievement_popup(world, "INSANE_SURVIVOR")

        #------Snake Length------
        if len(segments) >= LENGTH_THRESHOLDS[difficulty] and not rm.long_snake:
            rm.long_snake = True
            world.add_component(world.create_entity(),
                                ScoreEvent("LONG_SNAKE",
                                           ACHIEVEMENTS["LONG_SNAKE"]["score"]))
            spawn_achievement_popup(world, "LONG_SNAKE")

        #------Perfect Run-----
        for e, event in events.items():
            if event.kind == "DEATH" and rm.perfect and not rm.perfect_awarded:
                rm.perfect_awarded = True
                spawn_achievement_popup(world, "PERFECT_RUN")

        #-------Greedy------
        for e, event in events.items():
            if event.kind == "FOOD_HIT":
                food = world.get(Food).get(event.entity)
                if not food:
                    continue
                if food and food.golden:
                    rm.golden_eaten += 1
                    if rm.golden_eaten >= 5 and not rm.greedy:
                        rm.greedy = True
                        world.add_component(world.create_entity(),
                                            ScoreEvent("GREEDY",
                                                       ACHIEVEMENTS["GREEDY"]["score"]))
                        spawn_achievement_popup(world, "GREEDY")

        #------Lucky Bite-----
        for e, event in events.items():
            if event.kind == "FOOD_HIT":
                food = world.get(Food).get(event.entity)
                if not food or not food.golden:
                    continue

                combos = world.get(ComboCounter)
                combo = next(iter(combos.values()), None)
                if combo and combo.value == 1 and not rm.lucky_bite:
                    rm.lucky_bite = True
                    world.add_component(world.create_entity(),
                                        ScoreEvent("LUCKY_BITE",
                                                   ACHIEVEMENTS["LUCKY_BITE"]["score"]))
                    spawn_achievement_popup(world, "LUCKY_BITE")
                    break
def achievement_popup_system(world):
    popups = list(world.get(AchievementPopup).items())
    for e, popup in popups :
        popup.ticks -= 1
        if popup.ticks <= 0:
            world.remove_entity(e)


def game_over_system(world):
    """Transition to GAME_OVER when a DEATH event is present in the world.

    Called once per tick while in PLAYING state.  If any GameEvent with
    kind == "DEATH" exists, the state machine is advanced to GAME_OVER and
    all pending GameEvents are cleared so they don't linger into the next state.
    """
    events = world.get(GameEvent)
    for e, event in list(events.items()):
        if event.kind == "DEATH":
            GameStateManager.set_state(Gamestate.GAME_OVER)
            # Remove all game events so they don't bleed into the next state
            for ev_entity in list(events.keys()):
                world.remove_entity(ev_entity)
            return
