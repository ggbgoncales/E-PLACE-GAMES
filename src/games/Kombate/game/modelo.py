"""
modelo.py - Manequim articulado (estilo boneco de madeira/artista).
=================================================================
Como funciona:
  1) _pose() decide ONDE ficam quadril, pes e maos (em coordenadas locais,
     sempre olhando para a direita) conforme o estado/golpe do lutador.
  2) IK de 2 ossos (_ik) calcula joelhos e cotovelos automaticamente.
     -> o soco/chute vai exatamente ate a hitbox do golpe.
  3) A pose e suavizada entre frames (transicoes fluidas).
  4) Cada parte e desenhada com contorno, sombra, cor base e brilho
     (anti-aliasing com pygame.gfxdraw).
Cada personagem tem proporcao e acessorio proprios (faixa, cachecol,
ombreiras, capuz, barbatanas, lanca).
"""
import math

import pygame
from pygame import gfxdraw

from settings import CHAO_Y
from game.fx import glow

COXA, CANELA = 46, 46
BRACO, ANTEBRACO = 35, 34
LUZ = (-0.45, -0.89)                      # luz vindo de cima/esquerda


# ================================================================ cores
def _esc(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _clar(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


def _mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class Paleta:
    def __init__(self, base, linha=None, acento=(255, 255, 255)):
        self.base = base
        self.sombra = _esc(base, 0.6)
        self.luz = _clar(base, 0.5)
        self.linha = linha or _esc(base, 0.28)
        self.junta = _mix(_esc(base, 0.55), (70, 70, 80), 0.5)
        self.acento = acento

    def escura(self, f=0.78):
        p = Paleta(_esc(self.base, f), self.linha, self.acento)
        p.junta = _esc(self.junta, f)
        return p


PALETA_BRANCA = None


ESTILO = {
    #           largura  acento visor       linha (contorno)    acessorio
    "vermelho": (1.00, (255, 235, 210), None, "faixa"),
    "azul":     (1.28, (130, 225, 255), None, "ombreira"),
    "amarelo":  (0.90, (255, 255, 225), None, "barbatana"),
    "verde":    (0.92, (210, 255, 210), None, "cachecol"),
    "roxo":     (1.02, (255, 190, 255), None, "lanca"),
    "preto":    (1.00, (205, 130, 255), (150, 95, 225), "capuz"),
}


def _paleta(ch, flash):
    largura, acento, linha, acess = ESTILO.get(ch.key, (1.0, (255, 255, 255), None, None))
    if flash:
        p = Paleta((250, 250, 250), (255, 255, 255), acento)
        p.sombra = (225, 225, 235)
        return p, largura, acess
    base = ch.cor if sum(ch.cor) > 250 else (64, 64, 82)
    p = Paleta(base, linha, acento)
    if ch.key == "preto":
        p.luz = (125, 115, 160)
    return p, largura, acess


# ================================================================ primitivas AA
def _ip(p):
    return int(p[0] + 0.5), int(p[1] + 0.5)


def _poly(surf, pts, cor):
    pts = [(int(x + 0.5), int(y + 0.5)) for x, y in pts]
    if len(pts) >= 3:
        gfxdraw.filled_polygon(surf, pts, cor)
        gfxdraw.aapolygon(surf, pts, cor)


def _circ(surf, c, r, cor):
    r = int(round(r))
    if r < 1:
        return
    x, y = _ip(c)
    gfxdraw.filled_circle(surf, x, y, r, cor)
    gfxdraw.aacircle(surf, x, y, r, cor)


_SEMI = {n: [(math.cos(-math.pi / 2 + math.pi * i / n), math.sin(-math.pi / 2 + math.pi * i / n))
             for i in range(n + 1)] for n in (4, 5, 7)}


def _cap_pts(a, b, ra, rb, n=5):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    c, s = (dx / L, dy / L) if L > 1e-6 else (1.0, 0.0)
    semi = _SEMI[n]
    bx, by, ax, ay = b[0], b[1], a[0], a[1]
    pts = [(bx + (co * c - si * s) * rb, by + (co * s + si * c) * rb) for co, si in semi]
    pts += [(ax - (co * c - si * s) * ra, ay - (co * s + si * c) * ra) for co, si in semi]
    return pts


def _normal_luz(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-3:
        return LUZ
    n = (-dy / L, dx / L)
    if n[0] * LUZ[0] + n[1] * LUZ[1] < 0:
        n = (-n[0], -n[1])
    return n


def capsula(surf, a, b, ra, rb, pal, borda=2.5):
    """Membro cilindrico com contorno, sombra, cor e brilho."""
    _poly(surf, _cap_pts(a, b, ra + borda, rb + borda), pal.linha)
    _poly(surf, _cap_pts(a, b, ra, rb), pal.sombra)
    n = _normal_luz(a, b)
    k = 0.74
    a2 = (a[0] + n[0] * ra * (1 - k), a[1] + n[1] * ra * (1 - k))
    b2 = (b[0] + n[0] * rb * (1 - k), b[1] + n[1] * rb * (1 - k))
    _poly(surf, _cap_pts(a2, b2, ra * k, rb * k), pal.base)
    a3 = (a[0] + n[0] * ra * 0.52, a[1] + n[1] * ra * 0.52)
    b3 = (b[0] + n[0] * rb * 0.52, b[1] + n[1] * rb * 0.52)
    _poly(surf, _cap_pts(a3, b3, max(1.2, ra * 0.24), max(1.2, rb * 0.24), 4), pal.luz)


def esfera(surf, c, r, pal, cor=None, borda=2.5):
    base = cor or pal.base
    _circ(surf, c, r + borda, pal.linha)
    _circ(surf, c, r, _esc(base, 0.62))
    _circ(surf, (c[0] + LUZ[0] * r * 0.18, c[1] + LUZ[1] * r * 0.18), r * 0.8, base)
    _circ(surf, (c[0] + LUZ[0] * r * 0.45, c[1] + LUZ[1] * r * 0.45), max(1.5, r * 0.28), _clar(base, 0.55))


def _escala(pts, k, desl=(0, 0)):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return [(cx + (x - cx) * k + desl[0], cy + (y - cy) * k + desl[1]) for x, y in pts]


def peca(surf, pts, pal, cor=None, borda=3.0):
    """Peca rigida (peito, quadril, cabeca) com volume."""
    base = cor or pal.base
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    tam = max(max(xs) - min(xs), max(ys) - min(ys), 1)
    _poly(surf, _escala(pts, 1 + 2 * borda / tam), pal.linha)
    _poly(surf, pts, _esc(base, 0.62))
    _poly(surf, _escala(pts, 0.86, (LUZ[0] * tam * 0.06, LUZ[1] * tam * 0.06)), base)
    _poly(surf, _escala(pts, 0.38, (LUZ[0] * tam * 0.2, LUZ[1] * tam * 0.2)), _clar(base, 0.42))


# ================================================================ IK / util
def _ik(R, T, a, b, sinal):
    dx, dy = T[0] - R[0], T[1] - R[1]
    d = math.hypot(dx, dy)
    if d < 1e-3:
        dx, dy, d = 0.0, 1.0, 1.0
    ux, uy = dx / d, dy / d
    d2 = min(max(d, abs(a - b) + 1), a + b - 0.5)
    E = (R[0] + ux * d2, R[1] + uy * d2)
    cosA = (a * a + d2 * d2 - b * b) / (2 * a * d2)
    A = math.acos(max(-1.0, min(1.0, cosA)))
    ang = math.atan2(uy, ux) + sinal * A
    return (R[0] + math.cos(ang) * a, R[1] + math.sin(ang) * a), E


def _lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def _bez(a, c, b, t):
    return _lerp(_lerp(a, c, t), _lerp(c, b, t), t)


def _hit_atual(g, t):
    for h in g.hits:
        if t <= h.end + 2:
            return h
    return g.hits[-1]


def _progresso(t, h):
    if t < h.start:
        return 0.15 + 0.85 * (t / max(1, h.start)) ** 2
    if t <= h.end:
        return 1.0
    return max(0.0, 1.0 - (t - h.end) / 8)


def _chave(ch, g):
    for k, v in ch.golpes.items():
        if v is g:
            return k
    return ""


# ================================================================ POSES
def _guarda(resp, agach=False):
    if agach:
        return {"hip": (-2, -52 + resp * 0.5), "lean": 0.32, "head": -0.18,
                "ff": (28, -8), "fb": (-26, -8), "hf": (46, -104 + resp), "hb": (30, -116 + resp)}
    return {"hip": (0, -86 + resp), "lean": 0.12, "head": -0.05,
            "ff": (22, -8), "fb": (-26, -8), "hf": (42, -150 + resp), "hb": (24, -160 + resp)}


def _pose(f, tempo, vitoria):
    ch = f.char
    e = f.estado
    resp = math.sin(tempo * 0.09 + f.slot) * 2 if e in ("idle", "crouch") else 0
    P = _guarda(resp, f.agachado)
    P["lanca"] = None
    P["suave"] = 0.45
    alt = max(0.0, CHAO_Y - f.y)

    if e in ("knockdown", "ko"):
        if alt < 25 and f.vy >= 0:
            P.update(hip=(0, -16), lean=-math.pi / 2 - 0.06, head=-0.15,
                     ff=(76, -10), fb=(66, -8), hf=(-40, -12), hb=(-14, -8))
        else:
            gira = -0.7 - min(1.0, f.t * 0.05)
            P.update(hip=(0, -78), lean=gira, head=-0.4,
                     ff=(36, -44), fb=(22, -24), hf=(-46, -150), hb=(-24, -160))
        P["suave"] = 0.35
        return P

    if vitoria:
        P.update(lean=-0.04, head=-0.15, hf=(16, -224), hb=(-12, -112), ff=(20, -8), fb=(-24, -8))
        return P

    if e == "hitstun":
        k = min(1.0, f.stun / 10)
        P.update(hip=(-8, -84), lean=-0.25 - 0.25 * k, head=-0.4,
                 hf=(-6, -176), hb=(-46, -136), ff=(16, -8), fb=(-32, -8))
        P["suave"] = 0.6
        return P

    if f.defendendo() or e == "blockstun":
        if ch.arma:
            P.update(hf=(40, P["hip"][1] - 70), hb=(30, P["hip"][1] - 30), lean=0.0)
        elif f.agachado:
            P.update(hf=(36, -112), hb=(34, -92), lean=0.2)
        else:
            P.update(hf=(36, -164), hb=(34, -138), lean=-0.04, head=0.05)
        return P

    if e == "dash":
        frente = (f.vx * f.facing) >= 0
        if frente:
            P.update(lean=0.5, hip=(4, -80), ff=(40, -12), fb=(-42, -16), hf=(50, -130), hb=(12, -128))
        else:
            P.update(lean=-0.2, hip=(-4, -84), ff=(30, -14), fb=(-30, -8), hf=(40, -150), hb=(24, -158))
        return P

    if e == "jump" or (alt > 3 and e != "attack"):
        P.update(hip=(0, -86), lean=0.05, ff=(18, -36), fb=(-10, -24), hf=(36, -160), hb=(16, -168))
        return P

    if e == "walk":
        sentido = 1 if f.vx * f.facing >= 0 else -1
        ph = f.t * 0.36 * sentido
        s, c = math.sin(ph), math.cos(ph)
        P["ff"] = (22 + 16 * s, -8 - max(0.0, 12 * c))
        P["fb"] = (-24 - 16 * s, -8 - max(0.0, -12 * c))
        P["hip"] = (0, -86 + abs(s) * 3)
        return P

    if e == "attack" and f.golpe:
        _pose_golpe(f, P, tempo)
    elif ch.arma:                                    # Lanceiro segura a lanca apontada p/ frente
        hy = P["hip"][1]
        if e == "hitstun":
            P.update(hf=(-2, hy - 82), hb=(-30, hy - 50))
        else:
            P.update(hf=(44, hy - 44), hb=(14, hy - 26))
    return P


def _pose_golpe(f, P, tempo):
    ch, g, t = f.char, f.golpe, f.golpe_t
    chave = _chave(ch, g)
    P["suave"] = 0.85
    guarda = dict(P)

    if not g.hits:                                   # tiro / mina / detonar
        fr = g.spawn["frame"] if g.spawn else 8
        p = min(1.0, t / max(1, fr))
        if t > fr + 6:
            p = max(0.0, 1 - (t - fr - 6) / 8)
        tipo = g.spawn["tipo"] if g.spawn else ""
        if tipo == "mina":
            P.update(_guarda(0, True))
            P["lean"] = 0.3 + 0.3 * p
            P["hf"] = _bez(guarda["hf"], (20, -80), (58, -10), p)
        elif tipo == "detonar":
            P["hf"] = _bez(guarda["hf"], (40, -190), (18, -214), p)
            P["head"] = -0.25
        else:
            oy = g.spawn.get("oy", 100) if g.spawn else 100
            baixo = oy < 40
            if baixo:
                P.update(_guarda(0, True))
                alvo = (70, -34)
            else:
                alvo = (72, -(oy + 12))
            carga = (-8, -112) if not baixo else (-4, -70)
            pp = min(1.0, p * 1.4)
            P["hf"] = _bez(guarda["hf"], carga, alvo, pp)
            P["hb"] = (P["hf"][0] - 6, P["hf"][1] + 12)
            P["lean"] = (0.32 if baixo else 0.1) + 0.2 * p
            P["hip"] = (P["hip"][0] + 8 * p, P["hip"][1])
        return

    h = _hit_atual(g, t)
    p = _progresso(t, h)
    ox, oy, w, hh = h.box
    T = (ox + w - 6, -(oy + hh / 2))
    ativo = h.start <= t <= h.end
    if ativo:
        P["suave"] = 1.0

    if ch.arma:                                       # LANCA (Lanceiro)
        if g.agachado:
            P.update(_guarda(0, True))
        ombro = (P["hip"][0] + 10, P["hip"][1] - 52)
        dx, dy = T[0] - ombro[0], T[1] - ombro[1]
        L = math.hypot(dx, dy) or 1
        u = (dx / L, dy / L)
        alcance = 26 + 40 * p
        P["hf"] = (ombro[0] + u[0] * alcance, ombro[1] + u[1] * alcance)
        P["hb"] = (P["hf"][0] - u[0] * 34, P["hf"][1] - u[1] * 34 + 4)
        ponta = max(110.0, (L - alcance) * (1.0 if ativo else 0.0) + 20) if ativo else 110.0
        P["lanca"] = (u, ponta, ativo)
        P["lean"] = (0.4 if g.agachado else 0.12) + 0.2 * p
        P["hip"] = (P["hip"][0] + 10 * p, P["hip"][1])
        P["ff"] = (P["ff"][0] + 14 * p, P["ff"][1])
        return

    if h.grab:
        P["lean"] = 0.12 + 0.18 * p
        alvo = (ox + w * 0.55, -(oy + hh * 0.55))
        P["hf"] = _bez(guarda["hf"], (60, -170), alvo, p)
        P["hb"] = _bez(guarda["hb"], (40, -120), (alvo[0] - 6, alvo[1] + 22), p)
        P["hip"] = (P["hip"][0] + 10 * p, P["hip"][1])
        return

    if chave in ("chute", "rasteira", "aereo"):     # PERNAS
        if chave == "rasteira":
            P.update(_guarda(0, True))
            P.update(hip=(-8, -46), lean=0.42 + 0.1 * p, fb=(-22, -8), hb=(34, -36))
            P["ff"] = _bez((26, -8), (50, -26), T, p)
        elif chave == "aereo":
            P.update(hip=(0, -86), lean=-0.18 * p, fb=(-12, -34), hf=(30, -170), hb=(10, -164))
            P["ff"] = _bez((14, -34), (24, -70), T, p)
        else:
            P["lean"] = 0.12 - 0.42 * p
            P["hip"] = (-6 * p, -86 - 4 * p)
            P["fb"] = (-16, -8)
            P["ff"] = _bez((22, -8), (T[0] * 0.3, T[1] - 10), T, p)
            P["hf"] = (30, -158)
            P["hb"] = (6, -150)
        return

    # BRACOS (socos e especiais de mao)
    if g.agachado:
        P.update(_guarda(0, True))
    alto = hh >= 120                                  # gancho / antiaereo
    if alto:
        P["hip"] = (4 * p, -86 - 18 * p)
        P["lean"] = 0.1 - 0.16 * p
        P["ff"] = (18, -8 - 14 * p)
        T = (ox + w * 0.6, -(oy + hh - 14))
        P["hf"] = _bez((34, -96), (52, -120), T, p)
        P["hb"] = (14, -150)
        return
    # distancia extra -> avanca o quadril
    ombro = (P["hip"][0] + 8, P["hip"][1] - 54)
    falta = max(0.0, math.hypot(T[0] - ombro[0], T[1] - ombro[1]) - 66)
    P["hip"] = (P["hip"][0] + (8 + min(falta, 26)) * p, P["hip"][1])
    P["lean"] = P["lean"] + 0.2 * p
    P["ff"] = (P["ff"][0] + 10 * p, P["ff"][1])
    mao = "hf"
    if len(g.hits) > 2:                               # rajada: alterna as maos
        idx = g.hits.index(h)
        mao = "hf" if idx % 2 == 0 else "hb"
    base = guarda[mao]
    P[mao] = _bez(base, (base[0] - 12, base[1] + 8), T, p)
    if mao == "hf":
        P["hb"] = (14, P["hip"][1] - 70)


# ================================================================ suavizacao
_CHAVES = ("hip", "ff", "fb", "hf", "hb")


def _suavizar(f, P):
    ant = getattr(f, "_pose_ant", None)
    k = P["suave"]
    if ant is not None and k < 1.0:
        for c in _CHAVES:
            P[c] = _lerp(ant[c], P[c], k)
        P["lean"] = ant["lean"] + (P["lean"] - ant["lean"]) * k
        P["head"] = ant["head"] + (P["head"] - ant["head"]) * k
    f._pose_ant = {c: P[c] for c in _CHAVES + ("lean", "head")}
    return P


# ================================================================ desenho
def _sombra_chao(surf, x, chao, largura, alpha):
    s = pygame.Surface((largura, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (8, 4, 10, alpha), (0, 0, largura, 24))
    surf.blit(s, (x - largura // 2, chao - 12))


def _esqueleto(P, larg):
    hip, l = P["hip"], P["lean"]
    tu = (math.sin(l), -math.cos(l))
    tv = (math.cos(l), math.sin(l))

    def T(al, ac):
        return (hip[0] + tu[0] * al + tv[0] * ac * larg, hip[1] + tu[1] * al + tv[1] * ac * larg)

    hl = l + P["head"]
    hu = (math.sin(hl), -math.cos(hl))
    hv = (math.cos(hl), math.sin(hl))
    pesc = T(60, 2)
    cab = (pesc[0] + tu[0] * 6 + hu[0] * 20, pesc[1] + tu[1] * 6 + hu[1] * 20)

    def H(al, ac):
        return (cab[0] + hu[0] * al + hv[0] * ac, cab[1] + hu[1] * al + hv[1] * ac)

    S = {"T": T, "H": H, "tu": tu, "tv": tv, "hu": hu, "hv": hv, "cab": cab, "pesc": pesc}
    S["ombro_f"] = T(52, 7)
    S["ombro_b"] = T(52, -7)
    S["quad_f"] = T(0, 5)
    S["quad_b"] = T(0, -5)
    S["joelho_f"], S["pe_f"] = _ik(S["quad_f"], P["ff"], COXA, CANELA, -1)
    S["joelho_b"], S["pe_b"] = _ik(S["quad_b"], P["fb"], COXA, CANELA, -1)
    S["cot_f"], S["mao_f"] = _ik(S["ombro_f"], P["hf"], BRACO, ANTEBRACO, 1)
    S["cot_b"], S["mao_b"] = _ik(S["ombro_b"], P["hb"], BRACO, ANTEBRACO, 1)
    return S


def _perna(surf, W, quad, joelho, pe, pal, larg):
    q, j, p = W(quad), W(joelho), W(pe)
    capsula(surf, j, p, 9.5 * larg, 7 * larg, pal)
    dx, dy = p[0] - j[0], p[1] - j[1]
    L = math.hypot(dx, dy) or 1
    fwd = (-dy / L, dx / L) if (W((1, 0))[0] - W((0, 0))[0]) > 0 else (dy / L, -dx / L)
    if fwd[0] * (W((1, 0))[0] - W((0, 0))[0]) < 0:
        fwd = (-fwd[0], -fwd[1])
    ponta = (p[0] + fwd[0] * 20 + dx / L * 5, p[1] + fwd[1] * 20 + dy / L * 5)
    calc = (p[0] - fwd[0] * 7 + dx / L * 6, p[1] - fwd[1] * 7 + dy / L * 6)
    capsula(surf, calc, ponta, 7 * larg, 5.5 * larg, pal, 2.2)
    capsula(surf, q, j, 12.5 * larg, 9.5 * larg, pal)
    esfera(surf, j, 7.5 * larg, pal, pal.junta)


def _braco(surf, W, ombro, cot, mao, pal, larg, punho=9.5):
    o, c, m = W(ombro), W(cot), W(mao)
    capsula(surf, o, c, 8.5 * larg, 7 * larg, pal)
    esfera(surf, c, 6.5 * larg, pal, pal.junta)
    capsula(surf, c, m, 7.5 * larg, 8 * larg, pal)
    esfera(surf, m, punho * (1.1 if larg > 1.1 else 1.0), pal)


def _lanca(surf, W, mao_b, mao_f, info, tempo):
    a, b = W(mao_b), W(mao_f)
    if info is None:
        u = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*u) or 1
        u = (u[0] / L, u[1] / L)
        ponta_len, ativo = 110, False
    else:
        uu, ponta_len, ativo = info
        s = 1 if W((1, 0))[0] > W((0, 0))[0] else -1
        u = (uu[0] * s, uu[1])
    cabo = (a[0] - u[0] * 46, a[1] - u[1] * 46)
    ponta = (b[0] + u[0] * ponta_len, b[1] + u[1] * ponta_len)
    pygame.draw.line(surf, (30, 18, 10), _ip(cabo), _ip(ponta), 9)
    pygame.draw.line(surf, (140, 92, 48), _ip(cabo), _ip(ponta), 5)
    pygame.draw.line(surf, (190, 140, 85), _ip((cabo[0], cabo[1] - 1)), _ip((ponta[0], ponta[1] - 1)), 1)
    for k in (0.15, 0.3):                                       # amarracoes
        q = _lerp(cabo, ponta, k)
        pygame.draw.circle(surf, (210, 170, 60), _ip(q), 5)
    n = (-u[1], u[0])
    lam = [(ponta[0] + u[0] * 34, ponta[1] + u[1] * 34),
           (ponta[0] + n[0] * 9 + u[0] * 4, ponta[1] + n[1] * 9 + u[1] * 4),
           (ponta[0] - u[0] * 4, ponta[1] - u[1] * 4),
           (ponta[0] - n[0] * 9 + u[0] * 4, ponta[1] - n[1] * 9 + u[1] * 4)]
    if ativo:
        glow(surf, (120, 50, 170), _ip((ponta[0] + u[0] * 14, ponta[1] + u[1] * 14)), 60, 1.0)
    _poly(surf, _escala(lam, 1.25), (40, 30, 50))
    _poly(surf, lam, (215, 215, 235))
    _poly(surf, [lam[0], lam[1], lam[2]], (250, 250, 255))


def _tecido(surf, pts, larg0, cor, borda):
    """Fita/cachecol: linha grossa que afina."""
    for i in range(len(pts) - 1):
        lw = max(2, int(larg0 * (1 - i / len(pts))))
        pygame.draw.line(surf, borda, _ip(pts[i]), _ip(pts[i + 1]), lw + 4)
    for i in range(len(pts) - 1):
        lw = max(2, int(larg0 * (1 - i / len(pts))))
        pygame.draw.line(surf, cor, _ip(pts[i]), _ip(pts[i + 1]), lw)
        _circ(surf, pts[i + 1], lw / 2, cor)


def _rastro(f, inicio, tempo, d, vx):
    pts = [inicio]
    for i in range(1, 7):
        onda = math.sin(tempo * 0.3 - i * 0.9) * (3 + i * 1.2)
        arrasto = -d * (11 + min(10, abs(vx) * 1.4)) * i / 1
        pts.append((inicio[0] + arrasto * 0.95, inicio[1] + i * 4 + onda))
    return pts


def _desenhar_corpo(surf, f, P, S, W, pal, larg, acess, tempo, d, so_silhueta=False):
    pal_b = pal.escura(0.74)
    T, H = S["T"], S["H"]

    # --- acessorios atras do corpo
    if acess == "cachecol" and not so_silhueta:
        ini = W(T(58, -6))
        _tecido(surf, _rastro(f, ini, tempo, d, f.vx), 13, (235, 228, 200), (60, 50, 40))
    if acess == "capuz" and not so_silhueta:
        for k, off in ((0, -10), (1, 4)):
            ini = W(T(12, -10 + off))
            pts = [ini] + [(ini[0] - d * (6 + i * 7), ini[1] + i * 13 + math.sin(tempo * 0.2 + i + k) * 3)
                           for i in range(1, 6)]
            _tecido(surf, pts, 16, (34, 30, 46), (150, 95, 225))

    # --- braco e perna de tras
    _braco(surf, W, S["ombro_b"], S["cot_b"], S["mao_b"], pal_b, larg)
    _perna(surf, W, S["quad_b"], S["joelho_b"], S["pe_b"], pal_b, larg)

    # --- tronco
    abd_a, abd_b = W(T(16, 0)), W(T(36, 0))
    capsula(surf, abd_a, abd_b, 11 * larg, 13 * larg, pal)
    quadril = [T(20, -15), T(20, 13), T(6, 15), T(-6, 9), T(-8, -8), T(4, -16)]
    peca(surf, [W(p) for p in quadril], pal)
    faixa_cor = _mix(pal.base, (25, 20, 30), 0.65) if acess != "ombreira" else (215, 170, 60)
    faixa = [T(22, -16), T(22, 14), T(15, 15), T(15, -16)]
    _poly(surf, [W(p) for p in _escala(faixa, 1.08)], pal.linha)
    _poly(surf, [W(p) for p in faixa], faixa_cor)
    peito = [T(63, -13), T(65, 4), T(61, 15), T(47, 18), T(33, 13), T(29, -2), T(33, -15), T(49, -18)]
    peca(surf, [W(p) for p in peito], pal)
    pygame.draw.aaline(surf, pal.sombra, W(T(58, 1)), W(T(36, 1)))
    pygame.draw.aaline(surf, pal.sombra, W(T(46, -12)), W(T(46, 12)))

    # --- perna da frente
    _perna(surf, W, S["quad_f"], S["joelho_f"], S["pe_f"], pal, larg)

    # --- ombreira (Colosso / Lanceiro)
    if acess in ("ombreira", "lanca"):
        o = S["ombro_f"]
        pts = [T(64, 2), T(64, 22), T(46, 26), T(40, 10)] if acess == "ombreira" else \
              [T(62, 0), T(66, 16), T(50, 22), T(44, 8)]
        cor = (205, 160, 55) if acess == "ombreira" else _esc(pal.base, 0.7)
        peca(surf, [W(p) for p in pts], pal, cor)

    # --- pescoco e cabeca
    capsula(surf, W(T(56, 2)), W(S["pesc"]), 6.5 * larg, 6 * larg, pal, 2)
    cab = []
    for i in range(18):
        a = i / 18 * math.tau
        al = math.sin(a) * 19.5
        ac = math.cos(a) * 15.5 + (2.5 if math.cos(a) > 0 and math.sin(a) < 0 else 0)
        cab.append(H(al, ac))
    peca(surf, [W(p) for p in cab], pal)

    if acess == "capuz":
        capuz = [H(23, -4), H(20, 10), H(8, 18), H(2, 19), H(-6, 14), H(-24, 12), H(-20, -14),
                 H(-4, -25), H(14, -20)]
        peca(surf, [W(p) for p in capuz], pal, (36, 32, 50))
    if acess == "barbatana":
        for k in (0, 1):
            fin = [H(8 - k * 10, -12), H(26 - k * 6, -26), H(4 - k * 10, -18)]
            _poly(surf, [W(p) for p in _escala(fin, 1.3)], pal.linha)
            _poly(surf, [W(p) for p in fin], _esc(pal.base, 0.75))
    if acess == "faixa":
        banda = [H(9, -16), H(11, 2), H(10, 16), H(4, 16.5), H(5, 2), H(3, -16)]
        _poly(surf, [W(p) for p in _escala(banda, 1.1)], (10, 8, 12))
        _poly(surf, [W(p) for p in banda], (235, 232, 225))
        if not so_silhueta:
            ini = W(H(7, -15))
            _tecido(surf, _rastro(f, ini, tempo, d, f.vx)[:6], 7, (235, 232, 225), (40, 30, 30))

    # visor (mostra para onde olha)
    if not so_silhueta:
        visor = [H(6, 5), H(6, 17), H(-3, 16), H(-3, 4)]
        _poly(surf, [W(p) for p in visor], (16, 14, 24))
        olho_a, olho_b = W(H(1.5, 8)), W(H(1.5, 15.5))
        glow(surf, _esc(pal.acento, 0.38), _ip(_lerp(olho_a, olho_b, 0.5)), 24, 0.9)
        pygame.draw.line(surf, pal.acento, _ip(olho_a), _ip(olho_b), 3)

    # --- lanca / braco da frente
    if acess == "lanca":
        _lanca(surf, W, S["mao_b"], S["mao_f"], P.get("lanca"), tempo)
    _braco(surf, W, S["ombro_f"], S["cot_f"], S["mao_f"], pal, larg)


def desenhar_lutador(surf, f, tempo, debug=False, ox=0, oy=0, vitoria=False):
    ch = f.char
    d = f.facing
    X, Y = f.x + ox, f.y + oy
    chao = CHAO_Y + oy
    flash = f.flash > 0 and f.flash % 2 == 0
    pal, larg, acess = _paleta(ch, flash)
    alt = max(0.0, chao - Y)

    P = _suavizar(f, _pose(f, tempo, vitoria))
    S = _esqueleto(P, larg)

    def W(p):
        return (X + d * p[0], Y + p[1])

    _sombra_chao(surf, int(X), chao, int(max(50, 140 - alt / 3) * (larg ** 0.5)), int(max(40, 120 - alt / 3)))

    base_glow = ch.cor if sum(ch.cor) > 250 else (120, 70, 200)
    glow(surf, _esc(base_glow, 0.28), _ip(W((0, -100))), 120, 0.8)

    # rastro (dash / invulneravel a projetil)
    if f.estado == "dash" or f.ignora_projeteis():
        fant = pygame.Surface((360, 330))
        fant.fill((0, 0, 0))
        fant.set_colorkey((0, 0, 0))
        cor = _clar(base_glow, 0.35)
        pf = Paleta(cor, cor)
        pf.sombra = pf.luz = pf.junta = cor

        def Wf(p):
            return (180 + d * p[0], 300 + p[1])
        _desenhar_corpo(fant, f, P, S, Wf, pf, larg, None, tempo, d, so_silhueta=True)
        for k, a in ((2, 50), (1, 90)):
            fant.set_alpha(a)
            surf.blit(fant, (X - 180 - f.vx * 2.2 * k, Y - 300))

    _desenhar_corpo(surf, f, P, S, W, pal, larg, acess, tempo, d)

    if f.tem_armadura():
        pulso = 0.6 + 0.4 * math.sin(tempo * 0.7)
        glow(surf, (int(170 * pulso), int(100 * pulso), 15), _ip(W(S["T"](40, 0))), 130, 1.0)

    if f.estado == "ko" and alt < 25:
        c = W(S["cab"])
        for i in range(3):
            a = tempo * 0.1 + i * 2.1
            _circ(surf, (c[0] + math.cos(a) * 28, c[1] - 30 + math.sin(a) * 8), 4, (255, 230, 90))

    if debug:
        hb = f.hurtbox()
        if hb:
            pygame.draw.rect(surf, (0, 255, 120), (hb.x + ox, hb.y + oy, hb.w, hb.h), 2)
        for _, h in f.hits_ativos():
            b = f.caixa_golpe(h)
            pygame.draw.rect(surf, (255, 40, 40), (b.x + ox, b.y + oy, b.w, b.h), 3)
