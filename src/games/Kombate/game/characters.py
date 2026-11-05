"""
characters.py - DADOS dos personagens (sem logica de jogo).
=================================================================
Cada golpe e um Move com uma lista de Hit (hitboxes ativas por frame).
Para criar/ajustar um personagem, mexa so aqui.

Convencao da caixa de um Hit: box = (ox, oy, largura, altura)
  ox  -> distancia do CENTRO do lutador ate o inicio da caixa (na direcao que ele olha)
  oy  -> altura da BASE da caixa acima dos pes (negativo = abaixo dos pes)
Corpo do manequim: 70 de largura, 190 de altura em pe, 115 agachado.
Um golpe "high" com oy >= 115 passa por cima de quem esta agachado.
"""
import math
from dataclasses import dataclass, field

from settings import VELOCIDADE_GOLPES, VELOCIDADE_ANDAR, GRAVIDADE


@dataclass
class Hit:
    start: int                  # primeiro frame ativo do golpe
    end: int                    # ultimo frame ativo
    box: tuple                  # (ox, oy, w, h)
    dano: float
    altura: str = "mid"         # high | mid | low | overhead
    hitstun: int = 16
    blockstun: int = 10
    knockback: float = 6.0
    launch: float = 0.0         # velocidade vertical ao acertar (lanca para cima)
    knockdown: bool = False
    grab: bool = False          # agarrao: nao pode ser bloqueado


@dataclass
class Move:
    nome: str
    total: int                          # duracao total (frames)
    hits: list = field(default_factory=list)
    whiff_extra: int = 0                # recuperacao extra se ERRAR
    armadura: tuple = None              # (ini, fim) hiper-armadura
    invuln: tuple = None                # (ini, fim) invulneravel a tudo
    proj_invuln: tuple = None           # (ini, fim) atravessa projeteis
    movimento: list = None              # [(ini, fim, vx)] deslocamento
    spawn: dict = None                  # cria projetil / mina / detonacao
    agachado: bool = False
    aereo: bool = False
    pose: str = "golpe"                 # dica para o desenho: golpe | tiro | agarrao | mina


@dataclass
class Character:
    key: str
    nome: str
    arquetipo: str
    descricao: str
    cor: tuple
    max_hp: int
    vel_andar: float
    pulo: float
    vel_pulo_x: float
    dash_vel: float
    dash_frames: int
    golpes: dict
    dash_atravessa: bool = False        # dash ignora projeteis
    max_projeteis: int = 1
    max_minas: int = 0
    antiaereo: str = None               # botao do golpe antiaereo (para a IA)
    cooldown: dict = field(default_factory=dict)   # especial -> segundos de recarga
    arma: bool = False                  # desenha uma lanca (Roxo)
    ia: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Golpes basicos (todos tem), com modificadores por personagem
# ---------------------------------------------------------------------------
def golpes_basicos(dano=1.0, alcance=0, lento=0, whiff=0):
    s = lento
    return {
        "soco": Move("Soco", 18 + s * 2, [
            Hit(6 + s, 8 + s, (15, 125, 55 + alcance, 24), 5 * dano, "high",
                hitstun=15, blockstun=9, knockback=4)], whiff_extra=whiff),
        "chute": Move("Chute", 26 + s * 2, [
            Hit(9 + s, 12 + s, (15, 65, 70 + alcance, 40), 7 * dano, "mid",
                hitstun=17, blockstun=11, knockback=6)], whiff_extra=whiff),
        "soco_baixo": Move("Soco Agachado", 17 + s * 2, [
            Hit(6 + s, 8 + s, (15, 55, 50 + alcance, 24), 4 * dano, "mid",
                hitstun=14, blockstun=8, knockback=3)], agachado=True, whiff_extra=whiff),
        "rasteira": Move("Rasteira", 34 + s * 2, [
            Hit(11 + s, 14 + s, (10, 0, 80 + alcance, 28), 7 * dano, "low",
                knockdown=True, knockback=5, blockstun=12)], agachado=True, whiff_extra=whiff),
        "arremesso": Move("Arremesso", 30, [
            Hit(4, 6, (15, 40, 70, 130), 11, "mid", grab=True, knockdown=True, knockback=11)],
            whiff_extra=12, pose="agarrao"),
        "aereo": Move("Chute Aereo", 30, [
            Hit(5, 22, (5, -15, 65 + alcance // 2, 55), 7 * dano, "overhead",
                hitstun=18, blockstun=12, knockback=4)], aereo=True),
    }


def projetil(frame, vel, dano, altura, oy, w, h, cor, forma="bola"):
    return {"tipo": "projetil", "frame": frame, "vel": vel, "dano": dano,
            "altura": altura, "oy": oy, "w": w, "h": h, "cor": cor, "forma": forma}


# ---------------------------------------------------------------------------
# 1) VERMELHO - O Balanceado (Shoto)
# ---------------------------------------------------------------------------
def criar_vermelho():
    g = golpes_basicos(dano=1.3)
    g["especial1"] = Move("Bola de Energia", 40, [], whiff_extra=0, pose="tiro",
                          spawn=projetil(13, 9, 9, "mid", 100, 44, 36, (255, 120, 60)))
    g["especial2"] = Move("Gancho Ascendente", 46, [
        Hit(4, 10, (5, 70, 65, 160), 14, "mid", launch=-17, knockdown=True, knockback=4)],
        invuln=(1, 6), movimento=[(3, 10, 3)], whiff_extra=14)
    # alcance ajustado a arte do sprite (assets/sprites/rubro)
    g["soco"].hits[0].box = (15, 145, 100, 34)
    g["chute"].hits[0].box = (20, 150, 130, 50)
    g["chute"].hits[0].altura = "high"            # chute alto: passa por cima de quem agacha
    g["rasteira"].hits[0].box = (10, 0, 125, 40)
    return Character("vermelho", "RUBRO", "O Balanceado",
                     "Projetil reto e gancho antiaereo.",
                     (205, 45, 45), 1080, 4.2, -18.5, 5.0, 11, 10, g,
                     antiaereo="especial2",
                     ia={"dist": 100, "recua": 0.30, "tiro": 0.015})


# ---------------------------------------------------------------------------
# 2) AZUL - O Grappler
# ---------------------------------------------------------------------------
def criar_azul():
    g = golpes_basicos(dano=0.95, lento=2)
    g["especial1"] = Move("Agarrao Esmagador", 40, [
        Hit(6, 8, (15, 30, 70, 140), 16, "mid", grab=True, knockdown=True, knockback=9)],
        whiff_extra=18, pose="agarrao")
    g["especial2"] = Move("Punho Blindado", 50, [
        Hit(22, 26, (15, 95, 95, 50), 14, "mid", hitstun=24, blockstun=16, knockback=14)],
        armadura=(1, 26), movimento=[(1, 22, 1.6)], whiff_extra=8)
    return Character("azul", "COLOSSO", "O Grappler",
                     "Lento, muita vida. Agarrao e soco blindado.",
                     (45, 90, 215), 1020, 2.8, -16.0, 3.8, 8, 10, g,
                     ia={"dist": 85, "recua": 0.10, "tiro": 0.01})


# ---------------------------------------------------------------------------
# 3) AMARELO - O Zoner
# ---------------------------------------------------------------------------
def criar_amarelo():
    g = golpes_basicos(dano=1.1)
    g["especial1"] = Move("Disparo Alto", 30, [], pose="tiro",
                          spawn=projetil(9, 13, 15, "high", 125, 40, 24, (255, 220, 60), "raio"))
    g["especial2"] = Move("Disparo Rasteiro", 32, [], pose="tiro", agachado=True,
                          spawn=projetil(10, 9, 15, "low", 2, 46, 26, (255, 170, 40), "raio"))
    return Character("amarelo", "FAISCA", "O Zoner",
                     "Projeteis altos e baixos. Corpo a corpo fraco.",
                     (230, 200, 40), 1180, 4.1, -18.0, 4.6, 10, 10, g,
                     max_projeteis=3,
                     ia={"dist": 360, "recua": 0.55, "tiro": 0.035})


# ---------------------------------------------------------------------------
# 4) VERDE - O Rushdown
# ---------------------------------------------------------------------------
def criar_verde():
    g = golpes_basicos(dano=0.7)
    g["especial1"] = Move("Investida Fantasma", 28, [
        Hit(8, 18, (10, 70, 60, 60), 6, "mid", hitstun=18, knockback=5)],
        proj_invuln=(1, 20), movimento=[(1, 18, 17)], whiff_extra=8)
    rajada = [Hit(5 + i * 6, 6 + i * 6, (15, 90, 60, 40), 3.5, "mid",
                  hitstun=14, blockstun=8, knockback=1.5) for i in range(4)]
    rajada.append(Hit(31, 33, (15, 80, 70, 50), 6, "mid", knockdown=True, knockback=10))
    g["especial2"] = Move("Rajada Relampago", 46, rajada,
                          movimento=[(1, 30, 1.5)], whiff_extra=10)
    return Character("verde", "VULTO", "O Rushdown",
                     "Muito rapido. Dash atravessa projeteis.",
                     (40, 185, 80), 780, 5.4, -19.0, 6.0, 16, 12, g,
                     dash_atravessa=True,
                     ia={"dist": 90, "recua": 0.25, "tiro": 0.02})


# ---------------------------------------------------------------------------
# 5) ROXO - O Mid-Range (arma longa)
# ---------------------------------------------------------------------------
def criar_roxo():
    g = golpes_basicos(dano=0.9, alcance=45, whiff=10)
    g["especial1"] = Move("Estocada Longa", 52, [
        Hit(16, 20, (20, 105, 230, 26), 13, "mid", knockback=10, hitstun=20)],
        whiff_extra=26)
    g["especial2"] = Move("Varredura de Lanca", 54, [
        Hit(15, 19, (20, 0, 210, 32), 11, "low", knockdown=True, knockback=6)],
        agachado=True, whiff_extra=26)
    return Character("roxo", "LANCEIRO", "O Mid-Range",
                     "Longo alcance, mas pune muito se errar.",
                     (140, 60, 200), 920, 3.6, -17.5, 4.5, 10, 10, g,
                     arma=True,
                     ia={"dist": 200, "recua": 0.40, "tiro": 0.02})


# ---------------------------------------------------------------------------
# 6) PRETO - O Trapper (minas)
# ---------------------------------------------------------------------------
def criar_preto():
    g = golpes_basicos(dano=1.1)
    g["especial1"] = Move("Plantar Mina", 34, [], pose="mina", agachado=True,
                          spawn={"tipo": "mina", "frame": 14, "dist": 150,
                                 "arma": 18, "pavio": 220, "dano": 24, "raio": 80})
    g["especial2"] = Move("Detonar", 26, [], pose="tiro",
                          spawn={"tipo": "detonar", "frame": 8})
    return Character("preto", "SOMBRA", "O Trapper",
                     "Planta minas que explodem no tempo ou no contato.",
                     (55, 55, 65), 1000, 3.9, -18.0, 4.6, 12, 10, g,
                     max_minas=3,
                     ia={"dist": 200, "recua": 0.30, "tiro": 0.025})


# ---------------------------------------------------------------------------
# Ritmo do jogo: acelera TODOS os golpes e movimentos de uma vez so
# (os valores acima foram escritos para um ritmo mais lento)
# ---------------------------------------------------------------------------
def _acelerar(ch, k=VELOCIDADE_GOLPES, kv=VELOCIDADE_ANDAR):
    fr = lambda v: max(1, int(round(v * k)))
    for g in ch.golpes.values():
        g.total = fr(g.total)
        g.whiff_extra = int(round(g.whiff_extra * k))
        for nome in ("armadura", "invuln", "proj_invuln"):
            j = getattr(g, nome)
            if j:
                setattr(g, nome, (fr(j[0]), fr(j[1])))
        if g.movimento:
            g.movimento = [(fr(a), fr(b), v / k) for a, b, v in g.movimento]
        if g.spawn:
            g.spawn = dict(g.spawn)
            if "frame" in g.spawn:
                g.spawn["frame"] = fr(g.spawn["frame"])
            if "vel" in g.spawn:
                g.spawn["vel"] *= 1.3
        for h in g.hits:
            h.start = fr(h.start)
            h.end = max(h.start, fr(h.end))
            h.hitstun = fr(h.hitstun)
            h.blockstun = fr(h.blockstun)
    ch.vel_andar *= kv
    ch.vel_pulo_x *= 1.3
    ch.dash_vel *= 1.25
    ch.pulo *= math.sqrt(GRAVIDADE / 0.95)       # mesma altura, pulo mais rapido
    return ch


# ---------------------------------------------------------------------------
# Alcance ajustado a ARTE dos sprites: (ponta x, altura da ponta) medidas nas imagens
# ---------------------------------------------------------------------------
PONTA_SPRITE = {"vermelho": {"soco": (126, 166), "chute": (167, 197), "rasteira": (144, 41), "especial1": (118, 156), "especial2": (61, 118)}, "azul": {"soco": (142, 168), "chute": (161, 169), "rasteira": (155, 46), "especial1": (139, 152), "especial2": (137, 155)}, "amarelo": {"soco": (102, 147), "chute": (140, 166), "rasteira": (147, 20), "especial1": (109, 152), "especial2": (103, 58)}, "verde": {"soco": (112, 156), "chute": (145, 172), "rasteira": (119, 46), "especial1": (137, 109), "especial2": (92, 141)}, "roxo": {"soco": (201, 145), "chute": (172, 163), "rasteira": (159, 38), "especial1": (280, 125), "especial2": (165, 38)}, "preto": {"soco": (133, 163), "chute": (173, 174), "rasteira": (142, 40), "especial1": (115, 10), "especial2": (97, 143)}}


def _ajustar_alcance(ch, cap=1.6):
    pontas = PONTA_SPRITE.get(ch.key)
    if not pontas:
        return ch
    if ch.key == "azul":
        cap = 1.25                     # Colosso ja e forte: alcance cresce menos
    g = ch.golpes

    def alcance(hit, ponta):
        ox, oy, w, h = hit.box
        orig = ox + w
        novo = max(orig, min(ponta - 6, orig * cap))
        return ox, novo - ox

    for nome in ("soco", "chute", "rasteira"):
        if nome not in pontas or ch.key == "vermelho":
            continue
        hit = g[nome].hits[0]
        px, ph = pontas[nome]
        ox, w = alcance(hit, px)
        if nome == "soco":
            hit.box = (ox, ph - 17, w, 34)
        elif nome == "chute":
            hit.box = (ox, 70, w, max(40, ph + 20 - 70))
        else:
            hit.box = (ox, 0, w, max(40, ph + 15))
    k = ch.key
    if k == "vermelho":
        g["especial1"].spawn["oy"] = 110
        g["especial1"].spawn["ox"] = pontas["especial1"][0] - 10
    elif k == "azul":
        h1 = g["especial1"].hits[0]
        h1.box = (h1.box[0], h1.box[1], 110 - h1.box[0], h1.box[3])        # agarrao: ate 110
        h2 = g["especial2"].hits[0]
        ox, w = alcance(h2, pontas["especial2"][0])
        h2.box = (ox, 95, w, 80)
    elif k == "amarelo":
        g["especial1"].spawn.update(oy=140, ox=pontas["especial1"][0] - 10)
        g["especial2"].spawn.update(oy=30, ox=pontas["especial2"][0] - 10)
    elif k == "verde":
        h1 = g["especial1"].hits[0]
        ox, w = alcance(h1, pontas["especial1"][0])
        h1.box = (ox, 80, w, 60)
        for h in g["especial2"].hits:
            ox, w = alcance(h, pontas["soco"][0])
            h.box = (ox, 100, w, 55)
    elif k == "roxo":
        h1 = g["especial1"].hits[0]
        ox, w = alcance(h1, pontas["especial1"][0])
        h1.box = (ox, pontas["especial1"][1] - 13, w, 26)
        h2 = g["especial2"].hits[0]
        h2.box = (h2.box[0], 0, 200 - h2.box[0], 40)
    return ch


# ---------------------------------------------------------------------------
# Recarga (cooldown) dos especiais, em segundos
# ---------------------------------------------------------------------------
COOLDOWNS = {
    "vermelho": {"especial1": 2.0, "especial2": 3.0},
    "azul":     {"especial1": 4.5, "especial2": 4.5},
    "amarelo":  {"especial1": 0.9, "especial2": 0.9},
    "verde":    {"especial1": 1.8, "especial2": 2.4},
    "roxo":     {"especial1": 3.4, "especial2": 4.0},
    "preto":    {"especial1": 3.0, "especial2": 1.0},
}


def _cooldown(ch):
    ch.cooldown = dict(COOLDOWNS.get(ch.key, {"especial1": 2.5, "especial2": 2.5}))
    return ch


PERSONAGENS = [_cooldown(_ajustar_alcance(_acelerar(c))) for c in (criar_vermelho(), criar_azul(), criar_amarelo(),
                                      criar_verde(), criar_roxo(), criar_preto())]
