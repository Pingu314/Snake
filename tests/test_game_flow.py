"""Tick-level tests for the Game class in snake.py.

The Game is built without its __init__ so no window opens: only the world,
scoring and a fake score pen are set up. Audio has no sounds loaded, so
Audio.play() is a no-op.

Run with:
    python -m pytest tests/test_game_flow.py -v
"""

import pytest

import snake
from v1_1.config.settings import Settings
from v1_1.core.ecs.components import Position, SnakeHead, Velocity, GameEvent, Food, FoodTag, \
    RunModifier, Obstacle, SnakeSegment, NameEntry, RenderRequest
from v1_1.core.ecs.factories import spawn_obstacles_ecs
from v1_1.core.ecs.registry import World
from v1_1.core.ecs.ui_components import UIStateTag
from v1_1.core.game_state import GameState, GameStateManager
from v1_1.logic.scoring import Scoring


class FakePen:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


@pytest.fixture
def game():
    Settings.set_difficulty("normal")
    GameStateManager.clear_hooks()
    GameStateManager._current = GameState.PLAYING

    g = snake.Game.__new__(snake.Game)
    g.world = World()
    g.scoring = Scoring()
    g.score_pen = FakePen()
    g.reset_game()
    yield g

    GameStateManager.clear_hooks()
    Settings.set_difficulty("normal")


def head_of(world):
    return next(iter(world.get(SnakeHead)))


def place_food_in_front(world, golden=False):
    """Move the existing food right in front of the snake head (snake starts moving right)."""
    food_e = next(iter(world.get(FoodTag)))
    head_pos = world.get(Position)[head_of(world)]
    world.get(Position)[food_e].x = head_pos.x + Settings.grid_size
    world.get(Position)[food_e].y = head_pos.y
    world.get(Food)[food_e].golden = golden
    return food_e


# ---------------------------------------------------------------------------
# Game state hooks
# ---------------------------------------------------------------------------

class TestStateHooks:

    def setup_method(self):
        GameStateManager.clear_hooks()
        GameStateManager._current = GameState.TITLE

    def teardown_method(self):
        GameStateManager.clear_hooks()

    def test_multiple_enter_hooks_all_run(self):
        calls = []
        GameStateManager.register_on_enter(GameState.PAUSED, lambda: calls.append("ui"))
        GameStateManager.register_on_enter(GameState.PAUSED, lambda: calls.append("input"))
        GameStateManager.set_state(GameState.PAUSED)
        assert calls == ["ui", "input"]


# ---------------------------------------------------------------------------
# Eating food
# ---------------------------------------------------------------------------

class TestEating:

    def test_eating_grows_snake_and_scores(self, game):
        place_food_in_front(game.world)
        game.update_playing()

        assert len(game.world.get(SnakeSegment)) == Settings.START_LENGTH + 1
        assert game.scoring.score == 10
        assert len(game.world.get(FoodTag)) == 1      # new food spawned

    def test_food_hit_event_is_consumed(self, game):
        place_food_in_front(game.world)
        game.update_playing()
        game.update_playing()

        assert len(game.world.get(GameEvent)) == 0


# ---------------------------------------------------------------------------
# Dying
# ---------------------------------------------------------------------------

class TestDeath:

    def test_wall_death_goes_to_name_entry(self, game):
        Settings.set_difficulty("hard")          # no wrap
        game.world.get(Position)[head_of(game.world)].x = Settings.HALF_WIDTH
        game.update_playing()

        assert GameStateManager.current() == GameState.NAME_ENTRY
        assert len(game.world.get(NameEntry)) == 1

    def test_tick_keeps_running_after_death(self, game):
        """Regression: the main loop used to stop scheduling itself after a death."""
        scheduled = []

        class FakeScreen:
            def update(self): pass
            def ontimer(self, fn, ms): scheduled.append(fn)

        game.screen = FakeScreen()
        game.ui_pen = FakePen()
        game.pens = {"snake": FakePen(), "food": FakePen(), "overlay": FakePen()}

        Settings.set_difficulty("hard")
        game.world.get(Position)[head_of(game.world)].x = Settings.HALF_WIDTH
        game.tick()

        assert GameStateManager.current() == GameState.NAME_ENTRY
        assert scheduled == [game.tick]

    def test_death_removes_playing_ui(self, game):
        e = game.world.create_entity()
        game.world.add_component(e, UIStateTag(GameState.PLAYING))
        game.trigger_death()
        assert e not in game.world.get(UIStateTag)


# ---------------------------------------------------------------------------
# Achievements (these never fired before the event-order fix)
# ---------------------------------------------------------------------------

class TestAchievements:

    def rm(self, game):
        return next(iter(game.world.get(RunModifier).values()))

    def test_lucky_bite(self, game):
        place_food_in_front(game.world, golden=True)
        game.update_playing()
        assert self.rm(game).lucky_bite

    def test_greedy_after_five_golden(self, game):
        for _ in range(5):
            place_food_in_front(game.world, golden=True)
            game.update_playing()
        assert self.rm(game).greedy

    def test_tiny_death_on_hard(self, game):
        Settings.set_difficulty("hard")
        game.world.get(Position)[head_of(game.world)].x = Settings.HALF_WIDTH
        game.update_playing()

        assert self.rm(game).tiny_death
        assert game.scoring.score > 0

    def test_perfect_run_on_wall_death(self, game):
        Settings.set_difficulty("hard")
        game.world.get(Position)[head_of(game.world)].x = Settings.HALF_WIDTH
        game.update_playing()
        assert self.rm(game).perfect_awarded


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

class TestObstacles:

    def test_every_insane_obstacle_moves(self):
        Settings.set_difficulty("insane")
        world = World()
        spawn_obstacles_ecs(world, Settings.obstacle_positions())

        obstacles = world.get(Obstacle)
        velocities = world.get(Velocity)
        assert obstacles
        assert all(e in velocities for e in obstacles)
        # no stray velocity on a non-obstacle entity
        assert all(e in obstacles for e in velocities)
        Settings.set_difficulty("normal")


class TestThemeCycle:

    def test_cycle_theme_recolors_food(self, game, monkeypatch):
        monkeypatch.setattr(snake.Themes, "apply", lambda *a, **k: None)
        monkeypatch.setattr(snake.Audio, "play_theme", lambda *a, **k: None)
        game.screen = None
        game.snake_pen = game.food_turtle = game.ui_pen = FakePen()

        game.cycle_theme()   # used to raise NameError on `e`

        food_e = next(iter(game.world.get(FoodTag)))
        assert game.world.get(RenderRequest)[food_e].color == snake.Themes.get("food")
        snake.Themes._current_index = 0
