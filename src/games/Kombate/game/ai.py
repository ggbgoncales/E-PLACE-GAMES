"""
ai.py - CPU (State Machine: IDLE -> APPROACH -> ATTACK -> RETREAT)
=================================================================
A CPU NAO controla o lutador diretamente: ela gera os mesmos
Comandos que o teclado geraria. Assim o PlayerController e o
mesmo para humano e CPU (nada de "trapaca" na fisica).

Camadas:
  1) Defesa (reativa): se ha ameaca (golpe vindo, projetil, pulo),
     com chance X segura para tras (bloqueia), agacha contra golpe
     baixo, usa antiaereo ou, no caso do Verde, faz dash atravessando
     o projetil.
  2) Maquina de estados (proativa):
     IDLE     -> pensa um pouco e decide pela distancia preferida
     APPROACH -> anda/dasha ate a distancia de ataque (pula minas)
     ATTACK   -> escolhe o golpe certo para a distancia e personagem
     RETREAT  -> recua segurando para tras (o que tambem defende)
"""
import random

from game.fighter import Comandos

# 5 niveis de dificuldade (medidor no jogo)
NIVEIS = {
    1: {"nome": "MUITO FACIL", "reacao": 26, "defesa": 0.12, "antiaereo": 0.10, "pensar": (30, 60), "combo": 0.00},
    2: {"nome": "FACIL",       "reacao": 18, "defesa": 0.30, "antiaereo": 0.25, "pensar": (16, 36), "combo": 0.03},
    3: {"nome": "NORMAL",      "reacao": 11, "defesa": 0.50, "antiaereo": 0.45, "pensar": (7, 20),  "combo": 0.12},
    4: {"nome": "DIFICIL",     "reacao": 6,  "defesa": 0.72, "antiaereo": 0.70, "pensar": (3, 11),  "combo": 0.30},
    5: {"nome": "MESTRE",      "reacao": 3,  "defesa": 0.90, "antiaereo": 0.90, "pensar": (1, 5),   "combo": 0.60},
}
_ANTIGOS = {"facil": 2, "normal": 3, "dificil": 4}


def nivel_valido(nivel):
    nivel = _ANTIGOS.get(nivel, nivel)
    return nivel if nivel in NIVEIS else 3

NORMAIS = [("soco", False), ("chute", False), ("soco", True), ("chute", True)]

# golpe que cada CPU usa para emendar combo depois de um normal que acertou
COMBO_FINAL = {"vermelho": "especial2", "azul": "especial2", "amarelo": "especial1",
               "verde": "especial2", "roxo": "especial1", "preto": "chute"}


class CPU:
    def __init__(self, fighter, nivel=3):
        self.f = fighter
        self.set_nivel(nivel)
        self.rng = random.Random()
        self.reset()

    def set_nivel(self, nivel):
        self.nivel = nivel_valido(nivel)
        self.cfg = NIVEIS[self.nivel]

    def reset(self):
        self.estado = "IDLE"
        self.timer = 30
        self.defesa_t = 0
        self.defesa_baixa = False
        self.ameaca_cd = 0
        self.dash_cd = 0

    def _ir(self, estado, frames):
        self.estado, self.timer = estado, int(frames)

    @staticmethod
    def _segurar(c, direcao):
        if direcao > 0:
            c.direita = True
        else:
            c.esquerda = True

    # ------------------------------------------------------------------ main
    def update(self, op, combate):
        f, c, r = self.f, Comandos(), self.rng
        dx = op.x - f.x
        dist = abs(dx)
        frente = 1 if dx >= 0 else -1
        self.timer -= 1
        self.dash_cd -= 1
        self.ameaca_cd -= 1

        final = COMBO_FINAL.get(f.char.key, "chute")
        if (f.estado == "attack" and f.golpe_acertou and f.golpe and f.golpe.hits
                and op.estado == "hitstun" and r.random() < self.cfg["combo"]
                and f.cd.get(final, 0) <= 0):
            c.apertou.add(final)                                    # emenda combo
            return c
        if f.estado == "blockstun":                     # continua defendendo
            self._segurar(c, -frente)
            c.baixo = self.defesa_baixa
            return c
        if not f.livre() or not f.no_chao:
            return c

        # ---------------- 1) DEFESA
        if self.defesa_t > 0:
            self.defesa_t -= 1
            self._segurar(c, -frente)
            c.baixo = self.defesa_baixa
            return c

        ameaca = self._ameaca(op, combate, dist)
        if ameaca and self.ameaca_cd <= 0:
            self.ameaca_cd = self.cfg["reacao"]
            if (ameaca == "aereo" and f.char.antiaereo and r.random() < self.cfg["antiaereo"]
                    and f.cd.get(f.char.antiaereo, 0) <= 0):
                c.apertou.add(f.char.antiaereo)
                self._ir("IDLE", 10)
                return c
            if ameaca == "projetil_alto_baixo" and f.char.dash_atravessa and r.random() < 0.5:
                c.apertou.add("dash")                   # Verde: atravessa o projetil
                self._segurar(c, frente)
                return c
            if r.random() < self.cfg["defesa"]:
                self.defesa_baixa = ameaca in ("low", "projetil_alto_baixo")
                self.defesa_t = 12
                self._segurar(c, -frente)
                c.baixo = self.defesa_baixa
                return c

        # ---------------- 2) MAQUINA DE ESTADOS
        getattr(self, "_st_" + self.estado.lower())(c, op, combate, dist, frente)
        return c

    # ------------------------------------------------------------------ ameacas
    def _ameaca(self, op, combate, dist):
        f = self.f
        if op.estado == "attack" and op.golpe and op.golpe.hits:
            alcance = max(h.box[0] + h.box[2] for h in op.golpe.hits)
            ultimo = max(h.end for h in op.golpe.hits)
            if dist <= alcance + 45 and op.golpe_t <= ultimo:
                return "low" if any(h.altura == "low" for h in op.golpe.hits) else "alto"
        for p in combate.projeteis:
            if p.dono is op and (p.vel > 0) == (f.x > p.cx) and abs(p.cx - f.x) < 260:
                return "projetil_alto_baixo" if p.altura in ("high", "low") else "alto"
        for ex in combate.explosoes:
            if ex.dono is op and abs(ex.cx - f.x) < ex.raio + 60:
                return "alto"
        if not op.no_chao and dist < 240 and op.vy > -6:
            return "aereo"
        return None

    def _mina_no_caminho(self, op, combate, frente):
        for m in combate.minas_de(op):
            if 0 < (m.x - self.f.x) * frente < 110:
                return True
        return False

    # ------------------------------------------------------------------ estados
    def _st_idle(self, c, op, combate, dist, frente):
        if self.timer > 0:
            return
        ia = self.f.char.ia
        if dist > ia["dist"] + 60:
            self._ir("APPROACH", self.rng.randint(40, 120))
        elif dist < ia["dist"] - 80 and self.rng.random() < ia["recua"]:
            self._ir("RETREAT", self.rng.randint(20, 50))
        else:
            self._ir("ATTACK", 1)

    def _st_approach(self, c, op, combate, dist, frente):
        ia, r = self.f.char.ia, self.rng
        self._segurar(c, frente)
        if self._mina_no_caminho(op, combate, frente):
            c.cima = True                                       # pula a mina
        elif dist > 320 and self.dash_cd <= 0 and self.f.char.dash_vel >= 14:
            c.apertou.add("dash")
            self.dash_cd = 90
        elif dist < 300 and r.random() < 0.006:
            c.cima = True                                       # pulo de ataque
        if dist <= ia["dist"] + 20 or self.timer <= 0 or r.random() < ia["tiro"]:
            self._ir("ATTACK", 1)

    def _st_attack(self, c, op, combate, dist, frente):
        botao, baixo = self._escolher_ataque(op, combate, dist)
        if botao is None:
            if dist > 130:
                self._ir("APPROACH", 40)
            else:
                self._ir("RETREAT", 25)
            return
        if botao == "arremesso":
            c.apertou.update(("soco", "chute"))
        else:
            c.apertou.add(botao)
        c.baixo = baixo
        if self.rng.random() < self.f.char.ia["recua"]:
            self._ir("RETREAT", self.rng.randint(20, 45))
        else:
            self._ir("IDLE", self.rng.randint(*self.cfg["pensar"]))

    def _st_retreat(self, c, op, combate, dist, frente):
        self._segurar(c, -frente)                               # recuar = defender
        if self.timer <= 0:
            self._ir("IDLE", self.rng.randint(*self.cfg["pensar"]))

    # ------------------------------------------------------------------ golpes
    def _escolher_ataque(self, op, combate, dist):
        f, r = self.f, self.rng
        # contra quem fica so defendendo de perto: arremesso
        if (dist < 100 and op.no_chao and op.estado in ("blockstun", "crouch", "idle")
                and (op.segurando_tras or op.estado == "blockstun") and r.random() < 0.3 + 0.08 * self.nivel):
            return "arremesso", False
        botao, baixo = self._escolher_base(op, combate, dist)
        if botao in ("especial1", "especial2") and f.cd.get(botao, 0) > 0:   # recarregando
            outro = "especial2" if botao == "especial1" else "especial1"
            if f.cd.get(outro, 0) <= 0 and r.random() < 0.3 and f.pode_usar(outro, combate):
                return outro, False
            if dist < 120:
                return r.choice(NORMAIS)
            return None, False
        return botao, baixo

    def _escolher_base(self, op, combate, dist):
        f, r = self.f, self.rng
        k = f.char.key
        x = r.random()
        perto = dist < 115

        if k == "vermelho":
            if dist > 300 and combate.projeteis_de(f) == 0:
                return "especial1", False
            if perto:
                return r.choice(NORMAIS)
        elif k == "azul":
            if dist < 100 and x < 0.5:
                return "especial1", False
            if dist < 170 and x < 0.35:
                return "especial2", False
            if perto:
                return r.choice(NORMAIS)
        elif k == "amarelo":
            if dist > 220 and combate.projeteis_de(f) < 2:
                return r.choice([("especial1", False), ("especial2", False)])
            if perto:
                return r.choice([("chute", False), ("chute", True)])
        elif k == "verde":
            if perto:
                return ("especial2", False) if x < 0.45 else r.choice(NORMAIS)
            if 140 < dist < 380 and x < 0.5:
                return "especial1", False
        elif k == "roxo":
            if 130 < dist < 260:
                return r.choice([("especial1", False), ("especial2", False)])
            if dist <= 180:
                return r.choice([("soco", False), ("chute", False), ("chute", True)])
        elif k == "preto":
            minas = combate.minas_de(f)
            if any(m.armada and abs(m.x - op.x) < 90 for m in minas):
                return "especial2", False
            if len(minas) < 3 and (dist > 170 or x < 0.3):
                return "especial1", False
            if perto:
                return r.choice(NORMAIS)
        return None, False
