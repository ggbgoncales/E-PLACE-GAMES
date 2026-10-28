import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
import os
import sys
import json
import pygame
import random

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
from game.entities.mover import Mover
from game.entities.fx import Particle, Ripple

class Game:
    def __init__(self):
        pygame.init()
        # Tela cheia: o cenario continua pixel art (320x240 ampliado),
        # mas os TEXTOS sao desenhados direto na tela, com fonte normal e nitida.
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
        
        # tamanhos "virtuais" (na escala 320x240); viram fonte grande e nitida
        self.FONT = 8
        self.SMALL = 6
        self.BIG = 16

        self.recorde = carregar_recorde()
        self.novo_recorde = False
        self.frog = Frog()
        self.movers = self.make_level(1)
        self.tempo = self.tempo_nivel(1)
        self.particles = []
        self.ripples = []
        
        self.state = "title"
        self.death_reason = ""
        self.death_timer = 0
        self.message = ""
        self.message_timer = 0
        self.water_time = 0
        self.shake = 0

    # ------------------------------------------------------------------
    # MODO INFINITO: cada nivel e gerado na hora e fica mais dificil
    # ------------------------------------------------------------------
    def tempo_nivel(self, level):
        """Tempo para atravessar: comeca em 30s e cai ate 14s."""
        return max(14.0, 30.0 - (level - 1) * 1.5)

    def make_level(self, level):
        # velocidade sobe 14% por nivel (sem limite ate 3x)
        mult = min(1.0 + (level - 1) * 0.14, 3.0)
        # chance de jacare: 20% no nivel 1 ate 55%
        chance_jacare = min(0.20 + (level - 1) * 0.05, 0.55)
        # troncos encolhem: 60-90 no nivel 1 ate 34-50
        log_min = max(34, 60 - (level - 1) * 4)
        log_max = max(50, 90 - (level - 1) * 5)
        # buracos de agua entre os objetos aumentam
        gap_min = min(14 + (level - 1) * 2, 34)
        gap_max = min(34 + (level - 1) * 4, 70)

        movers = []
        direcao = random.choice((1, -1))
        for y in sorted(LANES):
            speed = random.uniform(26, 40) * mult * direcao
            direcao = -direcao
            x = random.uniform(-40, 0)
            logs_na_faixa = 0
            itens = []
            while x < VW + 20:
                # garante pelo menos 2 troncos por faixa (sempre da para passar)
                if random.random() < chance_jacare and logs_na_faixa >= 1 and itens and itens[-1][0] != "gator":
                    itens.append(("gator", x, 46))
                    x += 46
                else:
                    w = random.randint(log_min, log_max)
                    itens.append(("log", x, w))
                    logs_na_faixa += 1
                    x += w
                x += random.uniform(gap_min, gap_max)
            if logs_na_faixa < 2:
                itens.append(("log", x, log_max))
            movers += [Mover(ix, y, w, speed, kind) for kind, ix, w in itens]
        return movers

    def is_water(self, y):
        return any(row <= y < row + TILE for row in LANES)

    def splash(self, x, y, amount=18):
        for _ in range(amount):
            self.particles.append(Particle(x, y, random.choice((WATER_FOAM, WATER_LIGHT, WHITE))))
        self.ripples.extend((Ripple(x, y), Ripple(x, y, 0.18), Ripple(x, y, 0.36)))

    def begin_death(self, reason):
        if self.frog.invuln > 0 or self.state != "playing": return
        self.state = "dying"
        self.death_reason = reason
        self.death_timer = 1.05
        self.shake = 0.28
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
            self.tempo = self.tempo_nivel(self.frog.level)
            self.state = "playing"
            self.message = self.death_reason
            self.message_timer = 1.1

    def fonte(self, tamanho):
        px = max(10, int(tamanho * self.scale))
        if px not in self._fontes:
            caminho = None
            for nome in ("ubuntu", "notosans", "dejavusans", "liberationsans", "arial", "verdana"):
                caminho = pygame.font.match_font(nome, bold=True)
                if caminho:
                    break
            self._fontes[px] = pygame.font.Font(caminho, px) if caminho else pygame.font.Font(None, int(px * 1.35))
        return self._fontes[px]

    def texto(self, text, tamanho, x, y, color=WHITE, anchor="topleft"):
        """Agenda um texto (coordenadas 320x240) para ser desenhado nitido na tela."""
        self.textos.append((text, tamanho, x, y, color, anchor))

    def text_center(self, text, tamanho, y, color=WHITE):
        self.texto(text, tamanho, VW / 2, y, color, "midtop")

    def desenhar_textos(self, dx, dy):
        for text, tamanho, x, y, color, anchor in self.textos:
            fonte = self.fonte(tamanho)
            pos = (self.ox + dx + x * self.scale, self.oy + dy + y * self.scale)
            sombra = fonte.render(text, True, INK)
            self.window.blit(sombra, sombra.get_rect(**{anchor: (pos[0] + 2, pos[1] + 2)}))
            img = fonte.render(text, True, color)
            self.window.blit(img, img.get_rect(**{anchor: pos}))
        self.textos.clear()

    def draw_map(self):
        self.water_time += 1 / FPS
        for y in range(0, VH, TILE):
            if y in LANES:
                pixel_rect(self.canvas, WATER, (0, y, VW, TILE))
                pixel_rect(self.canvas, WATER_DARK, (0, y, VW, 2))
                wave = int(self.water_time * 18 + y) % 30
                for x in range(-30, VW + 30, 30):
                    xx = x + wave
                    pixel_rect(self.canvas, WATER_LIGHT, (xx, y + 6, 10, 1))
                    pixel_rect(self.canvas, WATER_LIGHT, (xx + 3, y + 5, 6, 1))
                    pixel_rect(self.canvas, WATER_DARK, (xx + 15, y + 14, 8, 1))
            elif y == 100:
                pixel_rect(self.canvas, SAND, (0, y, VW, TILE))
                pixel_rect(self.canvas, SAND_LIGHT, (0, y, VW, 2))
                for x in range(5, VW, 23):
                    pixel_rect(self.canvas, SAND_DARK, (x, y + 8 + (x % 7), 2, 1))
            else:
                base = GRASS if y % 40 else GRASS_DARK
                pixel_rect(self.canvas, base, (0, y, VW, TILE))
                pixel_rect(self.canvas, GRASS_DARK, (0, y, VW, 2))
                for x in range(4, VW, 19):
                    yy = y + 5 + ((x * 3 + y) % 11)
                    pixel_rect(self.canvas, GRASS_LIGHT, (x, yy, 1, 4))
                    pixel_rect(self.canvas, GRASS_LIGHT, (x + 1, yy, 1, 2))
        for x in (35, 96, 158, 221, 283):
            pixel_rect(self.canvas, GRASS_DARK, (x - 8, 6, 16, 7))
            pixel_rect(self.canvas, GRASS, (x - 10, 9, 20, 5))
            pixel_rect(self.canvas, FLOWER, (x - 1, 4, 3, 3))
            pixel_rect(self.canvas, GOLD, (x, 5, 1, 1))

    def draw_ui(self):
        pixel_rect(self.canvas, INK, (0, 0, VW, 15))
        pixel_rect(self.canvas, GRASS_LIGHT, (0, 14, VW, 1))
        self.texto(f"VIDAS {self.frog.lives}", self.FONT, 4, 3, WHITE)
        self.texto(f"PONTOS {self.frog.score}", self.FONT, 62, 3, GOLD)
        cor_tempo = RED if self.tempo <= 5 else WHITE
        self.texto(f"TEMPO {int(self.tempo) + 1}", self.FONT, 158, 3, cor_tempo)
        self.texto(f"NIVEL {self.frog.level}", self.FONT, VW - 4, 3, WHITE, "topright")
        # barra de tempo
        total = self.tempo_nivel(self.frog.level)
        largura = int(VW * max(0, self.tempo) / total)
        pixel_rect(self.canvas, RED if self.tempo <= 5 else GOLD, (0, 14, largura, 1))

    def draw_overlay(self, color):
        overlay = pygame.Surface((VW, VH), pygame.SRCALPHA)
        overlay.fill(color)
        self.canvas.blit(overlay, (0, 0))

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if self.state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "playing"
                    elif self.state == "gameover" and event.key == pygame.K_r:
                        self.frog = Frog()
                        self.movers = self.make_level(1)
                        self.tempo = self.tempo_nivel(1)
                        self.novo_recorde = False
                        self.particles.clear()
                        self.ripples.clear()
                        self.state = "playing"
                    elif self.state == "playing":
                        if event.key in (pygame.K_UP, pygame.K_w): self.frog.request_jump(0, -TILE)
                        elif event.key in (pygame.K_DOWN, pygame.K_s): self.frog.request_jump(0, TILE)
                        elif event.key in (pygame.K_LEFT, pygame.K_a): self.frog.request_jump(-TILE, 0)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d): self.frog.request_jump(TILE, 0)

            if self.state in ("playing", "dying"):
                for mover in self.movers: mover.update(dt)

            if self.state == "playing":
                self.frog.update(dt)
                self.frog.riding = None

                if self.frog.jump >= 1 and self.is_water(self.frog.rect.centery):
                    hits = [m for m in self.movers if self.frog.rect.colliderect(m.rect)]
                    gators = [m for m in hits if m.kind == "gator"]
                    logs = [m for m in hits if m.kind == "log"]
                    if gators: self.begin_death("O JACARE PEGOU O SAPO!")
                    elif logs: self.frog.riding = max(logs, key=lambda m: self.frog.rect.clip(m.rect).width)
                    else: self.begin_death("O SAPO CAIU NA AGUA!")

                if self.frog.x < -18 or self.frog.x > VW + 5:
                    self.begin_death("A CORRENTEZA LEVOU O SAPO!")

                # contagem regressiva
                self.tempo -= dt
                if self.tempo <= 0:
                    self.tempo = 0
                    self.begin_death("ACABOU O TEMPO!")

                if self.state == "playing" and self.frog.y < 19:
                    # bonus: nivel + tempo que sobrou
                    self.frog.score += 250 + 50 * (self.frog.level - 1) + int(self.tempo) * 10
                    self.frog.level += 1
                    self.frog.reset()
                    self.movers = self.make_level(self.frog.level)
                    self.tempo = self.tempo_nivel(self.frog.level)
                    if self.frog.level % 5 == 0 and self.frog.lives < 5:
                        self.frog.lives += 1
                        self.message = f"NIVEL {self.frog.level}: +1 VIDA!"
                    else:
                        self.message = f"NIVEL {self.frog.level}: MAIS DIFICIL!"
                    self.message_timer = 1.5

            elif self.state == "dying":
                self.death_timer -= dt
                self.frog.sink = min(9, self.frog.sink + dt * 12)
                if self.death_timer <= 0: self.finish_death()

            self.message_timer = max(0, self.message_timer - dt)
            self.shake = max(0, self.shake - dt)

            for particle in self.particles[:]:
                particle.update(dt)
                if particle.life <= 0: self.particles.remove(particle)
            for ripple in self.ripples[:]:
                ripple.update(dt)
                if ripple.age > ripple.life: self.ripples.remove(ripple)

            self.draw_map()
            for mover in self.movers: mover.draw(self.canvas)
            for ripple in self.ripples: ripple.draw(self.canvas)

            if self.state == "dying":
                self.frog.draw(self.canvas, alpha=max(0, int(255 * self.death_timer / 1.05)), sink=self.frog.sink)
            else:
                self.frog.draw(self.canvas)

            for particle in self.particles: particle.draw(self.canvas)
            self.draw_ui()

            if self.state == "title":
                self.draw_overlay((6, 20, 24, 218))
                old_blink, old_mouth = self.frog.blink, self.frog.mouth
                self.frog.blink, self.frog.mouth = 0, 0
                hero = self.frog.build_sprite()
                hero = pygame.transform.scale(hero, (78, 69))
                self.canvas.blit(hero, (VW // 2 - 39, 43))
                self.frog.blink, self.frog.mouth = old_blink, old_mouth
                self.text_center("SAPO AVENTUREIRO", self.BIG, 122, FROG_BELLY)
                self.text_center("TRAVESSIA PIXEL", self.FONT, 148, FROG_LIGHT)
                self.text_center("TRONCOS SAO SEGUROS - JACARES NAO", self.SMALL, 167, WHITE)
                self.text_center(f"MODO INFINITO  -  RECORDE: {self.recorde}", self.SMALL, 179, GOLD)
                self.text_center("[ ENTER ] JOGAR", self.FONT, 199, GOLD)
                self.text_center("WASD OU SETAS", self.SMALL, 216, WHITE)
            elif self.state == "gameover":
                self.draw_overlay((35, 5, 8, 220))
                self.text_center("FIM DE JOGO", self.BIG, 62, RED)
                self.text_center(f"PONTUACAO: {self.frog.score}", self.FONT, 98, WHITE)
                self.text_center(f"NIVEL ALCANCADO: {self.frog.level}", self.FONT, 113, WHITE)
                if self.novo_recorde:
                    self.text_center("NOVO RECORDE!", self.FONT, 130, FROG_BELLY)
                else:
                    self.text_center(f"RECORDE: {self.recorde}", self.FONT, 130, GOLD)
                self.text_center("R PARA RECOMECAR  -  ESC PARA SAIR", self.SMALL, 156, WHITE)
            elif self.message_timer > 0:
                pixel_rect(self.canvas, INK, (54, 25, 212, 18))
                pixel_rect(self.canvas, GOLD, (54, 25, 212, 1))
                self.text_center(self.message, self.FONT, 31, GOLD)

            scaled = pygame.transform.scale(self.canvas, (self.out_w, self.out_h))
            offset_x = offset_y = 0
            if self.shake > 0:
                offset_x, offset_y = random.randint(-5, 5), random.randint(-5, 5)
            self.window.fill(INK)
            self.window.blit(scaled, (self.ox + offset_x, self.oy + offset_y))
            self.desenhar_textos(offset_x, offset_y)
            pygame.display.flip()
