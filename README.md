# Snake

The classic arcade game in Python: chase high scores, chain combos, unlock achievements.
Four difficulties, themes with music, moving obstacles and a settings screen, with turtle
graphics on a small Entity Component System.

> **v1.1.0** - see [CHANGELOG.md](CHANGELOG.md). v1.0 is the original single-file version.

---

## Quick start

```bash
pip install -r requirements.txt
python snake.py
```

Needs Python 3.10+. Audio uses `pygame-ce`, a drop-in fork of pygame that installs on Python 3.14.

---

## Controls

| Where | Key | Action |
|-------|-----|--------|
| Title | `Space` | Start |
| | `←` `→` | Difficulty |
| | `T` | Next theme |
| | `S` | Settings |
| | `H` | Highscores |
| In game | Arrow keys | Steer (two quick presses are both used) |
| | `P` / `Esc` | Pause |
| Game over | `R` / `B` | Restart / back to title |
| Settings | `↑` `↓` / `←` `→` | Pick a row / change it |
| | `B` / `Esc` | Back (saves) |
| Highscores | `←` `→` / `B` | Difficulty / back |
| Title, game, pause | `M` / `Q` | Mute / quit |

---

## Gameplay

| Difficulty | Tick (start → fastest) | Walls | Obstacles | Combo window | Perfect bonus |
|------------|------------------------|-------|-----------|--------------|---------------|
| Easy | 150 → 60 ms | wrap | - | 2.5 s | - |
| Normal | 120 → 50 ms | wrap | - | 1.5 s | - |
| Hard | 80 → 35 ms | solid | static | 0.9 s | x1.25 |
| Insane | 50 → 25 ms | solid | sliding | 0.45 s | x1.5 |

- **Faster and faster** - like in v1.0, every food makes the snake a bit faster.
- **3-2-1** - a short countdown before the start and after every pause.
- **Food** is worth 10, **golden food** 50.
- **Combo** - every bite inside the combo window adds 10% to the food's points.
- **Perfect bonus** - every point is multiplied until you pause for the first time.
- **The field is framed**: everything outside it has its own colour, so you always see where
  it ends. With solid walls (Hard, Insane or "Solid" in the settings) the edge is a thick
  line in a warning colour - touching it is death. When the snake wraps, it is a thin line.
- **Obstacles** on Insane slide sideways and bounce off the walls, the snake and the food.
  Only driving into them kills you.
- **Highscores** - top 5 per difficulty. Type 3 initials, the third one saves. `HI` in the HUD
  shows the record and climbs along once you beat it. Only runs with the difficulty's own
  walls count; with custom walls the HUD says `UNRANKED`.
- **Achievements** are secret. Find them while playing - they pop up when earned, give bonus
  points and count for the current run only.
- **Game over** shows score, length and the achievements of the run.

### Settings

`S` on the title screen: difficulty, walls (default / wrap / solid), theme, music and effect volume.
Saved to `settings.json` next to the game. All themes play at the same loudness.

---

## Build an .exe

```bash
pip install pyinstaller
pyinstaller Snake.spec
```

The one-file build lands in `dist/`. Highscores and settings are saved next to the .exe.

---

## Tests

```bash
python -m pytest tests/
```

The tests cover every system, the full game flow, the settings screen and a regression test
for each fixed bug. `Game()` runs without a window until `setup_window()` is called, so the
tests need no display.

---

## Project structure

```
snake.py                   Game class: states, input, main loop
v1_1/
├── audio/audio.py         sound effects and theme music
├── config/                settings, themes, layout, paths, achievements
├── core/
│   ├── game_state.py      state machine with enter/exit hooks
│   ├── persistence.py     highscores and settings files
│   └── ecs/               World, components, systems, factories
├── logic/                 scoring, settings menu
└── util/input_manager.py  per-state key bindings
tests/
```

**ECS in short:** entities are IDs, components are plain data (`Position`, `Velocity`, `Food` ...),
systems are functions over the `World` (`movement_system`, `collision_system` ...). The `World`
also carries the shared resources (`world.settings`, `world.theme`, `world.audio`, `world.state`),
so there is no global state and every test gets a fresh game.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
