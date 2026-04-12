# Snake v1.0

A fully-featured Snake game built with Python's Turtle graphics library. Includes multiple difficulty levels, persistent high scores, sound effects, pause functionality, and a native menu bar.

Built as a personal project to learn Python through something fun.

---

## Features

- 4 difficulty levels with dynamic speed scaling (Easy → Insane)
- Persistent high score table per difficulty (top 10, stored locally)
- Sound effects (eat, crash, pause) — Windows
- Pause / Resume with debounce protection
- Auto-pause on window focus loss
- Restart confirmation (double-press R)
- High score reset with confirmation (double-press X)
- Native Tkinter menu bar
- Wrap-around borders (snake passes through walls)
- Score animation

---

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move |
| S | Start game |
| P | Pause / Resume |
| M | Toggle sound |
| H | View high scores |
| B | Back from high scores |
| R | Restart (in-game, double-press) |
| X | Reset high scores (title only, double-press) |
| D | Cycle difficulty (title only) |
| Q | Quit |

---

## Difficulties

| Level | Start Speed | Speed Increase | Min Delay |
|-------|------------|----------------|-----------|
| Easy | 250ms | -3ms per food | 80ms |
| Normal | 200ms | -5ms per food | 60ms |
| Hard | 150ms | -8ms per food | 40ms |
| Insane | 100ms | -12ms per food | 0ms |

---

## How to Run

```bash
python Snake.py
```

Requires Python 3.x. No external dependencies — uses only the standard library (`turtle`, `tkinter`, `winsound`).

> **Note:** Sound effects require Windows. The game runs on other platforms but without audio.

---

## High Scores

High scores are stored automatically in `highscore.txt` in the same directory as the script. Deleting this file resets all scores.

---

## Build (Windows)

```bash
pyinstaller --clean --onefile --noconsole --icon=snake.ico --add-data "sounds;sounds" Snake.py
```

> Rebuilding the exe requires re-running this command manually after any code changes.
> Delete the old exe before rebuilding.

## Status

`v1.0` — Code frozen. This version is preserved as-is. Future development continues in separate version folders.