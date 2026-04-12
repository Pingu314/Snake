#ECS Components

class FoodTag: pass
class SnakeTag: pass
class SnakeHead: pass
class Obstacle: pass
class ScoreDisplay: pass

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SnakeSegment:
    def __init__(self, index):
        self.index = index

class Collider:
    def __init__(self, radius=10):
        self.radius = radius

class Food:
    def __init__(self, golden=False):
        self.golden = golden

class PreviousPosition:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Facing:
    def __init__(self, angle = 0):
        self.angle = angle

class Velocity:
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

class RenderRequest:
    def __init__(self,shape, color, kind):
        self.shape = shape
        self.color = color
        self.kind = kind

class NameEntry:
    def __init__(self, max_len = 10):
        self.text = ""
        self.max_len = max_len
        self.blink_timer = 0

class ComboGlow:
    def __init__(self, ticks = 10):
        self.ticks = ticks
        self.max_ticks = ticks

class UIFade:
    def __init__(self, speed = 0.05):
        self.alpha = 0.0
        self.fade_speed = speed

class ComboCounter:
    def __init__(self):
        self.value = 1
        self.timer = 0

class GameEvent:
    def __init__(self, kind, entity = None):
        self.kind = kind
        self.entity = entity

class RunModifier:
    def __init__(self):
        self.perfect = True
        self.perfect_awarded = False
        self.combo_god = False
        self.long_snake = False
        self.tiny_death = False
        self.greedy = False
        self.lucky_bite = False
        self.nervous = False
        self.insane_survivor = False

        self.pause_ticks = []
        self.insane_ticks = 0
        self.golden_eaten = 0

class AchievementPopup:
    def __init__(self, achievement_id, index,  ticks = 120):
        self.id = achievement_id
        self.index = index
        self.ticks = ticks

class Score:
    def __init__(self):
        self.value = 0

class ScoreEvent:
    def __init__(self, kind, value=None):
        self.kind = kind
        self.value = value