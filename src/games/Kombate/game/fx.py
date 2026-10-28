"""
fx.py - "suco" do jogo: particulas, textos flutuantes, tremida de tela e sons.
Os sons sao sintetizados na hora (nao precisa de nenhum arquivo .wav).
"""
import array
import json
import math
import os
import random

import pygame


# ============================================================== brilho
_cache_glow = {}


def glow(surf, cor, centro, raio, forca=1.0):
    """Brilho radial aditivo (luz)."""
    raio = max(4, int(raio) // 6 * 6 + 6)                 # tamanhos "arredondados" -> cache
    forca = round(forca * 10) / 10
    cor = tuple(c // 8 * 8 for c in cor)
    chave = (cor, raio, forca)
    img = _cache_glow.get(chave)
    if img is None:
        img = pygame.Surface((raio * 2, raio * 2))
        img.fill((0, 0, 0))
        for r in range(raio, 0, -2):
            k = (1 - r / raio) ** 1.8 * forca
            c = tuple(min(255, int(v * k)) for v in cor)
            pygame.draw.circle(img, c, (raio, raio), r)
        if pygame.display.get_surface() is not None:
            img = img.convert()
        if len(_cache_glow) > 600:
            _cache_glow.clear()
        _cache_glow[chave] = img
    surf.blit(img, (centro[0] - raio, centro[1] - raio), special_flags=pygame.BLEND_RGB_ADD)


# ============================================================== particulas
class Particulas:
    def __init__(self):
        self.lista = []
        self.textos = []

    def faiscas(self, x, y, cor, n=14, vel=9.0, direcao=0):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            if direcao:
                a = random.uniform(-0.9, 0.9) + (0 if direcao > 0 else math.pi)
            v = random.uniform(vel * 0.4, vel)
            self.lista.append(["faisca", x, y, math.cos(a) * v, math.sin(a) * v - 1,
                               random.randint(10, 20), 20, cor, random.randint(2, 4), 0.35])

    def poeira(self, x, y, n=8, forca=1.0):
        for _ in range(n):
            vx = random.uniform(-3.5, 3.5) * forca
            self.lista.append(["poeira", x + random.uniform(-20, 20), y - 4, vx,
                               random.uniform(-1.6, -0.3) * forca, random.randint(18, 32), 32,
                               (150, 125, 120), random.randint(6, 13), -0.02])

    def fogo(self, x, y, n=30):
        for _ in range(n):
            a = random.uniform(math.pi, math.tau)
            v = random.uniform(2, 9)
            cor = random.choice(((255, 200, 80), (255, 120, 40), (255, 80, 30)))
            self.lista.append(["poeira", x, y, math.cos(a) * v, math.sin(a) * v, random.randint(16, 30),
                               30, cor, random.randint(7, 15), 0.15])
        self.faiscas(x, y - 20, (255, 220, 120), n=16, vel=12)

    def texto(self, msg, x, y, cor, tamanho=1.0):
        self.textos.append([msg, x, y, 0, cor, tamanho])

    def update(self):
        vivos = []
        for p in self.lista:
            p[1] += p[3]
            p[2] += p[4]
            p[4] += p[9]
            p[3] *= 0.93
            p[5] -= 1
            if p[5] > 0:
                vivos.append(p)
        self.lista = vivos
        for t in self.textos:
            t[3] += 1
            t[2] -= 0.8
        self.textos = [t for t in self.textos if t[3] < 60]

    def draw(self, surf):
        for tipo, x, y, vx, vy, vida, mx, cor, tam, _ in self.lista:
            k = vida / mx
            if tipo == "faisca":
                fim = (x - vx * 1.8, y - vy * 1.8)
                pygame.draw.line(surf, cor, (x, y), fim, max(1, int(tam * k + 0.5)))
            else:
                r = max(1, int(tam * (1.4 - k * 0.6)))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*cor, int(150 * k)), (r, r), r)
                surf.blit(s, (x - r, y - r))

    def draw_textos(self, surf, fonte, texto_fn):
        for msg, x, y, t, cor, tam in self.textos:
            if t < 6:
                img_escala = 1.6 - t * 0.1
            else:
                img_escala = 1.0
            img = fonte.render(msg, True, cor)
            if img_escala != 1.0:
                img = pygame.transform.smoothscale(
                    img, (int(img.get_width() * img_escala), int(img.get_height() * img_escala)))
            if t > 45:
                img.set_alpha(int(255 * (60 - t) / 15))
            sombra = fonte.render(msg, True, (15, 10, 15))
            if img_escala != 1.0:
                sombra = pygame.transform.smoothscale(sombra, img.get_size())
            r = img.get_rect(center=(x, y))
            surf.blit(sombra, r.move(3, 3))
            surf.blit(img, r)


class Tremor:
    def __init__(self):
        self.forca = 0.0

    def add(self, f):
        self.forca = min(18.0, max(self.forca, f))

    def offset(self):
        if self.forca < 0.4:
            self.forca = 0
            return 0, 0
        o = (random.uniform(-1, 1) * self.forca, random.uniform(-1, 1) * self.forca)
        self.forca *= 0.85
        return int(o[0]), int(o[1])


# ============================================================== sons
def ler_volume():
    """Usa o volume do launcher (config.json na raiz do E-PLACE), se existir."""
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for caminho in (os.path.join(aqui, "..", "..", "..", "config.json"),
                    os.path.join(aqui, "config.json")):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return max(0, min(100, int(json.load(f).get("volume", 70)))) / 100
        except Exception:
            continue
    return 0.7


class Sons:
    def __init__(self):
        self.ok = False
        self.sons = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(22050, -16, 1, 512)
                pygame.mixer.init()
            self.freq, _, self.canais = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(16)
            self.ok = True
        except Exception:
            return
        self.volume = ler_volume()
        rnd = random.Random(7)
        g = self._gerar
        self.sons = {
            "soco": g(0.09, 180, 70, 0.75, 0.9, rnd, decay=2.5),
            "forte": g(0.20, 130, 40, 0.65, 1.0, rnd, decay=1.8),
            "bloqueio": g(0.07, 1300, 700, 0.35, 0.6, rnd, onda="quad", decay=3),
            "whoosh": g(0.13, 300, 900, 0.95, 0.25, rnd, decay=1.2, ataque=0.4),
            "tiro": g(0.28, 900, 160, 0.15, 0.45, rnd, onda="quad", decay=1.2),
            "explosao": g(0.55, 90, 30, 0.85, 1.0, rnd, decay=1.5),
            "agarrao": g(0.30, 110, 50, 0.55, 1.0, rnd, decay=1.4),
            "ko": g(1.1, 220, 45, 0.35, 0.9, rnd, onda="quad", decay=1.1),
            "sino": g(1.0, 880, 870, 0.0, 0.55, rnd, onda="sino", decay=2.2),
            "menu": g(0.06, 660, 990, 0.0, 0.35, rnd, onda="quad", decay=2),
            "ok": g(0.16, 520, 1040, 0.0, 0.45, rnd, onda="quad", decay=1.5),
            "pulo": g(0.10, 250, 520, 0.2, 0.25, rnd, decay=2),
        }

    def _gerar(self, dur, f0, f1, ruido, vol, rnd, onda="sin", decay=2.0, ataque=0.0):
        n = int(self.freq * dur)
        dados = array.array("h")
        fase, ruido_v = 0.0, 0.0
        for i in range(n):
            k = i / n
            f = f0 + (f1 - f0) * k
            fase += math.tau * f / self.freq
            if onda == "quad":
                v = 1.0 if math.sin(fase) > 0 else -1.0
                v *= 0.6
            elif onda == "sino":
                v = math.sin(fase) * 0.7 + math.sin(fase * 2.76) * 0.3
            else:
                v = math.sin(fase)
            ruido_v = ruido_v * 0.55 + rnd.uniform(-1, 1) * 0.45      # ruido "grave"
            env = (1 - k) ** decay
            if ataque and k < ataque:
                env *= k / ataque
            s = (v * (1 - ruido) + ruido_v * 2.2 * ruido) * env * vol
            amostra = int(max(-1.0, min(1.0, s)) * 26000)
            for _ in range(self.canais):
                dados.append(amostra)
        return pygame.mixer.Sound(buffer=dados.tobytes())

    def tocar(self, nome, vol=1.0):
        if not self.ok or nome not in self.sons:
            return
        s = self.sons[nome]
        s.set_volume(max(0.0, min(1.0, self.volume * vol)))
        s.play()
