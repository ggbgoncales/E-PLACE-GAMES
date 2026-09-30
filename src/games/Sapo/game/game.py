import sys
import pygame
import random
from settings import *
from game.entities.frog import Frog
from game.entities.mover import Mover
from game.entities.fx import Particle, Ripple

class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Sapo Aventureiro Pixel")
        self.canvas = pygame.Surface((VW, VH))
        self.clock = pygame.time.Clock()
        
        self.FONT = pygame.font.SysFont("consolas", 8, bold=True)
        self.SMALL = pygame.font.SysFont("consolas", 6, bold=True)
        self.BIG = pygame.font.SysFont("consolas", 16, bold=True)

        self.frog = Frog()
        self.movers = self.make_level(1)
        self.particles = []
        self.ripples = []
        
        self.state = "title"
        self.death_reason = ""
        self.death_timer = 0
        self.message = ""
        self.message_timer = 0
        self.water_time = 0
        self.shake = 0

    def make_level(self, level):
        multiplier = min(1 + (level - 1) * 0.12, 1.65)
        specs = [
            (40, 27, [("log", -20, 70), ("gator", 88, 45), ("log", 170, 82), ("log", 300, 62)]),
            (60, -33, [("log", 5, 60), ("gator", 95, 48), ("log", 170, 72), ("gator", 272, 46), ("log", 340, 66)]),
            (80, 38, [("gator", -35, 46), ("log", 35, 86), ("log", 170, 63), ("gator", 263, 46), ("log", 337, 76)]),
            (120, -29, [("log", -50, 82), ("gator", 65, 46), ("log", 137, 80), ("log", 260, 70), ("gator", 357, 46)]),
            (140, 35, [("log", -35, 64), ("gator", 60, 47), ("log", 138, 84), ("gator", 260, 47), ("log", 337, 73)]),
            (160, -40, [("gator", -28, 47), ("log", 50, 80), ("log", 177, 66), ("gator", 273, 47), ("log", 347, 78)]),
        ]
        return [Mover(x, y, width, speed * multiplier, kind) for y, speed, items in specs for kind, x, width in items]

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
        else:
            self.frog.reset()
            self.state = "playing"
            self.message = self.death_reason
            self.message_timer = 1.1

    def text_center(self, text, font, y, color=WHITE):
        image = font.render(text, False, color)
        self.canvas.blit(image, (VW // 2 - image.get_width() // 2, y))

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
        self.canvas.blit(self.FONT.render(f"VIDAS {self.frog.lives}", False, WHITE), (5, 4))
        self.canvas.blit(self.FONT.render(f"PONTOS {self.frog.score}", False, GOLD), (75, 4))
        level_text = self.FONT.render(f"NIVEL {self.frog.level}", False, WHITE)
        self.canvas.blit(level_text, (VW - level_text.get_width() - 5, 4))

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
                    elif self.state in ("gameover", "win") and event.key == pygame.K_r:
                        self.frog = Frog()
                        self.movers = self.make_level(1)
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

                if self.frog.y < 19:
                    self.frog.score += 250
                    self.frog.level += 1
                    if self.frog.level > 5:
                        self.state = "win"
                    else:
                        self.frog.reset()
                        self.movers = self.make_level(self.frog.level)
                        self.message = f"NIVEL {self.frog.level}: MAIS RAPIDO!"
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
                self.text_center("TRONCOS SAO SEGUROS", self.SMALL, 169, WHITE)
                self.text_center("JACARES NAO SAO", self.SMALL, 179, RED)
                self.text_center("[ ENTER ] JOGAR", self.FONT, 199, GOLD)
                self.text_center("WASD OU SETAS", self.SMALL, 216, WHITE)
            elif self.state == "gameover":
                self.draw_overlay((35, 5, 8, 220))
                self.text_center("FIM DE JOGO", self.BIG, 77, RED)
                self.text_center(f"PONTUACAO: {self.frog.score}", self.FONT, 112, WHITE)
                self.text_center("PRESSIONE R", self.FONT, 137, GOLD)
                self.text_center("PARA RECOMECAR", self.SMALL, 152, WHITE)
            elif self.state == "win":
                self.draw_overlay((4, 30, 20, 212))
                self.text_center("TRAVESSIA", self.BIG, 68, FROG_LIGHT)
                self.text_center("CONCLUIDA!", self.BIG, 88, FROG_BELLY)
                self.text_center(f"PONTUACAO: {self.frog.score}", self.FONT, 124, GOLD)
                self.text_center("PRESSIONE R PARA JOGAR", self.SMALL, 153, WHITE)
            elif self.message_timer > 0:
                pixel_rect(self.canvas, INK, (54, 25, 212, 18))
                pixel_rect(self.canvas, GOLD, (54, 25, 212, 1))
                self.text_center(self.message, self.FONT, 31, GOLD)

            scaled = pygame.transform.scale(self.canvas, (W, H))
            if self.shake > 0:
                offset_x, offset_y = random.randint(-5, 5), random.randint(-5, 5)
                self.window.fill(INK)
                self.window.blit(scaled, (offset_x, offset_y))
            else:
                self.window.blit(scaled, (0, 0))

            pygame.display.flip()