"""
match.py - Partida (rounds, tempo, K.O., vencedor). Sem pygame.
"""
from settings import FPS, TEMPO_ROUND, ROUNDS_PARA_VENCER, MAX_ROUNDS, NIVEL_CPU
from game.fighter import Fighter, Comandos
from game.combat import CombatManager
from game.ai import CPU


class Partida:
    def __init__(self, char1, char2, cpu1=False, cpu2=True, nivel=NIVEL_CPU):
        self.f1 = Fighter(char1, 1)
        self.f2 = Fighter(char2, 2)
        self.combate = CombatManager()
        self.cpus = {1: CPU(self.f1, nivel) if cpu1 else None,
                     2: CPU(self.f2, nivel) if cpu2 else None}
        self.round = 0
        self.vencedor = None            # Fighter, ou "empate"
        self.novo_round()

    def novo_round(self):
        self.round += 1
        self.f1.reset(400, 1)
        self.f2.reset(880, -1)
        self.combate.reset()
        for cpu in self.cpus.values():
            if cpu:
                cpu.reset()
        self.tempo = TEMPO_ROUND * FPS
        self.fase, self.fase_t = "intro", 0
        self.vencedor_round = None
        self.motivo = ""
        self.slowmo = 0

    @property
    def segundos(self):
        return max(0, (self.tempo + FPS - 1) // FPS)

    def update(self, cmd1=None, cmd2=None):
        if self.slowmo > 0:                               # camera lenta no K.O.
            self.slowmo -= 1
            if self.slowmo % 2:
                return
        self.fase_t += 1
        vazio = Comandos()
        if self.fase == "luta":
            if self.cpus[1]:
                cmd1 = self.cpus[1].update(self.f2, self.combate)
            if self.cpus[2]:
                cmd2 = self.cpus[2].update(self.f1, self.combate)
            cmd1, cmd2 = cmd1 or vazio, cmd2 or vazio
        else:
            cmd1 = cmd2 = vazio
            if self.fase == "intro" and self.fase_t >= 70:
                self.fase, self.fase_t = "luta", 0

        for f in (self.f1, self.f2):
            f.hp_visual += (f.hp - f.hp_visual) * 0.06

        if self.combate.hitstop > 0:
            self.combate.hitstop -= 1
            return

        self.f1.update(cmd1, self.f2, self.combate)
        self.f2.update(cmd2, self.f1, self.combate)
        self.combate.separar(self.f1, self.f2)
        self.combate.update(self.f1, self.f2)

        if self.fase == "luta":
            self.tempo -= 1
            if self.f1.hp <= 0 or self.f2.hp <= 0 or self.tempo <= 0:
                self._fim_round()
        elif self.fase == "ko" and self.fase_t >= 115:
            if (max(self.f1.vitorias, self.f2.vitorias) >= ROUNDS_PARA_VENCER
                    or self.round >= MAX_ROUNDS):
                self.fase, self.fase_t = "fim", 0
                if self.f1.vitorias == self.f2.vitorias:
                    self.vencedor = "empate"
                else:
                    self.vencedor = self.f1 if self.f1.vitorias > self.f2.vitorias else self.f2
            else:
                self.novo_round()

    def _fim_round(self):
        self.motivo = "TEMPO!" if self.tempo <= 0 and self.f1.hp > 0 and self.f2.hp > 0 else "K.O.!"
        if self.f1.hp > self.f2.hp:
            self.vencedor_round = self.f1
        elif self.f2.hp > self.f1.hp:
            self.vencedor_round = self.f2
        else:
            self.vencedor_round = None
        if self.vencedor_round:
            self.vencedor_round.vitorias += 1
        self.fase, self.fase_t = "ko", 0
        if self.motivo == "K.O.!":
            self.slowmo = 40
