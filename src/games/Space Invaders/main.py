import os as _os, sys as _sys
_SRC_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _SRC_DIR not in _sys.path: _sys.path.insert(0, _SRC_DIR)
"""Ponto de entrada do Space Invaders."""
from game import Game


if __name__ == "__main__":
    Game().run()
