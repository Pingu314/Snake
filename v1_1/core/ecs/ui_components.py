#ECS v1.1 ui components

from v1_1.config.layout import FONT_TEXT

class UILabel:
    def __init__(self, text="", x=0, y=0, align="center", font=FONT_TEXT, color=None):
        self.text = text
        self.x = x
        self.y = y
        self.align = align
        self.font = font
        self.color = color      # theme key (e.g. "message"); None = the normal HUD text colour

class UIStateTag:
    def __init__(self, state):
        self.state = state
