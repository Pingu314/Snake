#v1.1 Achievement Config

COMBO_GOD_PRESETS = {"easy":   {"threshold": 25, "window_mul": 2.0, "decay_mul": 0.5, "gold_bonus": 0.15},
                     "normal": {"threshold": 20, "window_mul": 1.5, "decay_mul": 0.75, "gold_bonus": 0.10},
                     "hard":   {"threshold": 15, "window_mul": 1.25, "decay_mul": 0.9, "gold_bonus": 0.05},
                     "insane": {"threshold": 12, "window_mul": 1.0, "decay_mul": 1.0, "gold_bonus": 0.0}}

ACHIEVEMENTS = {"COMBO_GOD": {"title": "COMBO GOD!",
                               "sound": "achievement",
                               "score": None},
                "PERFECT_RUN": {"title": "PERFECT RUN!",
                                 "sound": "achievement",
                                 "score": None},
                "TINY_DEATH": {"title": "SO SMALL...",
                                "sound": "achievement",
                                "score": {"hard": 200,
                                           "insane": 400}},
                "NERVOUS": {"title": "NERVOUS?!",
                             "sound": "achievement",
                             "score": 100},
                "INSANE_SURVIVOR": {"title": "INSANE SURVIVOR!",
                                     "sound": "achievement",
                                     "score": 500},
                "LUCKY_BITE": {"title": "LUCKY BITE!",
                                "sound": "achievement",
                                "score": 400},
                "LONG_SNAKE": { "title": "GETTING HUGE!",
                                 "sound": "achievement",
                                 "score": 250}}

LENGTH_THRESHOLDS = {"easy": 30,
                     "normal": 40,
                     "hard": 50,
                     "insane": 60,}

FOODS = {"normal":10,
         "golden":50}