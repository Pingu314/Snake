"""conftest.py — Ensure the repo root is on sys.path.

This lets pytest discover and import the v1_1 package without requiring
an installation step. Run all tests from the repository root:

    python -m pytest tests/ -v
"""
import sys
import os

# Add the repository root (one level above /tests) to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
