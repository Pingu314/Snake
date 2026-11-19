#v1.1 UI layout
# Turtle coordinates: the 800x600 window is centred on (0, 0).

FONT_COUNTDOWN = ("Arial", 48, "bold")
FONT_TITLE = ("Arial", 32, "bold")
FONT_GAME_OVER = ("Arial", 28, "bold")
FONT_HEADING = ("Arial", 24, "bold")
FONT_PROMPT = ("Arial", 18, "bold")
FONT_TEXT = ("Arial", 16, "normal")
FONT_SMALL = ("Arial", 12, "normal")

# Frame around the playfield: drawn far enough out to fill even a resized window
FRAME_FAR = 3000
WALL_LINE_WIDTH = 4        # field edge when the walls kill (death zone)
BORDER_LINE_WIDTH = 1      # field edge when the snake wraps

OVERLAY_COLOR = "dim gray"   # pause overlay

# HUD row above the playfield (the field ends at y=250)
HUD_Y = 262
SCORE_X = -380      # left aligned
COMBO_X = 380       # right aligned

# Title screen
TITLE_Y = 120
TITLE_BOB = 6       # px the title floats up and down
DIFFICULTY_Y = 60
THEME_Y = 30
UNRANKED_Y = 0
CONTROLS_Y = -60
CONTROLS_STEP = 24

# Highscore screen
HIGHSCORES_TITLE_Y = 160
HIGHSCORES_FIRST_Y = 100
HIGHSCORES_STEP = 30
HIGHSCORES_HINT_Y = -180

# Settings screen: label column left, value column right
SETTINGS_TITLE_Y = 170
SETTINGS_FIRST_Y = 100
SETTINGS_STEP = 40
SETTINGS_LABEL_X = -220
SETTINGS_VALUE_X = 220
SETTINGS_HINT_Y = -180

# Pause screen
PAUSE_Y = 0
PAUSE_HINT_Y = -60

# Snake head glow after eating
COMBO_GLOW_SECONDS = 0.6

# Name entry
NAME_PROMPT_Y = 40
NAME_TEXT_Y = 0
CURSOR_BLINK_SECONDS = 0.5

# Game over screen: title, run summary, achievements of this run, key hints
GAME_OVER_Y = 170
GAME_OVER_STATS_Y = 125
GAME_OVER_LIST_Y = 80
GAME_OVER_LIST_STEP = 24
GAME_OVER_FIRST_HINT_Y = -150
GAME_OVER_HINT_STEP = 32

# 3-2-1 before the snake moves
COUNTDOWN_Y = 60
COUNTDOWN_STEP_SECONDS = 0.6

# Achievement popups stack upwards from here
POPUP_Y = -160
POPUP_STEP = 26
