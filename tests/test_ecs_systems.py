"""Unit tests for Snake v1.1 ECS systems.

Each test creates a minimal World with only the components needed for the
system under test. Every World brings its own Settings/Themes/StateMachine,
so tests never leak state into each other. No Turtle/tkinter objects are
touched, so these run headlessly under pytest without a display.

Run with:
    python -m pytest tests/test_ecs_systems.py -v
"""

from v1_1.core.ecs.components import (
    Position,
    GameEvent, ComboCounter, RunModifier, ScoreEvent,
)
from v1_1.core.ecs.systems import (
    movement_system,
    boundary_system,
    game_over_system,
    scoring_system,
    combo_decay_system,
)
from v1_1.logic.scoring import Scoring
from helpers import make_world, add_snake_head


def set_walls(world, wrap):
    world.settings.wrap_override = wrap
    return boundary_system(world)


# ---------------------------------------------------------------------------
# movement_system
# ---------------------------------------------------------------------------

class TestMovementSystem:

    def test_head_moves_right(self):
        world = make_world()
        head = add_snake_head(world, x=0, y=0, dx=20, dy=0)
        movement_system(world)
        pos = world.get(Position)[head]
        assert (pos.x, pos.y) == (20, 0)

    def test_head_moves_up(self):
        world = make_world()
        head = add_snake_head(world, x=0, y=0, dx=0, dy=20)
        movement_system(world)
        pos = world.get(Position)[head]
        assert (pos.x, pos.y) == (0, 20)

    def test_head_moves_left(self):
        world = make_world()
        head = add_snake_head(world, x=100, y=0, dx=-20, dy=0)
        movement_system(world)
        assert world.get(Position)[head].x == 80


# ---------------------------------------------------------------------------
# boundary_system  (wrap mode)
# ---------------------------------------------------------------------------

class TestBoundarySystemWrap:

    def test_wraps_right_to_left(self):
        world = make_world()
        head = add_snake_head(world, x=400, y=0)
        set_walls(world, wrap=True)
        assert world.get(Position)[head].x == -world.settings.half_width

    def test_wraps_left_to_right(self):
        world = make_world()
        head = add_snake_head(world, x=-400, y=0)
        set_walls(world, wrap=True)
        assert world.get(Position)[head].x == world.settings.half_width

    def test_wraps_top_to_bottom(self):
        world = make_world()
        head = add_snake_head(world, x=0, y=world.settings.half_height + 20)
        set_walls(world, wrap=True)
        assert world.get(Position)[head].y == -world.settings.half_height

    def test_no_wrap_returns_true_on_oob(self):
        world = make_world()
        add_snake_head(world, x=400, y=0)
        assert set_walls(world, wrap=False) is True

    def test_in_bounds_no_wrap_returns_false(self):
        world = make_world()
        add_snake_head(world, x=0, y=0)
        assert set_walls(world, wrap=False) is False

    def test_wrap_mode_defaults_to_difficulty(self):
        world = make_world("hard")      # hard has walls
        add_snake_head(world, x=400, y=0)
        assert boundary_system(world) is True


# ---------------------------------------------------------------------------
# game_over_system
# ---------------------------------------------------------------------------

class TestGameOverSystem:

    def test_death_event_reports_game_over(self):
        world = make_world()
        world.add_component(world.create_entity(), GameEvent("DEATH"))
        assert game_over_system(world) is True

    def test_death_event_is_cleaned_up(self):
        world = make_world()
        world.add_component(world.create_entity(), GameEvent("DEATH"))
        game_over_system(world)
        assert len(world.get(GameEvent)) == 0

    def test_no_death_event_keeps_playing(self):
        world = make_world()
        world.add_component(world.create_entity(), GameEvent("FOOD_HIT", None))
        assert game_over_system(world) is False
        assert len(world.get(GameEvent)) == 1


# ---------------------------------------------------------------------------
# scoring_system
# ---------------------------------------------------------------------------

class TestScoringSystem:

    def test_score_event_applied(self):
        world = make_world()
        scoring = Scoring()
        world.add_component(world.create_entity(), ScoreEvent(10))
        scoring_system(world, scoring)
        assert scoring.score == 10

    def test_score_event_consumed(self):
        world = make_world()
        scoring = Scoring()
        world.add_component(world.create_entity(), ScoreEvent(10))
        scoring_system(world, scoring)
        assert len(world.get(ScoreEvent)) == 0

    def test_perfect_multiplier_applied(self):
        """An unpaused run on hard scores x1.25 (the multiplier comes from RunModifier)."""
        world = make_world("hard")
        scoring = Scoring()
        world.add_component(world.create_entity(), RunModifier())
        world.add_component(world.create_entity(), ScoreEvent(10))
        scoring_system(world, scoring)
        assert scoring.score == 12   # round(12.5)

    def test_no_multiplier_after_pause(self):
        world = make_world("hard")
        scoring = Scoring()
        rm = RunModifier()
        rm.perfect = False
        world.add_component(world.create_entity(), rm)
        world.add_component(world.create_entity(), ScoreEvent(10))
        scoring_system(world, scoring)
        assert scoring.score == 10


# ---------------------------------------------------------------------------
# combo_decay_system
# ---------------------------------------------------------------------------

class TestComboDecaySystem:

    def make_combo(self, world, value, timer):
        combo = ComboCounter()
        combo.value, combo.timer = value, timer
        world.add_component(world.create_entity(), combo)
        world.add_component(world.create_entity(), RunModifier())
        return combo

    def test_combo_timer_decrements(self):
        world = make_world()
        combo = self.make_combo(world, value=3, timer=1000)
        combo_decay_system(world)
        assert combo.timer == 1000 - world.settings.speed()     # one tick of real time

    def test_combo_resets_when_timer_expires(self):
        world = make_world()
        combo = self.make_combo(world, value=5, timer=1)
        combo_decay_system(world)
        assert combo.value == 1
