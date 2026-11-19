#v1.1 Settings

class Settings:
    """Per-game settings. Class attributes are fixed presets, instance attributes can change."""

    grid_size = 20                  # cell size in px (turtle's built-in square/circle are 20 px too)

    # wrap_override values and their names (saved in settings.json, shown on the settings screen)
    WALL_MODES = {None: "default", True: "wrap", False: "solid"}

    # Outermost cell centres. The window is 800x600 and centred on (0, 0).
    half_width = 380
    half_height = 240
    # Edges of the playfield = where the walls are (half a cell beyond the outermost centres).
    # Everything outside is frame: side margins, bottom band and the HUD band at the top.
    FIELD_HALF_WIDTH = half_width + grid_size // 2      # 390
    FIELD_HALF_HEIGHT = half_height + grid_size // 2    # 250

    START_LENGTH = 3
    HIGHSCORE_LIMIT = 5
    MAX_QUEUED_TURNS = 2            # key presses buffered between two ticks
    OBSTACLE_STEP_SECONDS = 0.2     # moving obstacles advance one cell this often

    DEFAULT_DIFFICULTY = "normal"

    # speed = ms per tick. Like v1.0, every food takes speed_step ms off, down to min_speed.
    DIFFICULTY_PRESETS = {"easy": {"speed": 150,
                                   "speed_step": 2,
                                   "min_speed": 60,
                                   "golden_chance": 0.15,
                                   "combo_window": 2.5,
                                   "wrap": True,
                                   "moving_obstacles": False,
                                   "perfect_multiplier": 1.0},
                        "normal": {"speed": 120,
                                   "speed_step": 3,
                                   "min_speed": 50,
                                   "golden_chance": 0.08,
                                   "combo_window": 1.5,
                                   "wrap": True,
                                   "moving_obstacles": False,
                                   "perfect_multiplier": 1.0},
                          "hard": {"speed": 80,
                                   "speed_step": 4,
                                   "min_speed": 35,
                                   "golden_chance": 0.04,
                                   "combo_window": 0.9,
                                   "wrap": False,
                                   "moving_obstacles": False,
                                   "perfect_multiplier": 1.25},
                        "insane": {"speed": 50,
                                   "speed_step": 6,
                                   "min_speed": 25,
                                   "golden_chance": 0.01,
                                   "combo_window": 0.45,
                                   "wrap": False,
                                   "moving_obstacles": True,
                                   "perfect_multiplier": 1.5}}

    # Bottom-left cell and size (in cells) of each block. No block touches the start row (y=0),
    # so the moving ones on insane can never drive into the snake before the first input.
    OBSTACLES = {"easy": [],
                 "normal": [],
                 "hard": [{"pos":(-100,20),"size":(3,1)},
                          {"pos":(-60,-40),"size":(2,2)},
                          {"pos":(40,-60),"size":(2,2)},
                          {"pos":(100,40),"size":(4,3)},
                          {"pos":(60,-140),"size":(5,3)},
                          {"pos":(-100,120),"size":(3,2)}],
                 "insane": [{"pos":(120,120),"size":(2,2)},
                            {"pos":(-60,-120),"size":(2,1)},
                            {"pos":(40,-60),"size":(1,2)},
                            {"pos":(-240,120),"size":(2,2)},
                            {"pos":(60,-40),"size":(2,2)},
                            {"pos":(-60,-40),"size":(2,2)},
                            {"pos":(120,-100),"size":(3,2)},
                            {"pos":(-100,120),"size":(1,1)}]}

    def __init__(self, difficulty=DEFAULT_DIFFICULTY):
        self.difficulty = difficulty
        self.wrap_override = None   # None = the difficulty decides, True = wrap, False = solid walls
        self.speed_bonus = 0        # ms taken off the tick by eating; reset for every run

    @classmethod
    def difficulties(cls):
        return list(cls.DIFFICULTY_PRESETS.keys())

    def difficulty_config(self):
        return self.DIFFICULTY_PRESETS.get(self.difficulty,
                                           self.DIFFICULTY_PRESETS[self.DEFAULT_DIFFICULTY])

    def set_difficulty(self, diff):
        if diff in self.DIFFICULTY_PRESETS:
            self.difficulty = diff

    def cycle_difficulty(self, step):
        """Move to the next (step=1) or previous (step=-1) difficulty, wrapping around."""
        diffs = self.difficulties()
        i = diffs.index(self.difficulty)
        self.set_difficulty(diffs[(i + step) % len(diffs)])

    def speed(self):
        """Current ms per tick: the difficulty's start speed, minus what eating took off."""
        cfg = self.difficulty_config()
        return max(cfg["min_speed"], cfg["speed"] - self.speed_bonus)

    def speed_up(self):
        self.speed_bonus += self.difficulty_config()["speed_step"]

    def golden_chance(self):
        return self.difficulty_config()["golden_chance"]

    def combo_window(self):
        return self.difficulty_config()["combo_window"]

    def perfect_multiplier(self):
        return self.difficulty_config()["perfect_multiplier"]

    def moving_obstacles(self):
        return self.difficulty_config()["moving_obstacles"]

    def is_ranked(self):
        """Highscores only count with the difficulty's own walls."""
        return self.wrap_override in (None, self.difficulty_config()["wrap"])

    def get_wrap_mode(self):
        preset = self.difficulty_config()["wrap"]
        return self.wrap_override if self.wrap_override is not None else preset

    def bounds(self):
        return -self.half_width, self.half_width, -self.half_height, self.half_height

    def grid_positions(self):
        size = self.grid_size
        xs = list(range(-self.half_width, self.half_width + 1, size))
        ys = list(range(-self.half_height, self.half_height + 1, size))
        return xs, ys

    def direction_offsets(self):
        g = self.grid_size
        return {"up": (0, g),
                "down": (0, -g),
                "left": (-g, 0),
                "right": (g, 0)}

    def obstacle_positions(self):
        return self.OBSTACLES.get(self.difficulty, [])

    def obstacle_blocks(self):
        """One list of cell centres per obstacle block of the current difficulty."""
        g = self.grid_size
        blocks = []
        for obs in self.obstacle_positions():
            (x0, y0), (w, h) = obs["pos"], obs["size"]
            blocks.append([(x0 + i * g, y0 + j * g) for i in range(w) for j in range(h)])
        return blocks
