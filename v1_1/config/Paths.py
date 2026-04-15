#v1.1 Paths

import sys
from pathlib import Path

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return get_base_dir() / relative_path

BASE_DIR = get_base_dir()
SOUNDS_DIR = BASE_DIR / "audio" / "assets" / "sounds"
DATA_DIR = BASE_DIR.parent
HIGHSCORE_FILE = DATA_DIR / "highscore.txt"
