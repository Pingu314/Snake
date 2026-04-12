#v1.1 Scoring
from v1_1.config.AchievementConfig import ACHIEVEMENTS
from v1_1.config.Settings import Settings
from v1_1.core.ecs.Components import RunModifier, ScoreEvent


class Scoring:
    def __init__(self, combo_window = None):
        self.score = 0
        self.combo_window = combo_window
        self.combo = 1
        self.multiplier = 1.0

    def apply(self, event: ScoreEvent):
        if event.value is None:
            return
        self.score += int(event.value * self.multiplier)

    def set_combo(self, combo):
        self.combo = combo

    def set_multiplier(self, mul):
        self.multiplier = mul

    def reset(self):
        self.score = 0
        self.combo = 1
        self.multiplier = 1.0
