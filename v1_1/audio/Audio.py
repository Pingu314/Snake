# v1.1 Sound Manager
#pygame.mixer only


import pygame
from pathlib import Path
from v1_1.config.Paths import resource_path

class Audio:
    _initialized = False
    _theme_loaded = False
    muted = False

    _current_theme: Path | None = None
    _theme_volume = 0.6

    _sfx_volume = {
        "eat": 0.8,
        "golden": 1.0,
        "death": 1.0,
        "pause": 0.6,
        "resume": 0.6,
        "ui": 0.5}

    sounds: dict[str, pygame.mixer.Sound] = {}

    @classmethod
    def init(cls):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            Audio._initialized = True

        pygame.mixer.music.set_volume(cls._theme_volume)
        cls._initialized = True

    # ---------- SFX ----------

    @classmethod
    def load_sfx(cls, name: str, relative_path: str):
        path = resource_path(relative_path)
        cls.sounds[name] = pygame.mixer.Sound(str(path))

    @classmethod
    def play(cls, name: str):
        if cls.muted:
            return

        sound = cls.sounds.get(name)
        if not sound:
            return

        sound.set_volume(cls._sfx_volume.get(name, 1.0))
        sound.play()

    # ---------- MUSIC ----------

    @classmethod
    def play_theme(cls, path: Path, *, fade_ms=600):
        cls.init()

        if cls.muted:
            cls._current_theme = path
            return

        if cls._current_theme == path:
            return

        pygame.mixer.music.fadeout(fade_ms)
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1, fade_ms=fade_ms)

        cls._current_theme = path
        cls._theme_loaded = True

    @classmethod
    def resume_theme(cls):
        if not pygame.mixer.get_init():
            return
        if cls.muted:
            return

        pygame.mixer.music.unpause()

    # ---------- MUTE ----------

    @classmethod
    def toggle_mute(cls):
        cls.muted = not cls.muted

        if cls.muted:
            pygame.mixer.music.pause()
        else:
            if cls._current_theme:
                pygame.mixer.music.unpause()