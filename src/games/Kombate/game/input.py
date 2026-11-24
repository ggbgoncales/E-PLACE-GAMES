"""input.py - le o teclado e transforma em Comandos (P1 e P2)."""
import pygame

from settings import CONTROLES, DUPLO_TOQUE
from game.fighter import Comandos, BOTOES


class Teclado:
    def __init__(self, slot, controller=None):
        self.controller = controller if slot == 1 else None
        self.mapa = {acao: pygame.key.key_code(nome)
                     for acao, nome in CONTROLES[slot].items()}
        self.frame = 0
        self.ultimo = {"esquerda": -99, "direita": -99}

    def ler(self, eventos, teclas):
        m = self.mapa
        c = Comandos(esquerda=teclas[m["esquerda"]], direita=teclas[m["direita"]],
                     cima=teclas[m["cima"]], baixo=teclas[m["baixo"]])
        if self.controller and self.controller.connected:
            eixo_x, eixo_y = self.controller.axis(0), self.controller.axis(1)
            c.esquerda = c.esquerda or eixo_x < -0.35
            c.direita = c.direita or eixo_x > 0.35
            c.cima = c.cima or eixo_y < -0.35
            c.baixo = c.baixo or eixo_y > 0.35
            botoes = self.controller.pressed_buttons
            if 0 in botoes: c.apertou.add("soco")       # A
            if 2 in botoes: c.apertou.add("chute")      # X
            if 4 in botoes: c.apertou.add("especial1")  # LB
            if 5 in botoes: c.apertou.add("especial2")  # RB
            if 3 in botoes: c.apertou.add("dash")       # Y
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
