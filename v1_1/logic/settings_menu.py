#v1.1 Settings menu

from v1_1.config.settings import Settings

WALL_MODES = list(Settings.WALL_MODES)      # cycle order: default, wrap, solid
VOLUME_STEP = 0.1


class SettingsMenu:
    """Rows of the settings screen. ↑/↓ picks a row, ←/→ changes its value."""

    def __init__(self, settings, theme, audio, on_theme_change=lambda: None):
        self.settings = settings
        self.theme = theme
        self.audio = audio
        self.on_theme_change = on_theme_change
        self.selected = 0

        # (label, current value as text, change(step))
        self.rows = [("Difficulty", self._difficulty_text, self._change_difficulty),
                     ("Walls", self._walls_text, self._change_walls),
                     ("Theme", self.theme.current_name, self._change_theme),
                     ("Music volume", lambda: self._percent(self.audio.music_volume), self._change_music),
                     ("Effects volume", lambda: self._percent(self.audio.sfx_volume), self._change_sfx)]

    def entries(self):
        """[(label, value text), ...] for drawing."""
        return [(label, text()) for label, text, _ in self.rows]

    def move(self, step):
        self.selected = (self.selected + step) % len(self.rows)

    def change(self, step):
        self.rows[self.selected][2](step)

    #----------VALUES---------
    def _difficulty_text(self):
        return self.settings.difficulty.capitalize()

    def _change_difficulty(self, step):
        self.settings.cycle_difficulty(step)

    def _walls_text(self):
        names = Settings.WALL_MODES
        mode = self.settings.wrap_override
        if mode is None:
            return f"Default ({names[self.settings.difficulty_config()['wrap']].capitalize()})"
        return names[mode].capitalize()

    def _change_walls(self, step):
        i = WALL_MODES.index(self.settings.wrap_override)
        self.settings.wrap_override = WALL_MODES[(i + step) % len(WALL_MODES)]

    def _change_theme(self, step):
        self.theme.next(step)
        self.on_theme_change()

    @staticmethod
    def _percent(volume):
        return f"{round(volume * 100)} %"

    @staticmethod
    def _stepped(volume, step):
        return round(volume + step * VOLUME_STEP, 1)     # Audio's setters clamp to 0..1

    def _change_music(self, step):
        self.audio.set_music_volume(self._stepped(self.audio.music_volume, step))

    def _change_sfx(self, step):
        self.audio.set_sfx_volume(self._stepped(self.audio.sfx_volume, step))
