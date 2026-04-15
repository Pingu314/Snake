# Themes v1.1

from pathlib import Path
from v1_1.config.Paths import SOUNDS_DIR

class Themes:
    _screen = None
    _themes = [{"name": "Classic",
                "bg": "#0b1c2d",
                "snake": "#b0b0b0",
                "snake_head": "#e0e0e0",
                "snake_body": "#b0b0b0",
                "obstacle": "#3a4a5c",
                "food": "#d62828",
                "food_gold": "#fcbf49",
                "combo_glow": "#ffffff",
                "combo_glow_strong": "#ffd166",
                "hud_text": "#80ed99",
                "message": "#fcbf49",
                "music": "theme_classic.mp3"},

               {"name": "Neon",
                "bg": "#000000",
                "snake": "#00ffff",
                "snake_head": "#ffffff",
                "snake_body": "#00ffff",
                "obstacle": "#222222",
                "food": "#ff00ff",
                "food_gold": "#ffff00",
                "combo_glow": "#ffffff",
                "combo_glow_strong": "#00ffea",
                "hud_text": "#ffffff",
                "message": "#00ffff",
                "music": "themeloop_neon.mp3"},

               {"name": "Cyberpunk",
                "bg": "#0b0014",
                "snake": "#00ffff",
                "snake_head": "#ffffff",
                "snake_body": "#00ffff",
                "obstacle": "#1f0033",
                "food": "#ff00ff",
                "food_gold": "#ffd700",
                "combo_glow": "#00ff9c",
                "combo_glow_strong": "#ffffff",
                "hud_text": "#f8f8ff",
                "message": "#00ff9c",
                "music": "themelooped_cyber.wav"},

               {"name": "Lava",
                "bg": "#0d0d0d",
                "snake": "#ff4500",
                "snake_head": "#ffd1a1",
                "snake_body": "#ff4500",
                "obstacle": "#4a1a00",
                "food": "#ffa400",
                "food_gold": "#fff1a8",
                "combo_glow": "#ffffff",
                "combo_glow_strong": "#ffae00",
                "hud_text": "#ff8c00",
                "message": "#ff0000",
                "music": "themeslooped_lava.wav"},

               {"name": "Mint",
                "bg": "#E8F5E9",
                "snake": "#2E7D32",
                "snake_head": "#1B5E20",
                "snake_body": "#2E7D32",
                "obstacle": "#A5D6A7",
                "food": "#D32F2F",
                "food_gold": "#FBC02D",
                "combo_glow": "#66BB6A",
                "combo_glow_strong": "#1B5E20",
                "hud_text": "#1B5E20",
                "message": "#2E7D32",
                "music": "theme_mint.mp3"},

               {"name": "Sunset",
                "bg": "#FFF3E0",
                "snake": "#E65100",
                "snake_head": "#BF360C",
                "snake_body": "#E65100",
                "obstacle": "#FFCCBC",
                "food": "#D84315",
                "food_gold": "#FFB300",
                "combo_glow": "#FF8F00",
                "combo_glow_strong": "#E65100",
                "hud_text": "#4E342E",
                "message": "#BF360C",
                "music": "theme_sunset.mp3"},

               {"name": "Candy",
                "bg": "#FFF0F6",
                "snake": "#AD1457",
                "snake_head": "#880E4F",
                "snake_body": "#AD1457",
                "obstacle": "#F8BBD0",
                "food": "#6A1B9A",
                "food_gold": "#FDD835",
                "combo_glow": "#EC407A",
                "combo_glow_strong": "#6A1B9A",
                "hud_text": "#880E4F",
                "message": "#6A1B9A",
                "music": "theme_candy.mp3"}]

    _current_index = 0

    @classmethod
    def current(cls):
        return cls._themes[cls._current_index]

    @classmethod
    def next(cls):
        cls._current_index = (cls._current_index + 1) % len(cls._themes)

    @classmethod
    def current_name(cls):
        return cls.current()["name"]

    @classmethod
    def apply (cls,screen,turtles):
        cls._screen = screen
        theme = cls.current()
        screen.bgcolor(theme["bg"])
        turtles["snake"].color(theme["snake"])
        turtles["food"].color(theme["food"])
        turtles["text"].color(theme["hud_text"])
        if "hud" in turtles:
            turtles["hud"].color(theme["hud_text"])

    @classmethod
    def get(cls,key):
        return cls.current().get(key,"white")

    @classmethod
    def music(cls) -> Path:
        return SOUNDS_DIR / "music" / cls.current()["music"]

    @staticmethod
    def tint(color, overlay):
        return overlay if overlay else color
