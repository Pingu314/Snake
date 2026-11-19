"""Regression tests for the six gameplay bugs found in the audit.

Written before the fixes: each test failed on the old code.

Run with:
    python -m pytest tests/test_audit_bugs.py -v
"""

import random

import pytest

from v1_1.config.settings import Settings
from v1_1.core.ecs.components import Position, Velocity, Obstacle, ComboCounter, Food, \
    AchievementPopup
from v1_1.core.ecs.registry import World
from v1_1.core.ecs.systems import movement_system
from v1_1.core.game_state import GameState
from helpers import make_game, head_entity, place_food_in_front, run_modifier, make_world, add_snake_head


def obstacle_cells(world):
    return [(p.x, p.y) for e, p in world.get(Position).items() if e in world.get(Obstacle)]


# ---------------------------------------------------------------------------
# Bug 1: insane was unplayable (death on tick 1, obstacles gone after 1.2 s)
# ---------------------------------------------------------------------------

class TestInsaneObstacles:

    def test_no_death_at_the_start(self, tmp_path):
        """Without any input the snake must survive until it reaches the right wall."""
        deaths = 0
        for seed in range(100):
            random.seed(seed)
            game = make_game(tmp_path, "insane")
            for _ in range(15):          # head goes 40 -> 340, the wall is at 380
                game.update_playing()
            deaths += game.state.current != GameState.PLAYING
        assert deaths == 0

    def test_obstacles_stay_on_the_field(self):
        from v1_1.core.ecs.systems import obstacle_movement_system
        from v1_1.core.ecs.factories import spawn_obstacles_ecs

        world = World()
        world.settings.set_difficulty("insane")
        spawn_obstacles_ecs(world)
        start = len(world.get(Obstacle))
        min_x, max_x, min_y, max_y = world.settings.bounds()

        for _ in range(30_000 // world.settings.speed()):          # 30 seconds
            obstacle_movement_system(world)

        assert len(world.get(Obstacle)) == start
        assert all(min_x <= x <= max_x and min_y <= y <= max_y for x, y in obstacle_cells(world))

    def test_obstacle_blocks_move_as_one_piece(self):
        from v1_1.core.ecs.components import ObstacleMover
        from v1_1.core.ecs.systems import obstacle_movement_system
        from v1_1.core.ecs.factories import spawn_obstacles_ecs

        world = World()
        world.settings.set_difficulty("insane")
        spawn_obstacles_ecs(world)
        positions, movers = world.get(Position), world.get(ObstacleMover)

        def shapes():
            groups = {}
            for e in world.get(Obstacle):
                groups.setdefault(id(movers[e]), []).append((positions[e].x, positions[e].y))
            # each block's cells relative to its first cell
            return sorted(sorted((x - min(c)[0], y - min(c)[1]) for x, y in c) for c in groups.values())

        before = shapes()
        for _ in range(500):
            obstacle_movement_system(world)
        assert shapes() == before


# ---------------------------------------------------------------------------
# Bug 3: two quick turns inside one tick reversed the snake into itself
# ---------------------------------------------------------------------------

class TestQuickTurns:

    def test_up_then_left_within_one_tick(self, game):
        vel = game.world.get(Velocity)[head_entity(game.world)]

        game.turn("up")      # moving right: Up ...
        game.turn("left")    # ... then Left before the next tick
        game.update_playing()
        assert game.state.current == GameState.PLAYING
        assert (vel.dx, vel.dy) == (0, 20)       # first tick goes up

        game.update_playing()
        assert game.state.current == GameState.PLAYING
        assert (vel.dx, vel.dy) == (-20, 0)      # the queued Left follows

    def test_direct_reverse_is_ignored(self, game):
        vel = game.world.get(Velocity)[head_entity(game.world)]
        game.turn("left")
        game.update_playing()
        assert (vel.dx, vel.dy) == (20, 0)
        assert game.state.current == GameState.PLAYING


# ---------------------------------------------------------------------------
# Bug 4: the combo never changed the points
# ---------------------------------------------------------------------------

class TestComboPoints:

    def test_combo_raises_food_points(self, game):
        run_modifier(game).play_ms = 10_000   # no QUICK DRAW bonus
        points = []
        for _ in range(5):
            before = game.scoring.score
            place_food_in_front(game)
            game.update_playing()
            points.append(game.scoring.score - before)
        assert points == [10, 11, 12, 13, 14]

    def test_first_bite_starts_at_combo_one(self, game):
        place_food_in_front(game)
        game.update_playing()
        assert next(iter(game.world.get(ComboCounter).values())).value == 1


# ---------------------------------------------------------------------------
# Bug 5: "seconds" were counted as 60 FPS ticks, but the game ticks every 50-150 ms
# ---------------------------------------------------------------------------

class TestRealSeconds:

    @pytest.mark.parametrize("difficulty", Settings.difficulties())
    def test_combo_window_lasts_its_seconds(self, tmp_path, difficulty):
        game = make_game(tmp_path, difficulty)
        place_food_in_front(game)
        game.update_playing()

        combo = next(iter(game.world.get(ComboCounter).values()))
        assert combo.timer == game.settings.combo_window() * 1000

    @pytest.mark.parametrize("difficulty", Settings.difficulties())
    def test_popup_lasts_two_seconds(self, tmp_path, difficulty):
        from v1_1.core.ecs.factories import spawn_achievement_popup
        game = make_game(tmp_path, difficulty)
        spawn_achievement_popup(game.world, "NERVOUS")
        popup = next(iter(game.world.get(AchievementPopup).values()))
        assert popup.ms == 2000

    def test_insane_survivor_after_sixty_seconds(self, tmp_path):
        """Counted in real milliseconds: the tick gets shorter as the snake speeds up."""
        game = make_game(tmp_path, "insane")
        rm = run_modifier(game)

        rm.play_ms = 60_000 - 2 * game.settings.speed()
        game.update_playing()
        assert "INSANE_SURVIVOR" not in rm.earned

        game.update_playing()
        assert "INSANE_SURVIVOR" in rm.earned


# ---------------------------------------------------------------------------
# Bug 6: the insane speed factor 1.25 never reached the snake
# ---------------------------------------------------------------------------

def test_insane_head_moves_one_cell_per_tick():
    world = make_world("insane")
    e = add_snake_head(world)
    movement_system(world)
    assert world.get(Position)[e].x == 20


# ---------------------------------------------------------------------------
# Found by stress testing: moving obstacles vs. the snake
# ---------------------------------------------------------------------------

class TestMovingObstaclesAndSnake:
    """One single-cell moving block next to a short snake on insane."""

    def setup(self, tmp_path, body, velocity, block, step, food=(-300, 200)):
        from v1_1.core.ecs.components import ObstacleMover, Obstacle, SnakeSegment

        game = make_game(tmp_path, "insane")
        world = game.world
        for e in list(world.get(Obstacle)):
            world.remove_entity(e)

        for e, seg in world.get(SnakeSegment).items():
            world.get(Position)[e].x, world.get(Position)[e].y = body[seg.index]
        vel = world.get(Velocity)[head_entity(world)]
        vel.dx, vel.dy = velocity

        food_pos = world.get(Position)[next(iter(world.get(Food)))]
        food_pos.x, food_pos.y = food

        e = world.create_entity()
        world.add_component(e, Position(*block))
        world.add_component(e, Obstacle())
        mover = ObstacleMover(step)
        mover.elapsed = game.settings.OBSTACLE_STEP_SECONDS * 1000   # due: steps on the next tick
        world.add_component(e, mover)
        return game, world.get(Position)[e]

    def snake_cells(self, game):
        from v1_1.core.ecs.components import SnakeSegment
        pos = game.world.get(Position)
        return {(pos[e].x, pos[e].y) for e in game.world.get(SnakeSegment)}

    def test_head_and_block_cannot_swap(self, tmp_path):
        """Head 100 -> 120 while the block goes 120 -> 100: they used to pass through each other."""
        game, _ = self.setup(tmp_path, body=[(100, 0), (80, 0), (60, 0)], velocity=(20, 0),
                             block=(120, 0), step=-20)
        game.update_playing()
        assert game.state.current != GameState.PLAYING

    def test_block_bounces_off_the_body(self, tmp_path):
        """Snake goes up through x=100; the block next to the tail slides right into the body's column."""
        game, block = self.setup(tmp_path, body=[(100, 0), (100, -20), (100, -40)], velocity=(0, 20),
                                 block=(80, -20), step=20)
        game.update_playing()
        assert (block.x, block.y) not in self.snake_cells(game)
        assert (block.x, block.y) == (60, -20)          # bounced back
        assert game.state.current == GameState.PLAYING

    def test_block_does_not_cover_food(self, tmp_path):
        game, block = self.setup(tmp_path, body=[(100, 0), (80, 0), (60, 0)], velocity=(20, 0),
                                 block=(-160, 120), step=-20, food=(-200, 120))
        for _ in range(10):
            game.update_playing()
            assert (block.x, block.y) != (-200, 120)
        assert game.state.current == GameState.PLAYING
