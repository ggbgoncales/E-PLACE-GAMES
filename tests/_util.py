"""Apoio aos testes: caminhos do projeto e importacao isolada de cada jogo.

Cada jogo tem seus proprios pacotes "game" e "settings"; por isso, antes de importar
um jogo, os modulos do jogo anterior sao descartados.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
JOGOS = os.path.join(SRC, "games")


def entrar_no_jogo(nome_pasta):
    """Coloca a pasta do jogo no sys.path e limpa 'game'/'settings' de outros jogos."""
    pasta = os.path.join(JOGOS, nome_pasta)
    for nome in list(sys.modules):
        if nome in ("game", "settings", "main") or nome.startswith("game."):
            del sys.modules[nome]
    sys.path[:] = [p for p in sys.path if not p.startswith(JOGOS)]
    sys.path.insert(0, pasta)
    # Como nos main.py dos jogos: a pasta src fica no caminho para achar o modulo "gamepad".
    if SRC not in sys.path:
        sys.path.append(SRC)
    return pasta


def entrar_na_raiz():
    for nome in ("main",):
        sys.modules.pop(nome, None)
    sys.path[:] = [p for p in sys.path if not p.startswith(JOGOS)]
    if RAIZ not in sys.path:
        sys.path.insert(0, RAIZ)
    return RAIZ
