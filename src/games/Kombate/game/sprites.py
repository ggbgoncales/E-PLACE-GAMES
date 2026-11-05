"""
sprites.py - desenha os lutadores com IMAGENS (sprites) em vez do manequim.
=================================================================
- Cada personagem com sprites tem uma pasta em assets/sprites/<nome>/
  com um PNG por pose e um quadros.json (ponto de apoio de cada pose).
- Personagens SEM pasta continuam usando o manequim de game/modelo.py.
- Para ativar outro personagem: coloque a pasta e adicione em SPRITES.

Poses usadas (nome do arquivo .png):
  idle, andar, agachar, soco, chute, rasteira, especial1, especial2,
  defesa, dano, caido, vitoria
Poses derivadas automaticamente (giradas): aereo, voando, dash
"""
import json
import math
import os

import pygame

from settings import CHAO_Y
from game.fx import glow
from game import modelo

PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sprites")

# chave do personagem -> pasta dos sprites
SPRITES = {
    "vermelho": "rubro",
    "azul": "colosso",
    "amarelo": "faisca",
    "verde": "vulto",
    "roxo": "lanceiro",
    "preto": "sombra",
}

# golpe -> pose do sprite
POSE_GOLPE = {
    "soco": "soco", "chute": "chute", "soco_baixo": "agachar", "rasteira": "rasteira",
    "aereo": "aereo", "especial1": "especial1", "especial2": "especial2", "arremesso": "soco",
}

_folhas = {}


# ================================================================ carregamento
class Folha:
    def __init__(self, pasta, cor=(200, 60, 60)):
        self.cor = cor
        with open(os.path.join(pasta, "quadros.json"), "r", encoding="utf-8") as f:
            info = json.load(f)
        self.q = {}
        for nome, d in info["quadros"].items():
            img = pygame.image.load(os.path.join(pasta, nome + ".png")).convert_alpha()
            self._add(nome, img, d["ax"])
        # poses derivadas (giradas)
        self._girada("aereo", "chute", -52)          # chute aereo apontando para baixo
        self._alinhar_pe("aereo", (58, 12))          # pe na hitbox do chute aereo
        self._girada("voando", "dano", 32)           # arremessado no ar
        self._girada("dash", "andar", -9)            # corrida inclinada
        if "pulo" not in self.q and "idle" in self.q:
            self.q["pulo"] = self.q["idle"]       # pulo encolhido
        self.ciclo = [n for n in info.get("ciclo_andar", []) if n in self.q]
        if not self.ciclo and "andar" in self.q:
            self.ciclo = ["andar", "idle"]
        self.cabeca = None
        if "cabeca" in info and "idle" in self.q:
            cx, cy, r = info["cabeca"]
            img = self.q["idle"]["img"][1]
            rect = pygame.Rect(int(cx - r), int(cy - r), int(r * 2), int(r * 2)).clip(img.get_rect())
            self.cabeca = img.subsurface(rect).copy()

    def _alinhar_pe(self, nome, alvo):
        """Coloca a ponta do pe (ponto mais a frente/baixo) no alvo (x, altura) do golpe."""
        if nome not in self.q:
            return
        q = self.q[nome]
        img = q["img"][1]
        pts = pygame.mask.from_surface(img, 60).outline()
        if not pts:
            return
        tx, ty = max(pts, key=lambda p: p[0] + p[1] * 0.9)
        ax = tx - alvo[0]
        q["ax"] = {1: ax, -1: img.get_width() - ax}
        q["h"] = ty + alvo[1]

    def _add(self, nome, img, ax):
        w = img.get_width()
        self.q[nome] = {
            "img": {1: img, -1: pygame.transform.flip(img, True, False)},
            "ax": {1: ax, -1: w - ax},
            "h": img.get_height(),
            "flash": {},
            "fantasma": {},
        }

    def _girada(self, nome, base, ang):
        if nome in self.q or base not in self.q:
            return
        b = self.q[base]
        img = b["img"][1]
        w = img.get_width()
        rot = pygame.transform.rotozoom(img, ang, 1.0)
        ax = rot.get_width() / 2 + (b["ax"][1] - w / 2) * math.cos(math.radians(ang))
        self._add(nome, rot, ax)

    def imagem(self, nome, d, flash=False):
        q = self.q[nome]
        if not flash:
            return q["img"][d]
        img = q["flash"].get(d)
        if img is None:
            img = q["img"][d].copy()
            img.fill((170, 170, 170), special_flags=pygame.BLEND_RGB_ADD)   # pisca branco no acerto
            q["flash"][d] = img
        return img

    def fantasma(self, nome, d):
        q = self.q[nome]
        img = q["fantasma"].get(d)
        if img is None:
            img = q["img"][d].copy()
            img.fill(tuple(c // 3 for c in self.cor), special_flags=pygame.BLEND_RGB_ADD)
            img.set_alpha(85)
            q["fantasma"][d] = img
        return img


def folha_de(ch):
    """Folha de sprites do personagem, ou None (usa o manequim)."""
    nome = SPRITES.get(ch.key)
    if not nome:
        return None
    if nome not in _folhas:
        try:
            cor = ch.cor if sum(ch.cor) > 250 else (150, 80, 220)
            _folhas[nome] = Folha(os.path.join(PASTA, nome), cor)
        except Exception as ex:                         # pasta faltando -> manequim
            print("Sprites de", nome, "nao carregados:", ex)
            _folhas[nome] = None
    return _folhas[nome]


# ================================================================ escolha da pose
def _pose_golpe(f):
    g, t = f.golpe, f.golpe_t
    chave = modelo._chave(f.char, g)
    pose = POSE_GOLPE.get(chave, "soco")
    base = "agachar" if g.agachado else "idle"
    if chave == "aereo":
        return pose, 0, 0
    if g.hits:
        ini, fim = g.hits[0].start, max(h.end for h in g.hits)
    elif g.spawn:
        ini, fim = g.spawn.get("frame", 6) - 2, g.spawn.get("frame", 6) + 8
    else:
        ini, fim = 2, g.total
    total = g.total + (0 if f.golpe_acertou else g.whiff_extra)
    if t < ini - 1:                                    # preparacao: recua um pouco
        k = t / max(1, ini)
        return base, -8 * k, 0
    if t > fim + max(4, (total - fim) // 2):           # recuperacao: volta a guarda
        return base, 0, 0
    ativo = ini - 1 <= t <= fim
    dx = 8 if ativo else 3
    dy = 0
    if chave == "especial2" and f.char.key == "vermelho":   # gancho sobe
        dy = -26 * min(1.0, (t - ini + 1) / max(1, fim - ini + 1)) if ativo else -10
    if chave == "especial2" and f.char.key == "verde" and ativo:   # rajada alterna os punhos
        pose = "soco" if (t // 3) % 2 else "especial2"
    if chave == "soco_baixo" and ativo:
        dx = 14
    return pose, dx, dy


PASSO_PX = {"vermelho": 22, "azul": 18, "amarelo": 22, "verde": 20, "roxo": 22, "preto": 20}


def _escolher(f, tempo, vitoria, folha):
    e = f.estado
    alt = CHAO_Y - f.y
    if e in ("knockdown", "ko"):
        if alt < 25 and f.vy >= 0:
            return "caido", 0, 4
        return "voando", 0, 0
    if vitoria:
        return "vitoria", 0, 0
    if e == "hitstun":
        return ("dano" if alt < 3 else "voando"), 0, 0
    if e == "blockstun" or f.defendendo():
        return ("agachar" if f.agachado else "defesa"), 0, 0
    if e == "dash":
        ciclo = folha.ciclo
        if len(ciclo) > 2:
            i = int(abs(f.passo) / 30) % len(ciclo)
            return ciclo[i], 0, -3
        return "dash", 0, -round(abs(math.sin(f.t * 0.6)) * 4)
    if e == "attack" and f.golpe:
        return _pose_golpe(f)
    if e == "jump" or alt > 3:
        # pulo em pe (sem encolher): corpo esticado o tempo todo
        if f.vy > 0 and alt < 35:                      # chegando no chao: pose de guarda
            return "idle", 0, 0
        if "pulo_desce" in folha.q:                    # pernas esticadas
            return "pulo_desce", 0, 0
        return "idle", 0, 0
    if e == "crouch" or f.agachado:
        return "agachar", 0, 0
    if e == "walk":
        ciclo = folha.ciclo
        passo = PASSO_PX.get(f.char.key, 22)
        i = int(math.floor(f.passo / passo)) % len(ciclo)      # recuar = ciclo ao contrario
        return ciclo[i], 0, 0
    return "idle", 0, round(math.sin(tempo * 0.09 + f.slot) * 2)


# ================================================================ desenho
def desenhar_lutador(surf, f, tempo, debug=False, ox=0, oy=0, vitoria=False):
    folha = folha_de(f.char)
    if folha is None:
        return modelo.desenhar_lutador(surf, f, tempo, debug, ox, oy, vitoria)

    d = f.facing
    X, Y = f.x + ox, f.y + oy
    chao = CHAO_Y + oy
    alt = max(0.0, chao - Y)
    nome, dx, dy = _escolher(f, tempo, vitoria, folha)
    if nome not in folha.q:
        nome = "idle"
    q = folha.q[nome]

    modelo._sombra_chao(surf, int(X), chao, int(max(50, 150 - alt / 3)), int(max(40, 120 - alt / 3)))
    glow(surf, tuple(c // 4 for c in folha.cor), (int(X), int(Y - 100)), 120, 0.8)

    px = X + d * dx - q["ax"][d]
    py = Y + dy - q["h"]

    if f.estado == "dash" or f.ignora_projeteis():          # rastro
        fant = folha.fantasma(nome, d)
        for k in (2, 1):
            surf.blit(fant, (px - f.vx * 2.2 * k, py))

    flash = f.flash > 0 and f.flash % 2 == 0
    img = folha.imagem(nome, d, flash)
    # transicao suave: a pose anterior some aos poucos (menos "travado")
    ant = getattr(f, "_spr_ant", None)
    troca = ant is not None and ant[0] != nome and not (nome.startswith("andar_") and ant[0].startswith("andar_"))
    if troca:
        f._spr_fade = 4
        f._spr_velha = (ant[1], ant[2], ant[3])
    fade = getattr(f, "_spr_fade", 0)
    if fade > 0 and getattr(f, "_spr_velha", None):
        vimg, vx, vy = f._spr_velha
        vimg.set_alpha(int(150 * fade / 4))
        surf.blit(vimg, (vx, vy))
        vimg.set_alpha(255)
        f._spr_fade = fade - 1
    surf.blit(img, (px, py))
    f._spr_ant = (nome, img, px, py)

    if f.estado == "ko" and alt < 25:                        # estrelinhas
        cx = X - d * 110
        for i in range(3):
            a = tempo * 0.1 + i * 2.1
            pygame.draw.circle(surf, (255, 230, 90),
                               (int(cx + math.cos(a) * 26), int(Y - 60 + math.sin(a) * 8)), 4)

    if debug:
        hb = f.hurtbox()
        if hb:
            pygame.draw.rect(surf, (0, 255, 120), (hb.x + ox, hb.y + oy, hb.w, hb.h), 2)
        for _, h in f.hits_ativos():
            b = f.caixa_golpe(h)
            pygame.draw.rect(surf, (255, 40, 40), (b.x + ox, b.y + oy, b.w, b.h), 3)


def desenhar_retrato(surf, ch, centro, raio):
    """Retrato do HUD com a cabeca do sprite. Retorna False se nao tiver sprite."""
    folha = folha_de(ch)
    if folha is None or folha.cabeca is None:
        return False
    chave = (ch.key, raio)
    if chave in _retratos:
        surf.blit(_retratos[chave], (centro[0] - raio - 4, centro[1] - raio - 4))
        return True
    base = pygame.Surface((raio * 2 + 8, raio * 2 + 8), pygame.SRCALPHA)
    _desenhar_retrato(base, folha, (raio + 4, raio + 4), raio)
    _retratos[chave] = base
    surf.blit(base, (centro[0] - raio - 4, centro[1] - raio - 4))
    return True


_retratos = {}


def _desenhar_retrato(surf, folha, centro, raio):
    pygame.draw.circle(surf, (15, 10, 20), centro, raio + 4)
    pygame.draw.circle(surf, tuple(int(c * 0.7) for c in folha.cor), centro, raio + 2)
    fundo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    pygame.draw.circle(fundo, (*tuple(c // 5 for c in folha.cor), 255), (raio, raio), raio)
    img = pygame.transform.smoothscale(folha.cabeca, (raio * 2, raio * 2))
    mascara = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (raio, raio), raio)
    img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    fundo.blit(img, (0, 0))
    surf.blit(fundo, (centro[0] - raio, centro[1] - raio))
