"""Unit tests for Snake v1.1 ECS systems.

Each test creates a minimal World with only the components needed for the
system under test. No Turtle/tkinter objects are touched so these run
headlessly under pytest without a display.

Run with:
    python -m pytest tests/test_ecs_systems.py -v
"""

import pytest
from v1_1.core.ecs.Registry import World
from v1_1.core.ecs.Components import (
    Position, Velocity, SnakeHead, SnakeSegment, Collider,
    FoodTag, Food, Facing, PreviousPosition,
    GameEvent, ComboCounter, RunModifier, Score, ScoreEvent,
    Obstacle,
)
from v1_1.core.ecs.Systems import (
    movement_system,
    facing_system,
    boundary_system,
    snap_to_grid_system,
    collision_system,
    game_over_system,
    scoring_system,
    combo_decay_system,
)
from v1_1.core.Gamestate import Gamestate, GameStateManager
from v1_1.config.Settings import Settings
from v1_1.logic.Scoring import Scoring


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_world():
    """Return a fresh, empty World."""
    return World()


def add_snake_head(world, x=0, y=0, dx=20, dy=0):
    """Spawn a snake head entity and return its ID."""
    e = world.create_entity()
    world.add_component(e, SnakeHead())
    world.add_component(e, Position(x, y))
    world.add_component(e, Velocity(dx, dy))
    world.add_component(e, Collider())
    world.add_component(e, Facing())
    return e


# ---------------------------------------------------------------------------
# movement_system
# ---------------------------------------------------------------------------

class TestMovementSystem:

    def test_head_moves_right(self):
        world = make_world()
        Settings.difficulty = "normal"
        head = add_snake_head(world, x=0, y=0, dx=20, dy=0)
        movement_system(world)
        pos = world.get(Position)[head]
        assert pos.x == 20
        assert pos.y == 0

    def test_head_moves_up(self):
        world = make_world()
        Settings.difficulty = "normal"
        head = add_snake_head(world, x=0, y=0, dx=0, dy=20)
        movement_system(world)
        pos = world.get(Position)[head]
        assert pos.x == 0
        assert pos.y == 20

    def test_head_moves_left(self):
        world = make_world()
        Settings.difficulty = "normal"
        head = add_snake_head(world, x=100, y=0, dx=-20, dy=0)
        movement_system(world)
        pos = world.get(Position)[head]
        assert pos.x == 80

    def test_insane_speed_multiplier(self):
        """In insane mode the velocity is scaled by 1.25."""
        world = make_world()
        Settings.difficulty = "insane"
        head = add_snake_head(world, x=0, y=0, dx=20, dy=0)
        movement_system(world)
        pos = world.get(Position)[head]
        # 20 * 1.25 = 25, stored as int
        assert pos.x == 25
        Settings.difficulty = "normal"


# ---------------------------------------------------------------------------
# facing_system
# ---------------------------------------------------------------------------

class TestFacingSystem:

    def test_facing_right(self):
        world = make_world()
        head = add_snake_head(world, dx=20, dy=0)
        facing_system(world)
        assert world.get(Facing)[head].angle == 0

    def test_facing_up(self):
        world = make_world()
        head = add_snake_head(world, dx=0, dy=20)
        facing_system(world)
        assert world.get(Facing)[head].angle == 90

    def test_facing_left(self):
        world = make_world()
        head = add_snake_head(world, dx=-20, dy=0)
        facing_system(world)
        assert world.get(Facing)[head].angle == 180

    def test_facing_down(self):
        world = make_world()
        head = add_snake_head(world, dx=0, dy=-20)
        facing_system(world)
        assert world.get(Facing)[head].angle == 270


# ---------------------------------------------------------------------------
# boundary_system  (wrap mode)
# ---------------------------------------------------------------------------

class TestBoundarySystemWrap:

    def test_wraps_right_to_left(self):
        world = make_world()
        head = add_snake_head(world, x=400, y=0)
        boundary_system(world, wrap=True)
        pos = world.get(Position)[head]
        assert pos.x == -380    # min_x

    def test_wraps_left_to_right(self):
        world = make_world()
        head = add_snake_head(world, x=-400, y=0)
        boundary_system(world, wrap=True)
        pos = world.get(Position)[head]
        assert pos.x == 380

    def test_wraps_top_to_bottom(self):
        world = make_world()
        head = add_snake_head(world, x=0, y=300)
        boundary_system(world, wrap=True)
        pos = world.get(Position)[head]
        assert pos.y == -280

    def test_no_wrap_returns_true_on_oob(self):
        world = make_world()
        add_snake_head(world, x=400, y=0)
        result = boundary_system(world, wrap=False)
        assert result is True

    def test_in_bounds_no_wrap_returns_false(self):
        world = make_world()
        add_snake_head(world, x=0, y=0)
        result = boundary_system(world, wrap=False)
        assert result is False


# ---------------------------------------------------------------------------
# snap_to_grid_system
# ---------------------------------------------------------------------------

class TestSnapToGridSystem:

    def test_snaps_to_nearest_grid(self):
        world = make_world()
        head = add_snake_head(world, x=13, y=7)
        snap_to_grid_system(world, grid_size=20)
        pos = world.get(Position)[head]
        assert pos.x == 20
        assert pos.y == 0

    def test_already_on_grid(self):
        world = make_world()
        head = add_snake_head(world, x=40, y=60)
        snap_to_grid_system(world, grid_size=20)
        pos = world.get(Position)[head]
        assert pos.x == 40
        assert pos.y == 60


# ---------------------------------------------------------------------------
# game_over_system
# ---------------------------------------------------------------------------

class TestGameOverSystem:

    def setup_method(self):
        GameStateManager.set_state(Gamestate.PLAYING)

    def test_death_event_triggers_game_over(self):
        world = make_world()
        e = world.create_entity()
        world.add_component(e, GameEvent("DEATH", None))
        game_over_system(world)
        assert GameStateManager.current() == Gamestate.GAME_OVER

    def test_death_event_is_cleaned_up(self):
        world = make_world()
        e = world.create_entity()
        world.add_component(e, GameEvent("DEATH", None))
        game_over_system(world)
        assert len(world.get(GameEvent)) == 0

    def test_no_death_event_does_not_change_state(self):
        world = make_world()
        e = world.create_entity()
        world.add_component(e, GameEvent("FOOD_HIT", None))
        game_over_system(world)
        assert GameStateManager.current() == Gamestate.PLAYING


# ---------------------------------------------------------------------------
# scoring_system
# ---------------------------------------------------------------------------

class TestScoringSystem:

    def test_score_event_applied(self):
        world = make_world()
        scoring = Scoring()
        e = world.create_entity()
        world.add_component(e, ScoreEvent("FOOD", 10))
        scoring_system(world, scoring)
        assert scoring.score == 10

    def test_score_event_consumed(self):
        world = make_world()
        scoring = Scoring()
        e = world.create_entity()
        world.add_component(e, ScoreEvent("FOOD", 10))
        scoring_system(world, scoring)
        assert len(world.get(ScoreEvent)) == 0

    def test_multiplier_applied(self):
        world = make_world()
        scoring = Scoring()
        scoring.set_multiplier(2.0)
        e = world.create_entity()
        world.add_component(e, ScoreEvent("FOOD", 10))
        scoring_system(world, scoring)
        assert scoring.score == 20


# ---------------------------------------------------------------------------
# combo_decay_system
# ---------------------------------------------------------------------------

class TestComboDecaySystem:

    def test_combo_timer_decrements(self):
        world = make_world()
        Settings.difficulty = "normal"
        e = world.create_entity()
        combo = ComboCounter()
        combo.value = 3
        combo.timer = 100
        world.add_component(e, combo)
        rm_entity = world.create_entity()
        world.add_component(rm_entity, RunModifier())
        combo_decay_system(world)
        assert combo.timer == 99

    def test_combo_resets_when_timer_expires(self):
        world = make_world()
        Settings.difficulty = "normal"
        e = world.create_entity()
        combo = ComboCounter()
        combo.value = 5
        combo.timer = 1
        world.add_component(e, combo)
        rm_entity = world.create_entity()
        world.add_component(rm_entity, RunModifier())
        combo_decay_system(world)
        assert combo.value == 1
