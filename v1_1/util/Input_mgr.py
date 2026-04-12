# v1.1 Input handling

class Input:

    def __init__(self, screen):
        self.screen = screen
        self.bindings = {}

    def bind(self, key, fn):
        self.bindings[key] = fn
        self.screen.onkey(fn, key)

    def apply(self):
        for k, fn in self.bindings.items():
            self.screen.onkey(fn,k)

    def clear(self):
        for k in self.bindings:
            self.screen.onkey(None, k)
        self.bindings.clear()