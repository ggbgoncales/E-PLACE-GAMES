"""input.py - le o teclado e transforma em Comandos (P1 e P2)."""
import pygame

from settings import CONTROLES
from game.fighter import Comandos, BOTOES


class Teclado:
    def __init__(self, slot):
        self.mapa = {acao: pygame.key.key_code(nome)
                     for acao, nome in CONTROLES[slot].items()}

    def ler(self, eventos, teclas):
        m = self.mapa
        c = Comandos(esquerda=teclas[m["esquerda"]], direita=teclas[m["direita"]],
                     cima=teclas[m["cima"]], baixo=teclas[m["baixo"]])
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                for acao in BOTOES:
                    if e.key == m[acao]:
                        c.apertou.add(acao)
        return c

    def tecla(self, acao):
        return self.mapa[acao]
