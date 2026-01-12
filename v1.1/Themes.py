THEMES= {
    "Classic":{
        "background":"dark blue",
        "snake":"dark gray",
        "food":"red",
        "score":"yellow"
    },
    "Neon":{
        "background":"black",
        "snake":"cyan",
        "food":"magenta",
        "score":"lime"
    }
}
current_theme = "Classic"

def apply_theme(screen, pen, score_pen, food):
    theme=THEMES[current_theme]
    screen.bgcoloer(theme["background"])
    pen.color(theme["snake"])
    food.color(theme["food"])
    score_pen.color(theme["score"])
