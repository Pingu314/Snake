"""Tests for the playfield geometry, the settings screen and saved preferences.

Run with:
    python -m pytest tests/test_settings.py -v
"""

import json

import pytest

import snake
from v1_1.config.settings import Settings
from v1_1.core.game_state import GameState
from v1_1.logic.settings_menu import SettingsMenu
from helpers import make_game, labels


# ---------------------------------------------------------------------------
# Playfield
# ---------------------------------------------------------------------------

class TestPlayfield:

    def test_field_size(self):
        s = Settings()
        assert (s.half_width, s.half_height) == (380, 240)
        assert (Settings.FIELD_HALF_WIDTH, Settings.FIELD_HALF_HEIGHT) == (390, 250)


    @pytest.mark.parametrize("difficulty", ["hard", "insane"])
    def test_obstacles_are_inside_and_off_the_start_row(self, difficulty):
        s = Settings(difficulty)
        min_x, max_x, min_y, max_y = s.bounds()
        blocks = s.obstacle_blocks()
        assert blocks
        for cells in blocks:
            for x, y in cells:
                assert x % s.grid_size == 0 and y % s.grid_size == 0
                assert min_x <= x <= max_x and min_y <= y <= max_y
                assert y != 0, "start row must stay free"

    def test_no_grid_option_any_more(self, tmp_path):
        game = make_game(tmp_path)
        assert "Grid size" not in [row[0] for row in game.menu.rows]
        assert "grid_size" not in game.preferences()



# ---------------------------------------------------------------------------
# Settings menu
# ---------------------------------------------------------------------------

@pytest.fixture
def menu(tmp_path):
    game = snake.Game()
    return game.menu


def select(menu, label):
    menu.selected = [row[0] for row in menu.rows].index(label)


class TestSettingsMenu:

    def test_selection_wraps(self, menu):
        menu.move(-1)
        assert menu.selected == len(menu.rows) - 1
        menu.move(1)
        assert menu.selected == 0

    def test_difficulty(self, menu):
        select(menu, "Difficulty")
        menu.change(1)
        assert menu.settings.difficulty == "hard"

    def test_walls_cycle_and_survive_difficulty_change(self, menu):
        select(menu, "Walls")
        assert dict(menu.entries())["Walls"] == "Default (Wrap)"
        menu.change(1)
        assert menu.settings.wrap_override is True
        menu.change(1)
        assert menu.settings.wrap_override is False
        menu.settings.cycle_difficulty(1)
        assert menu.settings.get_wrap_mode() is False

    def test_theme_calls_back(self, tmp_path):
        calls = []
        settings, theme, audio = Settings(), snake.Themes(), snake.Audio()
        m = SettingsMenu(settings, theme, audio, on_theme_change=lambda: calls.append(theme.current_name()))
        select(m, "Theme")
        m.change(-1)
        assert calls == [snake.Themes.THEMES[-1]["name"]]

    @pytest.mark.parametrize("label, attr", [("Music volume", "music_volume"), ("Effects volume", "sfx_volume")])
    def test_volume_steps_and_clamps(self, menu, label, attr):
        select(menu, label)
        menu.change(1)
        assert getattr(menu.audio, attr) == 1.0           # already at max
        for _ in range(3):
            menu.change(-1)
        assert getattr(menu.audio, attr) == 0.7
        for _ in range(20):
            menu.change(-1)
        assert getattr(menu.audio, attr) == 0.0
        assert dict(menu.entries())[label] == "0 %"


class TestSettingsScreen:

    def test_open_change_and_leave(self, tmp_path):
        game = make_game(tmp_path)
        game.state.current = GameState.TITLE
        game.open_settings()
        assert game.state.current == GameState.SETTINGS
        assert "SETTINGS" in labels(game)

        game.settings_move(1)               # Walls
        game.settings_change(-1)            # Default -> Solid
        assert "◄ Solid ►" in labels(game)

        game.back_to_title()
        assert game.state.current == GameState.TITLE
        assert "UNRANKED (custom walls)" in labels(game)
        saved = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        assert saved["walls"] == "solid"


# ---------------------------------------------------------------------------
# Saved preferences
# ---------------------------------------------------------------------------

class TestPreferences:

    def test_round_trip(self, tmp_path):
        first = snake.Game()
        first.settings.set_difficulty("insane")
        first.settings.wrap_override = True
        first.theme.set_by_name("Lava")
        first.audio.set_music_volume(0.3)
        first.audio.set_sfx_volume(0.6)
        first.audio.muted = True
        first.save_preferences()

        second = snake.Game()
        assert second.preferences() == first.preferences()

    def test_broken_file_gives_defaults(self, tmp_path):
        (tmp_path / "settings.json").write_text("{not json", encoding="utf-8")
        game = snake.Game()
        assert game.settings.difficulty == Settings.DEFAULT_DIFFICULTY

    def test_bad_values_are_ignored(self, tmp_path):
        (tmp_path / "settings.json").write_text(json.dumps(
            {"difficulty": "nightmare", "grid_size": 7, "walls": "maybe", "theme": 3,
             "music_volume": "loud", "sfx_volume": 5, "muted": "yes"}), encoding="utf-8")
        game = snake.Game()
        assert game.settings.difficulty == "normal"
        assert game.settings.wrap_override is None
        assert game.theme.current_name() == "Classic"
        assert game.audio.music_volume == 1.0
        assert game.audio.sfx_volume == 1.0              # clamped
        assert game.audio.muted is False

    def test_save_failure_does_not_crash(self, tmp_path):
        game = snake.Game(highscore_file=tmp_path / "hs.txt", preferences_file=tmp_path)   # a folder
        game.save_preferences()
