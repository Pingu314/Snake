# Snake v1.1 - ECS Rewrite

> **Status: In Development** - This branch is a ground-up rewrite of v1.0 using an Entity Component System (ECS) architecture. Not yet stable.

A complete architectural overhaul of the classic Snake game. Where v1.0 was a single-file script, v1.1 separates concerns into a proper module structure with a game engine foundation.

---

## What Changed from v1.0

| Feature | v1.0 | v1.1 |
|---------|------|------|
| Architecture | Single file, global state | ECS with World/Registry |
| State management | String constants | Enum + enter/exit hooks |
| Input | Direct key bindings | State-aware Input Manager |
| Audio | `winsound` (Windows only) | Custom Audio manager |
| Themes | None | Multiple themes with music |
| Food | Single type | Normal + Golden food |
| Scoring | Simple counter | Combo system with multipliers |
| Achievements | None | Achievement system |
| Obstacles | None | Difficulty-based obstacle layouts |

---

## Architecture

```
snake.py                  ← entry point: Game class + main loop
│
v1_1/
├── audio/
│   └── audio.py          ← sound and music manager
├── config/
│   ├── settings.py       ← difficulty presets, grid config
│   ├── themes.py         ← visual themes + music mapping
│   ├── paths.py          ← file path constants
│   └── achievement_config.py
├── core/
│   ├── game_state.py     ← enum state machine with enter/exit hooks
│   ├── persistence.py    ← highscore save/load
│   └── ecs/
│       ├── registry.py   ← World / entity-component store
│       ├── components.py ← all ECS components (data only)
│       ├── systems.py    ← all game logic (movement, collision, render)
│       ├── factories.py  ← entity spawners (snake, food, UI)
│       └── ui_components.py
├── logic/
│   └── scoring.py        ← combo scoring logic
└── util/
    └── input_manager.py  ← state-based input binding manager
```

---

## ECS Pattern

The game uses an **Entity Component System** - a pattern common in professional game engines:

- **Entities** - just an ID (integer)
- **Components** - pure data, no logic (`Position`, `Velocity`, `Food`, `Score` etc.)
- **Systems** - pure logic, operate on components (`movement_system`, `collision_system`, `render_system` etc.)
- **World/Registry** - stores all entities and their components

This makes each system independently testable and keeps game logic cleanly separated from rendering and data.

---

## New Features

- **Golden food** - rare spawns with score multipliers
- **Combo system** - consecutive food hits within a time window build a combo
- **Achievements** - runtime badges for things like perfect runs, long snakes, combo god
- **Obstacles** - Hard and Insane difficulties have static obstacle layouts
- **Themes** - multiple visual themes each with their own music track
- **Wrap mode** - Easy/Normal wrap at borders, Hard/Insane do not
- **Name entry** - keyboard-based initials entry on new high score

---

## How to Run

```bash
pip install -r requirements.txt
python snake.py
```

Requires Python 3.10+ and `pygame-ce` (a drop-in fork of pygame that, unlike pygame 2.6, installs on Python 3.14) for audio.

---

## Known Issues / Status

- Marked as **unstable** - some edge cases in achievement and combo systems

---

## Testing

Unit tests live in `tests/`. Run from the repo root:

```
python -m pytest tests/ -v
```

Tests cover: movement, boundary wrap/nowrap, facing, grid snapping, GAME_OVER
wiring, scoring, and combo decay.  No Turtle/tkinter required - runs headlessly.

---

## Roadmap

- Stabilize achievement + combo edge cases
- Cross-platform audio
- Configurable grid size
- Proper settings screen
- PyInstaller build support
