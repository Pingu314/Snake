#v1.1 Achievement Config

COMBO_GOD_PRESETS = {"easy":   {"threshold": 25, "window_mul": 2.0, "decay_mul": 0.5, "gold_bonus": 0.15},
                     "normal": {"threshold": 20, "window_mul": 1.5, "decay_mul": 0.75, "gold_bonus": 0.10},
                     "hard":   {"threshold": 15, "window_mul": 1.25, "decay_mul": 0.9, "gold_bonus": 0.05},
                     "insane": {"threshold": 12, "window_mul": 1.0, "decay_mul": 1.0, "gold_bonus": 0.0}}

# All achievements are secret: none is listed anywhere, players find them by playing.
# They count for the current run only (arcade style) and pop up the moment they are earned.
ACHIEVEMENTS = {"COMBO_GOD": {"title": "COMBO GOD!",
                               "score": None},
                "PERFECT_RUN": {"title": "PERFECT RUN!",
                                 "score": None},
                "TINY_DEATH": {"title": "SO SMALL...",
                                "score": {"hard": 200,
                                           "insane": 400}},
                "NERVOUS": {"title": "NERVOUS?!",
                             "score": 100},
                "INSANE_SURVIVOR": {"title": "INSANE SURVIVOR!",
                                     "score": 500},
                "LUCKY_BITE": {"title": "LUCKY BITE!",
                                "score": 400},
                "LONG_SNAKE": { "title": "GETTING HUGE!",
                                 "score": 250},
                "GREEDY": {"title": "GREEDY!",
                            "score": 300},
                "GOLD_RUSH": {"title": "GOLD RUSH!",
                               "score": 300},
                "PATIENCE": {"title": "PATIENCE...",
                              "score": 150},
                "MARATHON": {"title": "MARATHON!",
                              "score": 750},
                "ON_THE_EDGE": {"title": "ON THE EDGE!",
                                 "score": 150},
                "SPEED_DEMON": {"title": "SPEED DEMON!",
                                 "score": 500},
                "ON_FIRE": {"title": "ON FIRE!",
                             "score": 200},
                "TOURIST": {"title": "TOURIST!",
                             "score": 150},
                "QUICK_DRAW": {"title": "QUICK DRAW!",
                                "score": 100},
                "HIGH_ROLLER": {"title": "HIGH ROLLER!",
                                 "score": 300},
                "SNAKE_EYES": {"title": "SNAKE EYES!",
                                "score": None}}

LENGTH_THRESHOLDS = {"easy": 30,
                     "normal": 40,
                     "hard": 50,
                     "insane": 60,}

FOODS = {"normal":10,
         "golden":50}

# Each combo step adds 10% to the points of a food (combo x3 -> 120%)
COMBO_BONUS_PER_STEP = 0.1

# Achievement tuning (durations in real seconds)
PERFECT_RUN_MIN_FOOD = 10       # PERFECT RUN: die after eating this much without ever pausing
GREEDY_GOLDEN = 5               # GREEDY: golden food eaten in one run
NERVOUS_PAUSES = 10             # NERVOUS?!: this many pauses ...
NERVOUS_WINDOW_SECONDS = 10     # ... within this time
INSANE_SURVIVOR_SECONDS = 60    # INSANE SURVIVOR: time alive on insane
PATIENCE_SECONDS = 20           # PATIENCE: time without food before the next bite
MARATHON_SECONDS = 300          # MARATHON: time alive in one run
ON_FIRE_COMBO = 66              # ON FIRE: combo reached
TOURIST_WRAPS = 200             # TOURIST: times through the wrapping edge in one run
QUICK_DRAW_SECONDS = 1.5        # QUICK DRAW: first food this soon after the start
HIGH_ROLLER_SCORE = 1000        # HIGH ROLLER: points in one run
POPUP_SECONDS = 2               # how long an achievement popup stays on screen
