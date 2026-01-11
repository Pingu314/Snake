# ===============================
# Snake v1.0
# Code frozen
# Only critical bug fixes allowed
# No refactors or new features
# ===============================

# Snake v1.0
# <Pingu>


import sys
import turtle
import random
import os
from tkinter import Menu
from tkinter import simpledialog
import time
import winsound


def resource_path(relative_path):
    try:
        base_path=sys._MEIPASS
    except (AttributeError,KeyError):
        base_path=os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")
if not os.path.exists(HIGHSCORE_FILE):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write("")


SOUND_DIR = resource_path("sounds")


GRID=20
CELL=GRID

w, h= 640, 640
assert w % GRID == 0 and h % GRID == 0, "Window size must be divisible by GRID"

HALF_W=w//2
HALF_H=h//2

MIN_X=-HALF_W+GRID
MAX_X=HALF_W-GRID
MIN_Y=-HALF_H+GRID
MAX_Y=HALF_H-GRID

MAX_HIGHSCORES=10
score=0
display_score=0

snake_dir="up"
dir_changed=False

snake_speed=0
snake=[]

food_position=(0,0)

high_scores={"Easy":[],
             "Normal":[],
             "Hard":[],
             "Insane":[]}

GAME_TITLE="title"
GAME_PLAYING="playing"
GAME_PAUSED="paused"
GAME_HIGHSCORES="highscores"

game_state = GAME_TITLE
prev_game_state=GAME_TITLE

PAUSE_DEBOUNCE_MS=300
last_pause_toggle=0

last_restart_press=0
RESTART_CONFIRM_MS=2000

MUTED = False

last_reset_press=0
RESET_CONFIRM_MS=2000

TEMP_MSG_MS=1200

DIFFICULTIES={"Easy":{"delay":250,"speed_inc":3,"min_delay":80},
              "Normal":{"delay":200,"speed_inc":5,"min_delay":60},
              "Hard":{"delay":150,"speed_inc":8,"min_delay":40},
              "Insane":{"delay":100,"speed_inc":12,"min_delay":0}}

current_difficulty="Easy"


offsets={"up":(0,GRID),
         "down":(0,-GRID),
         "left":(-GRID,0),
         "right":(GRID,0),}


def set_difficulty(diff):
    global current_difficulty
    if game_state != GAME_TITLE:
        return
    current_difficulty = diff
    show_title_screen()


def cycle_difficulty():
    if game_state!=GAME_TITLE:
        return
    diffs=list(DIFFICULTIES.keys())
    i=diffs.index(current_difficulty)
    set_difficulty(diffs[(i+1)%len(diffs)])


def play_sound(filename):
    if MUTED:
        return
    path = os.path.join(SOUND_DIR, filename)
    if os.path.exists(path):
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)


def toggle_mute():
    global MUTED

    if game_state not in (GAME_PLAYING,GAME_TITLE, GAME_PAUSED):
        return

    MUTED = not MUTED
    msg = "Sound off" if MUTED else "Sound on"

    show_temp_message(msg, color="orange")

    if game_state==GAME_TITLE:
        screen.ontimer(show_title_screen,TEMP_MSG_MS)
    elif game_state==GAME_PAUSED:
        screen.ontimer(draw_pause_screen,TEMP_MSG_MS)


def show_temp_message(text,duration=1000, color="yellow"):
    if game_state == GAME_HIGHSCORES:
        return

    score_pen.clear()
    score_pen.goto(0,-80)
    score_pen.color(color)
    score_pen.write(text, align="center", font=("Arial", 25, "bold italic"))

    screen.update()

    if game_state==GAME_TITLE:
        screen.ontimer(show_title_screen,duration)
    elif game_state==GAME_PLAYING:
        screen.ontimer(update_score,duration)


def save_high_scores():
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            for diff, scores in high_scores.items():
                for s, initials in scores:
                    f.write(f"{diff},{s},{initials}\n")

    except Exception as e:
        print("Failed to save high score",e)


def load_high_scores():
    global high_scores

    high_scores={k:[]for k in DIFFICULTIES}

    if not os.path.exists(HIGHSCORE_FILE):
        return

    with open(HIGHSCORE_FILE, "r") as f:
        for line in f:
            parts=line.strip().split(",")

            if len(parts)==3:
                diff,score,name=parts
                if diff in high_scores:
                    high_scores[diff].append((int(score),name))
            elif len(parts)==2:
                score,name=parts
                high_scores["Easy"].append((int(score),name))

    for diff in high_scores:
        high_scores[diff].sort(reverse=True)
        high_scores[diff] = high_scores[diff][:MAX_HIGHSCORES]


def check_high_scores(new_score):
    scores=high_scores[current_difficulty]

    if len(scores) < MAX_HIGHSCORES or new_score > scores [-1][0]:
        initials=simpledialog.askstring("New High Score!","Enter initials(---): ")
        initials=initials[:3].upper() if initials else "---"

        scores.append((new_score, initials))
        scores.sort(reverse=True)
        high_scores[current_difficulty]=scores[:MAX_HIGHSCORES]

        save_high_scores()


def reset():
    global snake, snake_dir, food_position, score, display_score, snake_speed

    settings = DIFFICULTIES[current_difficulty]

    snake = [(0, i * GRID) for i in range(5)]
    snake_dir = "up"
    snake_speed = settings["delay"]
    score=0
    display_score=0

    update_score()
    food_position = get_random_food_position()
    food.goto(food_position)
    draw_snake()
    screen.update()


def move_snake():
    global snake_dir
    if game_state != GAME_PLAYING:
        return

    if not snake:
       return

    global dir_changed
    dir_changed=False

    hx, hy = snake[-1]
    dx, dy = offsets[snake_dir]
    new_head = (hx + dx, hy + dy)

    x, y = new_head

    if x > MAX_X:
        x = MIN_X
    elif x < MIN_X:
        x = MAX_X

    if y > MAX_Y:
        y = MIN_Y
    elif y < MIN_Y:
        y = MAX_Y

    new_head = (x,y)

    if new_head in snake[:-1]:
        play_sound("crash.wav")
        check_high_scores(score)
        save_high_scores()
        show_title_screen()
        return

    snake.append(new_head)

    ate=food_collision()
    if not ate:
        snake.pop(0)

    draw_snake()
    screen.update()
    screen.ontimer(move_snake, snake_speed)


def food_collision():
    global score, food_position, snake_speed

    if snake[-1]==food_position:
        score += 10
        settings = DIFFICULTIES[current_difficulty]
        snake_speed = max(settings["min_delay"], snake_speed - settings["speed_inc"])
        animate_score()
        play_sound("eat.wav")
        food_position = get_random_food_position()
        food.goto(food_position)
        return True
    return False


def get_random_food_position():
    x_positions=list(range(MIN_X,MAX_X+1,GRID))
    y_positions=list(range(MIN_Y,MAX_Y+1,GRID))

    while True:
        x=random.choice(x_positions)
        y=random.choice(y_positions)
        if (x,y) not in snake:
            return x,y


def change_dir(new_dir):
    global snake_dir, dir_changed
    opposites = {"up":"down","down":"up","left":"right","right":"left"}

    if dir_changed:
        return
    if snake_dir != opposites[new_dir]:
        snake_dir=new_dir
        dir_changed=True


def go_up():
    if game_state != GAME_PLAYING:
        return
    change_dir("up")

def go_down():
    if game_state != GAME_PLAYING:
        return
    change_dir("down")

def go_left():
    if game_state != GAME_PLAYING:
        return
    change_dir("left")

def go_right():
    if game_state != GAME_PLAYING:
        return
    change_dir("right")


def draw_snake():
    pen.clearstamps()
    for x,y in snake:
        pen.goto(x,y)
        pen.stamp()


def update_score():
    if game_state != GAME_PLAYING:
        return

    score_pen.clear()
    score_pen.goto(0, HALF_H-40)
    scores=high_scores.get(current_difficulty,[])
    high_score_value=scores[0][0] if scores else 0
    score_pen.color("yellow")
    score_pen.write(f"Score: {display_score}  Highscore: {high_score_value}",align="center",font=("Arial", 20, "normal"))


def animate_score():
    global display_score

    if game_state != GAME_PLAYING:
        return

    if display_score < score:
        display_score += 1
        update_score()
        screen.ontimer(animate_score, 15)


def transition_flash():
    screen.tracer(0)
    for _ in range(2):
        screen.bgcolor("black")
        screen.update()
        time.sleep(0.04)
        screen.bgcolor("dark blue")
        screen.update()
        time.sleep(0.04)
    screen.tracer(0)


def start_game():
    global game_state

    if game_state != GAME_TITLE:
        return

    title_pen.clear()
    pen.showturtle()
    food.showturtle()
    game_state=GAME_PLAYING
    transition_flash()
    reset()
    move_snake()


def pause_game():
    global game_state
    if game_state !=GAME_PLAYING:
        return

    game_state=GAME_PAUSED
    play_sound("pause.wav")

    pen.clearstamps()
    pen.hideturtle()
    food.hideturtle()

    score_pen.clear()
    hs_pen.clear()
    title_pen.clear()

    clear_game_objects()
    pause_pen.clear()
    draw_pause_screen()


def resume_game():
    global game_state

    if game_state != GAME_PAUSED:
        return

    pause_pen.clear()
    score_pen.clear()
    hs_pen.clear()

    pen.showturtle()
    food.showturtle()

    game_state=GAME_PLAYING

    draw_snake()
    update_score()

    play_sound("pause.wav")
    transition_flash()
    move_snake()


def restart_game():
    global last_restart_press
    if game_state != GAME_PLAYING:
        return

    now=int(time.time()*1000)

    if now -last_restart_press > RESTART_CONFIRM_MS:
        last_restart_press=now

        score_pen.clear()
        score_pen.goto(0, -40)
        score_pen.color("yellow")
        score_pen.write("Press R again to restart", align="center",font=("Arial", 20, "italic"))

        screen.update()
        screen.ontimer(update_score,1000)
        return

    last_restart_press=0
    save_high_scores()
    show_title_screen()


def quit_game():
    save_high_scores()
    screen.bye()


def toggle_pause():
    global last_pause_toggle
    now=int(time.time()*1000)
    if now - last_pause_toggle<PAUSE_DEBOUNCE_MS:
        return

    last_pause_toggle=now

    if game_state==GAME_PLAYING:
        pause_game()
    elif game_state==GAME_PAUSED:
        resume_game()


def show_high_scores():
    global game_state, prev_game_state
    if game_state ==GAME_HIGHSCORES:
        return
    prev_game_state=game_state
    game_state=GAME_HIGHSCORES

    pen.clearstamps()
    score_pen.clear()
    pause_pen.clear()
    title_pen.clear()
    hs_pen.clear()
    pen.hideturtle()
    food.hideturtle()

    hs_pen.goto(0,200)
    hs_pen.write( f"HIGH SCORES ({current_difficulty})", align= "center", font=("Arial",25, "bold"))

    y=80

    scores=high_scores[current_difficulty]
    for i, (s, name) in enumerate(scores, 1):
        hs_pen.goto(0,y)
        hs_pen.write(f"{i}. {name} -{s}", align="center", font=("Arial", 22, "normal"))

        y-= 40

    hs_pen.goto(0,150)
    hs_pen.write("Press B to return", align="center", font=("Arial", 15, "normal"))

    screen.update()


def hide_high_scores():
    global game_state

    if game_state != GAME_HIGHSCORES:
        return

    hs_pen.clear()
    game_state=prev_game_state

    if game_state==GAME_PLAYING:
        pen.showturtle()
        food.showturtle()
        draw_snake()
        update_score()
        move_snake()
    elif game_state==GAME_PAUSED:
        clear_game_objects()
        draw_pause_overlay()
    else:
        show_title_screen()


def reset_high_scores():
    global high_scores, last_reset_press
    now=int(time.time()*1000)

    if game_state != GAME_TITLE:
        return

    if now - last_reset_press>RESET_CONFIRM_MS:
        last_reset_press=now

        score_pen.clear()
        score_pen.goto(0,-80)
        score_pen.color("red")
        score_pen.write("Press X again to reset highscores", align="center", font=("Arial", 22, "bold"))

        screen.update()

        screen.ontimer(show_title_screen,1000)
        return

    last_reset_press=0
    high_scores={k:[]for k in DIFFICULTIES}
    save_high_scores()

    score_pen.clear()
    score_pen.goto(0,-80)
    score_pen.color("red")
    score_pen.write("Highscores reset", align="center", font=("Arial", 22, "bold"))

    screen.update()

    screen.ontimer(show_title_screen,1000)


def show_title_screen():
    global game_state
    game_state=GAME_TITLE

    pen.clearstamps()
    score_pen.clear()
    hs_pen.clear()
    title_pen.clear()

    title_pen.goto(0,180)
    title_pen.write("SNAKE" , align="center", font=("Arial", 50, "bold italic"))

    title_pen.goto(0,120)
    title_pen.write("S = Start Game", align="center", font=("Arial", 30, "normal"))

    title_pen.goto(0,80)
    title_pen.write("H = High Scores  ", align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,60)
    title_pen.write("M = Toggle Sound/ Mute - Unmute",align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,40)
    title_pen.write("P = Pause" , align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,20)
    title_pen.write("Q = Quit" , align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,0)
    title_pen.write("R = Restart" , align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,-20)
    title_pen.write("X= Reset Highscores", align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,-120)
    title_pen.write(f"Difficulty:{current_difficulty} (D to change)", align="center", font=("Arial", 18, "normal"))

    title_pen.goto(0,-40)
    title_pen.write("Arrow Keys = Move", align="center", font=("Arial", 15, "normal"))

    title_pen.goto(0,-290)
    title_pen.write("v1.0  |  by <Pingu>", align="center", font=("Arial", 11, "italic"))

    pen.hideturtle()
    food.hideturtle()
    screen.update()


def on_focus_out(_):
    if game_state==GAME_PLAYING:
        pause_game()


def focus_check():
    if game_state==GAME_PLAYING:
        top=screen.getcanvas().winfo_toplevel()
        if not top.focus_displayof():
            pause_game()
    screen.getcanvas().after(100,focus_check)


def draw_pause_overlay():
    score_pen.clear()
    hs_pen.clear()

    pause_pen.clear()
    pause_pen.hideturtle()
    pause_pen.penup()
    pause_pen.speed(0)

    pause_pen.goto(-HALF_W, -HALF_H)
    pause_pen.fillcolor("dim gray")
    pause_pen.pendown()
    pause_pen.begin_fill()

    pause_pen.goto(HALF_W, -HALF_H)
    pause_pen.goto(HALF_W, HALF_H)
    pause_pen.goto(-HALF_W, HALF_H)
    pause_pen.goto(-HALF_W, -HALF_H)

    pause_pen.end_fill()
    pause_pen.penup()

    pause_pen.goto(0, 0)
    pause_pen.color("white")
    pause_pen.write("PAUSED", align="center", font=("Arial", 40, "bold italic"))

    screen.update()


def draw_pause_screen():
    screen.bgcolor("dark blue")
    draw_pause_overlay()
    screen.update()


def clear_game_objects():
    pen.clearstamps()
    food.hideturtle()
    pen.hideturtle()


screen = turtle.Screen()
screen.setup(w, h)
screen.title("SNAKE")
screen.bgcolor("dark blue")
screen.tracer(0)

pen = turtle.Turtle("square")
pen.shapesize(1,1,0)
pen.color("dark gray")
pen.penup()

score_pen=turtle.Turtle()
score_pen.hideturtle()
score_pen.penup()
score_pen.color("light green")

hs_pen=turtle.Turtle()
hs_pen.hideturtle()
hs_pen.penup()
hs_pen.color("light green")

food = turtle.Turtle()
food.shape("square")
food.color("red")
food.shapesize(0.9,0.9,0)
food.penup()

title_pen=turtle.Turtle()
title_pen.hideturtle()
title_pen.penup()
title_pen.color("light green")

pause_pen=turtle.Turtle()
pause_pen.hideturtle()
pause_pen.penup()

screen.listen()
screen.onkey(go_up, "Up")
screen.onkey(go_right, "Right")
screen.onkey(go_down, "Down")
screen.onkey(go_left, "Left")
screen.onkey(hide_high_scores, "b")
screen.onkey(cycle_difficulty,"d")
screen.onkey(show_high_scores, "h")
screen.onkey(toggle_mute, "m")
screen.onkey(toggle_pause, "p")
screen.onkey(quit_game, "q")
screen.onkey(restart_game, "r")
screen.onkey(start_game, "s")
screen.onkey(reset_high_scores,"x")
screen.getcanvas().bind("FocusOut", on_focus_out)


menu_screen=screen.getcanvas().winfo_toplevel()
menubar= Menu(menu_screen)
game_menu=Menu(menubar, tearoff=0)
game_menu.add_command(label="Restart", command=restart_game)
game_menu.add_command(label="Pause", command=pause_game)
game_menu.add_command(label="Resume", command=resume_game)
game_menu.add_command(label="Highscores", command=show_high_scores)
game_menu.add_separator()
difficulty_menu=Menu(game_menu,tearoff=0)
for diff in DIFFICULTIES:
    difficulty_menu.add_command(label=diff,command=lambda d=diff:set_difficulty(d))
game_menu.add_cascade(label="Difficulty", menu=difficulty_menu)
game_menu.add_separator()
game_menu.add_command(label="Toggle Sound", command=toggle_mute)
game_menu.add_separator()
game_menu.add_command(label="Quit", command=quit_game)
game_menu.add_separator()
game_menu.add_command(label="Reset Highscores", command=reset_high_scores)
menubar.add_cascade(label="Game", menu=game_menu)
menu_screen.config(menu=menubar)


focus_check()

load_high_scores()
show_title_screen()
turtle.done()