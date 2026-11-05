"""
fighter.py - PlayerController
=================================================================
Recebe Comandos (vindos do TECLADO ou da CPU - a mesma classe serve
para os dois) e cuida de:
  - maquina de estados do lutador
  - fisica (gravidade, pulo, dash, empurrao)
  - inicio/andamento dos golpes (frames de startup/ativo/recuperacao)
  - bloqueio (segurar para tras; agachado defende golpes baixos)
Nao desenha nada e nao usa pygame (da para testar sem tela).
"""
from dataclasses import dataclass, field

from settings import CHAO_Y, ARENA_MIN_X, ARENA_MAX_X, GRAVIDADE, FPS, GUARDA_MAX
from game.combat import Box

BOTOES = ("soco", "chute", "especial1", "especial2", "dash")
BUFFER_FRAMES = 8
NORMAIS = ("soco", "soco_baixo", "chute", "rasteira")
ESPECIAIS = ("especial1", "especial2")
ALCANCE_ARREMESSO = 105


@dataclass
class Comandos:
    esquerda: bool = False
    direita: bool = False
    cima: bool = False
    baixo: bool = False
    apertou: set = field(default_factory=set)     # botoes apertados NESTE frame

    def tras(self, facing):
        return self.esquerda if facing == 1 else self.direita

    def frente(self, facing):
        return self.direita if facing == 1 else self.esquerda


class Fighter:
    LARGURA = 70
    ALT_PE = 190
    ALT_AGACHADO = 115

    def __init__(self, char, slot):
        self.char = char
        self.slot = slot
        self.vitorias = 0
        self.reset(400, 1)

    def reset(self, x, facing):
        self.x, self.y = float(x), float(CHAO_Y)
        self.vx = self.vy = 0.0
        self.facing = facing
        self.hp = float(self.char.max_hp)
        self.hp_visual = self.hp
        self.estado, self.t = "idle", 0
        self.golpe, self.golpe_t = None, 0
        self.golpe_acertou, self.acertos = False, set()
        self.stun = 0
        self.agachado = False
        self.segurando_tras = False
        self.combo = 0
        self.dash_t, self.dash_dir = 0, 1
        self.usou_aereo = False
        self.kd_chao = 0
        self.flash = 0
        self.buf_botoes, self.buf_t = set(), 0
        self.segurando_baixo = False
        self.cancelou = False
        self.pousou = False            # True no frame em que toca o chao (para poeira)
        self.passo = 0.0               # distancia andada p/ frente(+)/tras(-): anima os passos
        self.cd = {k: 0 for k in ESPECIAIS}        # recarga dos especiais (frames)
        self.guarda = 0.0                          # sobe ao defender; cheia = guarda quebrada
        self.guarda_t = 0                          # frames desde a ultima defesa
        self.quebrou = False                       # evento p/ o app (texto/som)
        self.dist_op = 999.0

    # ================================================================ estado
    @property
    def no_chao(self):
        return self.y >= CHAO_Y - 0.01 and self.vy >= 0

    def livre(self):
        return self.estado in ("idle", "walk", "crouch", "jump")

    def set_estado(self, novo):
        self.estado, self.t = novo, 0

    def defendendo(self):
        return (self.no_chao and self.segurando_tras
                and self.estado in ("idle", "walk", "crouch", "blockstun"))

    def consegue_bloquear(self, altura):
        if not self.defendendo():
            return False
        if altura == "low":
            return self.agachado
        if altura == "overhead":
            return not self.agachado
        return True

    def _janela(self, nome):
        if self.estado != "attack" or not self.golpe:
            return False
        j = getattr(self.golpe, nome)
        return bool(j) and j[0] <= self.golpe_t <= j[1]

    def tem_armadura(self):
        return self._janela("armadura")

    def invulneravel(self):
        return self.estado in ("knockdown", "ko") or self._janela("invuln")

    def ignora_projeteis(self):
        if self.estado == "dash" and self.char.dash_atravessa:
            return True
        return self._janela("proj_invuln")

    # ================================================================ caixas
    def altura_corpo(self):
        return self.ALT_AGACHADO if self.agachado else self.ALT_PE

    def hurtbox(self):
        """Area onde o lutador PODE SER atingido."""
        if self.estado in ("knockdown", "ko"):
            return None
        h = self.altura_corpo()
        return Box(self.x - self.LARGURA / 2, self.y - h, self.LARGURA, h)

    def pushbox(self):
        """Area que impede os dois lutadores de se sobreporem."""
        h = 60 if self.estado in ("knockdown", "ko") else self.altura_corpo()
        return Box(self.x - self.LARGURA / 2, self.y - h, self.LARGURA, h)

    def caixa_golpe(self, hit):
        """Converte a hitbox do golpe para coordenadas da arena."""
        ox, oy, w, h = hit.box
        x = self.x + ox if self.facing == 1 else self.x - ox - w
        return Box(x, self.y - oy - h, w, h)

    def hits_ativos(self):
        if self.estado != "attack" or not self.golpe:
            return []
        return [(i, h) for i, h in enumerate(self.golpe.hits)
                if h.start <= self.golpe_t <= h.end and i not in self.acertos]

    def cd_max(self, nome):
        return max(1, int(self.char.cooldown.get(nome, 0) * FPS))

    def cd_frac(self, nome):
        """0 = pronto ... 1 = acabou de usar (para o HUD)."""
        return self.cd.get(nome, 0) / self.cd_max(nome)

    def pode_usar(self, nome, combate):
        g = self.char.golpes.get(nome)
        if g is None:
            return False
        if self.cd.get(nome, 0) > 0:                 # especial recarregando
            return False
        if g.spawn and g.spawn["tipo"] == "projetil":
            return combate.projeteis_de(self) < self.char.max_projeteis
        if g.spawn and g.spawn["tipo"] == "detonar":
            return bool(combate.minas_de(self))
        return True

    # ================================================================ update
    def update(self, cmd, oponente, combate):
        self.t += 1
        if self.flash > 0:
            self.flash -= 1
        self.segurando_tras = cmd.tras(self.facing)
        self.segurando_baixo = cmd.baixo
        self.pousou = False
        self.dist_op = abs(oponente.x - self.x)
        for k in self.cd:                                  # recarga dos especiais
            if self.cd[k] > 0:
                self.cd[k] -= 1
        self.guarda_t += 1
        if self.guarda_t > 30 and self.guarda > 0:         # meio segundo sem defender: recupera
            self.guarda = max(0.0, self.guarda - 1.5)

        # buffer: um botao apertado ate 6 frames antes ainda sai
        if cmd.apertou:
            self.buf_botoes, self.buf_t = set(cmd.apertou), BUFFER_FRAMES
        elif self.buf_t > 0:
            self.buf_t -= 1
            if self.buf_t == 0:
                self.buf_botoes = set()

        e = self.estado
        if e in ("hitstun", "blockstun"):
            if e == "blockstun":
                self.agachado = cmd.baixo
            self.stun -= 1
            if self.no_chao:
                self.vx *= 0.82
            if self.stun <= 0 and self.no_chao:
                if e == "hitstun":
                    self.combo = 0
                self.set_estado("idle")
        elif e == "knockdown":
            if self.no_chao:
                self.vx *= 0.8
                self.kd_chao += 1
                if self.kd_chao > 16:
                    self.combo = 0
                    self.set_estado("idle")
        elif e == "ko":
            if self.no_chao:
                self.vx *= 0.85
        elif e == "dash":
            self.dash_t -= 1
            self.vx = self.char.dash_vel * self.dash_dir
            if self.dash_t <= 0:
                self.vx = 0
                self.set_estado("idle")
        elif e == "attack":
            self._atualizar_golpe(combate)
        else:
            self._controle_livre(cmd, oponente, combate)

        self._fisica()
        if self.no_chao and self.estado in ("idle", "walk", "crouch"):
            self._virar(oponente)                          # livre no chao: sempre olha p/ o oponente

    def _virar(self, op):
        if abs(op.x - self.x) > 4:
            self.facing = 1 if op.x > self.x else -1

    def _controle_livre(self, cmd, op, combate):
        botoes = self.buf_botoes
        if self.no_chao:
            self.usou_aereo = False
            self._virar(op)
            self.agachado = cmd.baixo

            if {"soco", "chute"} <= botoes and self._pode_arremessar(op):
                self._consumir_buffer()
                self.iniciar_golpe("arremesso")
                return
            nome = self._escolher_golpe(botoes)
            if nome and self.pode_usar(nome, combate):
                self._consumir_buffer()
                self.iniciar_golpe(nome)
                return
            if "dash" in botoes:
                self._consumir_buffer()
                self.dash_dir = -self.facing if cmd.tras(self.facing) else self.facing
                self.dash_t = self.char.dash_frames
                self.agachado = False
                self.set_estado("dash")
                return
            if cmd.cima:
                dirx = int(cmd.direita) - int(cmd.esquerda)
                self.vy = self.char.pulo
                self.vx = dirx * self.char.vel_pulo_x
                self.agachado = False
                self.set_estado("jump")
                return
            if self.agachado:
                self.vx = 0
                if self.estado != "crouch":
                    self.set_estado("crouch")
            else:
                dirx = int(cmd.direita) - int(cmd.esquerda)
                fator = 0.75 if dirx == -self.facing else 1.0      # anda mais devagar para tras
                self.vx = dirx * self.char.vel_andar * fator
                novo = "walk" if dirx else "idle"
                if self.estado != novo:
                    self.set_estado(novo)
        else:
            if self.estado == "jump":                      # controle no ar (leve)
                dirx = int(cmd.direita) - int(cmd.esquerda)
                lim = self.char.vel_pulo_x * 1.1
                self.vx = max(-lim, min(lim, self.vx + dirx * 0.35))
            if ("soco" in botoes or "chute" in botoes) and not self.usou_aereo:
                self._consumir_buffer()
                self.usou_aereo = True
                self.iniciar_golpe("aereo")

    def _pode_arremessar(self, op):
        return (self.dist_op <= ALCANCE_ARREMESSO and op.no_chao
                and op.estado not in ("hitstun", "knockdown", "ko"))

    def _consumir_buffer(self):
        self.buf_botoes, self.buf_t = set(), 0

    def _escolher_golpe(self, botoes):
        if "especial1" in botoes:
            return "especial1"
        if "especial2" in botoes:
            return "especial2"
        if "chute" in botoes:
            return "rasteira" if self.agachado else "chute"
        if "soco" in botoes:
            return "soco_baixo" if self.agachado else "soco"
        return None

    def iniciar_golpe(self, nome):
        if nome in self.cd:
            self.cd[nome] = self.cd_max(nome)            # comeca a recarga
        self.golpe = self.char.golpes[nome]
        self.golpe_t = 0
        self.golpe_acertou = False
        self.cancelou = False
        self.acertos = set()
        if not self.golpe.aereo:
            self.vx = 0
            self.agachado = self.golpe.agachado
        self.set_estado("attack")

    def _tentar_cancel(self, combate):
        """COMBO: golpe normal que ACERTOU (ou foi defendido) pode ser cancelado
        em especial; soco tambem encadeia em chute."""
        g = self.golpe
        if not (self.golpe_acertou and g and g.hits and self.buf_botoes):
            return False
        atual = next((k for k in NORMAIS if self.char.golpes.get(k) is g), None)
        if atual is None or self.golpe_t <= max(h.end for h in g.hits):
            return False
        self.agachado = self.segurando_baixo
        nome = self._escolher_golpe(self.buf_botoes)
        if nome is None or nome in ("soco", "soco_baixo", atual):
            self.agachado = g.agachado
            return False
        if nome in ("chute", "rasteira") and atual not in ("soco", "soco_baixo"):
            self.agachado = g.agachado
            return False
        if not self.pode_usar(nome, combate):
            self.agachado = g.agachado
            return False
        self._consumir_buffer()
        self.iniciar_golpe(nome)
        self.cancelou = True
        combate.eventos.append(("cancel", self.x, self.y - 120, 0))
        return True

    def _atualizar_golpe(self, combate):
        if self._tentar_cancel(combate):
            return
        g = self.golpe
        self.golpe_t += 1

        if g.movimento:
            vx = 0
            for ini, fim, v in g.movimento:
                if ini <= self.golpe_t <= fim:
                    vx = v
            self.vx = vx * self.facing
        elif not g.aereo:
            self.vx = 0

        if g.spawn and self.golpe_t == g.spawn["frame"]:
            combate.spawn(self, g.spawn)

        if g.aereo:
            if self.no_chao and self.golpe_t > 1:
                self._fim_golpe()
            return

        total = g.total + (0 if self.golpe_acertou else g.whiff_extra)
        if self.golpe_t >= total:
            self._fim_golpe()

    def _fim_golpe(self):
        self.golpe = None
        self.vx = 0 if self.no_chao else self.vx
        self.set_estado("idle" if self.no_chao else "jump")

    # ================================================================ fisica
    def _fisica(self):
        if self.y < CHAO_Y or self.vy < 0:
            self.vy += GRAVIDADE
        self.x += self.vx
        self.y += self.vy
        if self.estado in ("walk", "dash"):
            self.passo += self.vx * self.facing
        if self.y >= CHAO_Y:
            caiu = self.vy > 0
            if caiu and self.vy > 3:
                self.pousou = True
            self.y, self.vy = float(CHAO_Y), 0.0
            if caiu and self.estado == "jump":
                self.vx = 0
                self.set_estado("idle")
        self.x = max(ARENA_MIN_X, min(ARENA_MAX_X, self.x))

    # ================================================================ dano
    def levar_dano(self, dano):
        self.hp = max(0.0, self.hp - dano)
        self.flash = 8

    def tomar_golpe(self, hit, direcao, dano):
        self.levar_dano(dano)
        self.combo += 1
        self.golpe = None
        if self.hp <= 0:
            self.agachado = False
            self.set_estado("ko")
            self.vy, self.vx = -9.0, direcao * 6.0
            return
        if hit.knockdown or hit.launch or hit.grab or not self.no_chao:
            self.agachado = False
            self.kd_chao = 0
            self.set_estado("knockdown")
            self.vy = hit.launch if hit.launch else -7.0
            self.vx = direcao * max(3.0, hit.knockback * 0.6)
        else:
            self.set_estado("hitstun")
            self.stun = hit.hitstun
            self.vx = direcao * hit.knockback

    def bloquear_golpe(self, hit, direcao, chip):
        self.hp = max(1.0, self.hp - chip)       # dano de raspao nao mata
        self.guarda += 8 + hit.dano * 1.2
        self.guarda_t = 0
        if self.guarda >= GUARDA_MAX:            # GUARDA QUEBRADA: fica tonto
            self.guarda = 0.0
            self.quebrou = True
            self.set_estado("hitstun")
            self.stun = 46
            self.vx = direcao * 3
            return
        self.set_estado("blockstun")
        self.stun = max(2, hit.blockstun - 2)     # sai da defesa um pouco antes (da p/ revidar)
        self.vx = direcao * hit.knockback * 0.8
