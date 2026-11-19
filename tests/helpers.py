"""Shared test helpers: a headless Game plus small helpers to steer, feed and kill the snake."""

import snake
from v1_1.core.ecs.components import Position, SnakeHead, Food, RunModifier, Velocity
from v1_1.core.ecs.registry import World
from v1_1.core.ecs.systems import BoardRenderer
from v1_1.core.ecs.ui_components import UILabel, UIStateTag
from v1_1.core.game_state import GameState


class FakePen:
    """Stands in for a turtle: accepts every call and remembers what was written."""
    def __init__(self):
        self.written = []

    def write(self, text, **kwargs):
        self.written.append(text)

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class FakeMusic:
    """Stands in for pygame.mixer.music: records the calls made and the volumes set."""
    def __init__(self):
        self.calls, self.volumes = [], []

    def set_volume(self, volume):
        self.calls.append("set_volume")
        self.volumes.append(volume)

    def __getattr__(self, name):
        return lambda *args, **kwargs: self.calls.append(name)


class FakeCanvas:
    """Stands in for the turtle canvas: hands out item ids and remembers line coordinates."""
    def __init__(self):
        self.items, self.next_id = {}, 0

    def create_line(self, *coords, **options):
        self.next_id += 1
        self.items[self.next_id] = list(coords)
        return self.next_id

    def coords(self, item, *coords):
        self.items[item] = list(coords)

    def delete(self, item):
        self.items.pop(item, None)

    def itemconfigure(self, item, **options):
        pass


class FakeScreen:
    def update(self): pass
    def ontimer(self, fn, ms): pass
    def bgcolor(self, color): pass


def make_game(tmp_path, difficulty="normal", start=False):
    """A Game without a window, in a run on `difficulty`.

    start=True goes through Game.start_game() and the state hooks (so the countdown runs)
    and gives the game fake pens and a fake screen, so Game.tick() works."""
    game = snake.Game(highscore_file=tmp_path / "highscore.txt", preferences_file=tmp_path / "settings.json")
    game.settings.set_difficulty(difficulty)
    if start:
        game.screen = FakeScreen()
        game.ui_pen = game.score_pen = FakePen()
        game.renderer = BoardRenderer({"snake": FakePen(), "food": FakePen(), "overlay": FakePen()}, FakeCanvas())
        game.frame_pen = FakePen()
        game.start_game()
    else:
        game.state.current = GameState.PLAYING
        game.reset_game()
    return game


def head_entity(world):
    return next(iter(world.get(SnakeHead)))


def head(game):
    return game.world.get(Position)[head_entity(game.world)]


def run_modifier(game):
    return next(iter(game.world.get(RunModifier).values()))


def place_food_in_front(game, golden=False):
    """Move the food right in front of the head (the snake starts moving right)."""
    world = game.world
    food = next(iter(world.get(Food)))
    pos = world.get(Position)[food]
    pos.x, pos.y = head(game).x + game.settings.grid_size, head(game).y
    world.get(Food)[food].golden = golden


def eat(game, golden=False):
    place_food_in_front(game, golden)
    game.update_playing()


def drive_into_wall(game):
    """Put the head on the right edge with solid walls and take one step."""
    game.settings.wrap_override = False
    head(game).x = game.settings.half_width
    game.update_playing()


def labels(game, state=None):
    """Texts of the UI labels, optionally only those shown in `state`."""
    tags = game.world.get(UIStateTag)
    return [label.text for e, label in game.world.get(UILabel).items()
            if state is None or (e in tags and tags[e].state == state)]


def make_world(difficulty="normal"):
    """A fresh, empty World (own Settings/Themes/StateMachine)."""
    world = World()
    world.settings.set_difficulty(difficulty)
    return world


def add_snake_head(world, x=0, y=0, dx=20, dy=0):
    """Spawn a bare snake head entity and return its id."""
    e = world.create_entity()
    world.add_component(e, SnakeHead())
    world.add_component(e, Position(x, y))
    world.add_component(e, Velocity(dx, dy))
    return e
