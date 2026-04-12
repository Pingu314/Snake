#ECS v1.1 ui components

class UILabel:
    def __init__(self, text="", x=0, y=0, align="center", font=("Arial",16,"normal")):
        self.text = text
        self.x = x
        self.y = y
        self.align = align
        self.font = font
        self.alpha = 0.0
        self.fade_speed = 0.05

class UIStateTag:
    def __init__(self, state):
        self.state = state