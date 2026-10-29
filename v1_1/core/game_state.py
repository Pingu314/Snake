#v1.1 GameState Manager

from collections import defaultdict
from enum import Enum, auto

class GameState(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    HIGHSCORES = auto()
    GAME_OVER = auto()
    NAME_ENTRY = auto()
    RESTART_PROMPT = auto()

class GameStateManager:
    _current = GameState.TITLE
    _previous = GameState.TITLE

    # Each state can have several hooks; they run in registration order
    _on_enter = defaultdict(list)
    _on_exit = defaultdict(list)

    _tick = 0

    @classmethod
    def current(cls):
        return cls._current

    @classmethod
    def previous(cls):
        return cls._previous

    @classmethod
    def register_on_enter(cls, state, fn):
        cls._on_enter[state].append(fn)

    @classmethod
    def register_on_exit(cls, state, fn):
        cls._on_exit[state].append(fn)

    @classmethod
    def clear_hooks(cls):
        cls._on_enter.clear()
        cls._on_exit.clear()

    @classmethod
    def set_state(cls, new_state):
        if cls._current == new_state:
            return

        for fn in cls._on_exit[cls._current]:
            fn()

        cls._previous = cls._current
        cls._current = new_state

        for fn in cls._on_enter[new_state]:
            fn()

    @classmethod
    def tick(cls):
        cls._tick += 1

    @classmethod
    def ticks(cls):
        return cls._tick
