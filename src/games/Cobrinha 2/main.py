import math
import random
import sys
from pathlib import Path
from collections import deque

import pygame
import pygame.gfxdraw

# SNAKE - versao organica, sem pixels e sem tema neon
# Instalar: python -m pip install pygame
# Executar: python snake_profissional.py

WIDTH, HEIGHT = 1280, 760
PANEL_W = 250
FIELD_W = WIDTH - PANEL_W
FPS = 60
SAVE_FILE = Path.home() / ".snake_recorde.txt"

CREAM = (239, 234, 215)
DARK = (24, 34, 29)
DARK_2 = (31, 44, 37)
MOSS = (78, 111, 74)
LEAF = (113, 148, 92)
LIGHT_GREEN = (161, 181, 112)
SCALE_DARK = (42, 70, 52)
RED = (182, 55, 50)
APPLE_LIGHT = (235, 103, 75)
GOLD = (214, 169, 79)
WHITE = (250, 248, 239)
MUTED = (166, 175, 161)

pygame.init()
pygame.display.set_caption("Snake")


def safe_record():
    try:
        return max(0, int(SAVE_FILE.read_text(encoding="utf-8")))
    except Exception:
        return 0


def save_record(value):
    try:
        SAVE_FILE.write_text(str(value), encoding="utf-8")
    except Exception:
        pass


def vec_from_angle(a):
    return pygame.Vector2(math.cos(a), math.sin(a))


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def draw_text(surface, font, text, color, pos, anchor="topleft"):
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(img, rect)
    return rect


class Particle:
    def __init__(self, pos, color):
        angle = random.random() * math.tau
        speed = random.uniform(45, 170)
        self.pos = pygame.Vector2(pos)
        self.vel = vec_from_angle(angle) * speed
        self.life = random.uniform(.35, .8)
        self.max_life = self.life
        self.radius = random.uniform(2.0, 5.5)
        self.color = color

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= .96
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(210 * self.life / self.max_life)
        r = max(1, int(self.radius * self.life / self.max_life))
        layer = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*self.color, a), layer.get_rect().center, r)
        surf.blit(layer, self.pos - pygame.Vector2(layer.get_size()) / 2)


class Snake:
    def __init__(self):
        self.head = pygame.Vector2(FIELD_W * .46, HEIGHT * .52)
        self.angle = 0.0
        self.target_angle = 0.0
        self.speed = 190.0
        self.radius = 19.0
        self.segment_gap = 9.0
        self.target_length = 44
        self.path = deque(maxlen=5000)
        for i in range(700):
            self.path.append(pygame.Vector2(self.head.x - i * 2, self.head.y))
        self.blink_wait = random.uniform(1.8, 3.8)
        self.blink_amount = 0.0
        self.tongue_clock = 0.0
        self.breath = 0.0
        self.dead = False

    def update_face(self, dt):
        self.blink_wait -= dt
        if self.blink_wait <= 0:
            self.blink_amount = 1.0
            self.blink_wait = random.uniform(2.0, 4.5)
        self.blink_amount = max(0.0, self.blink_amount - dt * 5.5)
        self.tongue_clock = (self.tongue_clock + dt) % 3.0
        self.breath += dt * 2.7

    def steer(self, direction, dt):
        if direction.length_squared() > .1:
            desired = math.atan2(direction.y, direction.x)
            diff = (desired - self.angle + math.pi) % math.tau - math.pi
            self.angle += clamp(diff, -3.5 * dt, 3.5 * dt)
            self.target_angle = desired

    def update(self, dt, direction):
        self.update_face(dt)
        if self.dead:
            return
        self.steer(direction, dt)
        forward = vec_from_angle(self.angle)
        self.head += forward * self.speed * dt
        self.path.appendleft(self.head.copy())

        # Mantem amostras densas para a curva do corpo ficar lisa.
        while len(self.path) > 3 and self.path[0].distance_to(self.path[1]) < 2.2:
            del self.path[1]

    def sample_body(self):
        points = [self.head.copy()]
        needed = self.target_length
        if len(self.path) < 2:
            return points
        target_distance = self.segment_gap
        accumulated = 0.0
        previous = self.path[0]
        for current in list(self.path)[1:]:
            d = previous.distance_to(current)
            if d <= 0:
                continue
            while accumulated + d >= target_distance and len(points) < needed:
                ratio = (target_distance - accumulated) / d
                point = previous.lerp(current, ratio)
                points.append(point)
                previous = point
                d = previous.distance_to(current)
                accumulated = 0.0
            accumulated += d
            previous = current
            if len(points) >= needed:
                break
        return points

    def body_radius(self, index, count):
        t = index / max(1, count - 1)
        neck = min(1.0, index / 4)
        taper = (1.0 - t ** 2.15)
        return max(2.8, self.radius * taper * lerp(1.05, 1.0, neck))

    def collision_with_self(self):
        body = self.sample_body()
        for i, p in enumerate(body[16:], 16):
            if self.head.distance_to(p) < self.radius + self.body_radius(i, len(body)) - 5:
                return True
        return False

    def draw(self, surf, food_pos):
        body = self.sample_body()
        if len(body) < 2:
            return

        # Sombra suave sob a cobra.
        shadow = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for i in range(len(body) - 1, 0, -1):
            r = self.body_radius(i, len(body))
            pygame.draw.circle(shadow, (5, 10, 7, 45), (int(body[i].x + 6), int(body[i].y + 9)), int(r + 3))
        surf.blit(shadow, (0, 0))

        # Corpo organico: circulos sobrepostos criam uma curva continua sem blocos.
        for i in range(len(body) - 1, -1, -1):
            p = body[i]
            r = self.body_radius(i, len(body))
            t = i / max(1, len(body) - 1)
            base = (
                int(lerp(LEAF[0], MOSS[0], t)),
                int(lerp(LEAF[1], MOSS[1], t)),
                int(lerp(LEAF[2], MOSS[2], t)),
            )
            pygame.gfxdraw.filled_circle(surf, int(p.x), int(p.y), int(r), base)
            pygame.gfxdraw.aacircle(surf, int(p.x), int(p.y), int(r), SCALE_DARK)

        # Escamas em losango acompanhando a curvatura, discretas e detalhadas.
        for i in range(5, len(body) - 3, 2):
            p = body[i]
            tangent = body[max(0, i - 2)] - body[min(len(body) - 1, i + 2)]
            if tangent.length_squared() == 0:
                continue
            tangent = tangent.normalize()
            normal = pygame.Vector2(-tangent.y, tangent.x)
            r = self.body_radius(i, len(body))
            if r < 6:
                continue
            for side in (-1, 1):
                c = p + normal * r * .43 * side
                length = max(3, r * .42)
                width = max(2, r * .24)
                pts = [
                    c + tangent * length,
                    c + normal * width,
                    c - tangent * length,
                    c - normal * width,
                ]
                shade = (63, 94, 65) if (i // 2 + side) % 2 else (101, 132, 83)
                pygame.gfxdraw.filled_polygon(surf, [(int(x), int(y)) for x, y in pts], shade)
                pygame.gfxdraw.aapolygon(surf, [(int(x), int(y)) for x, y in pts], SCALE_DARK)

        self.draw_head(surf, food_pos)

    def draw_head(self, surf, food_pos):
        forward = vec_from_angle(self.angle)
        side = pygame.Vector2(-forward.y, forward.x)
        breath = math.sin(self.breath) * .7
        center = self.head + forward * 3

        # Cabeca eliptica em superficie separada para permitir rotacao suave.
        size = 92
        head_layer = pygame.Surface((size, size), pygame.SRCALPHA)
        hc = pygame.Vector2(size / 2, size / 2)
        head_rect = pygame.Rect(15, 21 - breath, 64, 51 + breath * 2)
        pygame.draw.ellipse(head_layer, (105, 143, 88), head_rect)
        pygame.draw.ellipse(head_layer, SCALE_DARK, head_rect, 2)

        # Placas/escamas da testa.
        for row, y in enumerate((30, 39, 48)):
            count = 3 if row != 1 else 4
            start = 33 if count == 3 else 28
            for col in range(count):
                x = start + col * 10
                pts = [(x, y - 4), (x + 5, y), (x, y + 5), (x - 5, y)]
                shade = (126, 158, 99) if (row + col) % 2 else (88, 125, 79)
                pygame.gfxdraw.filled_polygon(head_layer, pts, shade)
                pygame.gfxdraw.aapolygon(head_layer, pts, (64, 91, 65))

        # Narinas.
        pygame.draw.ellipse(head_layer, (33, 49, 39), (70, 39, 5, 4))
        pygame.draw.ellipse(head_layer, (33, 49, 39), (70, 51, 5, 4))

        turned = pygame.transform.rotozoom(head_layer, -math.degrees(self.angle), 1.0)
        surf.blit(turned, turned.get_rect(center=center))

        # Olhos 3D posicionados no mundo e pupilas olhando para a comida.
        lid = clamp(1.0 - self.blink_amount * 2.2, .08, 1.0)
        look = pygame.Vector2(food_pos) - center
        if look.length_squared() > 0:
            look = look.normalize()
        for sign in (-1, 1):
            eye_c = center + forward * 12 + side * sign * 18
            ew, eh = 12, max(2, int(16 * lid))
            eye_rect = pygame.Rect(0, 0, ew, eh)
            eye_rect.center = eye_c
            pygame.draw.ellipse(surf, CREAM, eye_rect)
            pygame.draw.ellipse(surf, (39, 55, 42), eye_rect, 1)
            pupil = eye_c + look * 3
            pygame.draw.circle(surf, (15, 22, 17), pupil, max(1, int(4 * lid)))
            pygame.draw.circle(surf, WHITE, pupil + pygame.Vector2(-1, -1), 1)

        # Boca curta e sutil.
        mouth_a = center + forward * 25 - side * 7
        mouth_b = center + forward * 27 + side * 7
        pygame.draw.line(surf, (55, 65, 49), mouth_a, mouth_b, 2)

        # Lingua bifurcada animada.
        if self.tongue_clock < .72:
            phase = math.sin((self.tongue_clock / .72) * math.pi)
            start = center + forward * 31
            end = start + forward * (8 + phase * 23)
            pygame.draw.line(surf, (151, 42, 58), start, end, 3)
            fork = 7 * phase
            pygame.draw.line(surf, (151, 42, 58), end, end + forward * 7 + side * fork, 2)
            pygame.draw.line(surf, (151, 42, 58), end, end + forward * 7 - side * fork, 2)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("segoeui", 17)
        self.font_mid = pygame.font.SysFont("segoeui", 24, bold=True)
        self.font_big = pygame.font.SysFont("georgia", 58, bold=True)
        self.font_score = pygame.font.SysFont("segoeui", 42, bold=True)
        self.record = safe_record()
        self.state = "menu"
        self.fullscreen = False
        self.difficulty_index = 1
        self.difficulties = [("Calmo", 155), ("Classico", 190), ("Rapido", 235)]
        self.particles = []
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.snake.speed = self.difficulties[self.difficulty_index][1]
        self.score = 0
        self.food = self.new_food()
        self.special = None
        self.special_time = 0.0
        self.elapsed = 0.0
        self.shake = 0.0

    def new_food(self):
        return pygame.Vector2(random.randint(70, FIELD_W - 70), random.randint(70, HEIGHT - 70))

    def input_direction(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: direction.x += 1
        return direction.normalize() if direction.length_squared() else vec_from_angle(self.snake.angle)

    def burst(self, pos, color, amount=22):
        self.particles.extend(Particle(pos, color) for _ in range(amount))

    def eat_check(self):
        if self.snake.head.distance_to(self.food) < self.snake.radius + 14:
            self.score += 10
            self.snake.target_length += 5
            self.snake.speed = min(290, self.snake.speed + 1.7)
            self.burst(self.food, APPLE_LIGHT)
            self.food = self.new_food()
            if self.score and self.score % 50 == 0:
                self.special = self.new_food()
                self.special_time = 7.0
        if self.special and self.snake.head.distance_to(self.special) < self.snake.radius + 14:
            self.score += 35
            self.snake.target_length += 7
            self.burst(self.special, GOLD, 34)
            self.special = None

    def die(self):
        self.state = "gameover"
        self.snake.dead = True
        self.shake = 10
        self.burst(self.snake.head, RED, 48)
        if self.score > self.record:
            self.record = self.score
            save_record(self.record)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.shake = max(0, self.shake - dt * 25)
        self.snake.update_face(dt)
        if self.state != "playing":
            return
        self.elapsed += dt
        self.snake.update(dt, self.input_direction())
        self.eat_check()
        if self.special:
            self.special_time -= dt
            if self.special_time <= 0:
                self.special = None
        h = self.snake.head
        if h.x < 24 or h.x > FIELD_W - 24 or h.y < 24 or h.y > HEIGHT - 24 or self.snake.collision_with_self():
            self.die()

    def draw_background(self):
        self.canvas.fill((38, 51, 43))
        # Campo sem grade: textura organica discreta.
        for i in range(30):
            x = (i * 197 + 83) % FIELD_W
            y = (i * 109 + 47) % HEIGHT
            pygame.draw.circle(self.canvas, (43, 58, 47), (x, y), 52 + i % 4 * 13)
        # Moldura interna.
        pygame.draw.rect(self.canvas, (52, 68, 56), (18, 18, FIELD_W - 36, HEIGHT - 36), 2, border_radius=24)
        self.draw_leaves()
        pygame.draw.rect(self.canvas, DARK, (FIELD_W, 0, PANEL_W, HEIGHT))

    def draw_leaves(self):
        for i in range(15):
            x = 25 + (i * 137) % (FIELD_W - 50)
            y = 20 if i % 2 == 0 else HEIGHT - 23
            angle = (-25 + i * 17) if y < 100 else (205 + i * 13)
            layer = pygame.Surface((46, 25), pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (61, 82, 63, 95), (2, 3, 40, 16))
            leaf = pygame.transform.rotate(layer, angle)
            self.canvas.blit(leaf, leaf.get_rect(center=(x, y)))

    def draw_food(self, pos, special=False):
        x, y = int(pos.x), int(pos.y)
        pulse = 1 + math.sin(pygame.time.get_ticks() * .006) * .04
        if special:
            r = int(13 * pulse)
            pygame.draw.circle(self.canvas, (120, 89, 42), (x + 3, y + 5), r + 2)
            pygame.draw.circle(self.canvas, GOLD, (x, y), r)
            pygame.draw.circle(self.canvas, (245, 218, 142), (x - 4, y - 4), 3)
            return
        r = int(14 * pulse)
        pygame.draw.circle(self.canvas, (18, 28, 21), (x + 4, y + 7), r + 1)
        pygame.draw.circle(self.canvas, RED, (x, y + 1), r)
        pygame.draw.circle(self.canvas, APPLE_LIGHT, (x - 4, y - 4), 5)
        pygame.draw.line(self.canvas, (73, 53, 35), (x, y - 11), (x + 3, y - 20), 4)
        pygame.draw.ellipse(self.canvas, (98, 145, 72), (x + 1, y - 22, 15, 8))

    def draw_panel(self):
        x = FIELD_W + 30
        draw_text(self.canvas, self.font_big, "Snake", CREAM, (x, 46))
        draw_text(self.canvas, self.font_small, "movimento organico", MUTED, (x + 3, 111))
        pygame.draw.line(self.canvas, MOSS, (x, 150), (WIDTH - 30, 150), 1)

        self.card(x, 185, "PONTOS", str(self.score), CREAM)
        self.card(x, 290, "RECORDE", str(self.record), GOLD)
        self.card(x, 395, "COMPRIMENTO", str(self.snake.target_length), LIGHT_GREEN)

        draw_text(self.canvas, self.font_small, "DIFICULDADE", MUTED, (x, 526))
        draw_text(self.canvas, self.font_mid, self.difficulties[self.difficulty_index][0], CREAM, (x, 552))
        pygame.draw.line(self.canvas, MOSS, (x, 599), (WIDTH - 30, 599), 1)
        controls = ["WASD / setas   mover", "P ou ESC      pausar", "F11           tela cheia"]
        for i, text in enumerate(controls):
            draw_text(self.canvas, self.font_small, text, MUTED, (x, 627 + i * 27))

    def card(self, x, y, title, value, color):
        rect = pygame.Rect(x, y, 190, 82)
        pygame.draw.rect(self.canvas, DARK_2, rect, border_radius=15)
        pygame.draw.rect(self.canvas, (48, 68, 55), rect, 1, border_radius=15)
        draw_text(self.canvas, self.font_small, title, MUTED, (x + 16, y + 12))
        draw_text(self.canvas, self.font_score, value, color, (x + 15, y + 32))

    def overlay(self, title, subtitle, hint):
        layer = pygame.Surface((FIELD_W, HEIGHT), pygame.SRCALPHA)
        layer.fill((10, 16, 12, 185))
        self.canvas.blit(layer, (0, 0))
        draw_text(self.canvas, self.font_big, title, CREAM, (FIELD_W // 2, 276), "center")
        draw_text(self.canvas, self.font_mid, subtitle, LIGHT_GREEN, (FIELD_W // 2, 355), "center")
        draw_text(self.canvas, self.font_small, hint, MUTED, (FIELD_W // 2, 407), "center")

    def draw_menu(self):
        self.draw_background()
        self.snake.head = pygame.Vector2(FIELD_W * .52, HEIGHT * .56)
        self.snake.angle = -.08
        self.snake.draw(self.canvas, self.food)
        layer = pygame.Surface((FIELD_W, HEIGHT), pygame.SRCALPHA)
        layer.fill((13, 18, 14, 78))
        self.canvas.blit(layer, (0, 0))
        draw_text(self.canvas, pygame.font.SysFont("georgia", 88, bold=True), "Snake", CREAM, (75, 75))
        draw_text(self.canvas, self.font_mid, "Uma cobrinha mais viva, fluida e detalhada.", LIGHT_GREEN, (81, 177))

        play = pygame.Rect(80, 252, 250, 62)
        diff = pygame.Rect(80, 329, 250, 57)
        pygame.draw.rect(self.canvas, CREAM, play, border_radius=16)
        pygame.draw.rect(self.canvas, DARK_2, diff, border_radius=16)
        pygame.draw.rect(self.canvas, MOSS, diff, 2, border_radius=16)
        draw_text(self.canvas, self.font_mid, "JOGAR", DARK, play.center, "center")
        draw_text(self.canvas, self.font_small, f"DIFICULDADE: {self.difficulties[self.difficulty_index][0].upper()}", CREAM, diff.center, "center")
        draw_text(self.canvas, self.font_small, "Clique ou pressione ENTER", MUTED, (205, 414), "center")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.fullscreen = not self.fullscreen
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
            elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                if self.state == "playing": self.state = "paused"
                elif self.state == "paused": self.state = "playing"
                elif self.state == "gameover": self.state = "menu"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state in ("menu", "gameover"):
                    self.reset(); self.state = "playing"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.state == "menu":
            p = self.virtual_mouse(event.pos)
            if pygame.Rect(80, 252, 250, 62).collidepoint(p):
                self.reset(); self.state = "playing"
            elif pygame.Rect(80, 329, 250, 57).collidepoint(p):
                self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulties)
                self.reset()

    def virtual_mouse(self, pos):
        sw, sh = self.screen.get_size()
        scale = min(sw / WIDTH, sh / HEIGHT)
        return ((pos[0] - (sw - WIDTH * scale) / 2) / scale,
                (pos[1] - (sh - HEIGHT * scale) / 2) / scale)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_background()
            self.draw_food(self.food)
            if self.special:
                self.draw_food(self.special, True)
            self.snake.draw(self.canvas, self.food)
            for particle in self.particles:
                particle.draw(self.canvas)
            self.draw_panel()
            if self.state == "paused":
                self.overlay("Pausado", "A cobra esta esperando.", "P ou ESC para continuar")
            elif self.state == "gameover":
                self.overlay("Fim de jogo", f"Pontuacao: {self.score}   Recorde: {self.record}", "ENTER para jogar novamente | ESC para o menu")

        sw, sh = self.screen.get_size()
        scale = min(sw / WIDTH, sh / HEIGHT)
        frame = pygame.transform.smoothscale(self.canvas, (int(WIDTH * scale), int(HEIGHT * scale)))
        self.screen.fill((10, 14, 11))
        x = (sw - frame.get_width()) // 2
        y = (sh - frame.get_height()) // 2
        if self.shake:
            x += random.randint(-int(self.shake), int(self.shake))
            y += random.randint(-int(self.shake), int(self.shake))
        self.screen.blit(frame, (x, y))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, .04)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
