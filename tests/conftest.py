"""conftest.py — Ensure the repo root is on sys.path.

This lets pytest discover and import the v1_1 package without requiring
an installation step. Run all tests from the repository root:

    python -m pytest tests/ -v
"""
import sys
import os

# Add the repository root (one level above /tests) to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(autouse=True)
def isolated_save_files(tmp_path, monkeypatch):
    """No test may write the real highscore or settings files in the repo:
    a Game created without explicit paths saves into the test's temp folder instead."""
    import snake
    monkeypatch.setattr(snake.Game.__init__, "__defaults__",
                        (tmp_path / "highscore.txt", tmp_path / "settings.json"))


@pytest.fixture
def game(tmp_path):
    """A headless Game in a Normal run."""
    from helpers import make_game
    return make_game(tmp_path)


@pytest.fixture
def fake_music(monkeypatch):
    """pygame.mixer.music replaced by a recorder, with the mixer reported as started."""
    import pygame
    from helpers import FakeMusic
    music = FakeMusic()
    monkeypatch.setattr(pygame.mixer, "music", music)
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)
    return music
