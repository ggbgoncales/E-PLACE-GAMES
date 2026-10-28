"""
Kombate - prototipo de luta 1v1 (estilo Mortal Kombat) para o launcher E-PLACE.
Rode a partir do launcher ou com:  python3 main.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from game.app import App

if __name__ == "__main__":
    App().run()
