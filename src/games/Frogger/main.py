import os as _os, sys as _sys
_SRC_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _SRC_DIR not in _sys.path: _sys.path.insert(0, _SRC_DIR)
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from game.game import Game

if __name__ == "__main__":
    Game().run()
