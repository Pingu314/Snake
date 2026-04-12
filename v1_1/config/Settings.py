#v1.1 Settings

class Settings:
    grid_size = 20

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
        half_x = 380
        half_y = 280
        return -half_x, half_x, -half_y, half_y

    @classmethod
    def grid_positions(cls):
        size = cls.grid_size
        xs = list(range(-380, 381, size))
        ys = list(range(-280, 281, size))
        return xs, ys

    @staticmethod
    def difficulty_color():
        return {"easy": None,
                "normal": "#FFD966",
                "hard": "#FF6B6B",
                "insane": "#B71C1C"}.get(Settings.difficulty)

    @classmethod
    def obstacle_positions(cls):
        return cls.OBSTACLES.get(cls.difficulty, [])

    @staticmethod
    def perfect_multiplier():
        return {"easy" : 1.0,
                "normal" : 1.0,
                "hard" : 1.25,
                "insane" : 1.5}.get(Settings.difficulty)
