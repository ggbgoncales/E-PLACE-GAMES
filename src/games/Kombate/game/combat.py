"""
combat.py - CombatManager
=================================================================
Controla tudo que "acerta" alguem:
  - hitboxes (golpes ativos)  x  hurtboxes (corpo do oponente)
  - bloqueio alto/baixo, hiper-armadura, invulnerabilidade, agarrao
  - calculo de dano com escala de combo + dano de raspao (chip)
  - projeteis (inclusive projetil x projetil), minas e explosoes
  - hitstop (congela a luta alguns frames no impacto) e efeitos visuais
  - pushbox (os lutadores nao atravessam um ao outro)
"""
from settings import CHAO_Y, ARENA_MIN_X, ARENA_MAX_X, DANO_GLOBAL


class Box:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    def colide(self, o):
        return (self.x < o.x + o.w and o.x < self.x + self.w
                and self.y < o.y + o.h and o.y < self.y + self.h)

    @property
    def centerx(self):
        return self.x + self.w / 2

    @property
    def centery(self):
        return self.y + self.h / 2


class _HitSimples:
    """Hit gerado em tempo de execucao (projetil / explosao)."""
    def __init__(self, dano, altura, hitstun=18, blockstun=12, knockback=5.0,
                 knockdown=False, launch=0.0):
        self.dano, self.altura = dano, altura
        self.hitstun, self.blockstun, self.knockback = hitstun, blockstun, knockback
        self.knockdown, self.launch, self.grab = knockdown, launch, False


class Projetil:
    def __init__(self, dono, spec):
        self.dono = dono
        self.dir = dono.facing
        self.w, self.h = spec["w"], spec["h"]
        self.cx = dono.x + self.dir * spec.get("ox", 60)
        self.y = CHAO_Y - spec["oy"] - self.h
        self.vel = spec["vel"] * self.dir
        self.altura = spec["altura"]
        self.cor = spec["cor"]
        self.forma = spec.get("forma", "bola")
        self.hit = _HitSimples(spec["dano"], spec["altura"])
        self.vida = 240
        self.vivo = True
        self.t = 0

    def box(self):
        return Box(self.cx - self.w / 2, self.y, self.w, self.h)


class Mina:
    def __init__(self, dono, x, spec):
        self.dono, self.x = dono, x
        self.t = 0
        self.arma, self.pavio = spec["arma"], spec["pavio"]
        self.dano, self.raio = spec["dano"], spec["raio"]
        self.viva = True

    @property
    def armada(self):
        return self.t >= self.arma

    def box(self):
        return Box(self.x - 20, CHAO_Y - 14, 40, 14)


class Explosao:
    DURACAO = 18

    def __init__(self, mina):
        self.dono = mina.dono
        self.cx, self.raio = mina.x, mina.raio
        self.hit = _HitSimples(mina.dano, "mid", knockback=8, knockdown=True, launch=-11)
        self.t = 0
        self.acertou = False

    def box(self):
        r = self.raio
        return Box(self.cx - r, CHAO_Y - r * 1.7, r * 2, r * 1.7)


class CombatManager:
    HITSTOP_HIT = 4
    HITSTOP_BLOCK = 2
    HITSTOP_GRAB = 8

    def __init__(self):
        self.reset()

    def reset(self):
        self.projeteis, self.minas, self.explosoes, self.efeitos = [], [], [], []
        self.hitstop = 0
        self.eventos = []          # (tipo, x, y, forca) -> sons/particulas no app

    # ------------------------------------------------------------ consultas
    def projeteis_de(self, f):
        return sum(1 for p in self.projeteis if p.dono is f and p.vivo)

    def minas_de(self, f):
        return [m for m in self.minas if m.dono is f and m.viva]

    # ------------------------------------------------------------ spawn
    def spawn(self, f, spec):
        tipo = spec["tipo"]
        if tipo == "projetil":
            if self.projeteis_de(f) < f.char.max_projeteis:
                self.projeteis.append(Projetil(f, spec))
                self.eventos.append(("tiro", f.x, f.y - 100, 0))
        elif tipo == "mina":
            minhas = self.minas_de(f)
            if len(minhas) >= f.char.max_minas:
                minhas[0].viva = False                 # remove a mais antiga
            x = max(ARENA_MIN_X, min(ARENA_MAX_X, f.x + f.facing * spec["dist"]))
            self.minas.append(Mina(f, x, spec))
        elif tipo == "detonar":
            for m in self.minas_de(f):
                self._explodir(m)

    def _explodir(self, mina):
        mina.viva = False
        self.explosoes.append(Explosao(mina))
        self._efeito(mina.x, CHAO_Y - 30, "explosao", 40)

    def _efeito(self, x, y, tipo, forca=0.0):
        self.efeitos.append({"x": x, "y": y, "tipo": tipo, "t": 0})
        self.eventos.append((tipo, x, y, forca))

    # ------------------------------------------------------------ resolucao
    def _resolver(self, atacante, defensor, hit, direcao, projetil=False):
        """Decide o resultado de um contato. Retorna True se 'conectou'."""
        ponto_x = defensor.x - direcao * 25
        ponto_y = defensor.y - defensor.altura_corpo() * 0.6

        if hit.grab:
            if (not defensor.no_chao
                    or defensor.estado in ("hitstun", "blockstun", "knockdown", "ko")):
                return False                                  # agarrao erra
            defensor.tomar_golpe(hit, direcao, hit.dano * DANO_GLOBAL)
            atacante.golpe_acertou = True
            self.hitstop = self.HITSTOP_GRAB
            self._efeito(ponto_x, ponto_y, "agarrao", hit.dano * DANO_GLOBAL)
            return True

        if defensor.consegue_bloquear(hit.altura):
            chip = hit.dano * DANO_GLOBAL * (0.20 if projetil else 0.10)
            defensor.bloquear_golpe(hit, direcao, chip)
            if not projetil:
                atacante.golpe_acertou = True
            if defensor.quebrou:
                defensor.quebrou = False
                self.hitstop = self.HITSTOP_GRAB
                self._efeito(ponto_x, ponto_y, "agarrao", 30)
                self.eventos.append(("guarda", defensor.x, defensor.y - 240, 0))
                return True
            self.hitstop = self.HITSTOP_BLOCK
            self._efeito(ponto_x, ponto_y, "bloqueio")
            return True

        escala = max(0.45, 0.88 ** defensor.combo)           # combos longos dao menos dano
        dano = hit.dano * escala * DANO_GLOBAL
        counter = (not projetil and defensor.estado == "attack" and defensor.combo == 0)
        if counter:                                           # acertou no meio do golpe dele
            dano *= 1.25

        if defensor.tem_armadura():                           # hiper-armadura: toma dano, nao para
            defensor.levar_dano(dano * 0.8)
            if not projetil:
                atacante.golpe_acertou = True
            self.hitstop = self.HITSTOP_BLOCK
            self._efeito(ponto_x, ponto_y, "armadura")
            if defensor.hp <= 0:
                defensor.tomar_golpe(hit, direcao, 0)
            return True

        defensor.tomar_golpe(hit, direcao, dano)
        if counter and defensor.estado == "hitstun":
            defensor.stun += 8                                # counter da mais tempo de combo
        if not projetil:
            atacante.golpe_acertou = True
        self.hitstop = self.HITSTOP_HIT + (2 if dano >= 50 else 0) + (2 if counter else 0)
        self._efeito(ponto_x, ponto_y, "hit", dano)
        if counter:
            self.eventos.append(("counter", defensor.x, defensor.y - 230, dano))
        return True

    # ------------------------------------------------------------ update
    def update(self, f1, f2):
        # 1) golpes corpo a corpo: coleta os contatos ANTES de aplicar (permite "trade")
        contatos = []
        for at, df in ((f1, f2), (f2, f1)):
            hb = df.hurtbox()
            if hb is None or df.invulneravel():
                continue
            for i, hit in at.hits_ativos():
                if at.caixa_golpe(hit).colide(hb):
                    contatos.append((at, df, i, hit))
                    break
        for at, df, i, hit in contatos:
            at.acertos.add(i)
            self._resolver(at, df, hit, at.facing)

        # 2) projeteis
        for p in self.projeteis:
            p.cx += p.vel
            p.t += 1
            p.vida -= 1
            if p.vida <= 0 or p.cx < ARENA_MIN_X - 80 or p.cx > ARENA_MAX_X + 80:
                p.vivo = False
        vivos = [p for p in self.projeteis if p.vivo]
        for i, a in enumerate(vivos):
            for b in vivos[i + 1:]:
                if a.vivo and b.vivo and a.dono is not b.dono and a.box().colide(b.box()):
                    a.vivo = b.vivo = False
                    self._efeito((a.cx + b.cx) / 2, a.box().centery, "bloqueio")
        for p in self.projeteis:
            if not p.vivo:
                continue
            alvo = f2 if p.dono is f1 else f1
            hb = alvo.hurtbox()
            if (hb is not None and not alvo.invulneravel()
                    and not alvo.ignora_projeteis() and p.box().colide(hb)):
                p.vivo = False
                self._resolver(p.dono, alvo, p.hit, p.dir, projetil=True)

        # 3) minas
        for m in self.minas:
            if not m.viva:
                continue
            m.t += 1
            alvo = f2 if m.dono is f1 else f1
            hb = alvo.hurtbox()
            if m.t >= m.pavio:
                self._explodir(m)
            elif m.armada and hb is not None and m.box().colide(hb):
                self._explodir(m)

        # 4) explosoes (so atingem o oponente do dono)
        for ex in self.explosoes:
            ex.t += 1
            if not ex.acertou and ex.t <= 6:
                alvo = f2 if ex.dono is f1 else f1
                hb = alvo.hurtbox()
                if hb is not None and not alvo.invulneravel() and ex.box().colide(hb):
                    ex.acertou = True
                    direcao = 1 if alvo.x >= ex.cx else -1
                    self._resolver(ex.dono, alvo, ex.hit, direcao, projetil=True)

        # 5) limpeza e efeitos
        self.projeteis = [p for p in self.projeteis if p.vivo]
        self.minas = [m for m in self.minas if m.viva]
        self.explosoes = [e for e in self.explosoes if e.t < Explosao.DURACAO]
        for ef in self.efeitos:
            ef["t"] += 1
        self.efeitos = [ef for ef in self.efeitos if ef["t"] < 20]

    # ------------------------------------------------------------ pushbox
    def separar(self, f1, f2):
        a, b = f1.pushbox(), f2.pushbox()
        if not a.colide(b):
            return
        sobra = (a.w + b.w) / 2 - abs(f1.x - f2.x)
        if sobra <= 0:
            return
        if f1.x != f2.x:
            s = 1 if f1.x < f2.x else -1
        else:
            s = f1.facing
        f1.x -= s * sobra / 2
        f2.x += s * sobra / 2
        for f in (f1, f2):
            f.x = max(ARENA_MIN_X, min(ARENA_MAX_X, f.x))
        resto = (a.w + b.w) / 2 - abs(f1.x - f2.x)
        if resto > 0:                       # um deles esta na parede: empurra o outro
            if f1.x in (ARENA_MIN_X, ARENA_MAX_X):
                f2.x = max(ARENA_MIN_X, min(ARENA_MAX_X, f2.x + s * resto))
            else:
                f1.x = max(ARENA_MIN_X, min(ARENA_MAX_X, f1.x - s * resto))
