"""Tests for the 1.1 arcade extras: speed-up, countdown, HI score, game over summary
and the secret achievements (all per run, arcade style).

Run with:
    python -m pytest tests/test_arcade_extras.py -v
"""

import pytest

import snake
from v1_1.config.achievement_config import ACHIEVEMENTS, ON_FIRE_COMBO, TOURIST_WRAPS, QUICK_DRAW_SECONDS
from v1_1.core.ecs.components import Countdown, ComboCounter
from v1_1.core.ecs.systems import score_render_system
from v1_1.core.game_state import GameState
from helpers import FakePen, make_game, head, eat, run_modifier, labels, drive_into_wall


# ---------------------------------------------------------------------------
# Speed-up (as in v1.0)
# ---------------------------------------------------------------------------

class TestSpeedUp:

    @pytest.mark.parametrize("difficulty", ["easy", "normal", "hard", "insane"])
    def test_each_food_speeds_up_down_to_the_minimum(self, tmp_path, difficulty):
        game = make_game(tmp_path, difficulty)
        cfg = game.settings.difficulty_config()
        assert game.settings.speed() == cfg["speed"]
        eat(game)
        assert game.settings.speed() == cfg["speed"] - cfg["speed_step"]
        game.settings.speed_bonus = 10_000
        assert game.settings.speed() == cfg["min_speed"]

    def test_new_run_starts_at_normal_speed(self, tmp_path):
        game = make_game(tmp_path)
        eat(game)
        game.reset_game()
        assert game.settings.speed() == game.settings.difficulty_config()["speed"]


# ---------------------------------------------------------------------------
# Countdown 3-2-1
# ---------------------------------------------------------------------------

class TestCountdown:

    def test_snake_waits_for_the_countdown(self, tmp_path):
        game = make_game(tmp_path, start=True)
        countdown = next(iter(game.world.get(Countdown).values()))
        x = head(game).x
        ticks = -(-countdown.ms // game.settings.speed())      # ceil: ticks until the countdown runs out
        for _ in range(ticks - 1):
            game.tick()
            assert head(game).x == x
        game.tick()                     # countdown runs out: "go", the snake moves on this tick
        assert head(game).x == x + game.settings.grid_size
        assert not game.world.get(Countdown)

    def test_countdown_after_pause(self, tmp_path):
        game = make_game(tmp_path, start=True)
        for _ in range(20):
            game.tick()
        assert not game.world.get(Countdown)
        game.toggle_pause()
        game.toggle_pause()
        assert game.world.get(Countdown)

    def test_countdown_is_shown(self, tmp_path):
        game = make_game(tmp_path, start=True)
        game.tick()
        assert "3" in game.ui_pen.written


# ---------------------------------------------------------------------------
# Best score in the HUD
# ---------------------------------------------------------------------------

class TestHiScore:

    def hud(self, game, score, best):
        game.scoring.score = score
        pen = FakePen()
        score_render_system(game.world, pen, game.scoring.score, best=best)
        return pen.written

    def test_hi_shows_the_best(self, tmp_path):
        assert self.hud(make_game(tmp_path), 40, best=100) == ["SCORE 40", "HI 100"]

    def test_hi_climbs_live_once_beaten(self, tmp_path):
        assert self.hud(make_game(tmp_path), 150, best=100) == ["SCORE 150", "HI 150"]

    def test_no_new_best_during_the_run(self, tmp_path):
        assert "NEW BEST!" not in self.hud(make_game(tmp_path), 150, best=100)


# ---------------------------------------------------------------------------
# Game over summary
# ---------------------------------------------------------------------------

class TestGameOverSummary:

    def test_summary_lists_score_length_and_achievements(self, tmp_path):
        game = make_game(tmp_path, "hard")
        game.high_scores["hard"] = [(5000, "AAA")] * 5          # no name entry
        eat(game, golden=True)                                  # LUCKY BITE
        drive_into_wall(game)
        assert game.state.current == GameState.RESTART_PROMPT

        texts = labels(game, GameState.RESTART_PROMPT)
        assert any(t.startswith("Score ") and "Length 4" in t for t in texts)
        assert ACHIEVEMENTS["LUCKY_BITE"]["title"] in texts
        # popups are not shown twice on the game over screen
        assert not game.world.get(snake.AchievementPopup)

    def test_new_best_is_announced(self, tmp_path):
        game = make_game(tmp_path, "hard")
        game.high_scores["hard"] = [(10, "AAA")]
        eat(game)
        eat(game)
        drive_into_wall(game)
        assert game.last_run["new_best"] is True


# ---------------------------------------------------------------------------
# Hidden achievements, saved unlocks, achievements screen
# ---------------------------------------------------------------------------

class TestSecretAchievements:

    def test_gold_rush(self, tmp_path):
        game = make_game(tmp_path)
        eat(game, golden=True)
        assert "GOLD_RUSH" not in run_modifier(game).earned
        eat(game, golden=True)
        assert "GOLD_RUSH" in run_modifier(game).earned

    def test_patience(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).ms_since_food = 20_000
        eat(game)
        assert "PATIENCE" in run_modifier(game).earned

    def test_no_patience_for_quick_eaters(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).ms_since_food = 5_000
        eat(game)
        assert "PATIENCE" not in run_modifier(game).earned

    def test_marathon(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).play_ms = 300_000
        game.update_playing()
        assert "MARATHON" in run_modifier(game).earned

    def test_on_the_edge(self, tmp_path):
        game = make_game(tmp_path)
        head(game).x = game.settings.half_width - game.settings.grid_size    # food lands on the right edge
        eat(game)
        assert "ON_THE_EDGE" in run_modifier(game).earned

    def test_not_on_the_edge_in_the_middle(self, tmp_path):
        game = make_game(tmp_path)
        eat(game)
        assert "ON_THE_EDGE" not in run_modifier(game).earned

    def test_speed_demon(self, tmp_path):
        game = make_game(tmp_path)
        game.settings.speed_bonus = 10_000
        game.update_playing()
        assert "SPEED_DEMON" in run_modifier(game).earned

    def combo_at(self, game, value):
        combo = next(iter(game.world.get(ComboCounter).values()))
        combo.value, combo.timer = value, 10_000         # a running combo (ms left)

    def test_on_fire(self, tmp_path):
        game = make_game(tmp_path)
        self.combo_at(game, ON_FIRE_COMBO - 1)
        eat(game)                                        # the bite that reaches the combo
        game.update_playing()                            # checked on the next tick
        assert "ON_FIRE" in run_modifier(game).earned

    def test_not_on_fire_one_short(self, tmp_path):
        game = make_game(tmp_path)
        self.combo_at(game, ON_FIRE_COMBO - 2)
        eat(game)
        game.update_playing()
        assert "ON_FIRE" not in run_modifier(game).earned

    def wrap_once(self, game):
        head(game).x = game.settings.half_width          # normal wraps: the next step goes through the edge
        game.update_playing()

    def test_tourist(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).wraps = TOURIST_WRAPS - 2
        self.wrap_once(game)
        assert "TOURIST" not in run_modifier(game).earned
        self.wrap_once(game)
        assert run_modifier(game).wraps == TOURIST_WRAPS
        assert "TOURIST" in run_modifier(game).earned

    def test_quick_draw(self, tmp_path):
        game = make_game(tmp_path)
        # the bite lands exactly on the limit (this tick adds one tick of play time)
        run_modifier(game).play_ms = QUICK_DRAW_SECONDS * 1000 - game.settings.speed()
        eat(game)
        assert "QUICK_DRAW" in run_modifier(game).earned

    def test_no_quick_draw_one_tick_late(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).play_ms = QUICK_DRAW_SECONDS * 1000
        eat(game)
        assert "QUICK_DRAW" not in run_modifier(game).earned

    def test_quick_draw_only_for_the_first_food(self, tmp_path):
        game = make_game(tmp_path)
        run_modifier(game).play_ms = 5_000
        eat(game)
        run_modifier(game).play_ms = 0
        eat(game)
        assert "QUICK_DRAW" not in run_modifier(game).earned

    def test_high_roller(self, tmp_path):
        game = make_game(tmp_path)
        game.scoring.score = 1000
        game.update_playing()
        assert "HIGH_ROLLER" in run_modifier(game).earned

    def test_snake_eyes(self, tmp_path):
        game = make_game(tmp_path)
        game.scoring.score = 211
        drive_into_wall(game)
        assert "SNAKE_EYES" in run_modifier(game).earned

    def test_every_achievement_has_a_check(self):
        from v1_1.core.ecs.systems import ACHIEVEMENT_CHECKS
        assert set(ACHIEVEMENT_CHECKS) == set(ACHIEVEMENTS)


class TestPerRunOnly:
    """Arcade style: nothing about achievements is saved or listed between runs."""

    def test_new_run_starts_without_achievements(self, tmp_path):
        game = make_game(tmp_path)
        eat(game, golden=True)
        assert run_modifier(game).earned
        game.reset_game()
        assert not run_modifier(game).earned

    def test_nothing_is_written_to_disk(self, tmp_path):
        game = make_game(tmp_path)
        eat(game, golden=True)
        assert not list(tmp_path.glob("achievement*"))

    def test_no_achievements_screen(self):
        assert "ACHIEVEMENTS" not in GameState.__members__


# ---------------------------------------------------------------------------
# Ranked runs: only the standard rules count for the highscores
# ---------------------------------------------------------------------------

class TestRanked:

    @pytest.mark.parametrize("walls, ranked", [
        (None, True),           # standard
        (True, True),           # Normal wraps anyway: same rules
        (False, False),         # solid walls on Normal
    ])
    def test_which_rules_are_ranked(self, tmp_path, walls, ranked):
        game = make_game(tmp_path)               # normal
        game.settings.wrap_override = walls
        assert game.settings.is_ranked() is ranked

    def test_unranked_run_skips_name_entry(self, tmp_path):
        game = make_game(tmp_path)               # normal
        eat(game)                                # points that would be a first highscore
        drive_into_wall(game)                    # solid walls on Normal: unranked
        assert game.scoring.score > 0
        assert game.state.current == GameState.RESTART_PROMPT
        assert game.last_run["new_best"] is False

    def test_hud_says_unranked(self, tmp_path):
        game = make_game(tmp_path)
        game.settings.wrap_override = False
        pen = FakePen()
        score_render_system(game.world, pen, game.scoring.score, best=100)
        assert pen.written == ["SCORE 0", "UNRANKED"]

    def test_title_warns(self, tmp_path):
        game = make_game(tmp_path)
        game.settings.wrap_override = False
        game.build_title()
        assert any("UNRANKED" in t for t in labels(game, GameState.TITLE))


def test_escape_pauses_and_resumes(tmp_path):
    from v1_1.util.input_manager import InputManager

    class Screen:
        def onkey(self, fn, key): pass

    game = make_game(tmp_path)
    game.input = InputManager(Screen())
    game.bind_inputs_for_state(GameState.PLAYING)
    game.input.bindings["Escape"]()
    assert game.state.current == GameState.PAUSED
    game.input.bindings["Escape"]()
    assert game.state.current == GameState.PLAYING
