import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

# ============================================================
# Cobra Neon - jogo completo em um unico arquivo
# Controles: setas/WASD, P/ESC pausa, M som, F11 tela cheia
# Requer: pip install pygame
# ============================================================

WIDTH, HEIGHT = 1100, 720
HUD_W = 260
PLAY_W = WIDTH - HUD_W
CELL = 24
COLS = PLAY_W // CELL
ROWS = HEIGHT // CELL
FPS = 120
SAVE_FILE = Path.home() / ".cobra_neon_recorde.txt"

BG = (7, 11, 22)
PANEL = (12, 20, 36)
GRID = (19, 32, 49)
WHITE = (238, 246, 255)
MUTED = (134, 158, 184)
GREEN = (43, 235, 150)
GREEN_DARK = (18, 145, 101)
CYAN = (45, 210, 255)
PINK = (255, 77, 143)
GOLD = (255, 201, 74)
RED = (255, 77, 91)

pygame.init()
pygame.display.set_caption("Cobra Neon")


def clamp(value, low, high):
    return max(low, min(high, value))


def load_record():
    try:
        return max(0, int(SAVE_FILE.read_text(encoding="utf-8").strip()))
    except Exception:
        return 0


def save_record(value):
    try:
        SAVE_FILE.write_text(str(value), encoding="utf-8")
    except Exception:
        pass


class SilentSound:
    def play(self):
        pass


class SoundBank:
    """Efeitos sintetizados em memoria, sem arquivos externos."""

    def __init__(self):
        self.enabled = True
        self.eat = SilentSound()
        self.turn = SilentSound()
        self.game_over = SilentSound()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            from array import array

            self.eat = self._tone(array, 720, 0.08, 0.3, 980)
            self.turn = self._tone(array, 260, 0.025, 0.08, 300)
            self.game_over = self._tone(array, 240, 0.35, 0.3, 70)
        except Exception:
            pass

    @staticmethod
    def _tone(array_type, start_hz, duration, volume, end_hz):
        sample_rate = 22050
        count = int(sample_rate * duration)
        samples = array_type("h")
        phase = 0.0
        for i in range(count):
            t = i / max(1, count - 1)
            hz = start_hz + (end_hz - start_hz) * t
            phase += 2 * math.pi * hz / sample_rate
            envelope = min(1.0, i / 100) * (1.0 - t) ** 0.7
            samples.append(int(32767 * volume * envelope * math.sin(phase)))
        return pygame.mixer.Sound(buffer=samples)

    def play(self, sound):
        if self.enabled:
            sound.play()


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple
    radius: float

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= dt
        self.radius = max(0, self.radius - dt * 4)

    def draw(self, surface):
        if self.life <= 0 or self.radius <= 0:
            return
        alpha = int(255 * clamp(self.life / 0.7, 0, 1))
        layer = pygame.Surface((int(self.radius * 4 + 4), int(self.radius * 4 + 4)), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*self.color, alpha), layer.get_rect().center, int(self.radius))
        surface.blit(layer, (self.x - layer.get_width() / 2, self.y - layer.get_height() / 2))


class Button:
    def __init__(self, rect, text, action, accent=GREEN):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.accent = accent
        self.hover = 0.0

    def update(self, mouse, dt):
        target = 1.0 if self.rect.collidepoint(mouse) else 0.0
        self.hover += (target - self.hover) * min(1, dt * 12)

    def draw(self, surface, font):
        grow = int(4 * self.hover)
        rect = self.rect.inflate(grow, grow)
        shadow = rect.move(0, 7)
        pygame.draw.rect(surface, (3, 7, 14), shadow, border_radius=16)
        color = tuple(int(PANEL[i] + (self.accent[i] - PANEL[i]) * (0.28 + self.hover * 0.18)) for i in range(3))
        pygame.draw.rect(surface, color, rect, border_radius=16)
        pygame.draw.rect(surface, self.accent, rect, 2, border_radius=16)
        label = font.render(self.text, True, WHITE)
        surface.blit(label, label.get_rect(center=rect.center))


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("segoeui", 18)
        self.font_md = pygame.font.SysFont("segoeui", 25, bold=True)
        self.font_lg = pygame.font.SysFont("segoeui", 50, bold=True)
        self.font_xl = pygame.font.SysFont("segoeui", 76, bold=True)
        self.sounds = SoundBank()
        self.record = load_record()
        self.particles = []
        self.state = "menu"
        self.fullscreen = True
        self.difficulty = 1
        self.difficulties = [
            ("TRANQUILO", 7.0, CYAN),
            ("CLASSICO", 10.0, GREEN),
            ("INSANO", 14.0, PINK),
        ]
        self.buttons = []
        self.reset()
        self.make_menu_buttons()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy), (cx - 3, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = (0, 0)
        self.special_food = None
        self.special_timer = 0.0
        self.move_acc = 0.0
        self.score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.play_time = 0.0
        self.food_pulse = 0.0
        self.blink_timer = random.uniform(1.5, 3.5)
        self.blink = 0.0
        self.tongue_timer = 0.0
        self.shake = 0.0
        self.spawn_food()

    def spawn_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in self.snake]
        if not free:
            self.state = "gameover"
            return
        self.food = random.choice(free)
        if self.score and self.score % 50 == 0 and self.special_food is None:
            candidates = [p for p in free if p != self.food]
            if candidates:
                self.special_food = random.choice(candidates)
                self.special_timer = 7.0

    def make_menu_buttons(self):
        self.buttons = [
            Button((WIDTH // 2 - 155, 420, 310, 62), "JOGAR", "play", GREEN),
            Button((WIDTH // 2 - 155, 498, 310, 55), "DIFICULDADE", "difficulty", CYAN),
            Button((WIDTH // 2 - 155, 569, 310, 55), "SAIR", "quit", PINK),
        ]

    def set_state(self, action):
        if action == "play":
            self.reset()
            self.state = "playing"
        elif action == "difficulty":
            self.difficulty = (self.difficulty + 1) % len(self.difficulties)
        elif action == "quit":
            pygame.quit()
            sys.exit()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.screen = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)


    def add_burst(self, cell, color, count=18):
        x = cell[0] * CELL + CELL / 2
        y = cell[1] * CELL + CELL / 2
        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(45, 160)
            self.particles.append(Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                           random.uniform(0.35, 0.75), color, random.uniform(2, 5)))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif event.key == pygame.K_m:
                self.sounds.enabled = not self.sounds.enabled
            elif self.state == "menu" and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                if self.state == "playing":
                    self.state = "paused"
                elif self.state == "paused":
                    self.state = "playing"
                elif self.state == "gameover":
                    self.state = "menu"
            elif self.state == "menu" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.set_state("play")
            elif self.state == "gameover" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.set_state("play")
            elif self.state == "playing":
                directions = {
                    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
                }
                if event.key in directions:
                    candidate = directions[event.key]
                    if candidate != (-self.direction[0], -self.direction[1]):
                        self.next_direction = candidate
                        self.sounds.play(self.sounds.turn)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.state == "menu":
            virtual = self.virtual_mouse(event.pos)
            for button in self.buttons:
                if button.rect.collidepoint(virtual):
                    self.set_state(button.action)

    def virtual_mouse(self, pos):
        sw, sh = self.screen.get_size()
        scale = min(sw / WIDTH, sh / HEIGHT)
        ox = (sw - WIDTH * scale) / 2
        oy = (sh - HEIGHT * scale) / 2
        return ((pos[0] - ox) / scale, (pos[1] - oy) / scale)

    def update(self, dt):
        mouse = self.virtual_mouse(pygame.mouse.get_pos())
        for button in self.buttons:
            button.update(mouse, dt)
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.shake = max(0, self.shake - dt * 30)
        self.food_pulse += dt * 4
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.blink = 1.0
            self.blink_timer = random.uniform(2.0, 4.5)
        self.blink = max(0.0, self.blink - dt * 8)
        self.tongue_timer = (self.tongue_timer + dt) % 3.2

        if self.state != "playing":
            return
        self.play_time += dt
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer <= 0:
            self.combo = 1
        if self.special_food:
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.special_food = None

        speed = self.difficulties[self.difficulty][1] + min(6, self.score / 90)
        self.move_acc += dt
        step = 1.0 / speed
        while self.move_acc >= step:
            self.move_acc -= step
            self.move_snake()
            if self.state != "playing":
                break

    def move_snake(self):
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        head = (hx + dx, hy + dy)
        if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS or head in self.snake[:-1]:
            self.game_over()
            return
        self.snake.insert(0, head)
        ate = False
        if head == self.food:
            points = 10 * self.combo
            self.score += points
            self.combo = min(5, self.combo + 1)
            self.combo_timer = 2.2
            self.add_burst(head, PINK)
            self.sounds.play(self.sounds.eat)
            self.spawn_food()
            ate = True
        elif self.special_food and head == self.special_food:
            self.score += 35 * self.combo
            self.combo = min(5, self.combo + 1)
            self.combo_timer = 3.0
            self.add_burst(head, GOLD, 30)
            self.special_food = None
            self.sounds.play(self.sounds.eat)
            ate = True
        if not ate:
            self.snake.pop()

    def game_over(self):
        self.state = "gameover"
        self.shake = 10
        self.add_burst(self.snake[0], RED, 45)
        self.sounds.play(self.sounds.game_over)
        if self.score > self.record:
            self.record = self.score
            save_record(self.record)

    def glow_circle(self, surface, pos, radius, color, strength=3):
        size = int(radius * 5)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        for i in range(strength, 0, -1):
            r = int(radius * (1 + i * 0.45))
            alpha = int(15 + 20 * (strength - i + 1) / strength)
            pygame.draw.circle(layer, (*color, alpha), (center, center), r)
        pygame.draw.circle(layer, color, (center, center), int(radius))
        surface.blit(layer, (pos[0] - center, pos[1] - center))

    def draw_background(self):
        self.canvas.fill(BG)
        for y in range(0, HEIGHT, CELL):
            for x in range(0, PLAY_W, CELL):
                if (x // CELL + y // CELL) % 2 == 0:
                    pygame.draw.rect(self.canvas, (9, 16, 29), (x, y, CELL, CELL))
        for x in range(0, PLAY_W + 1, CELL):
            pygame.draw.line(self.canvas, GRID, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT + 1, CELL):
            pygame.draw.line(self.canvas, GRID, (0, y), (PLAY_W, y), 1)
        pygame.draw.rect(self.canvas, PANEL, (PLAY_W, 0, HUD_W, HEIGHT))
        pygame.draw.line(self.canvas, CYAN, (PLAY_W, 0), (PLAY_W, HEIGHT), 2)

    def cell_center(self, cell):
        return (cell[0] * CELL + CELL // 2, cell[1] * CELL + CELL // 2)

    def draw_food(self, cell, special=False):
        x, y = self.cell_center(cell)
        pulse = 1 + math.sin(self.food_pulse) * 0.12
        color = GOLD if special else PINK
        self.glow_circle(self.canvas, (x, y), 8 * pulse, color, 3)
        if not special:
            pygame.draw.circle(self.canvas, (255, 180, 205), (x - 3, y - 3), 2)
            pygame.draw.line(self.canvas, GREEN, (x, y - 7), (x + 4, y - 12), 3)
        else:
            points = []
            for i in range(10):
                a = -math.pi / 2 + i * math.pi / 5
                r = 10 if i % 2 == 0 else 4
                points.append((x + math.cos(a) * r, y + math.sin(a) * r))
            pygame.draw.polygon(self.canvas, WHITE, points, 2)

    def draw_snake(self):
        if not self.snake:
            return
        # Corpo sombreado e conectado
        centers = [self.cell_center(p) for p in self.snake]
        if len(centers) > 1:
            pygame.draw.lines(self.canvas, (4, 44, 38), False, [(x + 3, y + 5) for x, y in centers], CELL - 5)
            pygame.draw.lines(self.canvas, GREEN_DARK, False, centers, CELL - 7)
        for i in range(len(self.snake) - 1, -1, -1):
            x, y = centers[i]
            t = i / max(1, len(self.snake) - 1)
            color = (
                int(GREEN[0] * (1 - t * 0.45)),
                int(GREEN[1] * (1 - t * 0.35)),
                int(GREEN[2] * (1 - t * 0.42)),
            )
            radius = 9 if i else 12
            pygame.draw.circle(self.canvas, (4, 42, 35), (x + 2, y + 4), radius + 1)
            pygame.draw.circle(self.canvas, color, (x, y), radius)
            if i > 0 and i % 2 == 0:
                pygame.draw.circle(self.canvas, (113, 255, 200), (x - 3, y - 3), 2)
        self.draw_head_face(centers[0])

    def draw_head_face(self, center):
        x, y = center
        dx, dy = self.direction
        # Vetor perpendicular para posicionar olhos
        px, py = -dy, dx
        forward = (dx * 4, dy * 4)
        eye_sep = 5
        lid = clamp(1.0 - self.blink * 2.3, 0.12, 1.0)
        for side in (-1, 1):
            ex = int(x + forward[0] + px * eye_sep * side)
            ey = int(y + forward[1] + py * eye_sep * side)
            if dx != 0:
                eye_rect = pygame.Rect(ex - 3, ey - int(5 * lid), 6, max(2, int(10 * lid)))
            else:
                eye_rect = pygame.Rect(ex - int(5 * lid), ey - 3, max(2, int(10 * lid)), 6)
            pygame.draw.ellipse(self.canvas, WHITE, eye_rect)
            pupil_x = ex + dx * 2
            pupil_y = ey + dy * 2
            pygame.draw.circle(self.canvas, (6, 16, 27), (pupil_x, pupil_y), 2)
            pygame.draw.circle(self.canvas, CYAN, (pupil_x, pupil_y), 1)
        # Lingua aparece periodicamente e se movimenta
        tongue_phase = self.tongue_timer
        if tongue_phase < 0.62:
            amount = math.sin((tongue_phase / 0.62) * math.pi)
            start = (x + dx * 11, y + dy * 11)
            end = (x + dx * (12 + 14 * amount), y + dy * (12 + 14 * amount))
            pygame.draw.line(self.canvas, PINK, start, end, 3)
            tipx, tipy = end
            fork = 5
            pygame.draw.line(self.canvas, PINK, end, (tipx + dx * 5 + px * fork, tipy + dy * 5 + py * fork), 2)
            pygame.draw.line(self.canvas, PINK, end, (tipx + dx * 5 - px * fork, tipy + dy * 5 - py * fork), 2)

    def draw_hud(self):
        x = PLAY_W + 28
        title = self.font_md.render("COBRA NEON", True, GREEN)
        self.canvas.blit(title, (x, 30))
        self.canvas.blit(self.font_sm.render("ARCADE PROFISSIONAL", True, MUTED), (x, 64))

        self.stat_card(x, 112, "PONTOS", str(self.score), PINK)
        self.stat_card(x, 216, "RECORDE", str(self.record), GOLD)
        self.stat_card(x, 320, "TAMANHO", str(len(self.snake)), GREEN)

        diff_name, _, diff_color = self.difficulties[self.difficulty]
        pygame.draw.rect(self.canvas, (8, 15, 27), (x, 428, 204, 64), border_radius=14)
        self.canvas.blit(self.font_sm.render("MODO", True, MUTED), (x + 16, 437))
        self.canvas.blit(self.font_md.render(diff_name, True, diff_color), (x + 16, 458))

        if self.combo > 1 and self.combo_timer > 0:
            combo = self.font_md.render(f"COMBO x{self.combo}", True, CYAN)
            self.canvas.blit(combo, combo.get_rect(center=(PLAY_W + HUD_W // 2, 530)))
            bar = pygame.Rect(x, 553, 204, 8)
            pygame.draw.rect(self.canvas, (30, 46, 61), bar, border_radius=4)
            fill = bar.copy()
            fill.width = int(bar.width * self.combo_timer / 3.0)
            pygame.draw.rect(self.canvas, CYAN, fill, border_radius=4)

        controls = ["WASD / SETAS  Mover", "P / ESC       Pausar", "M             Som", "F11           Tela cheia"]
        self.canvas.blit(self.font_sm.render("CONTROLES", True, WHITE), (x, 598))
        for i, line in enumerate(controls):
            self.canvas.blit(pygame.font.SysFont("consolas", 14).render(line, True, MUTED), (x, 628 + i * 20))

    def stat_card(self, x, y, label, value, color):
        rect = pygame.Rect(x, y, 204, 84)
        pygame.draw.rect(self.canvas, (8, 15, 27), rect, border_radius=14)
        pygame.draw.rect(self.canvas, (*color, 255), rect, 1, border_radius=14)
        self.canvas.blit(self.font_sm.render(label, True, MUTED), (x + 16, y + 12))
        val = self.font_lg.render(value, True, WHITE)
        self.canvas.blit(val, (x + 14, y + 29))

    def draw_menu(self):
        self.canvas.fill(BG)
        # Fundo decorativo
        for i in range(12):
            x = (i * 113 + int(pygame.time.get_ticks() * 0.02)) % (WIDTH + 100) - 50
            y = 100 + (i * 67) % 520
            self.glow_circle(self.canvas, (x, y), 2 + (i % 3), CYAN if i % 2 else GREEN, 2)
        logo = self.font_xl.render("COBRA", True, WHITE)
        neon = self.font_xl.render("NEON", True, GREEN)
        self.canvas.blit(logo, logo.get_rect(center=(WIDTH // 2 - 88, 138)))
        self.canvas.blit(neon, neon.get_rect(center=(WIDTH // 2 + 128, 138)))
        subtitle = self.font_md.render("Sobreviva. Cresca. Supere o recorde.", True, MUTED)
        self.canvas.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 210)))

        # Mascote demonstrando olhos e lingua
        old_snake, old_dir = self.snake, self.direction
        self.snake = [(22 - i, 12) for i in range(10)]
        self.direction = (1, 0)
        self.draw_snake()
        self.snake, self.direction = old_snake, old_dir

        diff, _, color = self.difficulties[self.difficulty]
        self.buttons[1].text = f"DIFICULDADE: {diff}"
        for button in self.buttons:
            button.draw(self.canvas, self.font_md)
        hint = self.font_sm.render("ENTER para jogar  |  M para som  |  F11 tela cheia", True, MUTED)
        self.canvas.blit(hint, hint.get_rect(center=(WIDTH // 2, 665)))

    def draw_overlay(self, game_over=False):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((3, 7, 15, 195))
        self.canvas.blit(shade, (0, 0))
        title = "FIM DE JOGO" if game_over else "PAUSADO"
        color = PINK if game_over else CYAN
        label = self.font_lg.render(title, True, color)
        self.canvas.blit(label, label.get_rect(center=(PLAY_W // 2, 265)))
        if game_over:
            line = self.font_md.render(f"Pontuacao: {self.score}   |   Recorde: {self.record}", True, WHITE)
            hint = self.font_sm.render("ENTER para tentar novamente  |  ESC para o menu", True, MUTED)
        else:
            line = self.font_md.render("Respira... a cobra esta esperando.", True, WHITE)
            hint = self.font_sm.render("P ou ESC para continuar", True, MUTED)
        self.canvas.blit(line, line.get_rect(center=(PLAY_W // 2, 335)))
        self.canvas.blit(hint, hint.get_rect(center=(PLAY_W // 2, 390)))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_background()
            if self.special_food:
                self.draw_food(self.special_food, True)
            self.draw_food(self.food)
            self.draw_snake()
            for p in self.particles:
                p.draw(self.canvas)
            self.draw_hud()
            if self.state == "paused":
                self.draw_overlay(False)
            elif self.state == "gameover":
                self.draw_overlay(True)

        sw, sh = self.screen.get_size()
        scale = min(sw / WIDTH, sh / HEIGHT)
        fitted = pygame.transform.smoothscale(self.canvas, (int(WIDTH * scale), int(HEIGHT * scale)))
        self.screen.fill((2, 4, 9))
        ox = (sw - fitted.get_width()) // 2
        oy = (sh - fitted.get_height()) // 2
        if self.shake:
            ox += random.randint(-int(self.shake), int(self.shake))
            oy += random.randint(-int(self.shake), int(self.shake))
        self.screen.blit(fitted, (ox, oy))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    SnakeGame().run()
