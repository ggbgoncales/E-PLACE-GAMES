import math
import random
import sys
import pygame

pygame.init()

# ============================================================
# SAPO AVENTUREIRO PIXEL
# Jogo inteiro em um único arquivo, sem imagens externas.
# ============================================================

SCALE = 3
VW, VH = 320, 240
W, H = VW * SCALE, VH * SCALE
TILE = 20
FPS = 60

window = pygame.display.set_mode((W, H))
pygame.display.set_caption("Sapo Aventureiro Pixel")
canvas = pygame.Surface((VW, VH))
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 8, bold=True)
SMALL = pygame.font.SysFont("consolas", 6, bold=True)
BIG = pygame.font.SysFont("consolas", 16, bold=True)

# Paleta pixel art
INK = (18, 31, 30)
WHITE = (248, 248, 224)
CREAM = (250, 235, 162)
GOLD = (255, 211, 63)
RED = (218, 66, 68)

GRASS_DARK = (40, 105, 57)
GRASS = (56, 132, 67)
GRASS_LIGHT = (86, 157, 73)
FLOWER = (244, 147, 184)

WATER_DARK = (19, 77, 119)
WATER = (26, 105, 158)
WATER_LIGHT = (66, 159, 194)
WATER_FOAM = (157, 220, 226)

SAND_DARK = (159, 143, 78)
SAND = (203, 189, 109)
SAND_LIGHT = (230, 216, 137)

WOOD_DARK = (72, 42, 27)
WOOD = (116, 69, 36)
WOOD_LIGHT = (176, 107, 53)

FROG_OUTLINE = (86, 144, 73)
FROG_GREEN = (148, 193, 59)
FROG_LIGHT = (170, 207, 72)
FROG_BELLY = (224, 224, 25)
FROG_EYE = (253, 253, 245)
TONGUE = (239, 102, 129)

GATOR_DARK = (34, 75, 42)
GATOR = (56, 116, 58)
GATOR_LIGHT = (78, 145, 68)

LANES = {40, 60, 80, 120, 140, 160}
SAFE_ROWS = {20, 100, 180, 200, 220}


def text_center(text, font, y, color=WHITE):
    image = font.render(text, False, color)
    canvas.blit(image, (VW // 2 - image.get_width() // 2, y))


def pixel_rect(surface, color, rect):
    pygame.draw.rect(surface, color, pygame.Rect(*rect))


class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(10, 30)
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 13
        self.life = random.uniform(0.35, 0.75)
        self.max_life = self.life
        self.color = color
        self.size = random.choice((1, 1, 2))

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 32 * dt

    def draw(self):
        if self.life > 0:
            pygame.draw.rect(canvas, self.color,
                             (int(self.x), int(self.y), self.size, self.size))


class Ripple:
    def __init__(self, x, y, delay=0):
        self.x = x
        self.y = y
        self.age = -delay
        self.life = 0.75

    def update(self, dt):
        self.age += dt

    def draw(self):
        if 0 <= self.age <= self.life:
            t = self.age / self.life
            width = int(4 + 24 * t)
            height = max(2, width // 4)
            color = WATER_FOAM if t < 0.7 else WATER_LIGHT
            pygame.draw.ellipse(canvas, color,
                                (int(self.x - width / 2), int(self.y - height / 2),
                                 width, height), 1)


class Mover:
    def __init__(self, x, y, width, speed, kind):
        self.x = float(x)
        self.y = y
        self.width = width
        self.speed = speed
        self.kind = kind
        self.rect = pygame.Rect(int(x), y + 4, width, 14)
        self.anim = random.random() * 10

    def update(self, dt):
        self.anim += dt
        self.x += self.speed * dt
        if self.speed > 0 and self.x > VW + 28:
            self.x = -self.width - 28
        elif self.speed < 0 and self.x + self.width < -28:
            self.x = VW + 28
        self.rect.x = int(self.x)

    def draw_log(self):
        r = self.rect
        # sombra na água
        pixel_rect(canvas, WATER_DARK, (r.x + 2, r.y + 3, r.w, r.h - 1))
        pixel_rect(canvas, WOOD_DARK, (r.x, r.y + 2, r.w, r.h - 4))
        pixel_rect(canvas, WOOD, (r.x + 2, r.y, r.w - 4, r.h - 3))
        pixel_rect(canvas, WOOD_LIGHT, (r.x + 5, r.y + 2, max(2, r.w - 12), 2))
        # pontas quadradas pixeladas
        pixel_rect(canvas, WOOD_DARK, (r.x, r.y + 4, 3, r.h - 8))
        pixel_rect(canvas, WOOD_DARK, (r.right - 3, r.y + 4, 3, r.h - 8))
        pixel_rect(canvas, WOOD_LIGHT, (r.right - 2, r.y + 5, 1, 4))
        # casca
        for xx in range(r.x + 10, r.right - 7, 14):
            pixel_rect(canvas, WOOD_DARK, (xx, r.y + 4, 2, 6))
            pixel_rect(canvas, WOOD_LIGHT, (xx + 2, r.y + 3, 3, 1))

    def draw_gator(self):
        r = self.rect
        right = self.speed > 0
        # sombra
        pixel_rect(canvas, WATER_DARK, (r.x + 2, r.y + 4, r.w, 8))
        # corpo pixelado
        pixel_rect(canvas, GATOR_DARK, (r.x + 4, r.y + 3, r.w - 8, 9))
        pixel_rect(canvas, GATOR, (r.x + 7, r.y + 1, r.w - 14, 9))
        pixel_rect(canvas, GATOR_LIGHT, (r.x + 10, r.y + 2, max(2, r.w - 24), 2))
        # cabeça e focinho
        hx = r.right - 16 if right else r.x
        pixel_rect(canvas, GATOR, (hx, r.y, 16, 11))
        pixel_rect(canvas, GATOR_LIGHT, (hx + 2, r.y + 1, 11, 3))
        # olho
        ex = hx + 11 if right else hx + 4
        pixel_rect(canvas, GOLD, (ex, r.y, 3, 3))
        pixel_rect(canvas, INK, (ex + (1 if right else 0), r.y + 1, 1, 1))
        # boca e dentes
        pixel_rect(canvas, INK, (hx + 2, r.y + 7, 12, 1))
        for tx in range(hx + 4, hx + 13, 4):
            pixel_rect(canvas, WHITE, (tx, r.y + 8, 1, 2))
        # placas nas costas
        for xx in range(r.x + 12, r.right - 17, 8):
            pygame.draw.polygon(canvas, GATOR_DARK,
                                [(xx, r.y + 2), (xx + 3, r.y - 2), (xx + 6, r.y + 2)])
        # cauda
        if right:
            pygame.draw.polygon(canvas, GATOR_DARK,
                                [(r.x + 7, r.y + 3), (r.x - 5, r.y + 7), (r.x + 7, r.y + 10)])
        else:
            pygame.draw.polygon(canvas, GATOR_DARK,
                                [(r.right - 7, r.y + 3), (r.right + 5, r.y + 7),
                                 (r.right - 7, r.y + 10)])

    def draw(self):
        if self.kind == "log":
            self.draw_log()
        else:
            self.draw_gator()


class Frog:
    def __init__(self):
        self.lives = 3
        self.score = 0
        self.level = 1
        self.total_time = 0
        self.reset()

    def reset(self):
        self.x = VW // 2 - 9
        self.y = 217
        self.sx = self.tx = self.x
        self.sy = self.ty = self.y
        self.jump = 1.0
        self.riding = None
        self.invuln = 0.75
        self.best_y = self.y
        self.facing = "up"
        self.sink = 0
        self.blink = 0
        self.blink_timer = random.uniform(1.5, 4.0)
        self.second_blink = 0
        self.mouth = 0
        self.mouth_timer = random.uniform(2.5, 6.5)
        self.look_timer = random.uniform(0.8, 2.5)
        self.look_x = 0
        self.look_y = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) + 4, int(self.y) + 5, 11, 11)

    def request_jump(self, dx, dy):
        if self.jump < 1:
            return
        self.sx, self.sy = self.x, self.y
        self.tx = max(1, min(VW - 19, self.x + dx))
        self.ty = max(1, min(VH - 20, self.y + dy))
        self.jump = 0
        self.riding = None
        if dy < 0:
            self.facing = "up"
        elif dy > 0:
            self.facing = "down"
        elif dx < 0:
            self.facing = "left"
        elif dx > 0:
            self.facing = "right"

    def update(self, dt):
        self.total_time += dt
        self.invuln = max(0, self.invuln - dt)

        # piscada aleatória, às vezes dupla
        self.blink_timer -= dt
        if self.blink_timer <= 0 and self.blink <= 0 and self.second_blink <= 0:
            self.blink = 0.12
            self.second_blink = 0.22 if random.random() < 0.28 else 0
            self.blink_timer = random.uniform(1.8, 4.8)
        if self.blink > 0:
            self.blink -= dt
        elif self.second_blink > 0:
            self.second_blink -= dt
            if self.second_blink <= 0.08:
                self.blink = 0.11
                self.second_blink = 0

        # abre a boca de vez em quando
        self.mouth_timer -= dt
        if self.mouth_timer <= 0 and self.mouth <= 0:
            self.mouth = random.uniform(0.3, 0.55)
            self.mouth_timer = random.uniform(3.0, 7.0)
        self.mouth = max(0, self.mouth - dt)

        # olhos passeiam quando parado
        self.look_timer -= dt
        if self.look_timer <= 0:
            self.look_x = random.choice((-1, 0, 0, 0, 1))
            self.look_y = random.choice((-1, 0, 0, 1))
            self.look_timer = random.uniform(0.8, 2.8)

        if self.jump < 1:
            self.jump = min(1, self.jump + dt * 6.2)
            t = self.jump
            smooth = t * t * (3 - 2 * t)
            self.x = self.sx + (self.tx - self.sx) * smooth
            self.y = self.sy + (self.ty - self.sy) * smooth
            if self.jump >= 1 and self.y < self.best_y:
                self.score += 10
                self.best_y = self.y
        elif self.riding:
            self.x += self.riding.speed * dt
            self.sx = self.tx = self.x

    def build_sprite(self, alpha=255):
        """Sapo compacto, simetrico e inspirado no sprite de referencia."""
        s = pygame.Surface((26, 23), pygame.SRCALPHA)
        A = alpha

        # Pes largos com contorno definido
        pixel_rect(s, (*FROG_OUTLINE, A), (1, 18, 10, 4))
        pixel_rect(s, (*FROG_OUTLINE, A), (15, 18, 10, 4))
        pixel_rect(s, (*FROG_GREEN, A), (2, 18, 8, 3))
        pixel_rect(s, (*FROG_GREEN, A), (16, 18, 8, 3))
        pixel_rect(s, (*FROG_LIGHT, A), (3, 18, 5, 1))
        pixel_rect(s, (*FROG_LIGHT, A), (18, 18, 5, 1))

        # Coxas arredondadas em degraus de pixel
        pixel_rect(s, (*FROG_OUTLINE, A), (0, 13, 6, 7))
        pixel_rect(s, (*FROG_OUTLINE, A), (20, 13, 6, 7))
        pixel_rect(s, (*FROG_GREEN, A), (1, 13, 5, 6))
        pixel_rect(s, (*FROG_GREEN, A), (20, 13, 5, 6))
        pixel_rect(s, (*FROG_LIGHT, A), (2, 14, 3, 2))
        pixel_rect(s, (*FROG_LIGHT, A), (21, 14, 3, 2))

        # Corpo principal com silhueta menos quadrada
        pixel_rect(s, (*FROG_OUTLINE, A), (4, 5, 18, 15))
        pixel_rect(s, (*FROG_OUTLINE, A), (3, 8, 20, 8))
        pixel_rect(s, (*FROG_GREEN, A), (4, 7, 18, 11))
        pixel_rect(s, (*FROG_GREEN, A), (5, 5, 16, 14))
        pixel_rect(s, (*FROG_LIGHT, A), (6, 6, 14, 3))

        # Barriga amarela igual ao destaque da referencia
        pixel_rect(s, (*FROG_BELLY, A), (6, 11, 14, 8))
        pixel_rect(s, (*FROG_BELLY, A), (5, 12, 16, 4))
        pixel_rect(s, (235, 229, 45, A), (7, 12, 11, 1))

        # Bracos curtos junto ao corpo
        pixel_rect(s, (*FROG_OUTLINE, A), (2, 9, 4, 7))
        pixel_rect(s, (*FROG_OUTLINE, A), (20, 9, 4, 7))
        pixel_rect(s, (*FROG_GREEN, A), (2, 10, 3, 5))
        pixel_rect(s, (*FROG_GREEN, A), (21, 10, 3, 5))

        # Olhos altos e bem separados
        pixel_rect(s, (*FROG_OUTLINE, A), (4, 1, 8, 8))
        pixel_rect(s, (*FROG_OUTLINE, A), (14, 1, 8, 8))
        pixel_rect(s, (*FROG_GREEN, A), (6, 0, 4, 2))
        pixel_rect(s, (*FROG_GREEN, A), (16, 0, 4, 2))

        if self.blink > 0:
            pixel_rect(s, (*FROG_EYE, A), (5, 4, 6, 2))
            pixel_rect(s, (*FROG_EYE, A), (15, 4, 6, 2))
            pixel_rect(s, (*INK, A), (6, 5, 4, 1))
            pixel_rect(s, (*INK, A), (16, 5, 4, 1))
        else:
            pixel_rect(s, (*FROG_EYE, A), (5, 2, 6, 6))
            pixel_rect(s, (*FROG_EYE, A), (15, 2, 6, 6))
            lx, ly = self.look_x, self.look_y
            if self.facing == "left":
                lx = -1
            elif self.facing == "right":
                lx = 1
            elif self.facing == "up":
                ly = -1
            elif self.facing == "down":
                ly = 1
            pixel_rect(s, (*INK, A), (7 + lx, 3 + ly, 3, 4))
            pixel_rect(s, (*INK, A), (16 + lx, 3 + ly, 3, 4))
            pixel_rect(s, (*FROG_EYE, A), (7 + lx, 3 + ly, 1, 1))
            pixel_rect(s, (*FROG_EYE, A), (16 + lx, 3 + ly, 1, 1))

        # Narinas discretas
        pixel_rect(s, (*FROG_OUTLINE, A), (10, 9, 1, 1))
        pixel_rect(s, (*FROG_OUTLINE, A), (15, 9, 1, 1))

        # Sorriso largo da referencia e boca animada
        if self.mouth > 0:
            pixel_rect(s, (*INK, A), (6, 11, 14, 5))
            pixel_rect(s, (*INK, A), (5, 10, 2, 3))
            pixel_rect(s, (*INK, A), (19, 10, 2, 3))
            pixel_rect(s, (*TONGUE, A), (9, 14, 8, 2))
            pixel_rect(s, (255, 155, 171, A), (11, 14, 4, 1))
        else:
            pixel_rect(s, (*INK, A), (7, 13, 12, 2))
            pixel_rect(s, (*INK, A), (5, 11, 2, 4))
            pixel_rect(s, (*INK, A), (19, 11, 2, 4))

        return s

    def draw(self, alpha=255, sink=0):
        if self.invuln > 0 and int(self.invuln * 22) % 2:
            return

        lift = int(math.sin(self.jump * math.pi) * 5) if self.jump < 1 else 0
        breathe = 1 if self.jump >= 1 and math.sin(self.total_time * 3.2) > 0.8 else 0
        sprite = self.build_sprite(alpha)

        # Alongamento sutil, sem deformar demais o rosto
        if self.jump < 1:
            arc = math.sin(self.jump * math.pi)
            sprite = pygame.transform.scale(sprite, (max(23, int(26 - arc)), int(23 + arc)))

        angle = 0
        if self.jump < 1 and self.facing == "left":
            angle = 4
        elif self.jump < 1 and self.facing == "right":
            angle = -4
        if angle:
            sprite = pygame.transform.rotate(sprite, angle)

        shadow_w = max(7, 13 - lift)
        pygame.draw.ellipse(canvas, (15, 48, 50),
                            (int(self.x + 9 - shadow_w / 2), int(self.y + 17), shadow_w, 2))

        draw_x = int(self.x + 9 - sprite.get_width() / 2)
        draw_y = int(self.y + 9 - sprite.get_height() / 2 - lift + sink + breathe)
        canvas.blit(sprite, (draw_x, draw_y))

def make_level(level):
    multiplier = min(1 + (level - 1) * 0.12, 1.65)
    specs = [
        (40, 27, [("log", -20, 70), ("gator", 88, 45), ("log", 170, 82), ("log", 300, 62)]),
        (60, -33, [("log", 5, 60), ("gator", 95, 48), ("log", 170, 72), ("gator", 272, 46), ("log", 340, 66)]),
        (80, 38, [("gator", -35, 46), ("log", 35, 86), ("log", 170, 63), ("gator", 263, 46), ("log", 337, 76)]),
        (120, -29, [("log", -50, 82), ("gator", 65, 46), ("log", 137, 80), ("log", 260, 70), ("gator", 357, 46)]),
        (140, 35, [("log", -35, 64), ("gator", 60, 47), ("log", 138, 84), ("gator", 260, 47), ("log", 337, 73)]),
        (160, -40, [("gator", -28, 47), ("log", 50, 80), ("log", 177, 66), ("gator", 273, 47), ("log", 347, 78)]),
    ]
    return [Mover(x, y, width, speed * multiplier, kind)
            for y, speed, items in specs for kind, x, width in items]


frog = Frog()
movers = make_level(1)
particles = []
ripples = []
state = "title"
death_reason = ""
death_timer = 0
message = ""
message_timer = 0
water_time = 0
shake = 0


def is_water(y):
    return any(row <= y < row + TILE for row in LANES)


def splash(x, y, amount=18):
    for _ in range(amount):
        particles.append(Particle(x, y, random.choice((WATER_FOAM, WATER_LIGHT, WHITE))))
    ripples.extend((Ripple(x, y), Ripple(x, y, 0.18), Ripple(x, y, 0.36)))


def begin_death(reason):
    global state, death_reason, death_timer, shake
    if frog.invuln > 0 or state != "playing":
        return
    state = "dying"
    death_reason = reason
    death_timer = 1.05
    shake = 0.28
    splash(frog.rect.centerx, frog.rect.centery)


def finish_death():
    global state, message, message_timer
    frog.lives -= 1
    if frog.lives <= 0:
        state = "gameover"
    else:
        frog.reset()
        state = "playing"
        message = death_reason
        message_timer = 1.1


def draw_map():
    global water_time
    water_time += 1 / FPS

    for y in range(0, VH, TILE):
        if y in LANES:
            pixel_rect(canvas, WATER, (0, y, VW, TILE))
            pixel_rect(canvas, WATER_DARK, (0, y, VW, 2))
            # ondas quadradas deslocando
            wave = int(water_time * 18 + y) % 30
            for x in range(-30, VW + 30, 30):
                xx = x + wave
                pixel_rect(canvas, WATER_LIGHT, (xx, y + 6, 10, 1))
                pixel_rect(canvas, WATER_LIGHT, (xx + 3, y + 5, 6, 1))
                pixel_rect(canvas, WATER_DARK, (xx + 15, y + 14, 8, 1))
        elif y == 100:
            pixel_rect(canvas, SAND, (0, y, VW, TILE))
            pixel_rect(canvas, SAND_LIGHT, (0, y, VW, 2))
            for x in range(5, VW, 23):
                pixel_rect(canvas, SAND_DARK, (x, y + 8 + (x % 7), 2, 1))
        else:
            base = GRASS if y % 40 else GRASS_DARK
            pixel_rect(canvas, base, (0, y, VW, TILE))
            pixel_rect(canvas, GRASS_DARK, (0, y, VW, 2))
            for x in range(4, VW, 19):
                yy = y + 5 + ((x * 3 + y) % 11)
                pixel_rect(canvas, GRASS_LIGHT, (x, yy, 1, 4))
                pixel_rect(canvas, GRASS_LIGHT, (x + 1, yy, 1, 2))

    # vitória: folhas e flores
    for x in (35, 96, 158, 221, 283):
        pixel_rect(canvas, GRASS_DARK, (x - 8, 6, 16, 7))
        pixel_rect(canvas, GRASS, (x - 10, 9, 20, 5))
        pixel_rect(canvas, FLOWER, (x - 1, 4, 3, 3))
        pixel_rect(canvas, GOLD, (x, 5, 1, 1))


def draw_ui():
    pixel_rect(canvas, INK, (0, 0, VW, 15))
    pixel_rect(canvas, GRASS_LIGHT, (0, 14, VW, 1))
    canvas.blit(FONT.render(f"VIDAS {frog.lives}", False, WHITE), (5, 4))
    canvas.blit(FONT.render(f"PONTOS {frog.score}", False, GOLD), (75, 4))
    level_text = FONT.render(f"NIVEL {frog.level}", False, WHITE)
    canvas.blit(level_text, (VW - level_text.get_width() - 5, 4))


def draw_overlay(color):
    overlay = pygame.Surface((VW, VH), pygame.SRCALPHA)
    overlay.fill(color)
    canvas.blit(overlay, (0, 0))


while True:
    dt = min(clock.tick(FPS) / 1000.0, 0.033)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                state = "playing"
            elif state in ("gameover", "win") and event.key == pygame.K_r:
                frog = Frog()
                movers = make_level(1)
                particles.clear()
                ripples.clear()
                state = "playing"
            elif state == "playing":
                if event.key in (pygame.K_UP, pygame.K_w):
                    frog.request_jump(0, -TILE)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    frog.request_jump(0, TILE)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    frog.request_jump(-TILE, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    frog.request_jump(TILE, 0)

    if state in ("playing", "dying"):
        for mover in movers:
            mover.update(dt)

    if state == "playing":
        frog.update(dt)
        frog.riding = None

        if frog.jump >= 1 and is_water(frog.rect.centery):
            hits = [m for m in movers if frog.rect.colliderect(m.rect)]
            gators = [m for m in hits if m.kind == "gator"]
            logs = [m for m in hits if m.kind == "log"]
            if gators:
                begin_death("O JACARE PEGOU O SAPO!")
            elif logs:
                frog.riding = max(logs, key=lambda m: frog.rect.clip(m.rect).width)
            else:
                begin_death("O SAPO CAIU NA AGUA!")

        if frog.x < -18 or frog.x > VW + 5:
            begin_death("A CORRENTEZA LEVOU O SAPO!")

        if frog.y < 19:
            frog.score += 250
            frog.level += 1
            if frog.level > 5:
                state = "win"
            else:
                frog.reset()
                movers = make_level(frog.level)
                message = f"NIVEL {frog.level}: MAIS RAPIDO!"
                message_timer = 1.5

    elif state == "dying":
        death_timer -= dt
        frog.sink = min(9, frog.sink + dt * 12)
        if death_timer <= 0:
            finish_death()

    message_timer = max(0, message_timer - dt)
    shake = max(0, shake - dt)

    for particle in particles[:]:
        particle.update(dt)
        if particle.life <= 0:
            particles.remove(particle)
    for ripple in ripples[:]:
        ripple.update(dt)
        if ripple.age > ripple.life:
            ripples.remove(ripple)

    draw_map()
    for mover in movers:
        mover.draw()
    for ripple in ripples:
        ripple.draw()

    if state == "dying":
        frog.draw(alpha=max(0, int(255 * death_timer / 1.05)), sink=frog.sink)
    else:
        frog.draw()

    for particle in particles:
        particle.draw()

    draw_ui()

    if state == "title":
        draw_overlay((6, 20, 24, 218))
        # sapo grande na tela inicial usando o mesmo desenho do personagem
        old_blink, old_mouth = frog.blink, frog.mouth
        frog.blink = 0
        frog.mouth = 0
        hero = frog.build_sprite()
        hero = pygame.transform.scale(hero, (78, 69))
        canvas.blit(hero, (VW // 2 - 39, 43))
        frog.blink, frog.mouth = old_blink, old_mouth
        text_center("SAPO AVENTUREIRO", BIG, 122, FROG_BELLY)
        text_center("TRAVESSIA PIXEL", FONT, 148, FROG_LIGHT)
        text_center("TRONCOS SAO SEGUROS", SMALL, 169, WHITE)
        text_center("JACARES NAO SAO", SMALL, 179, RED)
        text_center("[ ENTER ] JOGAR", FONT, 199, GOLD)
        text_center("WASD OU SETAS", SMALL, 216, WHITE)

    elif state == "gameover":
        draw_overlay((35, 5, 8, 220))
        text_center("FIM DE JOGO", BIG, 77, RED)
        text_center(f"PONTUACAO: {frog.score}", FONT, 112, WHITE)
        text_center("PRESSIONE R", FONT, 137, GOLD)
        text_center("PARA RECOMECAR", SMALL, 152, WHITE)

    elif state == "win":
        draw_overlay((4, 30, 20, 212))
        text_center("TRAVESSIA", BIG, 68, FROG_LIGHT)
        text_center("CONCLUIDA!", BIG, 88, FROG_BELLY)
        text_center(f"PONTUACAO: {frog.score}", FONT, 124, GOLD)
        text_center("PRESSIONE R PARA JOGAR", SMALL, 153, WHITE)

    elif message_timer > 0:
        pixel_rect(canvas, INK, (54, 25, 212, 18))
        pixel_rect(canvas, GOLD, (54, 25, 212, 1))
        text_center(message, FONT, 31, GOLD)

    # Escala inteira, preservando os pixels nítidos
    scaled = pygame.transform.scale(canvas, (W, H))
    if shake > 0:
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        window.fill(INK)
        window.blit(scaled, (offset_x, offset_y))
    else:
        window.blit(scaled, (0, 0))

    pygame.display.flip()
