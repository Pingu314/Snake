# Snake v1.1 — ECS Rewrite

> **Status: In Development** — This branch is a ground-up rewrite of v1.0 using an Entity Component System (ECS) architecture. Not yet stable.

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
Snake.py                  ← entry point / game loop
│
v1_1/
├── audio/
│   └── Audio.py          ← sound and music manager
├── config/
│   ├── Settings.py       ← difficulty presets, grid config
│   ├── Themes.py         ← visual themes + music mapping
│   ├── Paths.py          ← file path constants
│   └── AchievementConfig.py
├── core/
│   ├── Gamestate.py      ← enum state machine with enter/exit hooks
│   ├── Persistence.py    ← highscore save/load
│   └── ecs/
│       ├── Registry.py   ← World / entity-component store
│       ├── Entity.py     ← entity ID management
│       ├── Components.py ← all ECS components (data only)
│       ├── Systems.py    ← all game logic (movement, collision, render)
│       ├── Factories.py  ← entity spawners (snake, food, UI)
│       └── UiComponents.py
├── logic/
│   └── Scoring.py        ← combo scoring logic
└── util/
    └── Input_mgr.py      ← state-based input binding manager
```

---

## ECS Pattern

The game uses an **Entity Component System** — a pattern common in professional game engines:

- **Entities** — just an ID (integer)
- **Components** — pure data, no logic (`Position`, `Velocity`, `Food`, `Score` etc.)
- **Systems** — pure logic, operate on components (`movement_system`, `collision_system`, `render_system` etc.)
- **World/Registry** — stores all entities and their components

This makes each system independently testable and keeps game logic cleanly separated from rendering and data.

---

## New Features

- **Golden food** — rare spawns with score multipliers
- **Combo system** — consecutive food hits within a time window build a combo
- **Achievements** — runtime badges for things like perfect runs, long snakes, combo god
- **Obstacles** — Hard and Insane difficulties have static obstacle layouts
- **Themes** — multiple visual themes each with their own music track
- **Wrap mode** — Easy/Normal wrap at borders, Hard/Insane do not
- **Name entry** — keyboard-based initials entry on new high score

---

## How to Run

```bash
python Snake.py
```

Requires Python 3.10+. No external dependencies beyond standard library.

> Sound requires Windows (`winsound`). Game runs on other platforms without audio.

---

## Known Issues / Status

- Marked as **unstable** — some edge cases in achievement and combo systems
- `GAME_OVER` state defined but not fully wired
- Audio paths are relative — must be run from repo root

---

## Roadmap

- Stabilize achievement + combo edge cases
- Wire `GAME_OVER` state fully
- Cross-platform audio
- Configurable grid size
- Proper settings screen
- PyInstaller build support