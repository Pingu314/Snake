# Snake v1.1
#< Pingu>
# Status: unstable

import string
import turtle

from v1_1.audio.audio import Audio

from v1_1.config.achievement_config import FOODS, COMBO_GOD_PRESETS
from v1_1.config.settings import Settings
from v1_1.config.themes import Themes
from v1_1.config.paths import HIGHSCORE_FILE

from v1_1.core.game_state import GameState, GameStateManager
from v1_1.core.persistence import Persistence

from v1_1.core.ecs.registry import World
from v1_1.core.ecs.factories import spawn_snake_ecs, spawn_food_ecs, grow_snake_system, spawn_title_ui, \
    spawn_pause_ui, spawn_highscores_ui, spawn_obstacles_ecs, spawn_restart_ui
from v1_1.core.ecs.components import Food, SnakeHead, Velocity, NameEntry, ComboGlow, ComboCounter, GameEvent, \
    RenderRequest, RunModifier, Score, ScoreEvent
from v1_1.core.ecs.systems import collision_system, movement_system, render_system, snake_follow_system, \
    boundary_system, cache_previous_positions, snap_to_grid_system, ui_render_system, combo_glow_system, \
    facing_system, ui_fade_system, combo_decay_system, score_render_system, scoring_system, achievement_system, \
    combo_window_system, achievement_popup_system, game_over_system
from v1_1.core.ecs.ui_components import UIStateTag, UILabel

from v1_1.logic.scoring import Scoring

from v1_1.util.input_manager import InputManager


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PAUSE_SPAM_WINDOW = 600   # ticks; pauses inside this window count towards NERVOUS?!

SFX = {"eat": "audio/assets/sounds/game/eat1.wav",
       "golden": "audio/assets/sounds/game/golden.wav",
       "death": "audio/assets/sounds/game/death1.wav",
       "pause": "audio/assets/sounds/ui/pause2.wav",
       "resume": "audio/assets/sounds/ui/resume2.wav",
       "highscore": "audio/assets/sounds/ui/hs2.wav",
       "achievement": "audio/assets/sounds/ui/achievement.wav"}


def make_pen(shape="classic", color=None):
    pen = turtle.Turtle(shape=shape)
    pen.hideturtle()
    pen.penup()
    if color:
        pen.color(color)
    return pen


class Game:
    def __init__(self):
        self.world = World()

        #--------SCREEN SETUP--------
        self.screen = turtle.Screen()
        self.screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.screen.bgcolor(Themes.get("bg"))
        self.screen.title("Snake")
        self.screen.tracer(0)
        self.screen.listen()

        #--------TURTLES(PENS)-------
        self.snake_pen = make_pen("square", Themes.get("snake"))
        self.food_turtle = make_pen("circle")
        self.score_pen = make_pen(color=Themes.get("hud_text"))
        self.ui_pen = make_pen(color=Themes.get("hud_text"))
        self.overlay_pen = make_pen("square")
        self.pens = {"snake": self.snake_pen,
                     "food": self.food_turtle,
                     "overlay": self.overlay_pen}

        #---------AUDIO-----------
        Audio.init()
        for name, path in SFX.items():
            Audio.load_sfx(name, path)
        Audio.play_theme(Themes.music())

        #----------GAME DATA---------
        self.scoring = Scoring()
        self.high_scores = Persistence.load_high_scores(HIGHSCORE_FILE,
                                                        difficulties=Settings.difficulties(),
                                                        limit=Settings.HIGHSCORE_LIMIT)
        self.input = InputManager(self.screen)

        canvas = self.screen.getcanvas()
        canvas.bind("<FocusOut>", self.on_focus_out)
        canvas.bind("<FocusIn>", lambda _: Audio.resume_theme())

        self._register_state_hooks()

    #----------STATE HOOKS---------
    def _register_state_hooks(self):
        GameStateManager.register_on_enter(GameState.TITLE, self.on_enter_title)
        GameStateManager.register_on_enter(GameState.PAUSED, self.on_enter_pause)
        GameStateManager.register_on_exit(GameState.PAUSED, self.on_exit_pause)
        GameStateManager.register_on_enter(GameState.RESTART_PROMPT, self.on_enter_restart)

        # Every state swaps in its own key bindings when entered
        for state in GameState:
            GameStateManager.register_on_enter(state, lambda s=state: self.bind_inputs_for_state(s))

    def on_enter_title(self):
        self.world.clear()

        self.snake_pen.clear()
        self.snake_pen.clearstamps()
        self.snake_pen.hideturtle()
        self.food_turtle.clear()
        self.food_turtle.hideturtle()
        self.score_pen.clear()
        self.ui_pen.clear()

        spawn_title_ui(self.world, Settings.difficulty)
        self.screen.update()

    def on_enter_pause(self):
        spawn_pause_ui(self.world)

    def on_exit_pause(self):
        self._remove_ui_for(GameState.PAUSED)

    def on_enter_restart(self):
        spawn_restart_ui(self.world)

    def on_focus_out(self, _=None):
        if GameStateManager.current() == GameState.PLAYING:
            GameStateManager.set_state(GameState.PAUSED)

    def _remove_ui_for(self, state):
        for e, tag in list(self.world.get(UIStateTag).items()):
            if tag.state == state:
                self.world.remove_entity(e)

    #----------INPUT---------
    def bind_inputs_for_state(self, state):
        bindings = {
            GameState.TITLE: {"Left": lambda: self.change_title_difficulty(-1),
                              "Right": lambda: self.change_title_difficulty(1),
                              "space": self.start_game,
                              "m": Audio.toggle_mute,
                              "t": self.cycle_theme,
                              "q": self.quit_game,
                              "h": self.show_highscores},
            GameState.PLAYING: {"Up": lambda: self.turn(0, 1),
                                "Down": lambda: self.turn(0, -1),
                                "Left": lambda: self.turn(-1, 0),
                                "Right": lambda: self.turn(1, 0),
                                "p": self.toggle_pause,
                                "m": Audio.toggle_mute,
                                "q": self.quit_game},
            GameState.PAUSED: {"p": self.toggle_pause,
                               "m": Audio.toggle_mute,
                               "q": self.quit_game},
            GameState.NAME_ENTRY: {**{c: lambda ch=c: self.name_entry_add_char(ch)
                                      for c in string.ascii_lowercase},
                                   "BackSpace": self.name_entry_backspace,
                                   "Return": self.name_entry_submit},
            GameState.HIGHSCORES: {"Left": lambda: self.change_highscore_difficulty(-1),
                                   "Right": lambda: self.change_highscore_difficulty(1),
                                   "b": self.back_to_title,
                                   "m": Audio.toggle_mute},
            GameState.RESTART_PROMPT: {"r": self.start_game,
                                       "q": self.quit_game},
        }

        self.input.clear()
        for key, fn in bindings.get(state, {}).items():
            self.input.bind(key, fn)
        self.input.apply()

    def turn(self, x, y):
        """Steer the snake; (x, y) is a unit direction. Reversing into itself is ignored."""
        dx, dy = x * Settings.grid_size, y * Settings.grid_size
        velocities = self.world.get(Velocity)

        for e in self.world.get(SnakeHead):
            vel = velocities[e]
            if (dx != 0 and vel.dx == -dx) or (dy != 0 and vel.dy == -dy):
                continue
            vel.dx = dx
            vel.dy = dy

    #----------NAME ENTRY---------
    def name_entry_add_char(self, ch):
        for entry in self.world.get(NameEntry).values():
            if len(entry.text) < entry.max_len:
                entry.text += ch.upper()

    def name_entry_backspace(self):
        for entry in self.world.get(NameEntry).values():
            entry.text = entry.text[:-1]

    def name_entry_submit(self):
        scores = self.high_scores[Settings.difficulty]
        for entry in self.world.get(NameEntry).values():
            scores.append((self.scoring.score, entry.text or "PLAYER"))

        scores.sort(key=lambda x: x[0], reverse=True)
        del scores[Settings.HIGHSCORE_LIMIT:]
        Persistence.save_high_scores(HIGHSCORE_FILE, self.high_scores)
        GameStateManager.set_state(GameState.RESTART_PROMPT)

    #----------MENUS---------
    def change_title_difficulty(self, step):
        Settings.cycle_difficulty(step)
        self.on_enter_title()

    def show_highscores(self):
        self.world.clear()
        spawn_highscores_ui(self.world, Settings.difficulty, self.high_scores[Settings.difficulty])
        GameStateManager.set_state(GameState.HIGHSCORES)

    def change_highscore_difficulty(self, step):
        Settings.cycle_difficulty(step)
        self.show_highscores()

    def back_to_title(self):
        GameStateManager.set_state(GameState.TITLE)

    def cycle_theme(self):
        Themes.next()
        for label in self.world.get(UILabel).values():
            if label.text.startswith("Theme:"):
                label.text = f"Theme: {Themes.current_name()}"

        Themes.apply(self.screen, {"snake": self.snake_pen,
                                   "food": self.food_turtle,
                                   "text": self.ui_pen,
                                   "hud": self.score_pen})

        foods = self.world.get(Food)
        for e, r in self.world.get(RenderRequest).items():
            if r.kind == "snake":
                r.color = Themes.get("snake_body")
            elif r.kind == "food":
                food = foods.get(e)
                r.color = Themes.get("food_gold" if food and food.golden else "food")
            elif r.kind == "obstacle":
                r.color = Themes.get("obstacle")

        Audio.play_theme(Themes.music())

    def quit_game(self):
        self.screen.bye()

    #----------GAME FLOW---------
    def toggle_pause(self):
        state = GameStateManager.current()
        if state == GameState.PLAYING:
            now = GameStateManager.ticks()
            for rm in self.world.get(RunModifier).values():
                rm.pause_ticks.append(now)
                rm.pause_ticks = [t for t in rm.pause_ticks if now - t <= PAUSE_SPAM_WINDOW]
            Audio.play("pause")
            GameStateManager.set_state(GameState.PAUSED)
        elif state == GameState.PAUSED:
            Audio.play("resume")
            GameStateManager.set_state(GameState.PLAYING)

    def start_game(self):
        self.reset_game()
        GameStateManager.set_state(GameState.PLAYING)

    def reset_game(self):
        world = self.world
        world.clear()
        self.scoring.reset()
        self.score_pen.clear()

        world.add_component(world.create_entity(), ComboCounter())
        world.add_component(world.create_entity(), Score())

        g = Settings.grid_size
        start = [(g * i, 0) for i in reversed(range(Settings.START_LENGTH))]
        spawn_snake_ecs(world, start, "right", Settings.direction_offsets())

        spawn_food_ecs(world, Settings.grid_positions(), Settings.golden_chance())
        spawn_obstacles_ecs(world, Settings.obstacle_positions())
        world.add_component(world.create_entity(), RunModifier())

    def trigger_death(self):
        Audio.play("death")
        self._remove_ui_for(GameState.PLAYING)
        self.world.add_component(self.world.create_entity(), NameEntry())
        GameStateManager.set_state(GameState.NAME_ENTRY)

    def handle_food_hits(self):
        world = self.world
        for e, event in list(world.get(GameEvent).items()):
            if event.kind != "FOOD_HIT":
                continue
            world.remove_entity(e)

            food = world.get(Food).get(event.entity)
            if not food:
                continue
            Audio.play("golden" if food.golden else "eat")

            value = FOODS["golden"] if food.golden else FOODS["normal"]
            if food.golden and any(rm.combo_god for rm in world.get(RunModifier).values()):
                value = int(value * (1 + COMBO_GOD_PRESETS[Settings.difficulty]["gold_bonus"]))
            world.add_component(world.create_entity(), ScoreEvent("FOOD", value))

            for combo in world.get(ComboCounter).values():
                combo.value += 1
                self.scoring.set_combo(combo.value)
            combo_window_system(world)

            for head in world.get(SnakeHead):
                world.add_component(head, ComboGlow(8))

            world.remove_entity(event.entity)
            grow_snake_system(world)
            spawn_food_ecs(world, Settings.grid_positions(), Settings.golden_chance())

    #----------MAIN LOOP---------
    def update_playing(self):
        world = self.world
        cache_previous_positions(world)
        facing_system(world)
        movement_system(world)
        snake_follow_system(world)
        snap_to_grid_system(world)
        combo_glow_system(world)
        combo_decay_system(world)

        if boundary_system(world, wrap=Settings.get_wrap_mode()):
            for head in world.get(SnakeHead):
                world.add_component(world.create_entity(), GameEvent("DEATH", head))

        collision_system(world)
        # Achievements read this tick's FOOD_HIT / DEATH events, so they run first
        achievement_system(world)
        self.handle_food_hits()

        scoring_system(world, self.scoring)
        achievement_popup_system(world)
        score_render_system(world, self.score_pen)

        game_over_system(world)
        if GameStateManager.current() == GameState.GAME_OVER:
            self.trigger_death()

    def tick(self):
        GameStateManager.tick()

        if GameStateManager.current() == GameState.PLAYING:
            self.update_playing()

        state = GameStateManager.current()
        render_system(self.world, self.pens, state)
        ui_fade_system(self.world, state)
        ui_render_system(self.world, self.ui_pen, state)
        self.screen.update()

        # Always schedule the next frame, whatever state we ended up in
        self.screen.ontimer(self.tick, Settings.speed())

    def run(self):
        self.on_enter_title()
        self.bind_inputs_for_state(GameState.TITLE)
        self.tick()
        self.screen.mainloop()


#------------BOOT------------
if __name__ == "__main__":
    Game().run()
