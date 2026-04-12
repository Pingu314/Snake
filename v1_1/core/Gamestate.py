#v1.1 GameState Manager

from enum import Enum,auto

class Gamestate(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    HIGHSCORES = auto()
    GAME_OVER = auto()
    NAME_ENTRY = auto()
    RESTART_PROMPT = auto()

class GameStateManager:
    _current = Gamestate.TITLE
    _previous = Gamestate.TITLE

    _on_enter = {}
    _on_exit = {}

    _tick = 0

    @classmethod
    def current(cls):
        return cls._current

    @classmethod
    def previous(cls):
        return cls._previous

    @classmethod
    def register_on_enter(cls, state, fn):
        cls._on_enter[state] = fn

    @classmethod
    def register_on_exit(cls, state, fn):
        cls._on_exit[state] = fn

    @classmethod
    def set_state(cls, new_state):
        if cls._current == new_state:
            return

        if cls._current in cls._on_exit:
            cls._on_exit[cls._current]()

        cls._previous = cls._current
        cls._current = new_state

        if new_state in cls._on_enter:
            cls._on_enter[new_state]()

    @classmethod
    def tick(cls):
        cls._tick += 1

    @classmethod
    def ticks(cls):
        return cls._tick