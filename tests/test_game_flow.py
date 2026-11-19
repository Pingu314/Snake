"""Tick-level tests for the Game class in snake.py.

Game() without setup_window() runs headless: no window, no pens, no sounds
loaded (Audio.play() is then a no-op). Highscores go to a temp file.

Run with:
    python -m pytest tests/test_game_flow.py -v
"""


import snake
from v1_1.config import layout
from v1_1.config.achievement_config import PERFECT_RUN_MIN_FOOD
from v1_1.core.ecs.components import GameEvent, Food, \
    SnakeSegment, NameEntry, RenderRequest, AchievementPopup
from v1_1.core.ecs.ui_components import UIStateTag, UILabel
from v1_1.core.game_state import GameState, StateMachine
from v1_1.core.ecs.systems import BoardRenderer
from helpers import FakePen, FakeCanvas, FakeScreen, make_game, head, place_food_in_front, eat, drive_into_wall, run_modifier, labels


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class TestStateHooks:

    def test_multiple_enter_hooks_all_run(self):
        sm = StateMachine()
        calls = []
        sm.register_on_enter(GameState.PAUSED, lambda: calls.append("ui"))
        sm.register_on_enter(GameState.PAUSED, lambda: calls.append("input"))
        sm.set_state(GameState.PAUSED)
        assert calls == ["ui", "input"]

    def test_pause_spawns_and_removes_its_ui(self, game):
        game.state.set_state(GameState.PAUSED)
        paused = [t for t in game.world.get(UIStateTag).values() if t.state == GameState.PAUSED]
        assert paused
        game.state.set_state(GameState.PLAYING)
        assert not [t for t in game.world.get(UIStateTag).values() if t.state == GameState.PAUSED]


# ---------------------------------------------------------------------------
# Eating food
# ---------------------------------------------------------------------------

class TestEating:

    def test_eating_grows_snake_and_scores(self, game):
        run_modifier(game).play_ms = 10_000      # too late for the QUICK DRAW bonus: food points only
        place_food_in_front(game)
        game.update_playing()

        assert len(game.world.get(SnakeSegment)) == game.settings.START_LENGTH + 1
        assert game.scoring.score == 10
        assert len(game.world.get(Food)) == 1      # new food spawned

    def test_food_hit_event_is_consumed(self, game):
        place_food_in_front(game)
        game.update_playing()
        game.update_playing()
        assert len(game.world.get(GameEvent)) == 0


# ---------------------------------------------------------------------------
# Dying
# ---------------------------------------------------------------------------

class TestDeath:

    def test_highscore_death_goes_to_name_entry(self, tmp_path):
        game = make_game(tmp_path, "hard")     # walls; TINY_DEATH gives points
        drive_into_wall(game)
        assert game.state.current == GameState.NAME_ENTRY
        assert len(game.world.get(NameEntry)) == 1

    def test_zero_score_skips_name_entry(self, game):
        game.settings.wrap_override = False
        drive_into_wall(game)
        assert game.state.current == GameState.RESTART_PROMPT

    def test_score_below_top5_skips_name_entry(self, tmp_path):
        game = make_game(tmp_path, "hard")
        game.high_scores["hard"] = [(1000, "AAA")] * 5
        drive_into_wall(game)
        assert game.state.current == GameState.RESTART_PROMPT

    def test_tick_keeps_running_after_death(self, tmp_path):
        """Regression: the main loop used to stop scheduling itself after a death."""
        game = make_game(tmp_path, "hard")
        scheduled = []

        class Screen(FakeScreen):
            def ontimer(self, fn, ms): scheduled.append(fn)

        game.screen = Screen()
        game.ui_pen = game.score_pen = FakePen()
        game.renderer = BoardRenderer({"snake": FakePen(), "food": FakePen(), "overlay": FakePen()}, FakeCanvas())

        head(game).x = game.settings.half_width
        game.tick()

        assert game.state.current == GameState.NAME_ENTRY
        assert scheduled == [game.tick]

    def test_achievement_popup_survives_death(self, tmp_path):
        game = make_game(tmp_path, "hard")
        drive_into_wall(game)      # earns TINY_DEATH

        popups = game.world.get(AchievementPopup)
        tags = game.world.get(UIStateTag)
        assert popups
        assert all(tags[e].state == GameState.NAME_ENTRY for e in popups)

    def test_highscore_save_failure_does_not_crash(self, tmp_path):
        game = make_game(tmp_path, "hard")
        game.highscore_file = tmp_path          # a folder: open() fails like a read-only location
        drive_into_wall(game)
        game.name_entry_submit()
        assert game.state.current == GameState.RESTART_PROMPT
        assert game.high_scores["hard"]          # kept in memory for this session


class TestRestartPrompt:

    def test_back_to_title(self, game):
        game.settings.wrap_override = False
        drive_into_wall(game)
        game.back_to_title()

        assert game.state.current == GameState.TITLE
        assert any(label.text == "SNAKE" for label in game.world.get(UILabel).values())


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

class TestAchievements:

    def test_lucky_bite(self, game):
        place_food_in_front(game, golden=True)
        game.update_playing()
        assert "LUCKY_BITE" in run_modifier(game).earned

    def test_greedy_after_five_golden(self, game):
        for _ in range(5):
            place_food_in_front(game, golden=True)
            game.update_playing()
        assert "GREEDY" in run_modifier(game).earned

    def test_tiny_death_on_hard(self, tmp_path):
        game = make_game(tmp_path, "hard")
        drive_into_wall(game)
        assert "TINY_DEATH" in run_modifier(game).earned
        assert game.scoring.score > 0

    def test_tiny_death_not_offered_on_normal(self, game):
        game.settings.wrap_override = False
        drive_into_wall(game)
        assert "TINY_DEATH" not in run_modifier(game).earned


class TestPerfectRun:
    """PERFECT RUN: eat PERFECT_RUN_MIN_FOOD without ever pausing, then die."""

    def test_awarded_without_pause(self, tmp_path):
        game = make_game(tmp_path, "hard")
        for _ in range(PERFECT_RUN_MIN_FOOD):
            eat(game)
        drive_into_wall(game)
        assert "PERFECT_RUN" in run_modifier(game).earned

    def test_not_awarded_for_a_short_run(self, tmp_path):
        game = make_game(tmp_path, "hard")
        drive_into_wall(game)
        assert "PERFECT_RUN" not in run_modifier(game).earned

    def test_pausing_loses_it(self, tmp_path):
        game = make_game(tmp_path, "hard")
        game.toggle_pause()
        game.toggle_pause()
        for _ in range(PERFECT_RUN_MIN_FOOD):
            eat(game)
        drive_into_wall(game)
        assert "PERFECT_RUN" not in run_modifier(game).earned


# ---------------------------------------------------------------------------
# Themes and audio
# ---------------------------------------------------------------------------

class TestThemeCycle:

    def test_cycle_theme_rebuilds_the_title(self, game):
        game.state.current = GameState.TITLE
        game.build_title()
        game.cycle_theme()
        assert f"Theme: {game.theme.current_name()}" in labels(game)

    def test_entities_store_theme_keys(self, game):
        """Colours are looked up while drawing, so a theme change needs no recolouring."""
        keys = set(snake.Themes.THEMES[0])
        for r in game.world.get(RenderRequest).values():
            assert r.color_key in keys


class TestMuteAndTheme:

    def test_theme_changed_while_muted_starts_after_unmute(self, tmp_path, fake_music):
        music = fake_music
        old, new = tmp_path / "old.mp3", tmp_path / "new.mp3"
        old.touch(); new.touch()

        audio = snake.Audio()
        audio.play_theme(old)
        audio.toggle_mute()          # mute
        audio.play_theme(new)        # theme switched while muted
        music.calls.clear()
        audio.toggle_mute()          # unmute

        assert "load" in music.calls and "play" in music.calls

    def test_unmute_same_theme_just_resumes(self, tmp_path, fake_music):
        music = fake_music
        track = tmp_path / "t.mp3"
        track.touch()

        audio = snake.Audio()
        audio.play_theme(track)
        audio.toggle_mute()
        music.calls.clear()
        audio.toggle_mute()

        assert music.calls == ["unpause"]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

class TestLayout:

    def test_hud_is_above_the_playfield(self, game):
        field_top = game.settings.half_height + game.settings.grid_size / 2
        assert layout.HUD_Y > field_top


class TestNameEntryAndOverlay:

    def test_third_initial_saves_right_away(self, tmp_path):
        game = make_game(tmp_path, "hard")
        drive_into_wall(game)
        game.name_entry_add_char("a")
        game.name_entry_add_char("b")
        assert game.state.current == GameState.NAME_ENTRY
        game.name_entry_add_char("c")
        assert game.state.current == GameState.RESTART_PROMPT
        assert game.high_scores["hard"][0][1] == "ABC"

    def test_score_is_saved_only_once(self, tmp_path):
        game = make_game(tmp_path, "hard")
        drive_into_wall(game)
        for ch in "abc":
            game.name_entry_add_char(ch)
        game.name_entry_submit()                 # a stray Enter afterwards
        assert len(game.high_scores["hard"]) == 1
        assert not game.world.get(NameEntry)

    def test_pause_overlay_covers_a_resized_window(self, game):
        class Screen:
            def window_width(self): return 1200
            def window_height(self): return 900

        sizes = []

        class OverlayPen(FakePen):
            def getscreen(self): return Screen()
            def shapesize(self, *a): sizes.append(a)

        game.state.set_state(GameState.PAUSED)
        BoardRenderer({"snake": FakePen(), "food": FakePen(), "overlay": OverlayPen()}, FakeCanvas()).draw(game.world)
        height_factor, width_factor = sizes[0]  # turtle's shapesize(stretch_wid, stretch_len) at heading 0
        assert width_factor * 20 >= 1200 and height_factor * 20 >= 900


class TestBoardRenderer:
    """Stamps only for cells that changed, the body as canvas lines."""

    def renderer(self, log):
        class Pen(FakePen):
            def __init__(self, name):
                super().__init__()
                self.name, self.next_id = name, 0
            def stamp(self):
                self.next_id += 1
                log.append(("stamp", self.name))
                return self.next_id
            def clearstamp(self, stamp_id): log.append(("clear", self.name))
            def getscreen(self): return Screen()

        class Screen:
            def window_width(self): return 800
            def window_height(self): return 600

        self.canvas = FakeCanvas()
        return BoardRenderer({"snake": Pen("snake"), "food": Pen("food"), "overlay": Pen("overlay")}, self.canvas)

    def test_body_is_one_line_however_long(self, game):
        from v1_1.core.ecs.factories import grow_snake_system
        log = []
        renderer = self.renderer(log)
        for _ in range(30):
            grow_snake_system(game.world)
        for _ in range(30):                      # unfold the body (normal wraps)
            game.update_playing()
        renderer.draw(game.world)
        assert len(self.canvas.items) <= 2       # one line, two if the body crosses the wrapping edge
        assert len([e for e in log if e == ("stamp", "snake")]) == 1      # only the head is a stamp

    def test_line_runs_through_the_body_cells(self, game):
        from v1_1.core.ecs.components import SnakeSegment, Position
        renderer = self.renderer([])
        renderer.draw(game.world)
        (coords,) = self.canvas.items.values()
        pos = game.world.get(Position)
        body = sorted(game.world.get(SnakeSegment).items(), key=lambda kv: kv[1].index)[1:]
        expected = [v for e, _ in body for v in (pos[e].x, -pos[e].y)]
        assert coords == expected

    def test_moving_restamps_only_the_head(self, game):
        log = []
        renderer = self.renderer(log)
        renderer.draw(game.world)
        log.clear()
        game.update_playing()
        renderer.draw(game.world)
        snake_ops = [e for e in log if e[1] == "snake"]
        assert snake_ops == [("clear", "snake"), ("stamp", "snake")]

    def test_reset_removes_the_body(self, game):
        renderer = self.renderer([])
        renderer.draw(game.world)
        renderer.reset()
        assert self.canvas.items == {}

    def test_overlay_is_stamped_last_while_paused(self, game):
        log = []
        renderer = self.renderer(log)
        renderer.draw(game.world)                # board drawn while playing
        game.state.set_state(GameState.PAUSED)
        log.clear()
        renderer.draw(game.world)
        assert log == [("stamp", "overlay")]     # the board stays, only the overlay goes on top

    def test_resume_removes_the_overlay(self, game):
        log = []
        renderer = self.renderer(log)
        game.state.set_state(GameState.PAUSED)
        renderer.draw(game.world)
        game.state.set_state(GameState.PLAYING)
        renderer.draw(game.world)
        assert ("clear", "overlay") in log


