#v1.1 Scoring
from v1_1.config.achievement_config import COMBO_BONUS_PER_STEP
from v1_1.core.ecs.components import ScoreEvent


def food_points(base, combo):
    """Points for one food: every combo step above 1 adds COMBO_BONUS_PER_STEP."""
    return round(base * (1 + COMBO_BONUS_PER_STEP * (combo - 1)))


class Scoring:
    def __init__(self):
        self.score = 0
        self.multiplier = 1.0

    def apply(self, event: ScoreEvent):
        self.score += round(event.value * self.multiplier)

    def set_multiplier(self, mul):
        self.multiplier = mul

    def reset(self):
        self.score = 0
        self.multiplier = 1.0
