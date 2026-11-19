#ECS Factories

import random

from v1_1.config import layout
from v1_1.config.achievement_config import ACHIEVEMENTS, POPUP_SECONDS
from v1_1.core.ecs.components import Position, SnakeSegment, SnakeHead, Food, Velocity, \
    RenderRequest, Obstacle, AchievementPopup, TurnBuffer, ObstacleMover
from v1_1.core.game_state import GameState
from v1_1.core.ecs.ui_components import UILabel, UIStateTag


def spawn_label(world, state, text, x, y, font=layout.FONT_TEXT, align="center", color=None):
    e = world.create_entity()
    world.add_component(e, UILabel(text, x, y, align=align, font=font, color=color))
    world.add_component(e, UIStateTag(state))
    return e

def spawn_pause_ui(world):
    bg = world.create_entity()
    world.add_component(bg, Position(0,0))
    world.add_component(bg, RenderRequest(color_key=None, kind="overlay"))
    world.add_component(bg, UIStateTag(GameState.PAUSED))

    spawn_label(world, GameState.PAUSED, "Pause", 0, layout.PAUSE_Y, layout.FONT_TITLE)
    spawn_label(world, GameState.PAUSED, "Press P or Esc to Resume", 0, layout.PAUSE_HINT_Y, layout.FONT_SMALL)

def spawn_title_ui(world):
    state = GameState.TITLE
    spawn_label(world, state, "SNAKE", 0, layout.TITLE_Y, layout.FONT_TITLE)
    spawn_label(world, state, f"Difficulty: {world.settings.difficulty}", 0, layout.DIFFICULTY_Y)
    spawn_label(world, state, f"Theme: {world.theme.current_name()}", 0, layout.THEME_Y)
    if not world.settings.is_ranked():
        spawn_label(world, state, "UNRANKED (custom walls)", 0, layout.UNRANKED_Y, layout.FONT_SMALL, color="message")

    controls = [
        "SPACE – Start Game",
        "← / → – Difficulty     T – Theme",
        "S – Settings     H – Highscores",
        "Arrow Keys – Move     P / Esc – Pause",
        "M – Mute     Q – Quit",
        "R – Restart / B – Title (when dead)"]

    y = layout.CONTROLS_Y
    for line in controls:
        spawn_label(world, state, line, 0, y, layout.FONT_SMALL)
        y -= layout.CONTROLS_STEP

def spawn_highscores_ui(world, scores):
    state = GameState.HIGHSCORES
    spawn_label(world, state, f"HIGHSCORES - {world.settings.difficulty.upper()}", 0,
                layout.HIGHSCORES_TITLE_Y, layout.FONT_HEADING)

    y = layout.HIGHSCORES_FIRST_Y
    for i, (score, name) in enumerate(scores):
        spawn_label(world, state, f"{i+1}. {name} {score}", 0, y)
        y -= layout.HIGHSCORES_STEP

    spawn_label(world, state, "← / → Change Difficulty   B – Back", 0, layout.HIGHSCORES_HINT_Y, layout.FONT_SMALL)

def spawn_settings_ui(world, entries, selected):
    """entries: [(label, value text), ...]; the selected row is highlighted and shows ◄ ►."""
    state = GameState.SETTINGS
    spawn_label(world, state, "SETTINGS", 0, layout.SETTINGS_TITLE_Y, layout.FONT_HEADING)

    y = layout.SETTINGS_FIRST_Y
    for i, (label, value) in enumerate(entries):
        active = i == selected
        color = "message" if active else None
        spawn_label(world, state, ("► " if active else "   ") + label, layout.SETTINGS_LABEL_X, y,
                    align="left", color=color)
        spawn_label(world, state, f"◄ {value} ►" if active else value, layout.SETTINGS_VALUE_X, y,
                    align="right", color=color)
        y -= layout.SETTINGS_STEP

    spawn_label(world, state, "↑ / ↓ Select     ← / → Change     B – Back", 0, layout.SETTINGS_HINT_Y,
                layout.FONT_SMALL)

def spawn_restart_ui(world, score=0, length=0, earned=(), new_best=False):
    """GAME OVER with the run's summary: score, length and the achievements earned this run."""
    state = GameState.RESTART_PROMPT
    spawn_label(world, state, "GAME OVER", 0, layout.GAME_OVER_Y, layout.FONT_GAME_OVER)
    spawn_label(world, state, f"Score {score}     Length {length}" + ("     NEW BEST!" if new_best else ""),
                0, layout.GAME_OVER_STATS_Y, color="message" if new_best else None)

    max_rows = (layout.GAME_OVER_LIST_Y - layout.GAME_OVER_FIRST_HINT_Y) // layout.GAME_OVER_LIST_STEP - 1
    titles = [ACHIEVEMENTS[a]["title"] for a in earned]
    if len(titles) > max_rows:
        titles = titles[:max_rows - 1] + [f"+ {len(titles) - max_rows + 1} more"]
    y = layout.GAME_OVER_LIST_Y
    for title in titles:
        spawn_label(world, state, title, 0, y, layout.FONT_SMALL, color="message")
        y -= layout.GAME_OVER_LIST_STEP

    y = layout.GAME_OVER_FIRST_HINT_Y
    for hint in ("Press R to Restart", "B - Back to Title", "Q - Quit"):
        spawn_label(world, state, hint, 0, y)
        y -= layout.GAME_OVER_HINT_STEP

def spawn_snake_ecs(world, positions, direction):
    dx, dy = world.settings.direction_offsets()[direction]
    entities = []

    for i, (x, y) in enumerate(positions):
        e = world.create_entity()

        world.add_component(e, Position(x, y))
        world.add_component(e, SnakeSegment(i))

        if i == 0:
            world.add_component(e, SnakeHead())
            world.add_component(e, Velocity(dx, dy))
            world.add_component(e, TurnBuffer())

        if i == 0:              # the body is drawn as a line, see BoardRenderer
            world.add_component(e, RenderRequest(color_key="snake_head", kind="snake"))
        entities.append(e)

    return entities

def grow_snake_system(world):
    positions = world.get(Position)
    segments = world.get(SnakeSegment)

    tail = max(segments.items(), key=lambda x: x[1].index)
    tail_entity, tail_seg = tail
    tail_pos = positions[tail_entity]

    new = world.create_entity()
    world.add_component(new, Position(tail_pos.x, tail_pos.y))
    world.add_component(new, SnakeSegment(tail_seg.index + 1))

def spawn_food_ecs(world):
    """Spawn food on a random free tile. Returns None when the board is full."""
    xs, ys = world.settings.grid_positions()
    occupied = {(p.x, p.y) for p in world.get(Position).values()}

    free_tiles =[(x,y)
                 for x in xs
                 for y in ys
                 if (x,y) not in occupied]
    if not free_tiles:
        return None

    x, y = random.choice(free_tiles)

    golden = random.random() < world.settings.golden_chance()

    e = world.create_entity()
    world.add_component(e, Position(x, y))
    world.add_component(e, Food(golden=golden))
    world.add_component(e, RenderRequest(color_key="food_gold" if golden else "food", kind="food"))
    return e

def spawn_obstacles_ecs(world):
    settings = world.settings
    occupied = {(p.x, p.y) for p in world.get(Position).values()}

    for cells in settings.obstacle_blocks():
        # One mover per block: every cell shares it, so the block never tears apart
        mover = None
        if settings.moving_obstacles():
            mover = ObstacleMover(random.choice([settings.grid_size, -settings.grid_size]))

        for px, py in cells:
            if (px, py) in occupied:
                continue

            e = world.create_entity()
            world.add_component(e, Position(px, py))
            world.add_component(e, Obstacle())
            world.add_component(e, RenderRequest(color_key="obstacle", kind="obstacle"))
            if mover:
                world.add_component(e, mover)


def spawn_achievement_popup(world, achievement_id):
    cfg = ACHIEVEMENTS[achievement_id]

    world.audio.play("achievement")

    index = max((p.index for p in world.get(AchievementPopup).values()), default =-1) + 1
    e = spawn_label(world, GameState.PLAYING, cfg["title"], 0, layout.POPUP_Y + index * layout.POPUP_STEP)
    world.add_component(e, AchievementPopup(index, POPUP_SECONDS * 1000))
