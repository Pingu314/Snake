"""Regression tests for problems found by the stress tests (fuzzing, bot runs, corrupt files).

Run with:
    python -m pytest tests/test_stress_findings.py -v
"""

import json

import pytest

import snake
from v1_1.core.ecs.components import Position, Food, SnakeHead, SnakeSegment
from v1_1.core.ecs.factories import spawn_food_ecs
from v1_1.core.ecs.registry import World
from v1_1.core.game_state import GameState
from v1_1.core.persistence import Persistence, _sign
from helpers import make_game


# ---------------------------------------------------------------------------
# Full board: no free tile left for food
# ---------------------------------------------------------------------------

class TestFullBoard:

    def test_spawn_food_on_a_full_board_returns_none(self):
        world = World()
        xs, ys = world.settings.grid_positions()
        for x in xs:
            for y in ys:
                world.add_component(world.create_entity(), Position(x, y))
        assert spawn_food_ecs(world) is None

    def test_filling_the_board_ends_the_run(self, tmp_path):
        """Eat the last food on a board with no room left: the run ends instead of crashing."""
        game = make_game(tmp_path)
        world = game.world
        pos = world.get(Position)
        head = pos[next(iter(world.get(SnakeHead)))]
        food = pos[next(iter(world.get(Food)))]
        food.x, food.y = head.x + game.settings.grid_size, head.y

        # fill every other free cell with dummy entities
        taken = {(p.x, p.y) for p in pos.values()} | {(food.x, food.y)}
        tail = max(world.get(SnakeSegment).items(), key=lambda kv: kv[1].index)[0]
        xs, ys = game.settings.grid_positions()
        for x in xs:
            for y in ys:
                if (x, y) not in taken:
                    world.add_component(world.create_entity(), Position(x, y))
        # the tail cell frees up when the snake moves; block it too
        world.add_component(world.create_entity(), Position(pos[tail].x, pos[tail].y))

        game.update_playing()
        assert game.state.current in (GameState.NAME_ENTRY, GameState.RESTART_PROMPT)


# ---------------------------------------------------------------------------
# Corrupt save files must never stop the game from starting
# ---------------------------------------------------------------------------

def signed(payload):
    return (payload + "\n" + _sign(payload)).encode()


@pytest.mark.parametrize("data", [
    bytes(range(256)) * 4,                         # binary garbage
    "normal,10,A\nabc".encode("utf-16"),           # saved by an editor in another encoding
    signed("normal,ten,A"),                        # valid signature, bad number
    signed("normal,10"),                           # valid signature, missing field
], ids=["binary", "utf16", "bad-number", "missing-field"])
def test_corrupt_highscore_file_loads_empty(tmp_path, data):
    f = tmp_path / "highscore.txt"
    f.write_bytes(data)
    scores = Persistence.load_high_scores(f, ["easy", "normal"], 5)
    assert scores == {"easy": [], "normal": []}


def test_good_lines_survive_a_bad_one(tmp_path):
    f = tmp_path / "highscore.txt"
    f.write_bytes(signed("normal,30,AAA\nnormal,oops,BBB\neasy,20,CCC"))
    scores = Persistence.load_high_scores(f, ["easy", "normal"], 5)
    assert scores == {"easy": [(20, "CCC")], "normal": [(30, "AAA")]}


def test_game_starts_with_a_corrupt_highscore_file(tmp_path):
    (tmp_path / "highscore.txt").write_bytes(bytes(range(256)))
    game = snake.Game()
    assert game.high_scores["normal"] == []


@pytest.mark.parametrize("raw", ['{"difficulty": [], "walls": {}, "theme": [], "grid_size": [20]}',
                                 '{"difficulty": null, "grid_size": 20.5, "music_volume": true}'])
def test_wrong_types_in_preferences_are_ignored(tmp_path, raw):
    (tmp_path / "settings.json").write_text(raw, encoding="utf-8")
    game = snake.Game()
    assert game.settings.difficulty == "normal"
    assert game.audio.music_volume == 1.0


@pytest.mark.parametrize("raw", ['{"music_volume": NaN}', '{"music_volume": Infinity}',
                                 '{"sfx_volume": -Infinity}'])
def test_non_finite_volumes_are_ignored(tmp_path, raw):
    (tmp_path / "settings.json").write_text(raw, encoding="utf-8")
    game = snake.Game()
    assert game.audio.music_volume == 1.0
    assert game.audio.sfx_volume == 1.0
    json.dumps(game.preferences(), allow_nan=False)      # what we save is valid JSON again
