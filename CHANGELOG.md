# Changelog

## v1.1.0 - 2026-10-30

Complete architectural rewrite. v1.0 was a single-file script; v1.1 splits the
game into a proper module structure built on an Entity Component System (ECS).

### Architecture
- ECS pattern: World/Registry, Entities, Components (data), Systems (logic)
- Full module layout under v1_1/ (audio, config, core, logic, util)
- Enum-based state machine with enter/exit hooks (replaces string constants)
- State-aware Input Manager (replaces direct key bindings)
- Game class owns the main loop; runs headless for tests until setup_window()
- No global state: settings, theme, audio and state machine live on the World
- Achievements are a table of small check functions
- Game clock in milliseconds: all timers count real time, not ticks
- Board renderer only redraws cells that changed; the snake's body is one canvas line,
  so long snakes no longer slow the game down (400 segments: 179 ms -> 5 ms per frame)
- Dead and duplicate code removed (unused components and systems, double score bookkeeping)

### New Features
- Golden food - rare spawns with score multipliers
- Combo system - every bite inside the combo window adds 10% to the food's points
- Perfect multiplier on Hard/Insane until you pause
- Achievements - 18 secret ones, found by playing; they pop up when earned, give bonus points
  and count for the current run only (arcade style, nothing is saved)
- Obstacles - static on Hard, sliding and bouncing on Insane
- Themes - multiple visual themes, each with its own music track
- Cross-platform audio manager (replaces winsound, Windows-only)
- Wrap mode per difficulty - Easy/Normal wrap, Hard/Insane do not
- Settings screen: difficulty, walls, theme, music and effect volume, saved to settings.json
- Framed playfield: the area outside the field has its own colour, and the field edge is a thick
  warning line when the walls kill (death zone) or a thin line when the snake wraps
- Calmer theme colours with similar contrast across all themes, clearly visible obstacles
- Balanced sound: every theme track plays at the same loudness, effects levelled against the music
- The snake speeds up with every food again, like in v1.0 (lost in the rewrite)
- 3-2-1 countdown before the start and after a pause
- Arcade HUD: SCORE, HI (the record, climbs along once beaten) and COMBO
- Highscores only count with the difficulty's own walls, other runs are UNRANKED
- Esc pauses too
- Game over screen sums up the run: score, length, achievements, NEW BEST!
- Mint theme music
- Lava music as gapless OGG, unused Cyberpunk tracks removed: the .exe shrinks from 86 to 40 MB
- .exe file properties name Pingu314 as the author

### Fixed
- Game froze after dying; pause and game over screens never showed up
- Insane: snake died on the first tick in most runs, obstacles left the field after 1.2 s
- Obstacles off the 20px grid killed you on tiles that looked free (food could spawn there)
- Two quick turns inside one tick reversed the snake into itself (turns are now buffered)
- Combo had no effect on points
- Durations (combo window, popups, Insane Survivor, Nervous) were counted in 60 FPS
  ticks although the game ticks every 50-150 ms; they now use real seconds
- Insane speed factor never reached the snake
- Achievements earned on death were never shown
- Theme changed while muted did not play after unmuting
- Name entry only appears for a top 5 score; the third initial saves; highscore sound plays
- HUD no longer overlaps the playfield
- B on the game over screen goes back to the title
- Saving highscores in a read-only folder no longer crashes
- Window uses snake.ico
- Moving obstacles could pass through the snake's head or slide over its body and the food;
  they now bounce off the snake and the food
- Crash when the board is full (no free tile for food); the run now ends
- Crash on start with a corrupt highscore.txt; broken files or lines are skipped
- Wrong value types in settings.json are ignored instead of crashing
- Pause overlay was 600x800 instead of covering the window; it now follows the window size
- Deaths at the edge looked like they happened inside the field: the window showed 10 px (sides)
  and 50 px (top) of field-coloured space that was already wall
- Food could spawn inside an obstacle block (the block left a hole for it)
- Game froze for ~0.7 s on every theme change (loading music during a fade-out blocks)

### Testing
- Unit and game flow tests in tests/, plus regression tests for every fixed bug
- Headless - no Turtle/tkinter needed to run tests

---

## v1.0 - 2026-01-11

First stable release. Single-file implementation using Python's Turtle graphics.

- 4 difficulty levels (Easy / Normal / Hard / Insane) with dynamic speed scaling
- Persistent high scores per difficulty, top 10, stored in highscore.txt
- Sound effects: eat, crash, pause/resume (Windows only via winsound)
- Pause with debounce protection and auto-pause on focus loss
- Restart and high score reset via double-press confirmation
- Native Tkinter menu bar, wrap-around borders, score animation
- PyInstaller compatible with exe-safe path handling
- Code frozen. No known issues.
