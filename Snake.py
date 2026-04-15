# Snake v1.1
#< Pingu>
# Status: unstable

import turtle

from v1_1.audio.Audio import Audio

from v1_1.config.AchievementConfig import FOODS, COMBO_GOD_PRESETS
from v1_1.config.Settings import Settings
from v1_1.config.Themes import Themes
from v1_1.config.Paths import HIGHSCORE_FILE

from v1_1.core.Gamestate import Gamestate, GameStateManager
from v1_1.core.Persistence import Persistence

from v1_1.core.ecs.Registry import World
from v1_1.core.ecs.Factories import spawn_snake_ecs, spawn_food_ecs, grow_snake_system, spawn_title_ui, spawn_pause_ui, \
    spawn_highscores_ui, spawn_obstacles_ecs, spawn_achievement_popup, spawn_restart_ui
from v1_1.core.ecs.Components import Food, SnakeHead, Velocity, NameEntry, ComboGlow, ComboCounter, GameEvent, \
    RenderRequest, RunModifier, Score, ScoreEvent, SnakeSegment
from v1_1.core.ecs.Systems import collision_system, movement_system, render_system, snake_follow_system, \
    boundary_system, cache_previous_positions, snap_to_grid_system, ui_render_system, combo_glow_system, facing_system, \
    ui_fade_system, combo_decay_system, score_render_system, \
    scoring_system, achievement_system, combo_window_system, achievement_popup_system, game_over_system
from v1_1.core.ecs.UiComponents import UIStateTag, UILabel

from v1_1.logic.Scoring import Scoring

from v1_1.util.Input_mgr import Input


#--------SCREEN SETUP--------
world = World()

screen = turtle.Screen()
screen.setup(width=800, height=600)
screen.bgcolor(Themes.get("bg"))
screen.title("Snake")
screen.tracer(0)
screen.listen()

#--------TURTLES(PENS)-------
snake_pen = turtle.Turtle(shape = "square")
snake_pen.color(Themes.get("snake"))
snake_pen.penup()
snake_pen.hideturtle()

food_turtle = turtle.Turtle(shape = "circle")
food_turtle.penup()
food_turtle.hideturtle()

score_pen = turtle.Turtle()
score_pen.hideturtle()
score_pen.penup()
score_pen.color(Themes.get("hud_text"))

ui_pen = turtle.Turtle()
ui_pen.hideturtle()
ui_pen.penup()
ui_pen.color(Themes.get("hud_text"))

overlay_pen = turtle.Turtle()
overlay_pen.hideturtle()
overlay_pen.penup()

#---------AUDIO-----------
Audio.init()
Audio.load_sfx("eat", "audio/assets/sounds/game/eat1.wav")
Audio.load_sfx("golden", "audio/assets/sounds/game/golden.wav")
Audio.load_sfx("death", "audio/assets/sounds/game/death1.wav")
Audio.load_sfx("pause", "audio/assets/sounds/ui/pause2.wav")
Audio.load_sfx("resume", "audio/assets/sounds/ui/resume2.wav")
Audio.load_sfx("highscore", "audio/assets/sounds/ui/hs2.wav")
Audio.load_sfx("achievement", "audio/assets/sounds/ui/achievement.wav")

#----------GAME DATA---------

scoring = Scoring(combo_window = Settings.combo_window())
high_scores = Persistence.load_high_scores(HIGHSCORE_FILE,
                                           difficulties = Settings.DIFFICULTY_PRESETS.keys(),
                                           limit = 5)

OFFSETS = {"up"  : (0,20),
           "down": (0,-20),
           "left" : (-20,0),
           "right" : (20,0)}

def name_entry_add_char(ch):
    entries = world.get(NameEntry)
    for entry in entries.values():
        if len(entry.text) < entry.max_len:
            entry.text += ch.upper()

def name_entry_backspace():
    entries = world.get(NameEntry)
    for entry in entries.values():
        entry.text = entry.text[:-1]

def name_entry_submit():
    entries = world.get(NameEntry)
    for entry in entries.values():
        high_scores[Settings.difficulty].append((scoring.score, entry.text or "PLAYER"))

    high_scores[Settings.difficulty] = sorted(high_scores[Settings.difficulty],
                                              key=lambda x: x[0],
                                              reverse=True)[:5]
    Persistence.save_high_scores(HIGHSCORE_FILE, high_scores)
    GameStateManager.set_state(Gamestate.RESTART_PROMPT)


def cycle_theme():
    Themes.next()
    for label in world.get(UILabel).values():
        if label.text.startswith("Theme:"):
            label.text = f"Theme: {Themes.current_name()}"

    Themes.apply(screen,{"snake" : snake_pen,
                                "food" : food_turtle,
                                "text" : ui_pen,
                                "hud" : score_pen})
    for r in world.get(RenderRequest).values():
        if r.kind == "snake":
            r.color = Themes.get("snake_body")
        elif r.kind == "food":
            food_comp = world.get(Food).get(e)
            r.color = Themes.get("food_gold" if food_comp and food_comp.golden else "food")
        elif r.kind == "obstacle":
            r.color = Themes.get("obstacle")
        elif r.kind == "overlay":
            r.color = "#000000"

    Audio.play_theme(Themes.music())
    snake_pen.clear()
    food_turtle.clear()
    screen.tracer(0)
    render_system(world, snake_pen, food_turtle, GameStateManager.current())
    ui_render_system(world, ui_pen, GameStateManager.current())
    snake_pen.color(Themes.get("snake_body"))
    food_turtle.color(Themes.get("food"))
    ui_pen.color(Themes.get("hud_text"))
    score_pen.color(Themes.get("hud_text"))
    screen.update()

Audio.play_theme(Themes.music())
input_mgr = Input(screen)


def set_snake_velocity(world, dx, dy):
    heads = world.get(SnakeHead)
    velocities = world.get(Velocity)

    for e in heads:
        vel = velocities[e]
        if (vel.dx != 0 and dx != 0 and vel.dx == -dx) or \
                (vel.dy != 0 and dy != 0 and vel.dy == -dy):
            continue
        vel.dx = dx
        vel.dy = dy

def turn_up():
    set_snake_velocity(world, 0, 20)

def turn_down():
    set_snake_velocity(world, 0, -20)

def turn_left():
    set_snake_velocity(world, -20, 0)

def turn_right():
    set_snake_velocity(world, 20, 0)

def next_difficulty():
    if GameStateManager.current() != Gamestate.TITLE:
        return
    diffs = Settings.difficulties()
    i = diffs.index(Settings.difficulty)
    Settings.set_difficulty(diffs[(i + 1) % len(diffs)])
    on_enter_title()
    GameStateManager.set_state(Gamestate.TITLE)

def prev_difficulty():
    if GameStateManager.current() != Gamestate.TITLE:
        return
    diffs = Settings.difficulties()
    i = diffs.index(Settings.difficulty)
    Settings.set_difficulty(diffs[(i - 1) % len(diffs)])
    on_enter_title()
    GameStateManager.set_state(Gamestate.TITLE)

def toggle_pause():
    if GameStateManager.current() == Gamestate.PLAYING:
        for rm in world.get(RunModifier).values():
            rm.pause_ticks.append(GameStateManager.ticks())
            rm.pause_ticks = [t for t in rm.pause_ticks
                              if GameStateManager.ticks() - t <= 600]
        Audio.play("pause")
        GameStateManager.set_state(Gamestate.PAUSED)
    elif GameStateManager.current() == Gamestate.PAUSED:
        Audio.play("resume")
        GameStateManager.set_state(Gamestate.PLAYING)

def start_game():
    reset_game()
    GameStateManager.set_state(Gamestate.PLAYING)

def on_focus_out(_=None):
    if GameStateManager.current() == Gamestate.PLAYING:
        GameStateManager.set_state(Gamestate.PAUSED)

screen.getcanvas().bind("<FocusOut>", on_focus_out)
screen.getcanvas().bind("<FocusIn>", lambda e: Audio.resume_theme())

def on_enter_title():
    _last_ui_tick = GameStateManager.ticks()

    world.entities.clear()
    world.components.clear()
    bind_inputs_for_state(Gamestate.TITLE)

    snake_pen.clear()
    snake_pen.clearstamps()
    snake_pen.hideturtle()

    food_turtle.clear()
    food_turtle.hideturtle()

    score_pen.clear()
    ui_pen.clear()

    spawn_title_ui(world, Settings.difficulty, high_scores[Settings.difficulty])
    render_system(world, snake_pen, food_turtle, Gamestate.TITLE)
    screen.update()

def on_enter_restart():
    spawn_restart_ui(world)

def on_enter_pause():
    spawn_pause_ui(world)

def on_exit_pause():
    for e, tag in world.get(UIStateTag).items():
        if tag.state == Gamestate.PAUSED:
            world.remove_entity(e)

GameStateManager.register_on_enter(Gamestate.TITLE, on_enter_title)
GameStateManager.register_on_enter(Gamestate.PAUSED, on_enter_pause)
GameStateManager.register_on_exit(Gamestate.PAUSED, on_exit_pause)
GameStateManager.register_on_enter(Gamestate.RESTART_PROMPT, on_enter_restart)

def bind_inputs_for_state(state):
    input_mgr.clear()

    if state == Gamestate.TITLE:
        input_mgr.bind("Left", prev_difficulty)
        input_mgr.bind("Right", next_difficulty)
        input_mgr.bind("space", start_game)
        input_mgr.bind("m", Audio.toggle_mute)
        input_mgr.bind("t", cycle_theme)
        input_mgr.bind("q", quit_game)
        input_mgr.bind("h", show_highscores)

    elif state == Gamestate.PLAYING:
        input_mgr.bind("Up", turn_up)
        input_mgr.bind("Down", turn_down)
        input_mgr.bind("Left", turn_left)
        input_mgr.bind("Right", turn_right)
        input_mgr.bind("p", toggle_pause)
        input_mgr.bind("m", Audio.toggle_mute)
        input_mgr.bind("q", quit_game)

    elif state == Gamestate.PAUSED:
        input_mgr.bind("p", toggle_pause)
        input_mgr.bind("m", Audio.toggle_mute)
        input_mgr.bind("q", quit_game)

    elif state == Gamestate.NAME_ENTRY:
        for c in "abcdefghijklmnopqrstuvwxyz":
            input_mgr.bind(c, lambda ch=c: name_entry_add_char(ch))
        input_mgr.bind("BackSpace", name_entry_backspace)
        input_mgr.bind("Return", name_entry_submit)

    elif state == Gamestate.HIGHSCORES:
        input_mgr.bind("Left", hs_prev_diff)
        input_mgr.bind("Right", hs_next_diff)
        input_mgr.bind("b", back_to_title)
        input_mgr.bind("m", Audio.toggle_mute)

    elif state == Gamestate.RESTART_PROMPT:
        input_mgr.bind("r", start_game)
        input_mgr.bind("q", quit_game)


    input_mgr.apply()

GameStateManager.register_on_enter(Gamestate.TITLE,
    lambda: bind_inputs_for_state(Gamestate.TITLE))
GameStateManager.register_on_enter(Gamestate.PLAYING,
    lambda: bind_inputs_for_state(Gamestate.PLAYING))
GameStateManager.register_on_enter(Gamestate.PAUSED,
    lambda: bind_inputs_for_state(Gamestate.PAUSED))
GameStateManager.register_on_enter(Gamestate.NAME_ENTRY,
    lambda: bind_inputs_for_state(Gamestate.NAME_ENTRY))
GameStateManager.register_on_enter(Gamestate.HIGHSCORES,
    lambda: bind_inputs_for_state(Gamestate.HIGHSCORES))
GameStateManager.register_on_enter(Gamestate.RESTART_PROMPT,
    lambda: bind_inputs_for_state(Gamestate.RESTART_PROMPT))

def trigger_death():
    Audio.play("death")

    for e, tag in list(world.get(UIStateTag).items()):
        if tag.state == Gamestate.PLAYING:
            world.remove_entity(e)

    score_e = world.create_entity()
    world.add_component(score_e, Score())

    e = world.create_entity()
    world.add_component(e, NameEntry())
    GameStateManager.set_state(Gamestate.NAME_ENTRY)
    bind_inputs_for_state(Gamestate.NAME_ENTRY)

def quit_game():
    screen.bye()

def reset_game():
    global scoring
    world.entities.clear()
    world.components.clear()
    scoring.reset()
    combo_entity = world.create_entity()
    world.add_component(combo_entity, ComboCounter())
    score_entity = world.create_entity()
    world.add_component(score_entity, Score())
    spawn_snake_ecs(world,
                    [(40, 0), (20, 0), (0, 0)],
                    "right",
                    OFFSETS)
    heads = world.get(SnakeHead)
    velocities = world.get(Velocity)
    for e in heads:
        velocities[e].dx = 20
        velocities[e].dy = 0

    spawn_food_ecs(world,
                   Settings.grid_positions(),
                   Settings.golden_chance())
    spawn_obstacles_ecs(world, Settings.obstacle_positions())
    run_mod = world.create_entity()
    world.add_component(run_mod, RunModifier())

def show_highscores():
    world.entities.clear()
    world.components.clear()
    spawn_highscores_ui(world, Settings.difficulty, high_scores[Settings.difficulty])
    GameStateManager.set_state(Gamestate.HIGHSCORES)

def hs_next_diff():
    diffs = Settings.difficulties()
    i = diffs.index(Settings.difficulty)
    Settings.set_difficulty(diffs[(i + 1) % len(diffs)])
    show_highscores()

def hs_prev_diff():
    diffs = Settings.difficulties()
    i = diffs.index(Settings.difficulty)
    Settings.set_difficulty(diffs[(i - 1) % len(diffs)])
    show_highscores()

def back_to_title():
    world.entities.clear()
    world.components.clear()
    spawn_title_ui(world,Settings.difficulty, high_scores[Settings.difficulty])
    GameStateManager.set_state(Gamestate.TITLE)

#----------MAIN LOOP---------
def game_tick():
    GameStateManager.tick()
    state = GameStateManager.current()

    if state in (Gamestate.NAME_ENTRY, Gamestate.HIGHSCORES):
        render_system(world, snake_pen, food_turtle, state)
        ui_render_system(world, ui_pen, state)
        screen.update()
        screen.ontimer(game_tick, Settings.speed())
        return

    if state == Gamestate.TITLE:
        pass

    if state == Gamestate.PLAYING:
        cache_previous_positions(world)
        facing_system(world)
        movement_system(world)
        snake_follow_system(world)
        snap_to_grid_system(world)
        combo_glow_system(world)
        combo_decay_system(world)

        wrap = Settings.get_wrap_mode()
        if boundary_system(world, wrap=wrap):
            trigger_death()
            return

        collision_system(world)
        game_over_system(world)

        if GameStateManager.current() == Gamestate.GAME_OVER:
            return

        events = world.get(GameEvent)
        for e, event in list(events.items()):

            if event.kind == "FOOD_HIT":
                food = world.get(Food).get(event.entity)
                if not food:
                    continue
                Audio.play("golden" if food.golden else "eat")

                base = FOODS["golden"] if food.golden else FOODS["normal"]
                value = base

                for rm in world.get(RunModifier).values():
                    if rm.combo_god and food.golden:
                        value = int(base * (1 + COMBO_GOD_PRESETS[Settings.difficulty]["gold_bonus"]))

                world.add_component(world.create_entity(),
                                    ScoreEvent("FOOD", value))

                combos = world.get(ComboCounter)
                if combos:
                    combo = next(iter(combos.values()))
                    combo.value += 1
                    combo_window_system(world)
                    scoring.set_combo(combo.value)
                    head = next(iter(world.get(SnakeHead)))
                world.add_component(head, ComboGlow(8))

                world.remove_entity(event.entity)
                grow_snake_system(world)

                spawn_food_ecs(world, Settings.grid_positions(), Settings.golden_chance())
                break
            world.remove_entity(e)

        scoring_system(world, scoring)
        achievement_system(world)
        achievement_popup_system(world)
        score_render_system(world, score_pen)

    elif state == Gamestate.GAME_OVER:
        trigger_death()
        return

    elif state == Gamestate.PAUSED:
        pass

    render_system(world, snake_pen, food_turtle, state)
    ui_fade_system(world, state)
    ui_render_system(world, ui_pen, state)
    screen.update()
    screen.ontimer(game_tick, Settings.speed())

#------------BOOT------------
GameStateManager.set_state(Gamestate.TITLE)
bind_inputs_for_state(Gamestate.TITLE)
on_enter_title()
game_tick()
screen.mainloop()
