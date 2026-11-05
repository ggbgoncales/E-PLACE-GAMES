"""input.py - le o teclado e transforma em Comandos (P1 e P2)."""
import pygame

from settings import CONTROLES, DUPLO_TOQUE
from game.fighter import Comandos, BOTOES


class Teclado:
    def __init__(self, slot):
        self.mapa = {acao: pygame.key.key_code(nome)
                     for acao, nome in CONTROLES[slot].items()}
        self.frame = 0
        self.ultimo = {"esquerda": -99, "direita": -99}

    def ler(self, eventos, teclas):
        m = self.mapa
        c = Comandos(esquerda=teclas[m["esquerda"]], direita=teclas[m["direita"]],
                     cima=teclas[m["cima"]], baixo=teclas[m["baixo"]])
        self.frame += 1
        for e in eventos:
            if e.type == pygame.KEYDOWN:
                for acao in BOTOES:
                    if e.key == m[acao]:
                        c.apertou.add(acao)
                for lado in ("esquerda", "direita"):           # toque duplo = dash
                    if e.key == m[lado]:
                        if self.frame - self.ultimo[lado] <= DUPLO_TOQUE:
                            c.apertou.add("dash")
                            self.ultimo[lado] = -99
                        else:
                            self.ultimo[lado] = self.frame
        return c

    def tecla(self, acao):
        return self.mapa[acao]
