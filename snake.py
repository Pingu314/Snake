# Snake v1.1.0 - arcade
#< Pingu>

import math
import string
import tkinter
import turtle

from v1_1.audio.audio import Audio

from v1_1.config import layout
from v1_1.config.achievement_config import ACHIEVEMENTS, FOODS, NERVOUS_WINDOW_SECONDS
from v1_1.config.settings import Settings
from v1_1.config.themes import Themes
from v1_1.config.paths import HIGHSCORE_FILE, ICON_FILE, PREFERENCES_FILE

from v1_1.core.game_state import GameState, StateMachine
from v1_1.core.persistence import Persistence

from v1_1.core.ecs.registry import World
from v1_1.core.ecs.factories import spawn_snake_ecs, spawn_food_ecs, grow_snake_system, spawn_title_ui, \
    spawn_pause_ui, spawn_highscores_ui, spawn_obstacles_ecs, spawn_restart_ui, spawn_settings_ui
from v1_1.core.ecs.components import Food, SnakeHead, NameEntry, ComboGlow, ComboCounter, GameEvent, \
    RunModifier, ScoreEvent, TurnBuffer, Countdown, SnakeSegment, AchievementPopup
from v1_1.core.ecs.systems import collision_system, movement_system, BoardRenderer, snake_follow_system, \
    boundary_system, cache_previous_positions, ui_render_system, combo_glow_system, \
    combo_decay_system, score_render_system, scoring_system, achievement_system, \
    combo_window_system, achievement_popup_system, game_over_system, combo_god, steering_system, \
    obstacle_movement_system, countdown_system, field_frame_system
from v1_1.core.ecs.ui_components import UIStateTag

from v1_1.logic.scoring import Scoring, food_points
from v1_1.logic.settings_menu import SettingsMenu

from v1_1.util.input_manager import InputManager


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

SFX = {"eat": "audio/assets/sounds/game/eat1.wav",
       "golden": "audio/assets/sounds/game/golden.wav",
       "death": "audio/assets/sounds/game/death1.wav",
       "pause": "audio/assets/sounds/ui/pause2.wav",
       "resume": "audio/assets/sounds/ui/resume2.wav",
       "highscore": "audio/assets/sounds/ui/hs2.wav",
       "achievement": "audio/assets/sounds/ui/achievement.wav"}


def make_pen(shape="classic"):
    """A hidden turtle without a trail. Colours are set while rendering."""
    pen = turtle.Turtle(shape=shape, undobuffersize=1)    # nothing uses undo; a big buffer slows clear()
    pen.hideturtle()
    pen.penup()
    return pen


class Game:
    """Game logic and state. setup_window() adds the turtle window, pens, sounds and keys.

    Without setup_window() the game runs headless, which is what the tests use.
    """

    def __init__(self, highscore_file=HIGHSCORE_FILE, preferences_file=PREFERENCES_FILE):
        self.settings = Settings()
        self.theme = Themes()
        self.audio = Audio()
        self.state = StateMachine()
        self.world = World(self.settings, self.theme, self.audio, self.state)

        self.scoring = Scoring()
        self.highscore_file = highscore_file
        self.high_scores = Persistence.load_high_scores(highscore_file,
                                                        difficulties=Settings.difficulties(),
                                                        limit=Settings.HIGHSCORE_LIMIT)
        self.preferences_file = preferences_file
        self.apply_preferences(Persistence.load_preferences(preferences_file))
        self.menu = SettingsMenu(self.settings, self.theme, self.audio, on_theme_change=self.apply_theme)
        self.last_run = {}      # summary for the game over screen
        self.screen = None

        self.state.register_on_enter(GameState.TITLE, self.build_title)
        # title changes (difficulty, theme) are saved once when the title is left, not per key press
        self.state.register_on_exit(GameState.TITLE, self.save_preferences)
        self.state.register_on_enter(GameState.SETTINGS, self.build_settings)
        self.state.register_on_exit(GameState.SETTINGS, self.save_preferences)
        self.state.register_on_enter(GameState.PAUSED, lambda: spawn_pause_ui(self.world))
        self.state.register_on_exit(GameState.PAUSED, lambda: self._remove_ui_for(GameState.PAUSED))
        self.state.register_on_enter(GameState.RESTART_PROMPT, lambda: spawn_restart_ui(self.world, **self.last_run))
        # 3-2-1 at the start of a run and after every pause
        self.state.register_on_enter(GameState.PLAYING, self.start_countdown)

    #----------PREFERENCES---------
    def preferences(self):
        return {"difficulty": self.settings.difficulty,
                "walls": Settings.WALL_MODES[self.settings.wrap_override],
                "theme": self.theme.current_name(),
                "music_volume": self.audio.music_volume,
                "sfx_volume": self.audio.sfx_volume,
                "muted": self.audio.muted}

    def apply_preferences(self, prefs):
        """Apply saved preferences; unknown or broken values keep their defaults."""
        def text(key):
            value = prefs.get(key)
            return value if isinstance(value, str) else None

        self.settings.set_difficulty(text("difficulty"))
        for mode, name in Settings.WALL_MODES.items():
            if text("walls") == name:
                self.settings.wrap_override = mode
        if text("theme"):
            self.theme.set_by_name(text("theme"))
        for key, setter in (("music_volume", self.audio.set_music_volume),
                            ("sfx_volume", self.audio.set_sfx_volume)):
            value = prefs.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                setter(value)
        if isinstance(prefs.get("muted"), bool):
            self.audio.muted = prefs["muted"]

    def save_preferences(self):
        try:
            Persistence.save_preferences(self.preferences_file, self.preferences())
        except OSError:
            pass    # read-only folder: settings only last for this session

    #----------WINDOW---------
    def setup_window(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.screen.bgcolor(self.theme.get("bg"))
        self.screen.title("Snake")
        self.screen.tracer(0)
        self.screen.listen()

        root = self.screen.getcanvas().winfo_toplevel()
        try:
            root.iconbitmap(str(ICON_FILE))
        except tkinter.TclError:
            pass    # no .ico support on this platform, keep the default icon

        #--------TURTLES(PENS)-------
        self.score_pen = make_pen()
        self.ui_pen = make_pen()
        self.frame_pen = make_pen()
        self.renderer = BoardRenderer({"snake": make_pen("square"),
                                       "food": make_pen("circle"),
                                       "overlay": make_pen("square")}, self.screen.getcanvas())

        #---------AUDIO-----------
        self.audio.init()
        for name, path in SFX.items():
            self.audio.load_sfx(name, path)
        self.audio.play_theme(self.theme.music(), self.theme.music_gain())

        #---------INPUT-----------
        self.input = InputManager(self.screen)
        self.screen.getcanvas().bind("<FocusOut>", self.on_focus_out)
        self.register_view_hooks()

    def register_view_hooks(self):
        """State hooks that need the window: clearing pens, drawing the frame, key bindings."""
        self.state.register_on_enter(GameState.TITLE, self.clear_pens)
        # the frame goes under everything else that is drawn during the run
        self.state.register_on_enter(GameState.PLAYING, lambda: field_frame_system(self.world, self.frame_pen))
        for state in GameState:
            self.state.register_on_enter(state, lambda s=state: self.bind_inputs_for_state(s))

    def clear_pens(self):
        self.renderer.reset()
        self.score_pen.clear()
        self.ui_pen.clear()
        self.frame_pen.clear()

    def on_focus_out(self, _=None):
        if self.state.current == GameState.PLAYING:
            self.state.set_state(GameState.PAUSED)

    #----------INPUT---------
    def bind_inputs_for_state(self, state):
        bindings = {
            GameState.TITLE: {"Left": lambda: self.change_title_difficulty(-1),
                              "Right": lambda: self.change_title_difficulty(1),
                              "space": self.start_game,
                              "m": self.toggle_mute,
                              "t": self.cycle_theme,
                              "s": self.open_settings,
                              "q": self.quit_game,
                              "h": self.show_highscores},
            GameState.SETTINGS: {"Up": lambda: self.settings_move(-1),
                                 "Down": lambda: self.settings_move(1),
                                 "Left": lambda: self.settings_change(-1),
                                 "Right": lambda: self.settings_change(1),
                                 "m": self.toggle_mute,
                                 "b": self.back_to_title,
                                 "Escape": self.back_to_title},
            GameState.PLAYING: {"Up": lambda: self.turn("up"),
                                "Down": lambda: self.turn("down"),
                                "Left": lambda: self.turn("left"),
                                "Right": lambda: self.turn("right"),
                                "p": self.toggle_pause,
                                "Escape": self.toggle_pause,
                                "m": self.toggle_mute,
                                "q": self.quit_game},
            GameState.PAUSED: {"p": self.toggle_pause,
                               "Escape": self.toggle_pause,
                               "m": self.toggle_mute,
                               "q": self.quit_game},
            GameState.NAME_ENTRY: {**{c: lambda ch=c: self.name_entry_add_char(ch)
                                      for c in string.ascii_lowercase},
                                   "BackSpace": self.name_entry_backspace,
                                   "Return": self.name_entry_submit},
            GameState.HIGHSCORES: {"Left": lambda: self.change_highscore_difficulty(-1),
                                   "Right": lambda: self.change_highscore_difficulty(1),
                                   "b": self.back_to_title,
                                   "m": self.toggle_mute},
            GameState.RESTART_PROMPT: {"r": self.start_game,
                                       "b": self.back_to_title,
                                       "q": self.quit_game},
        }

        self.input.clear()
        for key, fn in bindings.get(state, {}).items():
            self.input.bind(key, fn)
        self.input.apply()

    def turn(self, direction):
        """Queue a turn ("up", "down", "left", "right"). steering_system applies one per tick,
        so two quick presses (e.g. Up, Left) become two moves instead of a U-turn into the neck."""
        turn = self.settings.direction_offsets()[direction]

        for buffer in self.world.get(TurnBuffer).values():
            if buffer.turns and buffer.turns[-1] == turn:
                continue
            if len(buffer.turns) < Settings.MAX_QUEUED_TURNS:
                buffer.turns.append(turn)

    #----------NAME ENTRY---------
    def name_entry_add_char(self, ch):
        """Arcade style: the third initial saves the score right away."""
        for entry in self.world.get(NameEntry).values():
            if len(entry.text) < entry.max_len:
                entry.text += ch.upper()
            if len(entry.text) == entry.max_len:
                self.name_entry_submit()
                return

    def name_entry_backspace(self):
        for entry in self.world.get(NameEntry).values():
            entry.text = entry.text[:-1]

    def name_entry_submit(self):
        scores = self.high_scores[self.settings.difficulty]
        for e, entry in list(self.world.get(NameEntry).items()):
            scores.append((self.scoring.score, entry.text or "AAA"))
            self.world.remove_entity(e)         # saved once, never twice

        scores.sort(key=lambda x: x[0], reverse=True)
        del scores[Settings.HIGHSCORE_LIMIT:]
        try:
            Persistence.save_high_scores(self.highscore_file, self.high_scores)
        except OSError:
            pass    # read-only folder (e.g. Program Files): keep the scores for this session only
        self.state.set_state(GameState.RESTART_PROMPT)

    def is_highscore(self, score):
        scores = self.high_scores[self.settings.difficulty]
        if score <= 0 or not self.settings.is_ranked():
            return False
        return len(scores) < Settings.HIGHSCORE_LIMIT or score > scores[-1][0]

    #----------MENUS---------
    def build_title(self):
        self.settings.speed_bonus = 0
        self.world.clear()
        spawn_title_ui(self.world)

    def best_score(self):
        scores = self.high_scores[self.settings.difficulty]
        return scores[0][0] if scores else 0

    def change_title_difficulty(self, step):
        self.settings.cycle_difficulty(step)
        self.build_title()

    def show_highscores(self):
        self.world.clear()
        spawn_highscores_ui(self.world, self.high_scores[self.settings.difficulty])
        self.state.set_state(GameState.HIGHSCORES)

    def change_highscore_difficulty(self, step):
        self.settings.cycle_difficulty(step)
        self.show_highscores()

    def back_to_title(self):
        self.state.set_state(GameState.TITLE)

    def cycle_theme(self):
        self.theme.next()
        self.apply_theme()
        self.build_title()

    def toggle_mute(self):
        self.audio.toggle_mute()
        self.save_preferences()

    #----------SETTINGS SCREEN---------
    def open_settings(self):
        self.menu.selected = 0
        self.state.set_state(GameState.SETTINGS)

    def build_settings(self):
        self.world.clear()
        spawn_settings_ui(self.world, self.menu.entries(), self.menu.selected)

    def settings_move(self, step):
        self.menu.move(step)
        self.build_settings()

    def settings_change(self, step):
        self.menu.change(step)
        self.build_settings()

    def apply_theme(self):
        """Push the current theme to the window and the music (entities look their colours up while drawing)."""
        if self.screen:
            self.screen.bgcolor(self.theme.get("bg"))
        self.audio.play_theme(self.theme.music(), self.theme.music_gain())

    def quit_game(self):
        self.save_preferences()
        self.screen.bye()

    #----------GAME FLOW---------
    def toggle_pause(self):
        if self.state.current == GameState.PLAYING:
            now = self.state.ms
            for rm in self.world.get(RunModifier).values():
                rm.perfect = False
                rm.pause_times = [t for t in rm.pause_times if now - t <= NERVOUS_WINDOW_SECONDS * 1000] + [now]
            self.audio.play("pause")
            self.state.set_state(GameState.PAUSED)
        elif self.state.current == GameState.PAUSED:
            self.audio.play("resume")
            self.state.set_state(GameState.PLAYING)

    def start_game(self):
        self.reset_game()
        self.state.set_state(GameState.PLAYING)

    def start_countdown(self):
        step = round(layout.COUNTDOWN_STEP_SECONDS * 1000)
        for e in list(self.world.get(Countdown)):
            self.world.remove_entity(e)
        self.world.add_component(self.world.create_entity(), Countdown(3 * step, step))

    def reset_game(self):
        world = self.world
        world.clear()
        self.scoring.reset()
        self.settings.speed_bonus = 0

        world.add_component(world.create_entity(), ComboCounter())

        g = self.settings.grid_size
        start = [(g * i, 0) for i in reversed(range(Settings.START_LENGTH))]
        spawn_snake_ecs(world, start, "right")

        spawn_obstacles_ecs(world)
        spawn_food_ecs(world)               # after the obstacles: food never lands in a block
        world.add_component(world.create_entity(), RunModifier())

    def trigger_death(self):
        self.audio.play("death")

        score = self.scoring.score
        earned = set().union(*(rm.earned for rm in self.world.get(RunModifier).values()))
        self.last_run = {"score": score,
                         "length": len(self.world.get(SnakeSegment)),
                         "earned": [a for a in ACHIEVEMENTS if a in earned],
                         "new_best": self.settings.is_ranked() and score > self.best_score()}

        if self.is_highscore(score):
            self.audio.play("highscore")
            self.world.add_component(self.world.create_entity(), NameEntry())
            next_state = GameState.NAME_ENTRY
        else:
            next_state = GameState.RESTART_PROMPT

        # Popups of achievements earned by dying stay up during name entry;
        # the game over screen lists them anyway
        for e in list(self.world.get(AchievementPopup)):
            if next_state == GameState.NAME_ENTRY:
                self.world.get(UIStateTag)[e].state = next_state
            else:
                self.world.remove_entity(e)

        self.state.set_state(next_state)

    def _remove_ui_for(self, state):
        for e, tag in list(self.world.get(UIStateTag).items()):
            if tag.state == state:
                self.world.remove_entity(e)

    def handle_food_hits(self):
        world = self.world
        for e, event in list(world.get(GameEvent).items()):
            if event.kind != "FOOD_HIT":
                continue
            world.remove_entity(e)

            food = world.get(Food).get(event.entity)
            if not food:
                continue
            self.audio.play("golden" if food.golden else "eat")
            self.settings.speed_up()        # like v1.0: every food makes the snake a bit faster

            # A bite inside the combo window extends the combo, otherwise a new one starts
            combo_value = 1
            for combo in world.get(ComboCounter).values():
                combo.value = combo.value + 1 if combo.timer > 0 else 1
                combo_value = combo.value
            combo_window_system(world)

            base = FOODS["golden"] if food.golden else FOODS["normal"]
            god = combo_god(world)
            if food.golden and god:
                base = int(base * (1 + god["gold_bonus"]))
            world.add_component(world.create_entity(), ScoreEvent(food_points(base, combo_value)))

            for head in world.get(SnakeHead):
                world.add_component(head, ComboGlow(layout.COMBO_GLOW_SECONDS * 1000))

            world.remove_entity(event.entity)
            grow_snake_system(world)
            if spawn_food_ecs(world) is None:
                # No free tile left: the board is full, the run is over
                world.add_component(world.create_entity(), GameEvent("BOARD_FULL"))

    #----------MAIN LOOP---------
    def update_playing(self):
        """One tick of game logic. Draws nothing, so it also runs headless."""
        world = self.world
        steering_system(world)
        cache_previous_positions(world)
        movement_system(world)
        snake_follow_system(world)
        combo_glow_system(world)
        combo_decay_system(world)

        if boundary_system(world):
            for head in world.get(SnakeHead):
                world.add_component(world.create_entity(), GameEvent("DEATH"))

        collision_system(world)
        # Blocks move after the collision check and bounce off the snake, so they never pass through it
        obstacle_movement_system(world)
        # Achievements read this tick's FOOD_HIT / DEATH events, so they run first
        achievement_system(world, self.scoring.score)
        self.handle_food_hits()

        scoring_system(world, self.scoring)
        achievement_popup_system(world)

        if game_over_system(world):
            self.trigger_death()

    def render(self):
        self.renderer.draw(self.world)
        # Keep the score up after death too, so points earned by dying (e.g. TINY_DEATH) show up
        if self.state.current in (GameState.PLAYING, GameState.NAME_ENTRY, GameState.RESTART_PROMPT):
            score_render_system(self.world, self.score_pen, self.scoring.score, self.best_score())
        ui_render_system(self.world, self.ui_pen)
        self.screen.update()

    def tick(self):
        self.state.tick(self.settings.speed())

        # the snake waits while the 3-2-1 runs
        if self.state.current == GameState.PLAYING and not countdown_system(self.world):
            self.update_playing()

        self.render()
        # Always schedule the next frame, whatever state we ended up in
        self.screen.ontimer(self.tick, self.settings.speed())

    def run(self):
        self.setup_window()
        self.build_title()
        self.bind_inputs_for_state(GameState.TITLE)
        self.tick()
        self.screen.mainloop()


#------------BOOT------------
if __name__ == "__main__":
    Game().run()
