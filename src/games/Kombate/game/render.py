"""
render.py - desenho (arena, manequins, objetos, HUD).
Tudo e feito com formas + luz, sem imagens, para prototipagem.
Para colocar a arte final, troque o corpo de desenhar_lutador() por sprites
(use f.estado, f.golpe, f.golpe_t e f.facing para escolher o quadro).
"""
import math
import random

import pygame

from settings import LARGURA, ALTURA, CHAO_Y, GUARDA_MAX
from game.fx import glow


# ============================================================== cores / texto
def escurecer(cor, f=0.55):
    return tuple(int(c * f) for c in cor)


def clarear(cor, f=0.45):
    return tuple(int(c + (255 - c) * f) for c in cor)


def misturar(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def contorno_de(cor):
    """Contorno escuro; para personagens escuros (Sombra) usa um brilho roxo."""
    return (150, 110, 210) if sum(cor) < 250 else escurecer(cor, 0.4)


def cor_texto(cor):
    return (190, 170, 230) if sum(cor) < 250 else cor


def make_font(tamanho, bold=True):
    for nome in ("ubuntu", "notosans", "dejavusans", "liberationsans", "arial", "verdana"):
        caminho = pygame.font.match_font(nome, bold=bold)
        if caminho:
            return pygame.font.Font(caminho, tamanho)
    return pygame.font.Font(None, int(tamanho * 1.35))


_cache_txt = {}


def _texto_img(msg, fonte, cor, contorno):
    """Renderiza o texto com contorno uma vez so (cache)."""
    chave = (msg, id(fonte), cor, contorno)
    img = _cache_txt.get(chave)
    if img is None:
        frente = fonte.render(msg, True, cor)
        if contorno:
            sombra = fonte.render(msg, True, (12, 8, 16))
            c = contorno
            img = pygame.Surface((frente.get_width() + c * 2, frente.get_height() + c * 2 + 1), pygame.SRCALPHA)
            for ox, oy in ((0, c), (c * 2, c), (c, 0), (c, c * 2), (c * 2, c * 2 + 1)):
                img.blit(sombra, (ox, oy))
            img.blit(frente, (c, c))
        else:
            img = frente
        if len(_cache_txt) > 500:
            _cache_txt.clear()
        _cache_txt[chave] = img
    return img


def texto(surf, msg, fonte, cor, pos, anchor="center", contorno=2, escala=1.0, alpha=255):
    img = _texto_img(str(msg), fonte, tuple(cor), contorno)
    if escala != 1.0:
        tam = (max(1, int(img.get_width() * escala)), max(1, int(img.get_height() * escala)))
        img = pygame.transform.smoothscale(img, tam)
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    r = img.get_rect(**{anchor: pos})
    surf.blit(img, r)
    return r


def gradiente_v(surf, rect, topo, base):
    x, y, w, h = rect
    for i in range(h):
        pygame.draw.line(surf, misturar(topo, base, i / max(1, h - 1)), (x, y + i), (x + w - 1, y + i))


# ============================================================== arena
TOCHAS = ((120, 205), (1160, 205))


def criar_arena():
    rnd = random.Random(42)
    s = pygame.Surface((LARGURA, ALTURA))
    # ceu
    for y in range(CHAO_Y):
        k = y / CHAO_Y
        if k < 0.55:
            cor = misturar((14, 8, 30), (70, 22, 70), k / 0.55)
        else:
            cor = misturar((70, 22, 70), (215, 95, 70), (k - 0.55) / 0.45)
        pygame.draw.line(s, cor, (0, y), (LARGURA, y))
    for _ in range(140):                                         # estrelas
        x, y = rnd.randint(0, LARGURA), rnd.randint(0, 300)
        b = rnd.randint(120, 255)
        s.set_at((x, y), (b, b, min(255, b + 30)))
        if rnd.random() < 0.15:
            pygame.draw.circle(s, (b, b, 255), (x, y), 1)
    # lua
    glow(s, (120, 70, 90), (900, 210), 260, 0.9)
    pygame.draw.circle(s, (255, 225, 200), (900, 210), 78)
    pygame.draw.circle(s, (245, 205, 185), (885, 195), 70)
    for cx, cy, r in ((870, 190, 12), (920, 235, 9), (905, 180, 6), (875, 240, 7)):
        pygame.draw.circle(s, (230, 190, 170), (cx, cy), r)
    # nuvens
    for _ in range(9):
        cx, cy = rnd.randint(0, LARGURA), rnd.randint(250, 380)
        for _ in range(6):
            pygame.draw.ellipse(s, (120, 45, 80), (cx + rnd.randint(-90, 90), cy + rnd.randint(-10, 10),
                                                     rnd.randint(90, 180), rnd.randint(18, 30)))
    # montanhas (3 camadas)
    for camada, (cor, base_h, var) in enumerate((((70, 28, 64), 300, 110),
                                                ((48, 18, 46), 220, 90),
                                                ((32, 12, 32), 140, 70))):
        pts = [(0, CHAO_Y)]
        x = -40
        while x < LARGURA + 80:
            pts.append((x, CHAO_Y - base_h - rnd.randint(-var, var) * (0.6 if x % 2 else 1)))
            x += rnd.randint(60, 140)
        pts.append((LARGURA, CHAO_Y))
        pygame.draw.polygon(s, cor, pts)
    # templo (pagode)
    cx = 640
    sil = (24, 9, 24)
    for i, (w, h) in enumerate(((330, 90), (250, 70), (170, 60))):
        base = CHAO_Y - 60 - i * 95
        pygame.draw.rect(s, sil, (cx - w // 2 + 30, base - h, w - 60, h))
        pygame.draw.polygon(s, sil, [(cx - w // 2 - 25, base - h + 6), (cx, base - h - 40),
                                     (cx + w // 2 + 25, base - h + 6)])
        for jx in range(-w // 2 + 60, w // 2 - 50, 42):                     # janelas
            glow(s, (90, 40, 10), (cx + jx + 8, base - h // 2), 26, 0.8)
            pygame.draw.rect(s, (255, 170, 80), (cx + jx + 2, base - h // 2 - 10, 12, 20))
    pygame.draw.rect(s, sil, (cx - 200, CHAO_Y - 60, 400, 60))
    pygame.draw.polygon(s, sil, [(cx - 6, CHAO_Y - 395), (cx, CHAO_Y - 440), (cx + 6, CHAO_Y - 395)])
    # pilares com estandartes
    for px in (120, 1160):
        gradiente_v(s, (px - 34, 230, 68, CHAO_Y - 230), (70, 50, 70), (40, 26, 42))
        pygame.draw.rect(s, (90, 66, 90), (px - 46, 222, 92, 22), border_radius=4)
        pygame.draw.rect(s, (90, 66, 90), (px - 46, CHAO_Y - 24, 92, 24), border_radius=4)
        pygame.draw.polygon(s, (130, 25, 30), [(px - 26, 260), (px + 26, 260), (px + 26, 470),
                                               (px, 450), (px - 26, 470)])
        pygame.draw.circle(s, (220, 170, 60), (px, 330), 15, 3)
        pygame.draw.line(s, (220, 170, 60), (px - 9, 330), (px + 9, 330), 3)
        pygame.draw.rect(s, (60, 45, 40), (px - 10, 182, 20, 40))           # suporte da tocha
        pygame.draw.polygon(s, (80, 60, 50), [(px - 18, 182), (px + 18, 182), (px + 10, 196), (px - 10, 196)])
    # chao de pedra em perspectiva
    gradiente_v(s, (0, CHAO_Y, LARGURA, ALTURA - CHAO_Y), (92, 62, 70), (40, 24, 32))
    linhas_y = [CHAO_Y + d for d in (0, 12, 28, 50, 80)]
    for y in linhas_y:
        pygame.draw.line(s, (60, 38, 46), (0, y), (LARGURA, y), 2)
    for i in range(-14, 30):
        x0 = LARGURA / 2 + i * 58
        x1 = LARGURA / 2 + (x0 - LARGURA / 2) * 1.9
        pygame.draw.line(s, (60, 38, 46), (x0, CHAO_Y), (x1, ALTURA), 2)
    reflexo = pygame.Surface((240, ALTURA - CHAO_Y), pygame.SRCALPHA)       # reflexo da lua
    for i in range(ALTURA - CHAO_Y):
        pygame.draw.line(reflexo, (255, 210, 190, max(0, 70 - i)), (120 - 70 + i // 3, i),
                         (120 + 70 - i // 3, i))
    s.blit(reflexo, (780, CHAO_Y))
    pygame.draw.line(s, (180, 120, 120), (0, CHAO_Y), (LARGURA, CHAO_Y), 2)
    return s


def criar_vinheta():
    v = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for i in range(60):
        a = int(150 * (1 - i / 60) ** 2.2)
        pygame.draw.rect(v, (0, 0, 0, a), (i * 3, i * 2, LARGURA - i * 6, ALTURA - i * 4), 3)
    return v


class Ambiente:
    """Partes animadas do cenario: tochas, brasas subindo e neblina."""

    def __init__(self):
        self.brasas = [[random.uniform(0, LARGURA), random.uniform(0, ALTURA),
                        random.uniform(0.3, 1.2), random.uniform(0, 6.28)] for _ in range(45)]
        self.neblina = pygame.Surface((LARGURA * 2, 120), pygame.SRCALPHA)
        rnd = random.Random(3)
        for _ in range(70):
            x, y = rnd.randint(0, LARGURA * 2 - 200), rnd.randint(20, 90)
            pygame.draw.ellipse(self.neblina, (230, 180, 200, 9), (x, y, rnd.randint(150, 320), rnd.randint(30, 60)))
        if pygame.display.get_surface() is not None:
            self.neblina = self.neblina.convert_alpha()

    def desenhar(self, surf, t):
        for tx, ty in TOCHAS:
            fl = math.sin(t * 0.31 + tx) * 0.5 + math.sin(t * 0.73) * 0.5
            glow(surf, (120, 60, 15), (tx, ty), 120 + fl * 10, 0.9)
            for k, (cor, w, h) in enumerate((((255, 110, 30), 20, 40), ((255, 190, 70), 12, 28),
                                             ((255, 245, 200), 6, 14))):
                hh = h + fl * 6
                pygame.draw.polygon(surf, cor, [(tx - w // 2, ty - 6), (tx + w // 2, ty - 6),
                                                (tx + fl * 3, ty - 6 - hh)])
                pygame.draw.ellipse(surf, cor, (tx - w // 2, ty - 14, w, 16))
        for b in self.brasas:
            b[1] -= b[2]
            b[0] += math.sin(t * 0.03 + b[3]) * 0.4
            if b[1] < -10:
                b[0], b[1] = random.uniform(0, LARGURA), ALTURA + 10
            a = 0.5 + 0.5 * math.sin(t * 0.1 + b[3])
            cor = (255, int(120 + 80 * a), 60)
            pygame.draw.circle(surf, cor, (int(b[0]), int(b[1])), 1 + int(a * 1.6))
        dx = int(t * 0.4) % LARGURA
        surf.blit(self.neblina, (-dx, CHAO_Y - 80))


# ============================================================== lutador
def _sombra(surf, x, chao, largura, alpha=110):
    s = pygame.Surface((largura, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (10, 5, 12, alpha), (0, 0, largura, 22))
    surf.blit(s, (x - largura // 2, chao - 12))


def _membro(surf, pts, larg, cor, escuro, claro):
    pts = [(int(p[0]), int(p[1])) for p in pts]
    pygame.draw.lines(surf, escuro, False, pts, larg + 6)
    for p in pts:
        pygame.draw.circle(surf, escuro, p, (larg + 6) // 2)
    pygame.draw.lines(surf, cor, False, pts, larg)
    for p in pts:
        pygame.draw.circle(surf, cor, p, larg // 2)
    brilho = [(p[0] - 2, p[1] - 3) for p in pts]
    pygame.draw.lines(surf, claro, False, brilho, max(2, larg // 4))


def _punho(surf, p, r, cor, escuro, claro):
    p = (int(p[0]), int(p[1]))
    pygame.draw.circle(surf, escuro, p, r + 3)
    pygame.draw.circle(surf, cor, p, r)
    pygame.draw.circle(surf, claro, (p[0] - r // 3, p[1] - r // 3), max(2, r // 3))


def _ponto_alvo(f, hit, ox, oy):
    b = f.caixa_golpe(hit)
    tx = b.x + b.w if f.facing == 1 else b.x
    return tx + ox, b.centery + oy


def _progresso(f, hit):
    t = f.golpe_t
    if t < hit.start:
        return 0.1 + 0.25 * t / max(1, hit.start)
    if t <= hit.end:
        return 1.0
    return max(0.0, 1.0 - (t - hit.end) / 10)


def _hit_atual(g, t):
    for h in g.hits:
        if t <= h.end + 3:
            return h
    return g.hits[-1]


def _lanca(surf, a, b, brilho=False):
    pygame.draw.line(surf, (40, 25, 15), a, b, 10)
    pygame.draw.line(surf, (130, 85, 45), a, b, 6)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    ponta = (b[0] + math.cos(ang) * 30, b[1] + math.sin(ang) * 30)
    lado = (math.cos(ang + 1.57) * 10, math.sin(ang + 1.57) * 10)
    pts = [ponta, (b[0] + lado[0], b[1] + lado[1]), (b[0] - lado[0], b[1] - lado[1])]
    if brilho:
        glow(surf, (120, 60, 160), (int(b[0] + math.cos(ang) * 15), int(b[1] + math.sin(ang) * 15)), 45)
    pygame.draw.polygon(surf, (235, 235, 250), pts)
    pygame.draw.polygon(surf, (120, 120, 140), pts, 2)


def desenhar_lutador(surf, f, tempo, debug=False, ox=0, oy=0, vitoria=False):
    ch = f.char
    base = ch.cor
    flash = f.flash > 0 and f.flash % 2 == 0
    cor = (255, 255, 255) if flash else base
    escuro = contorno_de(base)
    claro = clarear(base, 0.5)
    sombra_corpo = escurecer(base, 0.72) if not flash else (220, 220, 220)
    x, y, d = int(f.x) + ox, int(f.y) + oy, f.facing
    chao = CHAO_Y + oy
    e = f.estado
    alt = max(0, chao - y)
    _sombra(surf, x, chao, max(50, 130 - alt // 3), max(40, 120 - alt // 3))

    # ---------------------------------------------------------- caido
    if e in ("knockdown", "ko") and alt < 25 and f.vy >= 0:
        cy = y - 22
        _membro(surf, [(x - d * 10, cy), (x + d * 55, cy + 6), (x + d * 95, cy + 14)], 15, cor, escuro, claro)
        _membro(surf, [(x - d * 10, cy + 4), (x + d * 50, cy + 14), (x + d * 92, cy + 20)], 15,
                sombra_corpo, escuro, claro)
        torso = pygame.Rect(0, 0, 105, 40)
        torso.center = (x - d * 50, cy)
        pygame.draw.rect(surf, escuro, torso.inflate(6, 6), border_radius=18)
        pygame.draw.rect(surf, cor, torso, border_radius=16)
        pygame.draw.circle(surf, escuro, (x - d * 122, cy - 4), 25)
        pygame.draw.circle(surf, cor, (x - d * 122, cy - 4), 22)
        _membro(surf, [(x - d * 85, cy - 10), (x - d * 60, cy - 40), (x - d * 30, cy - 30)], 12, cor, escuro, claro)
        if e == "ko":
            for i in range(3):
                a = tempo * 0.1 + i * 2.1
                pygame.draw.circle(surf, (255, 230, 90),
                                   (int(x - d * 122 + math.cos(a) * 30), int(cy - 40 + math.sin(a) * 8)), 4)
        return

    agach = f.agachado
    no_ar = alt > 2 or e == "jump"
    resp = math.sin(tempo * 0.09 + f.slot) * 2 if e in ("idle", "crouch") else 0
    quadril_y = y - (58 if agach else 98) + resp * 0.5
    ombro_y = y - (112 if agach else 162) + resp
    cabeca_y = y - (136 if agach else 188) + resp
    x_t = x - d * 10 if e in ("hitstun", "knockdown", "ko") else x + (d * 4 if e == "walk" else 0)

    # aura discreta da cor do personagem
    glow(surf, escurecer(base, 0.35 if sum(base) > 250 else 0.9), (x, y - 100), 115, 0.7)

    # rastro (dash / invulneravel a projetil)
    if e == "dash" or f.ignora_projeteis():
        for k in (3, 2, 1):
            fan = pygame.Surface((90, 210), pygame.SRCALPHA)
            pygame.draw.rect(fan, (*clarear(base, 0.3), 40 + 20 * (3 - k)), (5, 5, 80, 200), border_radius=34)
            surf.blit(fan, (x - 45 - f.vx * 2.0 * k, y - 210))

    g = f.golpe if e == "attack" else None
    hit = _hit_atual(g, f.golpe_t) if (g and g.hits) else None
    chute = hit is not None and hit.box[1] < 90 and not ch.arma
    especial = g is not None and g in (ch.golpes.get("especial1"), ch.golpes.get("especial2"))

    # ---------------------------------------------------------- pernas
    if agach:
        pernas = [[(x - 12, quadril_y), (x - 12 + d * 30, y - 28), (x - 10, y - 4)],
                  [(x + 12, quadril_y), (x + 12 - d * 4, y - 26), (x + 22 * d, y - 4)]]
    elif no_ar:
        pernas = [[(x - 10, quadril_y), (x - 10 + d * 28, quadril_y + 30), (x - 6, quadril_y + 66)],
                  [(x + 10, quadril_y), (x + 10 + d * 34, quadril_y + 20), (x + 16, quadril_y + 56)]]
    else:
        passo = math.sin(f.t * 0.3) * 16 if e in ("walk", "dash") else 0
        abre = 18 if e in ("idle", "blockstun") else 14
        pernas = [[(x - 10, quadril_y), (x - 14 - passo * 0.4 + d * 6, quadril_y + 50), (x - abre - passo, y - 4)],
                  [(x + 10, quadril_y), (x + 14 + passo * 0.4 + d * 6, quadril_y + 50), (x + abre + passo, y - 4)]]
    for i, perna in enumerate(pernas):
        if chute and i == (0 if d == -1 else 1):
            continue
        c = sombra_corpo if i == (1 if d == 1 else 0) else cor
        _membro(surf, perna, 17, c, escuro, claro)
        pe = perna[-1]
        pygame.draw.ellipse(surf, escuro, (pe[0] - 13 + d * 4, pe[1] - 6, 30, 12))

    # ---------------------------------------------------------- braco de tras (atras do corpo)
    ombro = (x_t + d * 6, ombro_y + 8)
    ombro_tras = (x_t - d * 12, ombro_y + 8)
    if not f.defendendo():
        bt = [ombro_tras, (ombro_tras[0] + d * 6, ombro_tras[1] + 32), (ombro_tras[0] + d * 26, ombro_tras[1] + 10)]
        if e == "hitstun":
            bt = [ombro_tras, (ombro_tras[0] - d * 28, ombro_tras[1] - 6), (ombro_tras[0] - d * 40, ombro_tras[1] - 30)]
        if vitoria:
            bt = [ombro_tras, (ombro_tras[0] - d * 6, ombro_tras[1] + 30), (ombro_tras[0] - d * 2, ombro_tras[1] + 56)]
        _membro(surf, bt, 13, sombra_corpo, escuro, claro)
        _punho(surf, bt[-1], 9, sombra_corpo, escuro, claro)

    # ---------------------------------------------------------- tronco
    ombro_l = 30
    cintura_l = 19
    torso = [(x_t - ombro_l, ombro_y), (x_t + ombro_l, ombro_y),
             (x_t + cintura_l, quadril_y + 4), (x_t - cintura_l, quadril_y + 4)]
    pygame.draw.polygon(surf, escuro, [(px + (3 if px > x_t else -3), py) for px, py in torso], 0)
    pygame.draw.polygon(surf, escuro, torso, 8)
    pygame.draw.polygon(surf, cor, torso)
    lado = [(x_t - d * ombro_l, ombro_y), (x_t - d * 4, ombro_y), (x_t - d * 4, quadril_y + 4),
            (x_t - d * cintura_l, quadril_y + 4)]
    pygame.draw.polygon(surf, sombra_corpo, lado)                                       # sombreamento
    pygame.draw.line(surf, claro, (x_t + d * 6, ombro_y + 8), (x_t + d * 18, ombro_y + 8), 3)
    pygame.draw.line(surf, escurecer(cor, 0.8), (x_t, ombro_y + 22), (x_t, quadril_y - 4), 2)
    for k in (0, 1):
        yy = ombro_y + 34 + k * 16
        pygame.draw.line(surf, escurecer(cor, 0.8), (x_t - 10, yy), (x_t + 10, yy), 2)
    faixa = (min(255, base[0] // 3 + 20), min(255, base[1] // 3 + 10), min(255, base[2] // 3 + 20))
    pygame.draw.rect(surf, faixa, (x_t - cintura_l - 2, quadril_y - 6, (cintura_l + 2) * 2, 12), border_radius=4)
    pygame.draw.polygon(surf, faixa, [(x_t - d * 10, quadril_y), (x_t - d * 34, quadril_y + 22 + resp * 2),
                                      (x_t - d * 22, quadril_y + 26 + resp * 2)])

    # ---------------------------------------------------------- cabeca
    cab = (int(x_t + (d * 3 if not agach else d * 6)), int(cabeca_y))
    pygame.draw.rect(surf, escuro, (cab[0] - 8, cab[1] + 12, 16, 16))
    pygame.draw.circle(surf, escuro, cab, 25)
    pygame.draw.circle(surf, cor, cab, 22)
    pygame.draw.circle(surf, sombra_corpo, (cab[0] - d * 6, cab[1] + 3), 16, draw_top_left=d == 1,
                       draw_bottom_left=d == 1, draw_top_right=d == -1, draw_bottom_right=d == -1)
    pygame.draw.circle(surf, claro, (cab[0] + d * 7, cab[1] - 10), 5)
    olho_cor = (255, 255, 255) if sum(base) > 250 else (200, 140, 255)
    olho = pygame.Rect(0, 0, 15, 5)
    olho.center = (cab[0] + d * 10, cab[1] - 2)
    glow(surf, escurecer(olho_cor, 0.35), olho.center, 18)
    pygame.draw.rect(surf, (15, 10, 20), olho.inflate(4, 4), border_radius=3)
    pygame.draw.rect(surf, olho_cor, olho, border_radius=3)

    # armadura (Colosso)
    if f.tem_armadura():
        pulso = 0.6 + 0.4 * math.sin(tempo * 0.7)
        glow(surf, (int(160 * pulso), int(90 * pulso), 10), (x_t, int(ombro_y + 50)), 120, 1.0)
        pygame.draw.polygon(surf, (255, 190, 60), torso, 3)

    # ---------------------------------------------------------- braco da frente / golpe
    if hit is not None:
        p = _progresso(f, hit)
        alvo = _ponto_alvo(f, hit, ox, oy)
        origem = (x + d * 8, quadril_y + 6) if chute else ombro
        fim = (origem[0] + (alvo[0] - origem[0]) * p, origem[1] + (alvo[1] - origem[1]) * p)
        meio = ((origem[0] + fim[0]) / 2 - d * 4, (origem[1] + fim[1]) / 2 + (8 if chute else 6))
        ativo = hit.start <= f.golpe_t <= hit.end
        if ativo:                                              # brilho do impacto
            glow(surf, escurecer(clarear(base, 0.6), 0.5), (int(fim[0]), int(fim[1])), 50 if especial else 34)
        if ch.arma:
            cabo = (ombro[0] - d * 40 * p, ombro[1] + 30 - 20 * p)
            _membro(surf, [ombro, meio, fim], 13, cor, escuro, claro)
            _lanca(surf, cabo, (fim[0] + d * 30, fim[1]), brilho=ativo)
            _punho(surf, fim, 10, cor, escuro, claro)
        else:
            _membro(surf, [origem, meio, fim], 17 if chute else 15, cor, escuro, claro)
            if chute:
                pygame.draw.ellipse(surf, escuro, (fim[0] - 15, fim[1] - 8, 30, 16))
            else:
                _punho(surf, fim, 13 if especial else 11, cor, escuro, claro)
            if hit.grab:
                mao2 = (fim[0] - d * 4, fim[1] + 24)
                _membro(surf, [(ombro[0] - d * 6, ombro[1] + 10), mao2], 13, sombra_corpo, escuro, claro)
                _punho(surf, mao2, 10, sombra_corpo, escuro, claro)
        if especial and ativo:
            glow(surf, clarear(base, 0.3), (int(fim[0]), int(fim[1])), 60, 0.8)
    elif g is not None:                                        # tiro / mina / detonar
        frame = g.spawn["frame"] if g.spawn else 10
        p = min(1.0, f.golpe_t / max(1, frame))
        if g.pose == "mina":
            fim = (x + d * (30 + 35 * p), y - 18)
        elif agach:
            fim = (x + d * (30 + 45 * p), y - 62)
        else:
            alt_tiro = (g.spawn.get("oy", 100) + 20) if g.spawn else 120
            fim = (x + d * (30 + 50 * p), y - min(alt_tiro, 150))
        meio = ((ombro[0] + fim[0]) / 2, (ombro[1] + fim[1]) / 2 + 8)
        _membro(surf, [ombro, meio, fim], 15, cor, escuro, claro)
        _punho(surf, fim, 12, cor, escuro, claro)
        if frame - 8 <= f.golpe_t <= frame + 6:
            k = 1 - abs(f.golpe_t - frame) / 8
            glow(surf, clarear(base, 0.4), (int(fim[0] + d * 14), int(fim[1])), int(30 + 40 * k), 1.0)
            pygame.draw.circle(surf, (255, 255, 240), (int(fim[0] + d * 14), int(fim[1])), int(6 + 8 * k))
    elif f.defendendo():
        for k, c in ((0, sombra_corpo), (1, cor)):
            cotovelo = (ombro[0] + d * (22 + k * 4), ombro[1] + 26 - k * 4)
            mao = (ombro[0] + d * (26 + k * 6), ombro[1] - 18 - k * 4)
            _membro(surf, [(ombro[0] - d * 8 * (1 - k), ombro[1]), cotovelo, mao], 14, c, escuro, claro)
            _punho(surf, mao, 10, c, escuro, claro)
        escudo = pygame.Surface((120, 190), pygame.SRCALPHA)
        a = 60 + int(30 * math.sin(tempo * 0.4))
        pygame.draw.arc(escudo, (120, 200, 255, a + 60), (0, 0, 120, 190),
                        -1.3 if d == 1 else 1.85, 1.3 if d == 1 else 4.45, 5)
        surf.blit(escudo, (x - 60 + d * 18, ombro_y - 40))
    else:
        bal = math.sin(tempo * 0.12) * 3
        if vitoria:
            braco = [ombro, (ombro[0] + d * 10, ombro[1] - 40), (ombro[0] + d * 4, ombro[1] - 82)]
        elif e == "hitstun":
            braco = [ombro, (ombro[0] - d * 20, ombro[1] - 20), (ombro[0] - d * 18, ombro[1] - 48)]
        elif no_ar:
            braco = [ombro, (ombro[0] + d * 26, ombro[1] - 4), (ombro[0] + d * 30, ombro[1] - 32)]
        else:
            braco = [ombro, (ombro[0] + d * 22, ombro[1] + 30), (ombro[0] + d * 40, ombro[1] + 2 + bal)]
        if ch.arma and not vitoria:
            _lanca(surf, (x_t - d * 40, ombro_y + 80), (x_t + d * 66, ombro_y - 60))
        _membro(surf, braco, 14, cor, escuro, claro)
        _punho(surf, braco[-1], 11, cor, escuro, claro)
        if vitoria:
            glow(surf, clarear(base, 0.3), (int(braco[-1][0]), int(braco[-1][1])), 45)

    if debug:
        hb = f.hurtbox()
        if hb:
            pygame.draw.rect(surf, (0, 255, 120), (hb.x + ox, hb.y + oy, hb.w, hb.h), 2)
        for _, h in f.hits_ativos():
            b = f.caixa_golpe(h)
            pygame.draw.rect(surf, (255, 40, 40), (b.x + ox, b.y + oy, b.w, b.h), 3)


# ============================================================== objetos
def desenhar_objetos(surf, combate, tempo):
    for m in combate.minas:
        restante = m.pavio - m.t
        pisca = m.armada and (tempo // max(3, restante // 12)) % 2 == 0
        cor = (255, 50, 70) if pisca else ((190, 60, 230) if m.armada else (110, 90, 130))
        glow(surf, escurecer(cor, 0.5), (int(m.x), CHAO_Y - 10), 40 if m.armada else 20)
        pygame.draw.ellipse(surf, (25, 20, 30), (m.x - 26, CHAO_Y - 16, 52, 18))
        pygame.draw.ellipse(surf, cor, (m.x - 17, CHAO_Y - 14, 34, 11))
        pygame.draw.circle(surf, (255, 255, 255) if pisca else clarear(cor), (int(m.x), CHAO_Y - 17), 4)
        if m.armada:
            raio = int(m.raio * (0.5 + 0.5 * ((tempo % 40) / 40)))
            anel = pygame.Surface((raio * 2, raio), pygame.SRCALPHA)
            pygame.draw.ellipse(anel, (*cor, 60), (0, 0, raio * 2, raio), 2)
            surf.blit(anel, (m.x - raio, CHAO_Y - raio // 2 - 6))

    for p in combate.projeteis:
        b = p.box()
        c = (int(b.centerx), int(b.centery))
        glow(surf, escurecer(p.cor, 0.6), c, int(b.h + 40), 1.0)
        for k in range(1, 6):                                     # cauda
            r = max(2, int(b.h / 2 - k * 3))
            tx = int(c[0] - p.dir * k * 14)
            pygame.draw.circle(surf, misturar(p.cor, (60, 20, 40), k / 6), (tx, c[1] + int(math.sin(p.t * 0.5 + k) * 3)), r)
        if p.forma == "raio":
            pygame.draw.ellipse(surf, p.cor, (b.x - 6, b.y - 2, b.w + 12, b.h + 4))
            pygame.draw.ellipse(surf, (255, 255, 235), (b.x + 6, b.y + 6, b.w - 12, b.h - 12))
        else:
            pulso = 3 * math.sin(p.t * 0.6)
            pygame.draw.circle(surf, p.cor, c, int(b.h / 2 + 4 + pulso))
            pygame.draw.circle(surf, (255, 250, 225), c, int(b.h / 3.2))

    for ex in combate.explosoes:
        k = ex.t / ex.DURACAO
        r = int(ex.raio * (0.5 + 0.9 * k))
        c = (int(ex.cx), CHAO_Y - 40)
        glow(surf, (int(255 * (1 - k)), int(130 * (1 - k)), int(30 * (1 - k))), c, r * 2, 1.0)
        anel = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(anel, (255, 230, 160, int(220 * (1 - k))), (r + 4, r + 4), r, max(2, int(10 * (1 - k))))
        surf.blit(anel, (c[0] - r - 4, c[1] - r - 4))


def desenhar_efeitos(surf, combate):
    cores = {"hit": (255, 240, 140), "bloqueio": (130, 200, 255),
             "armadura": (255, 170, 50), "agarrao": (255, 90, 90), "explosao": (255, 160, 70)}
    for ef in combate.efeitos:
        if ef["tipo"] == "explosao":
            continue
        k = ef["t"] / 20
        cor = cores.get(ef["tipo"], (255, 255, 255))
        if ef["t"] < 6:
            glow(surf, escurecer(cor, 0.8), (int(ef["x"]), int(ef["y"])), 70 - ef["t"] * 6, 1.0)
        r = 14 + 46 * k
        for i in range(10):
            a = i * math.pi / 5 + 0.3
            comp = 0.35 if i % 2 else 0.6
            p1 = (ef["x"] + math.cos(a) * r * comp, ef["y"] + math.sin(a) * r * comp)
            p2 = (ef["x"] + math.cos(a) * r, ef["y"] + math.sin(a) * r)
            pygame.draw.line(surf, cor, p1, p2, max(1, int(6 * (1 - k))))
        if ef["tipo"] == "bloqueio" and ef["t"] < 12:
            anel = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(anel, (130, 200, 255, int(200 * (1 - k))), (60, 60), int(20 + 35 * k), 4)
            surf.blit(anel, (ef["x"] - 60, ef["y"] - 60))


# ============================================================== HUD
def _cabeca_retrato(surf, ch, centro, raio):
    if desenhar_retrato(surf, ch, centro, raio):
        return
    c, esc = ch.cor, contorno_de(ch.cor)
    pygame.draw.circle(surf, (15, 10, 20), centro, raio + 4)
    pygame.draw.circle(surf, esc, centro, raio + 2)
    fundo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    pygame.draw.circle(fundo, (*escurecer(c, 0.35), 255), (raio, raio), raio)
    surf.blit(fundo, (centro[0] - raio, centro[1] - raio))
    pygame.draw.circle(surf, c, (centro[0], centro[1] + 4), int(raio * 0.62))
    pygame.draw.circle(surf, clarear(c, 0.5), (centro[0] + 6, centro[1] - 6), int(raio * 0.16))
    olho = pygame.Rect(0, 0, int(raio * 0.6), 5)
    olho.center = (centro[0] + 5, centro[1] + 2)
    pygame.draw.rect(surf, (255, 255, 255) if sum(c) > 250 else (200, 140, 255), olho, border_radius=2)


_hud_cache = {}


def _barra(w, h, topo, base):
    chave = (w, h, topo, base)
    s = _hud_cache.get(chave)
    if s is None:
        s = pygame.Surface((w, h))
        gradiente_v(s, (0, 0, w, h), topo, base)
        if len(_hud_cache) > 200:
            _hud_cache.clear()
        _hud_cache[chave] = s
    return s


def desenhar_hud(surf, partida, fontes, tempo):
    f1, f2 = partida.f1, partida.f2
    largura, alto, topo = 470, 26, 34
    placa = _hud_cache.get("placa")
    if placa is None:
        placa = pygame.Surface((LARGURA, 130), pygame.SRCALPHA)
        for i in range(130):
            pygame.draw.line(placa, (0, 0, 0, int(170 * (1 - i / 130))), (0, i), (LARGURA, i))
        _hud_cache["placa"] = placa
    surf.blit(placa, (0, 0))

    for f, lado in ((f1, -1), (f2, 1)):
        x0 = 110 if lado == -1 else LARGURA - 110 - largura
        retrato = (58, topo + 22) if lado == -1 else (LARGURA - 58, topo + 22)
        _cabeca_retrato(surf, f.char, retrato, 36)
        incl = 14
        if lado == -1:
            moldura = [(x0 - 6, topo - 6), (x0 + largura + 6 + incl, topo - 6),
                       (x0 + largura + 6, topo + alto + 6), (x0 - 6, topo + alto + 6)]
        else:
            moldura = [(x0 - 6 - incl, topo - 6), (x0 + largura + 6, topo - 6),
                       (x0 + largura + 6, topo + alto + 6), (x0 - 6, topo + alto + 6)]
        pygame.draw.polygon(surf, (20, 14, 22), moldura)
        pygame.draw.polygon(surf, (150, 120, 90), moldura, 2)
        pygame.draw.rect(surf, (60, 12, 18), (x0, topo, largura, alto))

        frac_v = max(0.0, f.hp_visual) / f.char.max_hp
        frac = max(0.0, f.hp) / f.char.max_hp
        baixa = frac < 0.25
        for fr, topo_cor, base_cor in ((frac_v, (255, 90, 70), (170, 30, 30)),
                                       (frac, (255, 235, 110), (235, 150, 30))):
            w = int(largura * fr)
            if w <= 0:
                continue
            if baixa and fr is frac:
                pulso = round((0.5 + 0.5 * math.sin(tempo * 0.3)) * 8) / 8
                topo_cor = misturar((255, 120, 90), (255, 235, 110), pulso)
                base_cor = misturar((200, 30, 30), (235, 150, 30), pulso)
            rx = x0 + largura - w if lado == -1 else x0
            barra = _barra(largura, alto, topo_cor, base_cor)
            surf.blit(barra, (rx, topo), (0, 0, w, alto))
        pygame.draw.line(surf, (255, 255, 255), (x0 + 2, topo + 3), (x0 + largura - 2, topo + 3), 1)

        nome_x = x0 if lado == -1 else x0 + largura
        texto(surf, f.char.nome, fontes["media"], (255, 255, 255),
              (nome_x, topo + alto + 22), "midleft" if lado == -1 else "midright")
        for i in range(2):                                        # vitorias (losangos)
            cx = (x0 + largura - 14 - i * 30) if lado == -1 else (x0 + 14 + i * 30)
            cy = topo + alto + 22
            pts = [(cx, cy - 11), (cx + 11, cy), (cx, cy + 11), (cx - 11, cy)]
            pygame.draw.polygon(surf, (20, 14, 22), pts)
            if f.vitorias > i:
                glow(surf, (120, 90, 10), (cx, cy), 26)
                pygame.draw.polygon(surf, (255, 210, 60), [(px + (cx - px) * 0.25, py + (cy - py) * 0.25) for px, py in pts])
            pygame.draw.polygon(surf, (150, 120, 90), pts, 2)

        # recarga dos especiais (2 icones) + barra de guarda
        teclas = ("R", "T") if f.slot == 1 else ("I", "O")
        if partida.cpus.get(f.slot) is not None:
            teclas = ("1", "2")
        for i, nome in enumerate(("especial1", "especial2")):
            cx = (x0 + 18 + i * 40) if lado == -1 else (x0 + largura - 18 - i * 40)
            cy = topo + alto + 58
            _icone_cd(surf, (cx, cy), f.cd_frac(nome), cor_texto(f.char.cor), teclas[i], fontes, tempo)
        if f.guarda > 1:
            gw = int(150 * min(1.0, f.guarda / GUARDA_MAX))
            gx = (x0 + 100) if lado == -1 else (x0 + largura - 100 - 150)
            gy = topo + alto + 54
            pygame.draw.rect(surf, (20, 14, 22), (gx - 2, gy - 2, 154, 10), border_radius=4)
            cor_g = (120, 200, 255) if f.guarda < GUARDA_MAX * 0.7 else ((255, 90, 70) if (tempo // 6) % 2 else (255, 200, 90))
            rx = gx if lado == -1 else gx + 150 - gw
            pygame.draw.rect(surf, cor_g, (rx, gy, gw, 6), border_radius=3)
            texto(surf, "GUARDA", fontes["mini"], cor_g, ((gx + 76), gy + 15), contorno=1)

        cpu = partida.cpus.get(f.slot)
        if cpu is not None:                                       # medidor da CPU no HUD
            from game.ai import NIVEIS
            mx = (x0 + 150) if lado == 1 else (x0 + largura - 150)
            rr = medidor_dificuldade(surf, (mx, topo + alto + 14), cpu.nivel, fontes, 0.42, nome=False)
            texto(surf, "CPU " + NIVEIS[cpu.nivel]["nome"], fontes["mini"], CORES_NIVEL[cpu.nivel],
                  (mx, topo + alto + 38), contorno=1)
        if f.combo >= 2 and f.estado in ("hitstun", "knockdown", "ko"):
            cx = 250 if lado == 1 else LARGURA - 250
            texto(surf, f"{f.combo}", fontes["titulo"], (255, 225, 80), (cx, 230), escala=0.9, contorno=3)
            texto(surf, "HITS", fontes["media"], (255, 255, 255), (cx, 290), contorno=2)

    # relogio
    seg = partida.segundos
    cor = (255, 80, 70) if seg <= 10 and partida.fase == "luta" and (tempo // 15) % 2 == 0 else (255, 255, 255)
    cx = LARGURA // 2
    pts = [(cx - 46, topo - 12), (cx + 46, topo - 12), (cx + 56, topo + 18), (cx + 40, topo + 58),
           (cx - 40, topo + 58), (cx - 56, topo + 18)]
    pygame.draw.polygon(surf, (20, 14, 22), pts)
    pygame.draw.polygon(surf, (190, 150, 100), pts, 3)
    texto(surf, seg, fontes["grande"], cor, (cx, topo + 22))


# modelo profissional (esqueleto + IK) substitui o desenho antigo
from game.modelo import desenhar_lutador  # noqa: E402,F811
# sprites (imagens) para quem tiver pasta em assets/sprites; os outros usam o manequim
from game.sprites import desenhar_lutador, desenhar_retrato  # noqa: E402,F811


# ============================================================== icone de recarga
def _icone_cd(surf, c, frac, cor, rotulo, fontes, tempo):
    """Circulo que se enche enquanto o especial recarrega; brilha quando pronto."""
    r = 15
    pygame.draw.circle(surf, (14, 10, 18), c, r + 3)
    if frac <= 0:
        pulso = 0.7 + 0.3 * math.sin(tempo * 0.15)
        glow(surf, escurecer(cor, 0.45 * pulso), c, 30, 0.9)
        pygame.draw.circle(surf, cor, c, r)
        pygame.draw.circle(surf, clarear(cor, 0.6), c, r, 2)
        texto(surf, rotulo, fontes["mini"], (20, 14, 22), c, contorno=0)
        return
    pygame.draw.circle(surf, (50, 42, 56), c, r)
    pronto = 1.0 - frac                                     # parte ja recarregada
    if pronto > 0.01:
        pts = [c]
        passos = max(2, int(36 * pronto))
        for i in range(passos + 1):
            a = -math.pi / 2 + math.tau * pronto * i / passos
            pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        pygame.draw.polygon(surf, escurecer(cor, 0.75), pts)
    pygame.draw.circle(surf, (110, 100, 120), c, r, 2)
    texto(surf, rotulo, fontes["mini"], (230, 225, 235), c, contorno=1)


# ============================================================== medidor de dificuldade
CORES_NIVEL = {1: (70, 210, 110), 2: (170, 220, 70), 3: (250, 200, 50), 4: (250, 120, 45), 5: (220, 50, 70)}


def medidor_dificuldade(surf, centro, nivel, fontes, escala=1.0, nome=True, tempo=0):
    """5 barras crescentes (verde -> vermelho). Retorna o retangulo ocupado."""
    from game.ai import NIVEIS
    larg_barra, gap = int(26 * escala), int(8 * escala)
    total = 5 * larg_barra + 4 * gap
    x0 = centro[0] - total // 2
    base_y = centro[1] + int(24 * escala)
    cor_n = CORES_NIVEL[nivel]
    for i in range(5):
        h = int((14 + i * 9) * escala)
        r = pygame.Rect(x0 + i * (larg_barra + gap), base_y - h, larg_barra, h)
        aceso = i < nivel
        pygame.draw.rect(surf, (12, 8, 14), r.inflate(6, 6), border_radius=5)
        if aceso:
            if i == nivel - 1:
                glow(surf, escurecer(cor_n, 0.55), r.center, int(34 * escala), 0.9)
            cor = CORES_NIVEL[i + 1]
            pygame.draw.rect(surf, cor, r, border_radius=4)
            pygame.draw.rect(surf, clarear(cor, 0.5), (r.x + 3, r.y + 3, max(2, r.w // 4), r.h - 6), border_radius=2)
        else:
            pygame.draw.rect(surf, (48, 40, 54), r, border_radius=4)
    if nome:
        fonte = fontes["media"] if escala >= 1 else fontes["pequena"]
        texto(surf, NIVEIS[nivel]["nome"], fonte, cor_n, (centro[0], base_y + int(26 * escala)))
    return pygame.Rect(x0, base_y - int(50 * escala), total, int(50 * escala))
