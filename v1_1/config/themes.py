# Themes v1.1

from pathlib import Path
from v1_1.config.paths import SOUNDS_DIR

class Themes:
    """The active visual theme. THEMES is the fixed list, the instance tracks which one is active.

    Palettes keep a similar contrast and avoid pure neon colours, so switching themes
    doesn't jump from calm to glaring. Per theme:
      bg        playfield            frame   everything outside the field (margins, HUD band)
      wall      deadly field edge    border  field edge when the snake wraps
      music_gain  brings every track to the same loudness (measured RMS, quietest track = 1.0)
    """

    THEMES = [{"name": "Classic",
                "bg": "#0b1c2d",
                "frame": "#1a3550",
                "wall": "#e06666",
                "border": "#3b5b7a",
                "snake_head": "#e6e6e6",
                "snake_body": "#a9b4bf",
                "obstacle": "#46607a",
                "food": "#e06666",
                "food_gold": "#f2c14e",
                "combo_glow": "#ffffff",
                "combo_glow_strong": "#f2c14e",
                "hud_text": "#8fd6a4",
                "message": "#f2c14e",
                "music": "theme_classic.mp3",
                "music_gain": 0.62},

               {"name": "Neon",
                "bg": "#0c0c16",
                "frame": "#1c1c30",
                "wall": "#f0708c",
                "border": "#36365a",
                "snake_head": "#e6f9ff",
                "snake_body": "#5ccfdc",
                "obstacle": "#3a3a60",
                "food": "#d66ad0",
                "food_gold": "#e8d870",
                "combo_glow": "#ffffff",
                "combo_glow_strong": "#7fe3da",
                "hud_text": "#d6e2ee",
                "message": "#7fe3da",
                "music": "themeloop_neon.mp3",
                "music_gain": 0.47},

               {"name": "Cyberpunk",
                "bg": "#140c20",
                "frame": "#261a3a",
                "wall": "#f07070",
                "border": "#45345f",
                "snake_head": "#efe6ff",
                "snake_body": "#52bfcc",
                "obstacle": "#4a3468",
                "food": "#cc66b0",
                "food_gold": "#e2c060",
                "combo_glow": "#76e0b0",
                "combo_glow_strong": "#efe6ff",
                "hud_text": "#e2dcee",
                "message": "#76e0b0",
                "music": "themelooped_cyber.wav",
                "music_gain": 0.65},

               {"name": "Lava",
                "bg": "#161111",
                "frame": "#2b1f1c",
                "wall": "#f06a4a",
                "border": "#4f3a33",
                "snake_head": "#ffd9b3",
                "snake_body": "#e07a45",
                "obstacle": "#634032",
                "food": "#eba545",
                "food_gold": "#f5e6a0",
                "combo_glow": "#ffe0c0",
                "combo_glow_strong": "#f5b55a",
                "hud_text": "#eba56a",
                "message": "#f0a070",
                "music": "themeslooped_lava.ogg",
                "music_gain": 1.0},

               {"name": "Mint",
                "bg": "#e8f5e9",
                "frame": "#c9e5cb",
                "wall": "#c74a4a",
                "border": "#9ccaa0",
                "snake_head": "#1f5c24",
                "snake_body": "#46a04c",
                "obstacle": "#86bd8a",
                "food": "#d05050",
                "food_gold": "#d9a520",
                "combo_glow": "#6cba70",
                "combo_glow_strong": "#1f5c24",
                "hud_text": "#1f5c24",
                "message": "#2f7a35",
                "music": "theme_mint.mp3",
                "music_gain": 0.81},

               {"name": "Sunset",
                "bg": "#fff3e0",
                "frame": "#f5dcc0",
                "wall": "#c74a3a",
                "border": "#e3bf9c",
                "snake_head": "#a5481f",
                "snake_body": "#dd7c40",
                "obstacle": "#e2ab88",
                "food": "#c8503a",
                "food_gold": "#e0a020",
                "combo_glow": "#eca050",
                "combo_glow_strong": "#a5481f",
                "hud_text": "#4e342e",
                "message": "#a5481f",
                "music": "theme_sunset.mp3",
                "music_gain": 0.62},

               {"name": "Candy",
                "bg": "#fff0f6",
                "frame": "#f5d3e2",
                "wall": "#c74a5a",
                "border": "#e6b8cc",
                "snake_head": "#86244f",
                "snake_body": "#c04a7e",
                "obstacle": "#e2a4c0",
                "food": "#7d48a8",
                "food_gold": "#dcae2a",
                "combo_glow": "#e47aa0",
                "combo_glow_strong": "#7d48a8",
                "hud_text": "#7a254c",
                "message": "#7d48a8",
                "music": "theme_candy.mp3",
                "music_gain": 0.67}]

    def __init__(self):
        self._current_index = 0

    def current(self):
        return self.THEMES[self._current_index]

    def next(self, step=1):
        self._current_index = (self._current_index + step) % len(self.THEMES)

    def current_name(self):
        return self.current()["name"]

    def set_by_name(self, name):
        for i, theme in enumerate(self.THEMES):
            if theme["name"] == name:
                self._current_index = i
                return

    def get(self, key):
        return self.current()[key]

    def music(self) -> Path:
        return SOUNDS_DIR / "music" / self.current()["music"]

    def music_gain(self):
        return self.current()["music_gain"]
