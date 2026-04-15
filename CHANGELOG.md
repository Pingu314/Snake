# Changelog

## v1.1 — in progress

Complete architectural rewrite. v1.0 was a single-file script; v1.1 splits the
game into a proper module structure built on an Entity Component System (ECS).

### Architecture
- ECS pattern: World/Registry, Entities, Components (data), Systems (logic)
- Full module layout under v1_1/ (audio, config, core, logic, util)
- Enum-based state machine with enter/exit hooks (replaces string constants)
- State-aware Input Manager (replaces direct key bindings)

### New Features
- Golden food — rare spawns with score multipliers
- Combo system — consecutive hits within a time window stack a multiplier
- Achievements — runtime badges (perfect runs, combo god, long snake, etc.)
- Obstacles — Hard and Insane difficulties include static obstacle layouts
- Themes — multiple visual themes, each with its own music track
- Cross-platform audio manager (replaces winsound, Windows-only)
- Wrap mode per difficulty — Easy/Normal wrap, Hard/Insane do not

### Testing
- Unit tests in tests/ covering movement, collision, scoring, combo decay
- Headless — no Turtle/tkinter needed to run tests

### Known Issues
- Achievement and combo edge cases not fully stabilized
- Audio paths must be run from repo root
- PyInstaller build not yet supported

---

## v1.0 — 2026-01-11

First stable release. Single-file implementation using Python's Turtle graphics.

- 4 difficulty levels (Easy / Normal / Hard / Insane) with dynamic speed scaling
- Persistent high scores per difficulty, top 10, stored in highscore.txt
- Sound effects: eat, crash, pause/resume (Windows only via winsound)
- Pause with debounce protection and auto-pause on focus loss
- Restart and high score reset via double-press confirmation
- Native Tkinter menu bar, wrap-around borders, score animation
- PyInstaller compatible with exe-safe path handling
- Code frozen. No known issues.
