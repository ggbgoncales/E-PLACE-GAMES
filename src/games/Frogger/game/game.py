import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
import sys
import json
import math
import random
import pygame
from utils import ui_arcade as ui
from gamepad import XboxController, draw_controller_text, draw_controls_table

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



def fonte_retro(tamanho, titulo):
    """Titulos em Press Start 2P e textos em VT323 (assets/fonts). Sem os arquivos, usa fonte do sistema."""
    import os
    nome = "PressStart2P-Regular.ttf" if titulo else "VT323-Regular.ttf"
    pasta = os.path.abspath(os.path.dirname(__file__))
    for _ in range(8):
        caminho = os.path.join(pasta, "assets", "fonts", nome)
        if os.path.exists(caminho):
            return pygame.font.Font(caminho, max(8, int(tamanho)))
        pasta = os.path.dirname(pasta)
    return pygame.font.SysFont("arial,helveticaneue,dejavusans", int(tamanho), bold=titulo)


class Game:
    def __init__(self):
        pygame.init()
        self.controle = XboxController()
        # Alguns drivers/versoes do Windows podem retornar lista vazia no get_desktop_sizes.
        try:
            tamanhos = pygame.display.get_desktop_sizes()
            tamanho_tela = tamanhos[0] if tamanhos else (pygame.display.Info().current_w, pygame.display.Info().current_h)
            if not tamanho_tela[0] or not tamanho_tela[1]:
                raise RuntimeError("resolucao indisponivel")
        except Exception:
            info = pygame.display.Info()
            tamanho_tela = (info.current_w or 1280, info.current_h or 720)
        self.window = pygame.display.set_mode(tamanho_tela, pygame.NOFRAME)
        ww, wh = self.window.get_size()
        self.scale = min(ww / VW, wh / VH)
        self.out_w, self.out_h = int(VW * self.scale), int(VH * self.scale)
        self.ox, self.oy = (ww - self.out_w) // 2, (wh - self.out_h) // 2
        self.textos = []
        self._fontes = {}
        pygame.display.set_caption("Frogger")
        self.canvas = pygame.Surface((VW, VH))
        self.clock = pygame.time.Clock()
        self.FONT = 10
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
        self.show_controls = False
        self.title_menu_idx = 0

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
            if tamanho >= 12:   # titulos: Press Start 2P
                self._fontes[px] = fonte_retro(max(8, px * 0.55), True)
            else:               # textos e HUD: VT323
                self._fontes[px] = fonte_retro(px * 1.35, False)
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

    def caixa(self, y, h, cor=None):
        """Caixa central das mensagens (fase, pausa, fim de jogo), no mesmo estilo dos menus."""
        cor = cor or ui.AMARELO
        w = 300
        rect = pygame.Rect((VW - w) // 2, y, w, h)
        ui.brilho(self.canvas, rect, cor, intensidade=60, raio=6, camadas=2, passo=4, espessura=1)
        ui.painel(self.canvas, rect, borda=cor, fundo=ui.PAINEL, raio=6, largura_borda=1, alfa=235)

    # ------------------------------------------------------------------
    # LOOP
    # ------------------------------------------------------------------
    def teclas(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.show_controls:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_F1, pygame.K_F2, pygame.K_TAB, pygame.K_y):
                self.show_controls = False
            return

        # Atalho universal: Y (Xbox), triangulo (PlayStation), X (Switch).
        if self.state == "title" and event.key in (pygame.K_y, pygame.K_F1, pygame.K_F2, pygame.K_TAB):
            self.show_controls = True
            return

        if self.state == "title":
            if event.key in (pygame.K_UP, pygame.K_w):
                self.title_menu_idx = (self.title_menu_idx - 1) % 3
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.title_menu_idx = (self.title_menu_idx + 1) % 3
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.title_menu_idx == 0:
                    self.novo_jogo()
                elif self.title_menu_idx == 1:
                    self.show_controls = True
                else:
                    pygame.quit()
                    sys.exit()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            return

        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        if self.state == "gameover" and event.key in (pygame.K_r, pygame.K_RETURN):
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

    # ------------------------------------------------------------------
    # MENUS E MENSAGENS (na resolução da janela, com os componentes do launcher)
    # ------------------------------------------------------------------
    def _ui_estado(self):
        area = pygame.Rect(self.ox, self.oy, self.out_w, self.out_h)
        h, w = area.h, area.w
        t = pygame.time.get_ticks() / 1000

        def f8(v):                      # Press Start 2P fica nítida em múltiplos de 8
            return ui.fonte(max(8, int(round(v / 8.0)) * 8), True)

        def vt(v):
            return ui.fonte(max(14, int(v)), False)

        tecla = ui.fonte(max(10, int(0.016 * h)), True)
        legenda = vt(0.034 * h)
        centro = area.centerx

        if self.state == "title":
            painel = pygame.Rect(0, 0, int(0.78 * w), int(0.705 * h))
            painel.midtop = (centro, area.y + int(0.26 * h))
            ui.painel(self.window, painel, borda=ui.LINHA, fundo=ui.PAINEL, raio=int(0.03 * h), alfa=238)
            ui.texto(self.window, f8(0.0625 * h), "FROGGER", ui.VERDE, (centro, area.y + int(0.335 * h)), "center", sombra=True)
            ui.texto(self.window, vt(0.045 * h), "TRAVESSIA PIXEL - FASES INFINITAS", ui.AMARELO, (centro, area.y + int(0.395 * h)), "center")
            ui.texto(self.window, vt(0.036 * h), "Troncos e tartarugas sao seguros. Jacares, cobras e agua nao.", ui.TEXTO,
                     (centro, area.y + int(0.455 * h)), "center")
            ui.texto(self.window, vt(0.036 * h), "Chegue na vitoria-regia no topo para passar de fase. Mosca vale +200.", ui.TEXTO,
                     (centro, area.y + int(0.505 * h)), "center")
            ui.texto(self.window, f8(0.03 * h), f"RECORDE  {self.recorde}", ui.AMARELO, (centro, area.y + int(0.567 * h)), "center")
            ui.lista_menu(self.window, ("JOGAR", "CONTROLES", "SAIR"), self.title_menu_idx, ui.VERDE, f8(0.032 * h),
                          centro, area.y + int(0.612 * h), int(0.46 * w), int(0.078 * h), int(0.014 * h), t,
                          cores=(ui.VERDE, ui.CIANO, ui.VERMELHO), raio=int(0.022 * h))
            ui.rodape_atalhos(self.window, tecla, legenda,
                              [("SETAS", "Navegar"), ("ENTER", "Confirmar"), ("F1", "Controles"), ("ESC", "Sair")],
                              area.y + int(0.9 * h), self.window.get_width())
            if self.controle.connected:
                draw_controller_text(self.window, vt(0.032 * h),
                                     f"CONFIRMAR: {self.controle.button_icon(0)}   VOLTAR: {self.controle.button_icon(1)}   CONTROLES: {self.controle.button_icon(3)}",
                                     ui.CIANO, (centro, area.y + int(0.955 * h)), self.controle, "center")
        elif self.state == "pause":
            r = pygame.Rect(0, 0, int(0.5 * w), int(0.25 * h))
            r.center = area.center
            ui.modal(self.window, r, "PAUSADO", ui.AMARELO, f8(0.05 * h), escurecer=0)
            ui.rodape_atalhos(self.window, tecla, legenda, [("P", "Continuar"), ("ESC", "Menu")], r.bottom - int(0.085 * h), self.window.get_width())
        elif self.state == "gameover":
            r = pygame.Rect(0, 0, int(0.6 * w), int(0.66 * h))
            r.center = area.center
            ui.modal(self.window, r, "FIM DE JOGO", ui.VERMELHO, f8(0.05 * h), escurecer=0)
            cartoes = (("PONTUACAO", str(self.frog.score), ui.TEXTO), ("FASE", str(self.frog.level), ui.CIANO),
                       ("RECORDE", str(self.recorde), ui.AMARELO))
            cw = (r.w - int(0.06 * w)) // 3
            for k, (rot, val, cor) in enumerate(cartoes):
                cr = pygame.Rect(r.x + int(0.02 * w) + k * (cw + int(0.01 * w)), r.y + int(0.2 * h), cw, int(0.2 * h))
                ui.painel(self.window, cr, borda=ui.LINHA, fundo=ui.PAINEL2, raio=int(0.02 * h))
                ui.texto(self.window, vt(0.036 * h), rot, ui.TEXTO3, (cr.centerx, cr.y + int(0.05 * h)), "center")
                ui.texto(self.window, f8(0.04 * h), val, cor, (cr.centerx, cr.y + int(0.13 * h)), "center")
            ui.texto(self.window, vt(0.04 * h), f"Cenario: {self.cfg['nome']}", ui.TEXTO2, (centro, r.y + int(0.45 * h)), "center")
            if self.novo_recorde:
                ui.texto(self.window, f8(0.03 * h), "NOVO RECORDE!", ui.VERDE, (centro, r.y + int(0.5 * h)), "center")
            ui.rodape_atalhos(self.window, tecla, legenda, [("R", "Recomecar"), ("ESC", "Sair")], r.bottom - int(0.1 * h), self.window.get_width())
        elif self.state == "intro":
            r = pygame.Rect(0, 0, int(0.66 * w), int(0.28 * h))
            r.center = area.center
            ui.modal(self.window, r, f"FASE {self.frog.level}", ui.CIANO, f8(0.05 * h), escurecer=0)
            ui.texto(self.window, f8(0.03 * h), self.cfg["nome"], ui.VERDE, (centro, r.y + int(0.135 * h)), "center")
            ui.texto(self.window, vt(0.04 * h), self.cfg["dica"], ui.TEXTO, (centro, r.y + int(0.205 * h)), "center")
        elif self.state == "clear":
            r = pygame.Rect(0, 0, int(0.66 * w), int(0.24 * h))
            r.center = area.center
            ui.modal(self.window, r, "FASE COMPLETA!", ui.VERDE, f8(0.045 * h), escurecer=0)
            ui.texto(self.window, vt(0.045 * h), f"Bonus +{self.ultimo_bonus}  -  Proxima: fase {self.frog.level + 1}", ui.TEXTO,
                     (centro, r.y + int(0.165 * h)), "center")

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

        # Menus e mensagens são desenhados depois, na resolução da janela (_ui_estado),
        # para o texto ficar nítido e legível. Aqui só escurecemos o cenário.
        if self.state == "title":
            self.draw_overlay((6, 20, 24, 225))
            hero = pygame.transform.scale(self.frog.build_sprite(), (84, 74))
            self.canvas.blit(hero, (VW // 2 - 42, 14))
        elif self.state == "pause":
            self.draw_overlay((6, 20, 24, 150))
        elif self.state == "gameover":
            self.draw_overlay((35, 5, 8, 215))

        if self.show_controls:
            # A tela do Frogger usa textos desenhados em uma segunda etapa
            # (desenhar_textos). Limpe a fila e o canvas antes da tabela para
            # impedir que o titulo, o HUD e as opcoes do menu aparecam por cima.
            self.textos.clear()
            self.canvas.fill(INK)
            draw_controls_table(
                self.canvas,
                [
                    ('MOVER', 'D-PAD / ANALOGICO', 'D-PAD / ANALOG', 'D-PAD / ANALOG'),
                    ('PULAR / CONFIRMAR', 'X', 'A', 'A'),
                    ('VOLTAR / SAIR', 'O', 'B', 'B'),
                    ('PAUSAR', 'OPTIONS', 'MENU', '+'),
                ],
                title="FROGGER - CONTROLES",
                footer="ESC / ENTER: VOLTAR AO MENU",
            )
        scaled = pygame.transform.scale(self.canvas, (self.out_w, self.out_h))
        dx = dy = 0
        if self.shake > 0:
            dx, dy = random.randint(-5, 5), random.randint(-5, 5)
        self.window.fill(INK)
        self.window.blit(scaled, (self.ox + dx, self.oy + dy))
        self.desenhar_textos(dx, dy)
        if not self.show_controls:
            self._ui_estado()
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            for event in pygame.event.get() + self.controle.poll_keys():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.teclas(event)
            self.update(dt)
            self.draw()
