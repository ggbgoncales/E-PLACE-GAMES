"""
mapas.py - os 4 mapas (arenas) do Kombate.
=================================================================
Cada mapa tem:
  - criar()   -> fundo fixo (1280x720), chao na linha CHAO_Y
  - Animacao  -> partes que se mexem (chuva, fogo, faiscas, petalas...)
Para criar um mapa novo: escreva as duas coisas e adicione em MAPAS.
"""
import math
import random

import pygame

from settings import LARGURA, ALTURA, CHAO_Y
from game.fx import glow
from game import render
from game.render import misturar, gradiente_v, escurecer


def _ceu(s, cores):
    """Degrade vertical com varias paradas: cores = [(k, cor), ...]."""
    for y in range(CHAO_Y):
        k = y / CHAO_Y
        for i in range(len(cores) - 1):
            k0, c0 = cores[i]
            k1, c1 = cores[i + 1]
            if k0 <= k <= k1:
                pygame.draw.line(s, misturar(c0, c1, (k - k0) / max(1e-6, k1 - k0)), (0, y), (LARGURA, y))
                break


def _estrelas(s, rnd, n, ymax):
    for _ in range(n):
        x, y = rnd.randint(0, LARGURA), rnd.randint(0, ymax)
        b = rnd.randint(110, 255)
        s.set_at((x, y), (b, b, min(255, b + 30)))


def _chao_pedra(s, topo, base, linha):
    gradiente_v(s, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y), topo, base)
    for d in (0, 12, 28, 50, 80):
        pygame.draw.line(s, linha, (0, CHAO_Y + d), (LARGURA, CHAO_Y + d), 2)
    for i in range(-14, 30):
        x0 = LARGURA / 2 + i * 58
        x1 = LARGURA / 2 + (x0 - LARGURA / 2) * 1.9
        pygame.draw.line(s, linha, (x0, CHAO_Y), (x1, ALTURA), 2)


# ======================================================================
# 1) TEMPLO DA LUA - templo a noite com cerejeiras
# ======================================================================
def _cerejeira(s, rnd, x, base, escala, tronco=(40, 18, 30)):
    pts = [(x, base)]
    cx, cy = x, base
    for _ in range(4):
        cx += rnd.randint(-14, 14) * escala
        cy -= 42 * escala
        pts.append((cx, cy))
    pygame.draw.lines(s, tronco, False, pts, int(14 * escala))
    for gx, gy in pts[2:]:
        for _ in range(3):
            ang = rnd.uniform(-2.6, -0.5)
            ex, ey = gx + math.cos(ang) * 70 * escala, gy + math.sin(ang) * 50 * escala
            pygame.draw.line(s, tronco, (gx, gy), (ex, ey), max(2, int(5 * escala)))
    copa_c = pts[-1]
    for _ in range(int(55 * escala)):
        ox = rnd.gauss(0, 75 * escala)
        oy = rnd.gauss(-10, 40 * escala)
        r = rnd.randint(int(14 * escala), int(30 * escala))
        cor = rnd.choice(((240, 140, 180), (255, 175, 205), (215, 105, 155), (250, 195, 215)))
        pygame.draw.circle(s, cor, (int(copa_c[0] + ox), int(copa_c[1] + oy)), r)


def criar_templo():
    s = render.criar_arena()                         # o cenario original (lua, pagode, pilares)
    rnd = random.Random(11)
    for x in (420, 860):                             # lanternas de pedra
        pygame.draw.rect(s, (50, 40, 52), (x - 10, CHAO_Y - 70, 20, 70))
        pygame.draw.rect(s, (70, 56, 70), (x - 26, CHAO_Y - 108, 52, 40), border_radius=4)
        pygame.draw.polygon(s, (60, 46, 60), [(x - 36, CHAO_Y - 108), (x + 36, CHAO_Y - 108), (x, CHAO_Y - 134)])
        glow(s, (120, 70, 20), (x, CHAO_Y - 88), 60, 1.0)
        pygame.draw.rect(s, (255, 200, 110), (x - 12, CHAO_Y - 98, 24, 20), border_radius=3)
    return s


class AnimTemplo:
    def __init__(self):
        self.amb = render.Ambiente()                 # tochas, brasas e neblina originais

    def desenhar(self, s, t):
        self.amb.desenhar(s, t)


# ======================================================================
# 2) CIDADE NEON - telhado cyberpunk na chuva
# ======================================================================
NEONS = [(150, 330, 110, 40, (255, 60, 180)), (470, 250, 70, 120, (60, 230, 255)),
         (760, 300, 130, 34, (180, 90, 255)), (1060, 220, 60, 150, (255, 210, 60)),
         (330, 420, 90, 26, (60, 255, 160)), (930, 410, 100, 30, (255, 80, 80))]


def criar_neon():
    s = pygame.Surface((LARGURA, ALTURA))
    rnd = random.Random(21)
    _ceu(s, [(0, (8, 6, 26)), (0.6, (40, 14, 60)), (1, (90, 30, 90))])
    glow(s, (70, 20, 90), (640, 560), 600, 0.8)                     # poluicao luminosa
    for camada, (cor, hmin, hmax, larg) in enumerate((((28, 18, 48), 250, 470, (60, 120)),
                                                     ((18, 12, 34), 170, 380, (70, 150)),
                                                     ((10, 8, 22), 110, 300, (90, 170)))):
        x = -30
        while x < LARGURA + 30:
            w = rnd.randint(*larg)
            h = rnd.randint(hmin, hmax)
            topo = CHAO_Y - 40 - h
            pygame.draw.rect(s, cor, (x, topo, w, h + 40))
            if rnd.random() < 0.4:                                      # antena
                pygame.draw.line(s, cor, (x + w // 2, topo), (x + w // 2, topo - rnd.randint(20, 60)), 3)
                pygame.draw.circle(s, (255, 60, 60), (x + w // 2, topo - 40), 2)
            for wy in range(topo + 10, CHAO_Y - 40, 16):                # janelas
                for wx in range(x + 6, x + w - 8, 12):
                    if rnd.random() < 0.28 - camada * 0.06:
                        c = rnd.choice(((255, 220, 140), (140, 220, 255), (255, 140, 220)))
                        pygame.draw.rect(s, escurecer(c, 0.55 + camada * 0.15), (wx, wy, 5, 8))
            x += w + rnd.randint(4, 20)
    # telhado: muretas, caixas d'agua, ventiladores
    pygame.draw.rect(s, (30, 28, 40), (0, CHAO_Y - 46, LARGURA, 46))
    pygame.draw.line(s, (80, 70, 110), (0, CHAO_Y - 46), (LARGURA, CHAO_Y - 46), 3)
    for x in (70, 1150):
        pygame.draw.rect(s, (40, 38, 54), (x - 50, CHAO_Y - 150, 100, 104))
        pygame.draw.rect(s, (60, 56, 80), (x - 56, CHAO_Y - 158, 112, 14))
        for k in range(3):
            pygame.draw.line(s, (25, 24, 36), (x - 50, CHAO_Y - 130 + k * 28), (x + 50, CHAO_Y - 130 + k * 28), 3)
    gradiente_v(s, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y), (55, 52, 70), (18, 16, 26))
    for i in range(0, LARGURA, 64):
        pygame.draw.line(s, (35, 33, 48), (i, CHAO_Y), (i - 30, ALTURA), 2)
    pygame.draw.line(s, (120, 110, 160), (0, CHAO_Y), (LARGURA, CHAO_Y), 2)
    return s


class AnimNeon:
    def __init__(self):
        self.chuva = [[random.uniform(0, LARGURA), random.uniform(0, ALTURA), random.uniform(14, 22)]
                      for _ in range(140)]
        self.respingos = []
        self.carros = [[random.uniform(0, LARGURA), random.uniform(120, 240), random.choice((-1, 1)) * random.uniform(2, 4)]
                       for _ in range(4)]

    def desenhar(self, s, t):
        for c in self.carros:                                           # carros voadores
            c[0] += c[2]
            if c[0] < -40:
                c[0] = LARGURA + 40
            elif c[0] > LARGURA + 40:
                c[0] = -40
            glow(s, (90, 30, 30), (int(c[0]), int(c[1])), 26, 1.0)
            pygame.draw.rect(s, (30, 28, 40), (int(c[0]) - 14, int(c[1]) - 4, 28, 8), border_radius=3)
            pygame.draw.circle(s, (255, 90, 90) if c[2] > 0 else (255, 240, 200),
                               (int(c[0] + (12 if c[2] > 0 else -12)), int(c[1])), 2)
        for g in self.chuva:
            g[1] += g[2]
            g[0] -= 3
            if g[1] > CHAO_Y + random.uniform(0, 70):
                self.respingos.append([g[0], g[1], 0])
                g[0], g[1] = random.uniform(0, LARGURA + 200), random.uniform(-80, 0)
            pygame.draw.line(s, (150, 170, 220), (g[0], g[1]), (g[0] + 3, g[1] - 14), 1)
        for r in self.respingos:
            r[2] += 1
            pygame.draw.ellipse(s, (170, 190, 230), (r[0] - r[2] * 2, r[1] - 2, r[2] * 4, 4), 1)
        self.respingos = [r for r in self.respingos if r[2] < 5]


# ======================================================================
# 3) COLISEU - arena ao por do sol
# ======================================================================
BRASEIROS = (150, 1130)


def criar_coliseu():
    s = pygame.Surface((LARGURA, ALTURA))
    rnd = random.Random(31)
    _ceu(s, [(0, (60, 20, 50)), (0.35, (190, 70, 50)), (0.7, (250, 160, 70)), (1, (255, 205, 120))])
    glow(s, (140, 70, 10), (640, 330), 300, 0.9)
    pygame.draw.circle(s, (255, 225, 150), (640, 330), 70)
    for _ in range(6):                                                  # nuvens
        cx, cy = rnd.randint(0, LARGURA), rnd.randint(80, 240)
        for _ in range(5):
            pygame.draw.ellipse(s, (210, 110, 80), (cx + rnd.randint(-80, 80), cy + rnd.randint(-8, 8),
                                                    rnd.randint(90, 170), rnd.randint(14, 26)))
    pedra, pedra2, sombra = (150, 100, 80), (120, 78, 64), (70, 40, 38)
    andares = [(CHAO_Y - 70, 120, 60), (CHAO_Y - 190, 110, 50), (CHAO_Y - 300, 96, 44)]
    pygame.draw.rect(s, pedra2, (0, CHAO_Y - 400, LARGURA, 340))
    for base, alt, w in andares:                                        # arcos em 3 andares
        pygame.draw.rect(s, pedra, (0, base - alt, LARGURA, alt))
        pygame.draw.line(s, escurecer(pedra, 0.7), (0, base - alt), (LARGURA, base - alt), 4)
        x = -w // 2
        while x < LARGURA:
            arco = pygame.Rect(x + 10, base - alt + 16, w - 20, alt - 16)
            pygame.draw.rect(s, sombra, (arco.x, arco.y + arco.w // 2, arco.w, arco.h - arco.w // 2))
            pygame.draw.ellipse(s, sombra, (arco.x, arco.y, arco.w, arco.w))
            for _ in range(3):                                          # publico (silhuetas)
                px = arco.x + rnd.randint(6, arco.w - 6)
                py = arco.bottom - rnd.randint(4, 14)
                pygame.draw.circle(s, (40, 22, 24), (px, py - 12), 6)
                pygame.draw.rect(s, (40, 22, 24), (px - 7, py - 6, 14, 14), border_radius=4)
            pygame.draw.rect(s, escurecer(pedra, 1.1), (x, base - alt, 10, alt))
            x += w
    pygame.draw.rect(s, (110, 70, 58), (0, CHAO_Y - 400, LARGURA, 14))
    for x in range(0, LARGURA, 160):                                   # bandeiras
        pygame.draw.line(s, (60, 40, 30), (x + 60, CHAO_Y - 400), (x + 60, CHAO_Y - 470), 3)
        pygame.draw.polygon(s, (170, 30, 30), [(x + 62, CHAO_Y - 468), (x + 100, CHAO_Y - 458),
                                               (x + 62, CHAO_Y - 446)])
    pygame.draw.rect(s, (95, 58, 48), (0, CHAO_Y - 70, LARGURA, 70))  # muro da arena
    pygame.draw.line(s, (60, 36, 32), (0, CHAO_Y - 70), (LARGURA, CHAO_Y - 70), 4)
    for x in BRASEIROS:
        pygame.draw.rect(s, (60, 45, 40), (x - 10, CHAO_Y - 120, 20, 120))
        pygame.draw.polygon(s, (80, 60, 50), [(x - 34, CHAO_Y - 150), (x + 34, CHAO_Y - 150),
                                              (x + 18, CHAO_Y - 118), (x - 18, CHAO_Y - 118)])
    gradiente_v(s, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y), (215, 170, 110), (140, 96, 64))  # areia
    for _ in range(400):
        x, y = rnd.randint(0, LARGURA), rnd.randint(CHAO_Y + 2, ALTURA)
        s.set_at((x, y), (170, 120, 80))
    pygame.draw.line(s, (240, 200, 140), (0, CHAO_Y), (LARGURA, CHAO_Y), 2)
    return s


class AnimColiseu:
    def __init__(self):
        self.poeira = [[random.uniform(0, LARGURA), random.uniform(CHAO_Y - 300, CHAO_Y),
                        random.uniform(0.2, 0.8), random.uniform(0, 6.28)] for _ in range(40)]

    def desenhar(self, s, t):
        for x in BRASEIROS:
            fl = math.sin(t * 0.3 + x) * 0.5 + math.sin(t * 0.7) * 0.5
            y = CHAO_Y - 152
            glow(s, (130, 60, 10), (x, y - 20), 130 + fl * 10, 0.9)
            for cor, w, h in (((255, 110, 30), 50, 60), ((255, 190, 70), 30, 42), ((255, 245, 200), 14, 20)):
                hh = h + fl * 8
                pygame.draw.polygon(s, cor, [(x - w // 2, y), (x + w // 2, y), (x + fl * 5, y - hh)])
        for p in self.poeira:
            p[0] += p[2]
            p[1] += math.sin(t * 0.02 + p[3]) * 0.3
            if p[0] > LARGURA + 10:
                p[0] = -10
            pygame.draw.circle(s, (255, 220, 170), (int(p[0]), int(p[1])), 1 + int(1.5 * abs(math.sin(t * 0.05 + p[3]))))


# ======================================================================
# 4) FABRICA ABANDONADA - fundicao com metal derretido
# ======================================================================
def criar_fabrica():
    s = pygame.Surface((LARGURA, ALTURA))
    rnd = random.Random(41)
    _ceu(s, [(0, (12, 12, 18)), (0.7, (30, 24, 26)), (1, (60, 34, 24))])
    for x in range(80, LARGURA, 260):                                  # janelas quebradas (luar)
        janela = pygame.Rect(x, 70, 150, 190)
        pygame.draw.rect(s, (40, 60, 90), janela)
        glow(s, (20, 35, 60), janela.center, 150, 0.9)
        for k in range(1, 4):
            pygame.draw.line(s, (20, 18, 24), (janela.x, janela.y + k * 47), (janela.right, janela.y + k * 47), 5)
        pygame.draw.line(s, (20, 18, 24), (janela.centerx, janela.y), (janela.centerx, janela.bottom), 5)
        for _ in range(3):
            px, py = rnd.randint(janela.x, janela.right), rnd.randint(janela.y, janela.bottom)
            pygame.draw.polygon(s, (14, 14, 20), [(px, py), (px + rnd.randint(10, 30), py + 6),
                                                  (px + 4, py + rnd.randint(14, 30))])
    aco, aco2 = (58, 50, 52), (38, 32, 34)
    for y in (300, 330):                                                # vigas horizontais
        pygame.draw.rect(s, aco, (0, y, LARGURA, 16))
    for x in range(0, LARGURA, 90):                                     # trelica
        pygame.draw.line(s, aco2, (x, 300), (x + 90, 346), 5)
        pygame.draw.line(s, aco2, (x + 90, 300), (x, 346), 5)
    for x in (230, 1050):                                               # pilares de aco
        pygame.draw.rect(s, aco, (x - 22, 0, 44, CHAO_Y))
        for y in range(20, CHAO_Y, 60):
            pygame.draw.circle(s, aco2, (x - 12, y), 4)
            pygame.draw.circle(s, aco2, (x + 12, y), 4)
    for x, comp in ((420, 230), (520, 160), (880, 260)):               # correntes
        for y in range(0, comp, 12):
            pygame.draw.ellipse(s, (70, 64, 60), (x - 4, y, 8, 14), 2)
        pygame.draw.arc(s, (90, 80, 70), (x - 14, comp, 28, 30), 3.4, 6.0, 4)
    # cadinho (balde gigante) derramando metal
    cx, cy = 640, 150
    pygame.draw.polygon(s, (50, 40, 38), [(cx - 90, cy - 40), (cx + 70, cy - 60), (cx + 80, cy + 30), (cx - 70, cy + 50)])
    pygame.draw.polygon(s, (255, 140, 30), [(cx + 60, cy - 58), (cx + 92, cy - 52), (cx + 76, cy - 40)])
    pygame.draw.rect(s, (60, 52, 52), (cx - 6, 0, 12, cy - 50))
    tanque = pygame.Rect(540, CHAO_Y - 110, 220, 110)                  # tanque de metal liquido
    pygame.draw.rect(s, (50, 40, 36), tanque.inflate(16, 0))
    for x in range(0, LARGURA, 140):                                    # canos
        pygame.draw.rect(s, (70, 56, 50), (x, CHAO_Y - 200 - (x % 3) * 30, 24, 200 + (x % 3) * 30))
    pygame.draw.rect(s, (70, 56, 50), (0, CHAO_Y - 210, LARGURA, 18))
    pygame.draw.rect(s, (50, 40, 36), tanque.inflate(16, 0))
    glow(s, (150, 60, 10), tanque.center, 200, 1.0)
    gradiente_v(s, (tanque.x, tanque.y + 10, tanque.w, 24), (255, 220, 120), (255, 110, 20))
    gradiente_v(s, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y), (70, 58, 54), (24, 20, 20))  # piso de grade
    for x in range(0, LARGURA, 22):
        pygame.draw.line(s, (36, 30, 30), (x, CHAO_Y), (x - 20, ALTURA), 3)
    for y in (CHAO_Y + 20, CHAO_Y + 48):
        pygame.draw.line(s, (36, 30, 30), (0, y), (LARGURA, y), 3)
    pygame.draw.line(s, (130, 100, 80), (0, CHAO_Y), (LARGURA, CHAO_Y), 2)
    return s


class AnimFabrica:
    def __init__(self):
        self.faiscas = []
        self.vapor = [[random.uniform(0, LARGURA), random.uniform(CHAO_Y - 260, CHAO_Y), random.uniform(0, 6.28)]
                      for _ in range(18)]

    def desenhar(self, s, t):
        cx, cy = 716, 100                                               # jato de metal derretido
        for i in range(0, 430, 6):
            y = cy + i
            x = cx + 10 * math.sin(i * 0.02 + t * 0.2) * (i / 430)
            w = 10 + 4 * math.sin(i * 0.1 - t * 0.5)
            pygame.draw.line(s, (255, 150 + int(60 * math.sin(i * 0.05 - t * 0.3)), 40), (x - w / 2, y), (x + w / 2, y), 6)
        glow(s, (120, 50, 5), (cx, 330), 120, 0.7 + 0.2 * math.sin(t * 0.2))
        if random.random() < 0.6:
            self.faiscas.append([cx + random.uniform(-10, 10), CHAO_Y - 110, random.uniform(-5, 5), random.uniform(-8, -3), 30])
        if t % 90 < 20 and random.random() < 0.5:                       # solda la em cima
            self.faiscas.append([230, 300, random.uniform(-3, 3), random.uniform(-1, 2), 40])
        for f in self.faiscas:
            f[0] += f[2]
            f[1] += f[3]
            f[3] += 0.35
            f[4] -= 1
            pygame.draw.line(s, (255, 220, 120), (f[0], f[1]), (f[0] - f[2], f[1] - f[3]), 2)
        self.faiscas = [f for f in self.faiscas if f[4] > 0 and f[1] < CHAO_Y + 40]
        for v in self.vapor:
            v[1] -= 0.6
            v[0] += math.sin(t * 0.02 + v[2]) * 0.5
            if v[1] < CHAO_Y - 300:
                v[1] = CHAO_Y
            k = (CHAO_Y - v[1]) / 300
            r = int(20 + 30 * k)
            nuvem = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(nuvem, (200, 190, 190, int(30 * (1 - k))), (r, r), r)
            s.blit(nuvem, (v[0] - r, v[1] - r))


# ======================================================================
# ======================================================================
# Cenarios PINTADOS (assets/mapas/*.jpg) + animacoes leves por cima
# ======================================================================
import os
PASTA_MAPAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "mapas")


def _carregar(nome, reserva):
    try:
        return pygame.image.load(os.path.join(PASTA_MAPAS, nome + ".jpg"))
    except Exception as ex:                       # sem a imagem: usa o cenario desenhado
        print("Mapa", nome, "sem imagem:", ex)
        return reserva()


def _fogo(s, t, pontos, forca=1.0):
    """Fogo/luz pulsando sobre as tochas e braseiros da pintura."""
    for i, (x, y, r) in enumerate(pontos):
        fl = 0.75 + 0.25 * math.sin(t * 0.31 + i * 1.7) * math.sin(t * 0.17 + i)
        glow(s, (int(110 * fl * forca), int(50 * fl * forca), 8), (x, y), int(r * (0.9 + 0.15 * fl)), 0.9)


class _Brasas:
    def __init__(self, n=40, cor=(255, 170, 70), ymin=0):
        self.cor, self.ymin = cor, ymin
        self.p = [[random.uniform(0, LARGURA), random.uniform(ymin, ALTURA), random.uniform(0.4, 1.4),
                   random.uniform(0, 6.28)] for _ in range(n)]

    def desenhar(self, s, t):
        for b in self.p:
            b[1] -= b[2]
            b[0] += math.sin(t * 0.03 + b[3]) * 0.5
            if b[1] < self.ymin:
                b[0], b[1] = random.uniform(0, LARGURA), ALTURA + 5
            a = 0.5 + 0.5 * math.sin(t * 0.1 + b[3])
            pygame.draw.circle(s, (self.cor[0], int(self.cor[1] * (0.7 + 0.3 * a)), self.cor[2]),
                               (int(b[0]), int(b[1])), 1 + int(a * 1.5))


class _Neblina:
    def __init__(self, cor=(220, 200, 230), alpha=10, y=CHAO_Y - 90):
        self.y = y
        self.img = pygame.Surface((LARGURA * 2, 130), pygame.SRCALPHA)
        rnd = random.Random(5)
        for _ in range(60):
            x, yy = rnd.randint(0, LARGURA * 2 - 200), rnd.randint(10, 90)
            pygame.draw.ellipse(self.img, (*cor, alpha), (x, yy, rnd.randint(160, 340), rnd.randint(30, 60)))

    def desenhar(self, s, t, vel=0.5):
        dx = int(t * vel) % LARGURA
        s.blit(self.img, (-dx, self.y))


class AnimTemploP:
    def __init__(self):
        self.brasas, self.neblina = _Brasas(35), _Neblina()

    def desenhar(self, s, t):
        _fogo(s, t, [(76, 190, 70), (1204, 190, 70), (240, 230, 40), (1010, 230, 40)])
        self.brasas.desenhar(s, t)
        self.neblina.desenhar(s, t)


class AnimNeonP(AnimNeon):
    def __init__(self):
        super().__init__()
        self.carros = []                              # a pintura ja tem os carros

    def desenhar(self, s, t):
        if (t // 4) % 160 == 0:                        # relampago de vez em quando
            glow(s, (60, 60, 90), (900, 60), 500, 1.0)
        super().desenhar(s, t)


class AnimColiseuP:
    def __init__(self):
        self.poeira = _Brasas(30, (255, 220, 170), CHAO_Y - 300)
        self.neblina = _Neblina((240, 200, 150), 12)

    def desenhar(self, s, t):
        _fogo(s, t, [(80, 150, 70), (1176, 150, 70), (515, 190, 30), (765, 190, 30)])
        self.neblina.desenhar(s, t, 0.3)
        self.poeira.desenhar(s, t)


class AnimFabricaP:
    def __init__(self):
        self.faiscas = []
        self.vapor = _Neblina((200, 180, 170), 12)

    def desenhar(self, s, t):
        _fogo(s, t, [(890, 300, 140), (890, 200, 80)], 1.2)
        if random.random() < 0.7:
            self.faiscas.append([random.uniform(840, 940), random.uniform(260, 320),
                                 random.uniform(-6, 6), random.uniform(-9, -3), 32])
        for f in self.faiscas:
            f[0] += f[2]
            f[1] += f[3]
            f[3] += 0.4
            f[4] -= 1
            pygame.draw.line(s, (255, 220, 120), (f[0], f[1]), (f[0] - f[2], f[1] - f[3]), 2)
        self.faiscas = [f for f in self.faiscas if f[4] > 0 and f[1] < CHAO_Y]
        self.vapor.desenhar(s, t, 0.4)


MAPAS = [
    {"id": "templo", "nome": "TEMPLO DA LUA", "desc": "Tochas e luar sobre o templo nas montanhas.",
     "criar": lambda: _carregar("templo", criar_templo), "anim": AnimTemploP, "cor": (190, 170, 255)},
    {"id": "neon", "nome": "CIDADE NEON", "desc": "Telhado na chuva, entre arranha-ceus iluminados.",
     "criar": lambda: _carregar("neon", criar_neon), "anim": AnimNeonP, "cor": (90, 230, 255)},
    {"id": "coliseu", "nome": "COLISEU", "desc": "A arena antiga ao por do sol, com o publico lotado.",
     "criar": lambda: _carregar("coliseu", criar_coliseu), "anim": AnimColiseuP, "cor": (255, 190, 90)},
    {"id": "fabrica", "nome": "FABRICA ABANDONADA", "desc": "Fundicao em ruinas com metal derretido.",
     "criar": lambda: _carregar("fabrica", criar_fabrica), "anim": AnimFabricaP, "cor": (255, 130, 50)},
]


class Mapa:
    """Mapa pronto para usar: fundo + vinheta + animacao."""

    def __init__(self, info):
        self.info = info
        fundo = info["criar"]()
        if fundo.get_size() != (LARGURA, ALTURA):
            fundo = pygame.transform.smoothscale(fundo.convert(), (LARGURA, ALTURA))
        fundo = fundo.copy()
        fundo.blit(render.criar_vinheta(), (0, 0))
        self.fundo = fundo.convert() if pygame.display.get_surface() else fundo
        self.anim = info["anim"]()

    def desenhar(self, s, t):
        s.blit(self.fundo, (0, 0))
        self.anim.desenhar(s, t)
