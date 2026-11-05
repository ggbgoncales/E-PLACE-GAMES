import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
import sys
import json
import math
import random
import pygame

RECORDE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorde.json")


def carregar_recorde():
    try:
        with open(RECORDE_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("recorde", 0))
    except Exception:
        return 0


def salvar_recorde(valor):
    try:
        with open(RECORDE_FILE, "w", encoding="utf-8") as f:
            json.dump({"recorde": valor}, f)
    except Exception:
        pass


from settings import *
from game.entities.frog import Frog
from game.entities.mover import Mover, TURTLE_W, LOOP_MARGIN
from game.entities.fx import Particle, Ripple

# ----------------------------------------------------------------------
# FASES. Depois da 5 entra no modo infinito (repete os temas mais dificil)
# ----------------------------------------------------------------------
FASES = [
    dict(nome="LAGOA CALMA", dica="Pule nos troncos e tartarugas ate a vitoria-regia!",
         mult=1.00, jacare=0.00, tartaruga=0.30, mergulho=0.00, cobras=0,
         log=(46, 74), gap=(46, 86), tempo=60, noite=False, agua=(26, 105, 158), grama=(56, 132, 67)),
    dict(nome="RIO DOS TRONCOS", dica="Cuidado: algumas tartarugas MERGULHAM!",
         mult=1.15, jacare=0.12, tartaruga=0.35, mergulho=0.45, cobras=0,
         log=(42, 66), gap=(54, 96), tempo=55, noite=False, agua=(30, 98, 150), grama=(60, 128, 62)),
    dict(nome="PANTANO DOS JACARES", dica="Jacares no rio e COBRA na margem do meio!",
         mult=1.25, jacare=0.35, tartaruga=0.30, mergulho=0.55, cobras=1,
         log=(40, 60), gap=(58, 100), tempo=52, noite=False, agua=(38, 92, 92), grama=(66, 110, 52)),
    dict(nome="CORREDEIRA", dica="Correnteza forte: tudo bem mais rapido!",
         mult=1.60, jacare=0.25, tartaruga=0.35, mergulho=0.60, cobras=1,
         log=(36, 56), gap=(62, 106), tempo=48, noite=False, agua=(20, 118, 176), grama=(52, 138, 74)),
    dict(nome="NOITE NO BREJO", dica="Escuridao total. So voce ilumina o caminho.",
         mult=1.45, jacare=0.30, tartaruga=0.40, mergulho=0.70, cobras=2,
         log=(36, 54), gap=(62, 110), tempo=55, noite=True, agua=(22, 70, 120), grama=(40, 96, 60)),
]
NINHOS = 5
ROMANOS = ["", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def romano(n):
    return ROMANOS[n - 1] if n <= len(ROMANOS) else str(n)


def config_fase(n):
    """Fases INFINITAS: os 5 temas se repetem em ciclos, sempre mais dificeis."""
    base = dict(FASES[(n - 1) % len(FASES)])
    ciclo = (n - 1) // len(FASES) + 1
    if n > len(FASES):
        extra = n - len(FASES)
        k = extra / (extra + 12)
        base["mult"] = base["mult"] * (1 + 1.6 * k)
        base["jacare"] = base["jacare"] + (0.50 - base["jacare"]) * k
        base["mergulho"] = base["mergulho"] + (0.85 - base["mergulho"]) * k
        base["cobras"] = min(base["cobras"] + 1 + extra // 8, 5)
        base["tempo"] = max(30, int(base["tempo"] - 25 * k))
        base["log"] = (max(32, int(base["log"][0] - 10 * k)), max(44, int(base["log"][1] - 18 * k)))
        base["gap"] = (int(base["gap"][0] + 30 * k), int(base["gap"][1] + 40 * k))
        base["dica"] = f"CICLO {ciclo}: tudo mais rapido e perigoso!"
    base["nome"] = (base["nome"] + " " + romano(ciclo)).strip()
    base["ciclo"] = ciclo
    return base


def escurecer(cor, f):
    return tuple(max(0, min(255, int(c * f))) for c in cor)


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)
        ww, wh = self.window.get_size()
        self.scale = min(ww / VW, wh / VH)
        self.out_w, self.out_h = int(VW * self.scale), int(VH * self.scale)
        self.ox, self.oy = (ww - self.out_w) // 2, (wh - self.out_h) // 2
        self.textos = []
        self._fontes = {}
        pygame.display.set_caption("Sapo Aventureiro Pixel")
        self.canvas = pygame.Surface((VW, VH))
        self.clock = pygame.time.Clock()
        self.FONT = 8
        self.SMALL = 6.5
        self.BIG = 18
        self.recorde = carregar_recorde()
        self.novo_recorde = False
        self.particles = []
        self.ripples = []
        self.water_time = 0
        self.shake = 0
        self.message = ""
        self.message_timer = 0
        self.death_reason = ""
        self.ultimo_bonus = 0
        self.novo_jogo()
        self.state = "title"

    # ------------------------------------------------------------------
    # FASES
    # ------------------------------------------------------------------
    def novo_jogo(self):
        self.frog = Frog()
        self.novo_recorde = False
        self.particles.clear()
        self.ripples.clear()
        self.iniciar_fase(1)

    def iniciar_fase(self, n):
        self.frog.level = n
        self.cfg = config_fase(n)
        self.movers = self.make_level(self.cfg)
        self.ninhos = [False] * NINHOS
        self.ninho_x = [int(VW * (i + 1) / (NINHOS + 1)) for i in range(NINHOS)]
        self.mosca = None
        self.mosca_timer = random.uniform(4, 8)
        self.tempo = self.cfg["tempo"]
        self.message_timer = 0
        self.frog.reset()
        self.state = "intro"
        self.intro_timer = 2.6

    def make_level(self, cfg):
        mult = cfg["mult"]
        movers = []
        direcao = random.choice((1, -1))
        x0 = -LOOP_MARGIN
        for y in sorted(LANES):
            fator = 0.85 if y in RIVER_2 else 1.05
            speed = random.uniform(24, 40) * mult * fator * direcao
            direcao = -direcao
            usa_tartaruga = random.random() < cfg["tartaruga"]
            itens = []
            perigo_antes = True     # a faixa sempre comeca com um apoio seguro
            x = x0
            # regra: nunca 2 perigos seguidos (jacare / tartaruga que mergulha)
            while x < VW + LOOP_MARGIN:
                r = random.random()
                if not perigo_antes and r < cfg["jacare"]:
                    kind, w, dive = "gator", 46, False
                elif usa_tartaruga:
                    kind, w = "turtle", random.choice((2, 3, 3)) * TURTLE_W
                    dive = (not perigo_antes) and random.random() < cfg["mergulho"]
                else:
                    kind, w, dive = "log", random.randint(*cfg["log"]), False
                perigo_antes = kind == "gator" or dive
                itens.append((kind, x, w, dive))
                x += w + random.uniform(*cfg["gap"])
            loop = x - x0
            movers += [Mover(ix, y, w, speed, kind, dive, loop) for kind, ix, w, dive in itens]
        for i in range(cfg["cobras"]):
            sp = random.uniform(30, 46) * min(mult, 2.0) * (1 if i % 2 == 0 else -1)
            movers.append(Mover(random.uniform(0, VW), SAND_ROW, 34, sp, "snake"))
        return movers

    # ------------------------------------------------------------------
    def is_water(self, y):
        return any(row <= y < row + TILE for row in LANES)

    def splash(self, x, y, amount=18):
        for _ in range(amount):
            self.particles.append(Particle(x, y, random.choice((WATER_FOAM, WATER_LIGHT, WHITE))))
        self.ripples.extend((Ripple(x, y), Ripple(x, y, 0.18), Ripple(x, y, 0.36)))

    def festa(self, x, y, cores=(GOLD, WHITE, FROG_LIGHT), amount=30):
        for _ in range(amount):
            self.particles.append(Particle(x, y, random.choice(cores)))

    def begin_death(self, reason):
        if self.frog.invuln > 0 or self.state != "playing":
            return
        self.state = "dying"
        self.death_reason = reason
        self.death_timer = 1.05
        self.shake = 0.28
        self.frog.riding = None
        self.splash(self.frog.rect.centerx, self.frog.rect.centery)

    def finish_death(self):
        self.frog.lives -= 1
        if self.frog.lives <= 0:
            self.state = "gameover"
            if self.frog.score > self.recorde:
                self.recorde = self.frog.score
                self.novo_recorde = True
                salvar_recorde(self.recorde)
        else:
            self.frog.reset()
            self.tempo = self.cfg["tempo"]
            self.state = "playing"
            self.message = self.death_reason
            self.message_timer = 1.3

    def chegou_no_topo(self):
        """Chegou numa vitoria-regia = FASE COMPLETA -> vai pra proxima fase."""
        cx = self.frog.rect.centerx
        for i, nx in enumerate(self.ninho_x):
            if abs(cx - nx) <= 13:
                self.ninhos[i] = True
                bonus = 500 + 100 * self.frog.level + int(self.tempo) * 10
                if self.mosca and self.mosca[0] == i:
                    bonus += 200
                    self.mosca = None
                self.frog.score += bonus
                self.ultimo_bonus = bonus
                if self.frog.lives < 6 and self.frog.level % 2 == 0:
                    self.frog.lives += 1
                self.festa(nx, GOAL_ROW + 10, amount=50)
                self.state = "clear"
                self.clear_timer = 2.2
                return
        self.begin_death("ERROU A VITORIA-REGIA!")

    # ------------------------------------------------------------------
    # TEXTO NITIDO (desenhado direto na tela, na resolucao real)
    # ------------------------------------------------------------------
    def fonte(self, tamanho):
        px = max(12, int(tamanho * self.scale))
        if px not in self._fontes:
            caminho = None
            for nome in ("segoeui", "verdana", "tahoma", "arial", "dejavusans"):
                caminho = pygame.font.match_font(nome, bold=True)
                if caminho:
                    break
            self._fontes[px] = pygame.font.Font(caminho, px) if caminho else pygame.font.Font(None, int(px * 1.35))
        return self._fontes[px]

    def texto(self, text, tamanho, x, y, color=WHITE, anchor="topleft"):
        self.textos.append((text, tamanho, x, y, color, anchor))

    def text_center(self, text, tamanho, y, color=WHITE):
        self.texto(text, tamanho, VW / 2, y, color, "midtop")

    def desenhar_textos(self, dx, dy):
        for text, tamanho, x, y, color, anchor in self.textos:
            fonte = self.fonte(tamanho)
            pos = (self.ox + dx + x * self.scale, self.oy + dy + y * self.scale)
            sombra = fonte.render(text, True, INK)
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
                self.window.blit(sombra, sombra.get_rect(**{anchor: (pos[0] + ox, pos[1] + oy)}))
            img = fonte.render(text, True, color)
            self.window.blit(img, img.get_rect(**{anchor: pos}))
        self.textos.clear()

    # ------------------------------------------------------------------
    # CENARIO
    # ------------------------------------------------------------------
    def draw_map(self):
        agua = self.cfg["agua"]
        agua_d, agua_l = escurecer(agua, 0.72), escurecer(agua, 1.5)
        grama = self.cfg["grama"]
        grama_d, grama_l = escurecer(grama, 0.72), escurecer(grama, 1.25)
        for y in range(0, VH, TILE):
            if y in LANES:
                pixel_rect(self.canvas, agua, (0, y, VW, TILE))
                pixel_rect(self.canvas, agua_d, (0, y, VW, 2))
                direc = 1 if (y // TILE) % 2 else -1
                wave = int(self.water_time * 18 * direc + y) % 30
                for x in range(-30, VW + 30, 30):
                    xx = x + wave
                    pixel_rect(self.canvas, agua_l, (xx, y + 6, 10, 1))
                    pixel_rect(self.canvas, agua_l, (xx + 3, y + 5, 6, 1))
                    pixel_rect(self.canvas, agua_d, (xx + 15, y + 14, 8, 1))
            elif y == SAND_ROW:
                pixel_rect(self.canvas, SAND, (0, y, VW, TILE))
                pixel_rect(self.canvas, SAND_LIGHT, (0, y, VW, 2))
                pixel_rect(self.canvas, SAND_DARK, (0, y + TILE - 2, VW, 2))
                for x in range(5, VW, 23):
                    pixel_rect(self.canvas, SAND_DARK, (x, y + 8 + (x % 7), 2, 1))
                for x in range(40, VW, 140):
                    pixel_rect(self.canvas, (130, 130, 120), (x, y + 10, 6, 4))
                    pixel_rect(self.canvas, (170, 170, 160), (x + 1, y + 10, 3, 1))
            elif y == GOAL_ROW:
                pixel_rect(self.canvas, grama_d, (0, y, VW, TILE))
                for x in range(0, VW, 12):
                    pixel_rect(self.canvas, grama, (x, y + 2 + (x % 5), 10, 6))
                    pixel_rect(self.canvas, grama_l, (x + 2, y + 3 + (x % 5), 4, 2))
            elif y == HUD_ROW:
                continue
            else:
                base = grama if (y // TILE) % 2 else grama_d
                pixel_rect(self.canvas, base, (0, y, VW, TILE))
                pixel_rect(self.canvas, grama_d, (0, y, VW, 2))
                for x in range(4, VW, 19):
                    yy = y + 5 + ((x * 3 + y) % 11)
                    pixel_rect(self.canvas, grama_l, (x, yy, 1, 4))
                    pixel_rect(self.canvas, grama_l, (x + 1, yy, 1, 2))
                for x in range(17, VW, 97):
                    if (x + y) % 3 == 0:
                        pixel_rect(self.canvas, FLOWER, (x, y + 8, 3, 3))
                        pixel_rect(self.canvas, GOLD, (x + 1, y + 9, 1, 1))
        for i, nx in enumerate(self.ninho_x):
            pixel_rect(self.canvas, agua, (nx - 15, GOAL_ROW + 1, 30, TILE - 1))
            pixel_rect(self.canvas, agua_d, (nx - 15, GOAL_ROW + 1, 30, 2))
            pygame.draw.ellipse(self.canvas, (60, 150, 70), (nx - 11, GOAL_ROW + 4, 22, 13))
            pygame.draw.ellipse(self.canvas, (90, 185, 85), (nx - 9, GOAL_ROW + 5, 18, 9))
            pygame.draw.line(self.canvas, agua, (nx, GOAL_ROW + 10), (nx + 9, GOAL_ROW + 6), 2)
            if self.ninhos[i]:
                mini = pygame.transform.scale(self.frog.build_sprite(), (18, 16))
                self.canvas.blit(mini, (nx - 9, GOAL_ROW + 2))
            elif self.mosca and self.mosca[0] == i:
                fy = GOAL_ROW + 8 + int(math.sin(self.water_time * 10) * 2)
                pixel_rect(self.canvas, INK, (nx - 2, fy, 4, 3))
                pixel_rect(self.canvas, WHITE, (nx - 4, fy - 2, 3, 2))
                pixel_rect(self.canvas, WHITE, (nx + 1, fy - 2, 3, 2))

    def draw_noite(self):
        if not self.cfg["noite"]:
            return
        escuro = pygame.Surface((VW, VH), pygame.SRCALPHA)
        escuro.fill((4, 8, 30, 215))
        cx, cy = self.frog.rect.center
        for r, a in ((70, 150), (55, 90), (42, 30), (32, 0)):
            pygame.draw.circle(escuro, (4, 8, 30, a), (cx, cy), r)
        for nx in self.ninho_x:
            pygame.draw.circle(escuro, (4, 8, 30, 120), (nx, GOAL_ROW + 10), 16)
        self.canvas.blit(escuro, (0, 0))
        t = self.water_time
        for i in range(14):
            fx = (i * 97 + t * 14 * (1 if i % 2 else -1)) % VW
            fy = 40 + (i * 53) % 280 + math.sin(t * 2 + i) * 6
            if math.sin(t * 3 + i * 1.7) > 0:
                pixel_rect(self.canvas, (220, 255, 120), (int(fx), int(fy), 2, 2))

    def draw_ui(self):
        pixel_rect(self.canvas, INK, (0, 0, VW, TILE))
        pixel_rect(self.canvas, GRASS_LIGHT, (0, TILE - 1, VW, 1))
        largura = int(VW * max(0, self.tempo) / self.cfg["tempo"])
        pixel_rect(self.canvas, RED if self.tempo <= 8 else GOLD, (0, TILE - 2, largura, 2))
        y = 4
        self.texto(f"VIDAS {self.frog.lives}", self.FONT, 6, y, WHITE)
        self.texto(f"PONTOS {self.frog.score}", self.FONT, VW * 0.14, y, GOLD)
        if self.message_timer > 0 and self.state in ("playing", "dying", "clear"):
            self.texto(self.message, self.FONT, VW / 2, y, GOLD, "midtop")
        else:
            self.texto(f"FASE {self.frog.level} - {self.cfg['nome']}", self.FONT, VW / 2, y, FROG_LIGHT, "midtop")
        self.texto(f"RECORDE {max(self.recorde, self.frog.score)}", self.FONT, VW * 0.74, y, WHITE)
        self.texto(f"TEMPO {math.ceil(self.tempo)}", self.FONT, VW - 6, y, RED if self.tempo <= 8 else WHITE, "topright")

    def draw_overlay(self, color):
        overlay = pygame.Surface((VW, VH), pygame.SRCALPHA)
        overlay.fill(color)
        self.canvas.blit(overlay, (0, 0))

    def caixa(self, y, h):
        w = 300
        x = (VW - w) // 2
        caixa = pygame.Surface((w, h), pygame.SRCALPHA)
        caixa.fill((8, 20, 26, 225))
        self.canvas.blit(caixa, (x, y))
        pixel_rect(self.canvas, GOLD, (x, y, w, 1))
        pixel_rect(self.canvas, GOLD, (x, y + h - 1, w, 1))

    # ------------------------------------------------------------------
    # LOOP
    # ------------------------------------------------------------------
    def teclas(self, event):
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        if self.state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.novo_jogo()
        elif self.state == "gameover" and event.key in (pygame.K_r, pygame.K_RETURN):
            self.novo_jogo()
        elif self.state == "intro" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.intro_timer = 0
        elif self.state == "playing":
            if event.key in (pygame.K_UP, pygame.K_w): self.frog.request_jump(0, -TILE)
            elif event.key in (pygame.K_DOWN, pygame.K_s): self.frog.request_jump(0, TILE)
            elif event.key in (pygame.K_LEFT, pygame.K_a): self.frog.request_jump(-TILE, 0)
            elif event.key in (pygame.K_RIGHT, pygame.K_d): self.frog.request_jump(TILE, 0)
            elif event.key == pygame.K_p: self.state = "pause"
        elif self.state == "pause" and event.key in (pygame.K_p, pygame.K_RETURN, pygame.K_SPACE):
            self.state = "playing"

    def check_frog(self):
        fr = self.frog.rect
        for m in self.movers:
            if m.kind == "snake" and fr.colliderect(m.rect):
                self.begin_death("A COBRA PEGOU O SAPO!")
                return
        if self.is_water(fr.centery):
            hits = [m for m in self.movers if m.kind != "snake" and fr.colliderect(m.rect)]
            gators = [m for m in hits if m.kind == "gator"]
            seguros = [m for m in hits if m.safe]
            afundou = [m for m in hits if m.kind == "turtle" and not m.safe]
            if gators:
                self.begin_death("O JACARE PEGOU O SAPO!")
            elif seguros:
                self.frog.riding = max(seguros, key=lambda m: fr.clip(m.rect).width)
            elif afundou:
                self.begin_death("A TARTARUGA MERGULHOU!")
            else:
                self.begin_death("O SAPO CAIU NA AGUA!")
        if self.state == "playing" and self.frog.y <= GOAL_Y + 1:
            self.chegou_no_topo()

    def update(self, dt):
        self.water_time += dt
        if self.state in ("playing", "dying", "intro", "title", "clear"):
            for mover in self.movers:
                mover.update(dt)

        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "playing"

        elif self.state == "playing":
            self.frog.update(dt)
            self.frog.riding = None
            if self.frog.jump >= 1:
                self.check_frog()
            if self.state == "playing" and (self.frog.rect.centerx < 0 or self.frog.rect.centerx > VW):
                self.begin_death("A CORRENTEZA LEVOU O SAPO!")
            if self.state == "playing":
                self.tempo -= dt
                if self.tempo <= 0:
                    self.tempo = 0
                    self.frog.invuln = 0
                    self.begin_death("ACABOU O TEMPO!")
            if self.mosca:
                self.mosca = (self.mosca[0], self.mosca[1] - dt)
                if self.mosca[1] <= 0:
                    self.mosca = None
            else:
                self.mosca_timer -= dt
                livres = [i for i, ok in enumerate(self.ninhos) if not ok]
                if self.mosca_timer <= 0 and livres:
                    self.mosca = (random.choice(livres), 5.0)
                    self.mosca_timer = random.uniform(6, 11)

        elif self.state == "dying":
            self.death_timer -= dt
            self.frog.sink = min(9, self.frog.sink + dt * 12)
            if self.death_timer <= 0:
                self.finish_death()

        elif self.state == "clear":
            self.clear_timer -= dt
            if random.random() < 0.3:
                self.festa(random.uniform(0, VW), random.uniform(40, 300), amount=6)
            if self.clear_timer <= 0:
                self.iniciar_fase(self.frog.level + 1)

        self.message_timer = max(0, self.message_timer - dt)
        self.shake = max(0, self.shake - dt)
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for r in self.ripples:
            r.update(dt)
        self.ripples = [r for r in self.ripples if r.age <= r.life]

    def draw(self):
        self.draw_map()
        for mover in self.movers:
            mover.draw(self.canvas)
        for ripple in self.ripples:
            ripple.draw(self.canvas)
        if self.state == "dying":
            self.frog.draw(self.canvas, alpha=max(0, int(255 * self.death_timer / 1.05)), sink=self.frog.sink)
        elif self.state not in ("title", "gameover"):
            self.frog.draw(self.canvas)
        for particle in self.particles:
            particle.draw(self.canvas)
        self.draw_noite()
        self.draw_ui()

        cy = VH // 2
        if self.state == "title":
            self.draw_overlay((6, 20, 24, 200))
            hero = pygame.transform.scale(self.frog.build_sprite(), (104, 92))
            self.canvas.blit(hero, (VW // 2 - 52, 58))
            self.text_center("SAPO AVENTUREIRO", self.BIG, 162, FROG_BELLY)
            self.text_center("TRAVESSIA PIXEL - FASES INFINITAS", self.FONT, 192, FROG_LIGHT)
            self.text_center("Troncos e tartarugas sao seguros. Jacares, cobras e agua nao.", self.SMALL, 214, WHITE)
            self.text_center("Chegue numa vitoria-regia no topo para passar de fase. Mosca vale +200.", self.SMALL, 228, WHITE)
            self.text_center(f"RECORDE: {self.recorde}", self.FONT, 250, GOLD)
            self.text_center("[ ENTER ] JOGAR", self.FONT + 2, 276, GOLD)
            self.text_center("WASD / SETAS  -  P PAUSA  -  ESC SAIR", self.SMALL, 304, WHITE)
        elif self.state == "intro":
            self.caixa(cy - 46, 92)
            self.text_center(f"FASE {self.frog.level}", self.FONT + 2, cy - 38, GOLD)
            self.text_center(self.cfg["nome"], self.BIG, cy - 20, FROG_BELLY)
            self.text_center(self.cfg["dica"], self.SMALL, cy + 18, WHITE)
        elif self.state == "clear":
            self.caixa(cy - 36, 72)
            self.text_center("FASE COMPLETA!", self.BIG, cy - 28, GOLD)
            self.text_center(f"BONUS +{self.ultimo_bonus}   -   PROXIMA: FASE {self.frog.level + 1}", self.FONT, cy + 10, WHITE)
        elif self.state == "pause":
            self.draw_overlay((6, 20, 24, 150))
            self.text_center("PAUSADO", self.BIG, cy - 20, GOLD)
            self.text_center("P PARA CONTINUAR", self.FONT, cy + 12, WHITE)
        elif self.state == "gameover":
            self.draw_overlay((35, 5, 8, 215))
            self.text_center("FIM DE JOGO", self.BIG, cy - 80, RED)
            self.text_center(f"PONTUACAO: {self.frog.score}", self.FONT + 1, cy - 38, WHITE)
            self.text_center(f"FASE ALCANCADA: {self.frog.level} - {self.cfg['nome']}", self.FONT, cy - 18, WHITE)
            if self.novo_recorde:
                self.text_center("NOVO RECORDE!", self.FONT + 2, cy + 6, FROG_BELLY)
            else:
                self.text_center(f"RECORDE: {self.recorde}", self.FONT, cy + 6, GOLD)
            self.text_center("R / ENTER PARA RECOMECAR  -  ESC PARA SAIR", self.SMALL, cy + 40, WHITE)

        scaled = pygame.transform.scale(self.canvas, (self.out_w, self.out_h))
        dx = dy = 0
        if self.shake > 0:
            dx, dy = random.randint(-5, 5), random.randint(-5, 5)
        self.window.fill(INK)
        self.window.blit(scaled, (self.ox + dx, self.oy + dy))
        self.desenhar_textos(dx, dy)
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.teclas(event)
            self.update(dt)
            self.draw()
