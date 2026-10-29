#v1.1 Settings

class Settings:
    grid_size = 20

    # Playfield half-extents in pixels (window is 800x600)
    HALF_WIDTH = 380
    HALF_HEIGHT = 280

    START_LENGTH = 3
    HIGHSCORE_LIMIT = 5
    TICKS_PER_SECOND = 60

    DEFAULT_DIFFICULTY = "normal"
    difficulty = DEFAULT_DIFFICULTY
    wrap_override = None

    DIFFICULTY_PRESETS = {"easy": {"speed": 150,
                                   "golden_chance": 0.15,
                                   "combo_window": 2.5,
                                   "wrap": True},
                        "normal": {"speed": 120,
                                   "golden_chance": 0.08,
                                   "combo_window": 1.5,
                                   "wrap": True},
                          "hard": {"speed": 80,
                                   "golden_chance": 0.04,
                                   "combo_window": 0.9,
                                   "wrap": False},
                        "insane": {"speed": 50,
                                   "golden_chance": 0.01,
                                   "combo_window": 0.45,
                                   "wrap": False}}

    OBSTACLES = {"easy": [],
                 "normal": [],
                 "hard": [{"pos":(-100,20),"size":(3,1)},
                          {"pos":(-60,-40),"size":(2,2)},
                          {"pos":(50,-60),"size":(2,2)},
                          {"pos":(110,50),"size":(4,3)},
                          {"pos":(70,-130),"size":(5,3)},
                          {"pos":(-100,120),"size":(3,2)}],
                 "insane": [{"pos":(120,120),"size":(2,2)},
                            {"pos":(-60,-120),"size":(2,1)},
                            {"pos":(50,-60),"size":(1,2)},
                            {"pos":(-230,130),"size":(2,2)},
                            {"pos":(70,-30),"size":(2,2)},
                            {"pos":(-60,-40),"size":(2,2)},
                            {"pos":(120,-100),"size":(3,2)},
                            {"pos":(-100,120),"size":(1,1)}]}

    @classmethod
    def difficulties(cls):
        return list(cls.DIFFICULTY_PRESETS.keys())

    @classmethod
    def difficulty_config(cls):
        return cls.DIFFICULTY_PRESETS.get(cls.difficulty,
                                          cls.DIFFICULTY_PRESETS[cls.DEFAULT_DIFFICULTY])

    @classmethod
    def set_difficulty(cls, diff):
        if diff in cls.DIFFICULTY_PRESETS:
            cls.difficulty = diff
            cls.wrap_override = None

    @classmethod
    def cycle_difficulty(cls, step):
        """Move to the next (step=1) or previous (step=-1) difficulty, wrapping around."""
        diffs = cls.difficulties()
        i = diffs.index(cls.difficulty)
        cls.set_difficulty(diffs[(i + step) % len(diffs)])

    @classmethod
    def speed(cls):
        return cls.difficulty_config()["speed"]

    @classmethod
    def golden_chance(cls):
        return cls.difficulty_config()["golden_chance"]

    @classmethod
    def combo_window(cls):
        return cls.difficulty_config()["combo_window"]

    @classmethod
    def get_wrap_mode(cls):
        preset = cls.difficulty_config()["wrap"]
        return cls.wrap_override if cls.wrap_override is not None else preset

    @classmethod
    def bounds(cls):
        return -cls.HALF_WIDTH, cls.HALF_WIDTH, -cls.HALF_HEIGHT, cls.HALF_HEIGHT

    @classmethod
    def grid_positions(cls):
        size = cls.grid_size
        xs = list(range(-cls.HALF_WIDTH, cls.HALF_WIDTH + 1, size))
        ys = list(range(-cls.HALF_HEIGHT, cls.HALF_HEIGHT + 1, size))
        return xs, ys

    @classmethod
    def direction_offsets(cls):
        g = cls.grid_size
        return {"up": (0, g),
                "down": (0, -g),
                "left": (-g, 0),
                "right": (g, 0)}

    @classmethod
    def obstacle_positions(cls):
        return cls.OBSTACLES.get(cls.difficulty, [])

    @staticmethod
    def perfect_multiplier():
        return {"easy" : 1.0,
                "normal" : 1.0,
                "hard" : 1.25,
                "insane" : 1.5}.get(Settings.difficulty)
