#v1.1 Paths

import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

# Folder of the v1_1 package (dev) or of the .exe (PyInstaller build)
BASE_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent.parent

def resource_path(relative_path):
    """Bundled read-only assets. A one-file build unpacks them to _MEIPASS."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return BASE_DIR / relative_path

SOUNDS_DIR = resource_path("audio/assets/sounds")

# Writable data: next to the .exe when built, the repo root in dev
DATA_DIR = BASE_DIR if FROZEN else BASE_DIR.parent
HIGHSCORE_FILE = DATA_DIR / "highscore.txt"
PREFERENCES_FILE = DATA_DIR / "settings.json"

# Window icon: bundled at the root of the build (see Snake.spec), repo root in dev
ICON_FILE = Path(sys._MEIPASS) / "snake.ico" if hasattr(sys, "_MEIPASS") else BASE_DIR.parent / "snake.ico"
