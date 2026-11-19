"""Tests for the playfield frame (death zone), theme palettes and balanced sound levels.

Run with:
    python -m pytest tests/test_field_and_sound.py -v
"""

import pytest

import snake
from v1_1.config import layout
from v1_1.config.paths import SOUNDS_DIR
from v1_1.config.themes import Themes
from v1_1.core.ecs.systems import field_frame_system
from helpers import FakePen, make_game
from v1_1.core.game_state import GameState


class RecordingPen(FakePen):
    """Remembers colours, line widths and the corners of drawn lines and filled shapes."""
    def __init__(self):
        super().__init__()
        self.colors, self.widths, self.line, self.fills = [], [], [], []
        self.down, self.filling = False, None
        self.x = self.y = 0

    def color(self, c): self.colors.append(c)
    def pensize(self, w): self.widths.append(w)
    def pendown(self): self.down = True
    def penup(self): self.down = False
    def begin_fill(self): self.filling = [(self.x, self.y)]
    def end_fill(self): self.fills.append(self.filling); self.filling = None

    def goto(self, x, y=None):
        if y is None:
            x, y = x
        self.x, self.y = x, y
        if self.filling is not None:
            self.filling.append((x, y))
        if self.down:
            self.line.append((x, y))


def frame_of(game):
    pen = RecordingPen()
    field_frame_system(game.world, pen)
    return pen


# ---------------------------------------------------------------------------
# Field frame and death zone
# ---------------------------------------------------------------------------

class TestFieldFrame:

    @pytest.mark.parametrize("difficulty", ["hard", "insane"])
    def test_solid_walls_are_a_thick_warning_line(self, tmp_path, difficulty):
        game = make_game(tmp_path, difficulty)
        pen = frame_of(game)
        assert pen.widths[-1] == layout.WALL_LINE_WIDTH
        assert pen.colors[-1] == game.theme.get("wall")

    @pytest.mark.parametrize("difficulty", ["easy", "normal"])
    def test_wrapping_edge_is_a_thin_line(self, tmp_path, difficulty):
        game = make_game(tmp_path, difficulty)
        pen = frame_of(game)
        assert pen.widths[-1] == layout.BORDER_LINE_WIDTH
        assert pen.colors[-1] == game.theme.get("border")

    def test_custom_walls_count(self, tmp_path):
        game = make_game(tmp_path)               # normal wraps ...
        game.settings.wrap_override = False      # ... but the player picked solid walls
        assert frame_of(game).colors[-1] == game.theme.get("wall")

    def test_line_lies_just_outside_the_outermost_cells(self, tmp_path):
        game = make_game(tmp_path, "hard")
        pen = frame_of(game)
        s, half_line = game.settings, layout.WALL_LINE_WIDTH / 2
        xs = {abs(x) for x, _ in pen.line}
        ys = {abs(y) for _, y in pen.line}
        assert xs == {s.FIELD_HALF_WIDTH + half_line}
        assert ys == {s.FIELD_HALF_HEIGHT + half_line}

    def test_everything_outside_the_field_is_frame(self, tmp_path):
        """The 4 filled bands cover the window outside the field, the field itself stays free."""
        game = make_game(tmp_path, "hard")
        pen = frame_of(game)
        assert pen.colors[0] == game.theme.get("frame")
        fw, fh = game.settings.FIELD_HALF_WIDTH, game.settings.FIELD_HALF_HEIGHT

        def covered(x, y):
            for corners in pen.fills:
                xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
                if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
                    return True
            return False

        # window corners, side margins, HUD band and bottom band are frame ...
        for point in [(-399, 299), (399, -299), (395, 0), (-395, 0), (0, 270), (0, -270)]:
            assert covered(*point), point
        # ... the field (including its outermost cells) is not
        for point in [(0, 0), (fw - 1, fh - 1), (-(fw - 1), -(fh - 1))]:
            assert not covered(*point), point

    def test_frame_is_drawn_when_a_run_starts(self, tmp_path):
        from v1_1.util.input_manager import InputManager

        class Screen:
            def onkey(self, fn, key): pass

        game = make_game(tmp_path, start=True)
        game.frame_pen = pen = RecordingPen()
        game.input = InputManager(Screen())
        game.register_view_hooks()
        game.state.set_state(GameState.TITLE)
        game.start_game()
        assert pen.fills and pen.line


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

KEYS = {"name", "bg", "frame", "wall", "border", "snake_head", "snake_body", "obstacle", "food", "food_gold",
        "combo_glow", "combo_glow_strong", "hud_text", "message", "music", "music_gain"}


@pytest.mark.parametrize("theme", Themes.THEMES, ids=[t["name"] for t in Themes.THEMES])
def test_theme_is_complete(theme):
    assert set(theme) == KEYS
    assert 0 < theme["music_gain"] <= 1.0
    assert (SOUNDS_DIR / "music" / theme["music"]).exists()


@pytest.mark.parametrize("theme", Themes.THEMES, ids=[t["name"] for t in Themes.THEMES])
def test_frame_differs_from_the_field(theme):
    assert theme["frame"].lower() != theme["bg"].lower()


# ---------------------------------------------------------------------------
# Sound levels
# ---------------------------------------------------------------------------

class TestMusicGain:

    def test_theme_gain_scales_the_music(self, tmp_path, fake_music):
        track = tmp_path / "t.mp3"
        track.touch()
        audio = snake.Audio()
        audio.play_theme(track, 0.5)
        assert fake_music.volumes[-1] == pytest.approx(snake.Audio.THEME_VOLUME * 0.5)

    def test_player_volume_keeps_the_gain(self, tmp_path, fake_music):
        track = tmp_path / "t.mp3"
        track.touch()
        audio = snake.Audio()
        audio.play_theme(track, 0.5)
        audio.set_music_volume(0.4)
        assert fake_music.volumes[-1] == pytest.approx(snake.Audio.THEME_VOLUME * 0.4 * 0.5)


def test_every_sound_effect_has_a_balanced_level():
    for name in snake.SFX:
        assert name in snake.Audio.SFX_VOLUME, f"{name} has no level"
        assert 0 < snake.Audio.SFX_VOLUME[name] <= 1.0


@pytest.mark.parametrize("difficulty", ["hard", "insane"])
def test_obstacle_blocks_are_never_cut_open_by_the_food(tmp_path, difficulty):
    """Food used to be placed first, so an obstacle skipped that cell: food 'inside' a block."""
    import random
    from v1_1.core.ecs.components import Obstacle
    expected = sum(len(cells) for cells in snake.Settings(difficulty).obstacle_blocks())
    for seed in range(200):
        random.seed(seed)
        game = make_game(tmp_path, difficulty)
        assert len(game.world.get(Obstacle)) == expected, f"seed {seed}"
