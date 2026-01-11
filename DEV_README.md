**# Snake – Development Notes**

-----------------------------------------------------


**## Version Structure**

Each version lives in its own folder:

Snake/
* v1.0/
* v1.1/
* v1.2/
* v2.0/
* ...

Never modify released versions.
All new work happens in the next version folder.

-----------------------------------------------------


**## v1.0 Status**

Code frozen.
Only critical bug fixes allowed.
No refactors or new features.

-----------------------------------------------------


**## Planned for v1.1**

\- Improved pause/menu state handling
\- Cleaner UI layer separation
\- Optional speed limit removal for Insane mode
\- Configurable grid size
\- Proper asset manager
\- High score storage in AppData
\- Taskbar icon investigation (Windows/Tk limitation)
\- Animated snake head
\- Optional fullscreen mode

-----------------------------------------------------


**## Build Notes**

\- PyInstaller one-file build
\- Windows-only
\- Turtle + Tkinter based

-------------------------------------------------------------


Snake v1.0 – Developer Notes

Code Status
-----------
Code frozen.
Only critical bug fixes allowed.
No refactors or new features.

Architecture
------------
- Single-file Turtle-based game
- Global state machine:
  TITLE / PLAYING / PAUSED / HIGHSCORES

Known Constraints
-----------------
- Turtle rendering requires full redraws
- Text must never be layered across states
- Temporary messages must auto-clear or redraw parent state

Future Versions
---------------
v1.1+
- UI refactor
- Proper pause menu
- Settings screen
- Better asset management
- Cross-platform sound

