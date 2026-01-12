from Snake import pen, score_pen, food, pause_pen, hs_pen, GAME_TITLE
from Snake import game_state,GAME_PLAYING,GAME_PAUSED,GAME_HIGHSCORES, GAME_HIGHSCORES
from Snake import draw_snake,update_score,draw_pause_screen,show_title_screen,show_high_scores

def render_state():     #central render manager for v1.1
    if game_state == GAME_TITLE:
        show_title_screen()
    elif game_state == GAME_PAUSED:
        draw_pause_screen()
    elif game_state == GAME_HIGHSCORES:
        show_high_scores()
    elif game_state == GAME_PLAYING:
        draw_snake()
        update_score()