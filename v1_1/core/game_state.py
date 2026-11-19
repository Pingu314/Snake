#v1.1 GameState Manager

from collections import defaultdict
from enum import Enum, auto

class GameState(Enum):
    TITLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    HIGHSCORES = auto()
    SETTINGS = auto()
    NAME_ENTRY = auto()
    RESTART_PROMPT = auto()

class StateMachine:
    def __init__(self):
        self.current = GameState.TITLE
        self.ms = 0                 # game clock: real time since start, advanced every tick

        # Each state can have several hooks; they run in registration order
        self._on_enter = defaultdict(list)
        self._on_exit = defaultdict(list)

    def register_on_enter(self, state, fn):
        self._on_enter[state].append(fn)

    def register_on_exit(self, state, fn):
        self._on_exit[state].append(fn)

    def set_state(self, new_state):
        if self.current == new_state:
            return

        for fn in self._on_exit[self.current]:
            fn()

        self.current = new_state

        for fn in self._on_enter[new_state]:
            fn()

    def tick(self, ms):
        self.ms += ms
