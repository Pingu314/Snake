#ECS Components

class SnakeHead: pass
class Obstacle: pass

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SnakeSegment:
    def __init__(self, index):
        self.index = index

class Food:
    def __init__(self, golden=False):
        self.golden = golden

class PreviousPosition:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Velocity:
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

class TurnBuffer:
    """Turns pressed since the last tick, applied one per tick."""
    def __init__(self):
        self.turns = []

class ObstacleMover:
    """Shared by every cell of one moving obstacle block, so the block moves as one piece."""
    def __init__(self, step):
        self.step = step
        self.elapsed = 0            # ms since the block last moved

class RenderRequest:
    def __init__(self, color_key, kind):
        self.color_key = color_key  # theme key, looked up while drawing (None for the pause overlay)
        self.kind = kind

class NameEntry:
    def __init__(self):
        self.text = ""
        self.max_len = 3            # arcade-style initials

class ComboGlow:
    def __init__(self, ms):
        self.ms = ms                # time left
        self.max_ms = ms

class ComboCounter:
    def __init__(self):
        self.value = 1
        self.timer = 0              # ms left in the combo window

class GameEvent:
    def __init__(self, kind, entity = None):
        self.kind = kind
        self.entity = entity

class RunModifier:
    """Per-run bookkeeping for the multiplier and achievements."""
    def __init__(self):
        self.perfect = True        # still eligible for the perfect multiplier / PERFECT RUN
        self.earned = set()        # achievement ids already awarded this run

        self.pause_times = []      # game clock (ms) of recent pauses
        self.play_ms = 0           # time alive in this run
        self.ms_since_food = 0
        self.foods_eaten = 0
        self.golden_eaten = 0
        self.last_food_golden = False
        self.wraps = 0             # times the head went through a wrapping edge

class Countdown:
    """3-2-1 before the snake moves (start of a run and after a pause)."""
    def __init__(self, ms, step):
        self.ms = ms               # time left
        self.step = step           # ms per shown number

class AchievementPopup:
    def __init__(self, index, ms):
        self.index = index
        self.ms = ms               # time left on screen

class ScoreEvent:
    def __init__(self, value):
        self.value = value
