#ECS Factories

import random

from v1_1.config.AchievementConfig import ACHIEVEMENTS
from v1_1.audio.Audio import Audio
from v1_1.config.Themes import Themes
from v1_1.config.Settings import Settings
from v1_1.core.ecs.Components import Position, Collider, SnakeSegment, SnakeHead, SnakeTag, Food, FoodTag, Velocity, \
    RenderRequest, UIFade, Obstacle, AchievementPopup
from v1_1.core.Gamestate import Gamestate
from v1_1.core.ecs.UiComponents import UILabel, UIStateTag

DIFFICULTY_COLORS ={"easy" : None,
                    "normal" : "#FFD966",
                    "hard" : "#FF6B6B",
                    "insane" : "#B71C1C"}

def spawn_pause_ui(world):
    bg = world.create_entity()
    world.add_component(bg, Position(0,0))
    world.add_component(bg, RenderRequest(shape="square",
                                          color= "dim gray",
                                          kind="overlay"))
    world.add_component(bg, UIStateTag(Gamestate.PAUSED))

    e = world.create_entity()
    world.add_component(e, UILabel("Pause",0,0, font=("Arial",32,"bold")))
    world.add_component(e, UIStateTag(Gamestate.PAUSED))
    world.add_component(e, UIFade())

    e2 = world.create_entity()
    world.add_component(e2, UILabel("Press P to Resume", 0,-60, font=("Arial",12,"normal")))
    world.add_component(e2, UIStateTag(Gamestate.PAUSED))
    world.add_component(e2, UIFade())

def spawn_title_ui(world, difficulty, highscores):
    e = world.create_entity()
    world.add_component(e, UILabel("SNAKE", 0, 120, font=("Arial",32,"bold")))
    world.add_component(e, UIStateTag(Gamestate.TITLE))

    e2 = world.create_entity()
    world.add_component(e2, UILabel(f"Difficulty: {difficulty}",0,60))
    world.add_component(e2, UIStateTag(Gamestate.TITLE))

    e3 = world.create_entity()
    world.add_component(e3, UILabel(f"Theme: {Themes.current_name()}",0,-40))
    world.add_component(e3, UIStateTag(Gamestate.TITLE))

    controls = [
        "SPACE – Start Game",
        "← / → – Change Difficulty",
        "Arrow Keys – Movement in Game",
        "T – Change Theme (only on Title)",
        "M – Mute",
        "P – Pause (in Game)",
        "H - Highscore",
        "Q – Quit",
        "R – Restart(when dead)"]

    y = -80
    for line in controls:
        e = world.create_entity()
        world.add_component(e, UILabel(line, 0, y, font=("Arial", 12, "normal")))
        world.add_component(e, UIStateTag(Gamestate.TITLE))
        y -= 22

def spawn_highscores_ui(world, difficulty, scores):
    title = world.create_entity()
    world.add_component(title, UILabel(f"HIGHSCORES - {difficulty.upper()}",0,160,
                                       font = ("Arial", 24, "bold")))
    world.add_component(title, UIStateTag(Gamestate.HIGHSCORES))

    y = 100
    for i, (score,name) in enumerate(scores):
        e = world.create_entity()
        world.add_component(e, UILabel(
            f"{i+1}. {name} {score}",0,y ))
        world.add_component(e, UIStateTag(Gamestate.HIGHSCORES))
        y -= 30

    hint = world.create_entity()
    world.add_component(hint, UILabel("← / → Change Difficulty   B – Back", 0, -180, font=("Arial", 12, "normal")))
    world.add_component(hint, UIStateTag(Gamestate.HIGHSCORES))

def spawn_restart_ui(world):
    e = world.create_entity()
    world.add_component(e, UILabel("GAME OVER", 0,60, font=("Arial",28,"bold")))
    world.add_component(e, UIStateTag(Gamestate.RESTART_PROMPT))

    e2 = world.create_entity()
    world.add_component(e2, UILabel("Press R to Restart", 0,-20))
    world.add_component(e2, UIStateTag(Gamestate.RESTART_PROMPT))

    e3 = world.create_entity()
    world.add_component(e3, UILabel("Q - Quit", 0,-60))
    world.add_component(e3, UIStateTag(Gamestate.RESTART_PROMPT))

def spawn_name_entry_ui(world):
    e = world.create_entity()
    world.add_component(e, UILabel("ENTER YOUR NAME", 0, 40))
    world.add_component(e, UIStateTag(Gamestate.NAME_ENTRY))

def spawn_snake_ecs(world, positions, direction, offsets):
    dx, dy = offsets[direction]
    entities = []

    for i, (x, y) in enumerate(positions):
        e = world.create_entity()

        world.add_component(e, Position(x, y))
        world.add_component(e, SnakeTag())
        world.add_component(e, SnakeSegment(i))
        world.add_component(e, Collider(radius=10))

        if i == 0:
            world.add_component(e, SnakeHead())
            world.add_component(e, Velocity(dx, dy))

        # skin selection
        if i == 0:
            color = Themes.get("snake_head")
        else:
            color = Themes.get("snake_body")

        world.add_component(e, RenderRequest(shape="square",
                                             color=color,
                                             kind="snake"))
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
    world.add_component(new, SnakeTag())
    world.add_component(new, SnakeSegment(tail_seg.index + 1))
    world.add_component(new, Collider(radius=10))
    world.add_component(new, RenderRequest(shape="square",
                                           color=Themes.get("snake_body"),
                                           kind="snake"))

def spawn_food_ecs(world, grid_positions, golden_chance):
    positions = world.get(Position)
    snake_tiles = {(p.x, p.y) for p in positions.values()}

    free_tiles =[(x,y)
                 for x in grid_positions[0]
                 for y in grid_positions[1]
                 if (x,y) not in snake_tiles]

    x, y = random.choice(free_tiles)

    golden = random.random() < golden_chance

    e = world.create_entity()
    world.add_component(e, Position(x, y))
    world.add_component(e, Collider(radius=10))
    world.add_component(e, FoodTag())
    world.add_component(e, Food(golden=golden))
    base_color =Themes.get("food_gold" if golden else "food")
    world.add_component(e, RenderRequest(shape="circle",
                                         color=base_color,
                                         kind="food"))
    return e

def spawn_obstacles_ecs(world, obstacle_defs):
    positions = world.get(Position)
    occupied = {(p.x, p.y) for p in positions.values()}
    e = world.create_entity()

    for obs in obstacle_defs:
        (x,y) = obs["pos"]
        w,h = obs["size"]

        for dx in range(w):
            for dy in range(h):
                px = x + dx * Settings.grid_size
                py = y + dy * Settings.grid_size

                if (px, py) in occupied:
                    continue

                if Settings.difficulty == "insane":
                    world.add_component(e, Velocity(random.choice([20, -20]), 0))

                e = world.create_entity()
                world.add_component(e, Position(px, py))
                world.add_component(e, Collider(radius=10))
                world.add_component(e, Obstacle())
                world.add_component(e, RenderRequest(shape="square",
                                                     color=Themes.get("obstacle"),
                                                     kind="obstacle"))


def spawn_achievement_popup(world, achievement_id):
    cfg = ACHIEVEMENTS[achievement_id]

    Audio.play(cfg["sound"])

    index = max((p.index for p in world.get(AchievementPopup).values()), default =-1) + 1
    e = world.create_entity()
    world.add_component(e, AchievementPopup(achievement_id, index))
    world.add_component(e, UILabel(cfg["title"], 0, -160 + index * 26))
    world.add_component(e, UIFade())
    world.add_component(e, UIStateTag(Gamestate.PLAYING))