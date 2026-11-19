# v1.1 Sound Manager
#pygame.mixer only


import pygame
from pathlib import Path
from v1_1.config.paths import resource_path

class Audio:
    # Levels balanced from measured loudness (RMS): every theme track is evened out with the
    # theme's music_gain, music sits around -26 dB, the frequent eat/golden sounds are clearly
    # on top, pause/resume stay in the background, death/highscore/achievement no longer blast.
    THEME_VOLUME = 0.45
    FADE_MS = 600

    SFX_VOLUME = {
        "eat": 1.0,
        "golden": 1.0,
        "death": 0.7,
        "pause": 0.65,
        "resume": 0.7,
        "highscore": 0.55,
        "achievement": 0.5}

    def __init__(self):
        self.muted = False
        self.music_volume = 1.0     # player setting, 0.0 - 1.0, on top of THEME_VOLUME
        self.sfx_volume = 1.0       # player setting, 0.0 - 1.0, on top of SFX_VOLUME
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self._wanted_theme: Path | None = None    # the track that should be playing
        self._loaded_theme: Path | None = None    # the track the mixer actually has
        self._theme_gain = 1.0                    # evens out the loudness of the theme tracks

    def init(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self.set_music_volume(self.music_volume)

    def set_music_volume(self, volume):
        self.music_volume = min(1.0, max(0.0, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.THEME_VOLUME * self.music_volume * self._theme_gain)

    def set_sfx_volume(self, volume):
        self.sfx_volume = min(1.0, max(0.0, volume))

    # ---------- SFX ----------

    def load_sfx(self, name: str, relative_path: str):
        path = resource_path(relative_path)
        self.sounds[name] = pygame.mixer.Sound(str(path))

    def play(self, name: str):
        if self.muted:
            return

        sound = self.sounds.get(name)
        if not sound:
            return

        sound.set_volume(self.SFX_VOLUME.get(name, 1.0) * self.sfx_volume)
        sound.play()

    # ---------- MUSIC ----------

    def play_theme(self, path: Path, gain=1.0):
        self._wanted_theme = path
        self._theme_gain = gain
        self.set_music_volume(self.music_volume)
        if not self.muted:
            self._start_wanted_theme()

    def _start_wanted_theme(self):
        # Without a mixer (headless tests) only remember the wish; init() + play_theme() start it later
        if self._loaded_theme == self._wanted_theme or not pygame.mixer.get_init():
            return

        # stop(), not fadeout(): load() during a fade-out blocks until the fade is over (~0.7 s freeze)
        pygame.mixer.music.stop()
        self._loaded_theme = self._wanted_theme

        # A theme without a music file just plays silence instead of crashing
        if self._wanted_theme is None or not Path(self._wanted_theme).exists():
            return

        pygame.mixer.music.load(self._wanted_theme)
        pygame.mixer.music.play(-1, fade_ms=self.FADE_MS)

    # ---------- MUTE ----------

    def toggle_mute(self):
        self.muted = not self.muted

        if not pygame.mixer.get_init():
            return
        if self.muted:
            pygame.mixer.music.pause()
        elif self._wanted_theme != self._loaded_theme:
            # The theme changed while muted: start the new track instead of resuming the old one
            self._start_wanted_theme()
        else:
            pygame.mixer.music.unpause()
