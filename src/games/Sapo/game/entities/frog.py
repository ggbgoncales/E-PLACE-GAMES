import math
import random
import pygame
from settings import VW, VH, FROG_OUTLINE, FROG_GREEN, FROG_LIGHT, FROG_BELLY, FROG_EYE, TONGUE, INK, pixel_rect

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
        if self.jump < 1: return
        self.sx, self.sy = self.x, self.y
        self.tx = max(1, min(VW - 19, self.x + dx))
        self.ty = max(1, min(VH - 20, self.y + dy))
        self.jump = 0
        self.riding = None
        if dy < 0: self.facing = "up"
        elif dy > 0: self.facing = "down"
        elif dx < 0: self.facing = "left"
        elif dx > 0: self.facing = "right"

    def update(self, dt):
        self.total_time += dt
        self.invuln = max(0, self.invuln - dt)
        
        self.blink_timer -= dt
        if self.blink_timer <= 0 and self.blink <= 0 and self.second_blink <= 0:
            self.blink = 0.12
            self.second_blink = 0.22 if random.random() < 0.28 else 0
            self.blink_timer = random.uniform(1.8, 4.8)
        if self.blink > 0: self.blink -= dt
        elif self.second_blink > 0:
            self.second_blink -= dt
            if self.second_blink <= 0.08:
                self.blink = 0.11
                self.second_blink = 0

        self.mouth_timer -= dt
        if self.mouth_timer <= 0 and self.mouth <= 0:
            self.mouth = random.uniform(0.3, 0.55)
            self.mouth_timer = random.uniform(3.0, 7.0)
        self.mouth = max(0, self.mouth - dt)

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
        s = pygame.Surface((26, 23), pygame.SRCALPHA)
        A = alpha
        pixel_rect(s, (*FROG_OUTLINE, A), (1, 18, 10, 4))
        pixel_rect(s, (*FROG_OUTLINE, A), (15, 18, 10, 4))
        pixel_rect(s, (*FROG_GREEN, A), (2, 18, 8, 3))
        pixel_rect(s, (*FROG_GREEN, A), (16, 18, 8, 3))
        pixel_rect(s, (*FROG_LIGHT, A), (3, 18, 5, 1))
        pixel_rect(s, (*FROG_LIGHT, A), (18, 18, 5, 1))
        pixel_rect(s, (*FROG_OUTLINE, A), (0, 13, 6, 7))
        pixel_rect(s, (*FROG_OUTLINE, A), (20, 13, 6, 7))
        pixel_rect(s, (*FROG_GREEN, A), (1, 13, 5, 6))
        pixel_rect(s, (*FROG_GREEN, A), (20, 13, 5, 6))
        pixel_rect(s, (*FROG_LIGHT, A), (2, 14, 3, 2))
        pixel_rect(s, (*FROG_LIGHT, A), (21, 14, 3, 2))
        pixel_rect(s, (*FROG_OUTLINE, A), (4, 5, 18, 15))
        pixel_rect(s, (*FROG_OUTLINE, A), (3, 8, 20, 8))
        pixel_rect(s, (*FROG_GREEN, A), (4, 7, 18, 11))
        pixel_rect(s, (*FROG_GREEN, A), (5, 5, 16, 14))
        pixel_rect(s, (*FROG_LIGHT, A), (6, 6, 14, 3))
        pixel_rect(s, (*FROG_BELLY, A), (6, 11, 14, 8))
        pixel_rect(s, (*FROG_BELLY, A), (5, 12, 16, 4))
        pixel_rect(s, (235, 229, 45, A), (7, 12, 11, 1))
        pixel_rect(s, (*FROG_OUTLINE, A), (2, 9, 4, 7))
        pixel_rect(s, (*FROG_OUTLINE, A), (20, 9, 4, 7))
        pixel_rect(s, (*FROG_GREEN, A), (2, 10, 3, 5))
        pixel_rect(s, (*FROG_GREEN, A), (21, 10, 3, 5))
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
            if self.facing == "left": lx = -1
            elif self.facing == "right": lx = 1
            elif self.facing == "up": ly = -1
            elif self.facing == "down": ly = 1
            pixel_rect(s, (*INK, A), (7 + lx, 3 + ly, 3, 4))
            pixel_rect(s, (*INK, A), (16 + lx, 3 + ly, 3, 4))
            pixel_rect(s, (*FROG_EYE, A), (7 + lx, 3 + ly, 1, 1))
            pixel_rect(s, (*FROG_EYE, A), (16 + lx, 3 + ly, 1, 1))

        pixel_rect(s, (*FROG_OUTLINE, A), (10, 9, 1, 1))
        pixel_rect(s, (*FROG_OUTLINE, A), (15, 9, 1, 1))

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

    def draw(self, surface, alpha=255, sink=0):
        if self.invuln > 0 and int(self.invuln * 22) % 2: return
        lift = int(math.sin(self.jump * math.pi) * 5) if self.jump < 1 else 0
        breathe = 1 if self.jump >= 1 and math.sin(self.total_time * 3.2) > 0.8 else 0
        sprite = self.build_sprite(alpha)

        if self.jump < 1:
            arc = math.sin(self.jump * math.pi)
            sprite = pygame.transform.scale(sprite, (max(23, int(26 - arc)), int(23 + arc)))

        angle = 0
        if self.jump < 1 and self.facing == "left": angle = 4
        elif self.jump < 1 and self.facing == "right": angle = -4
        if angle: sprite = pygame.transform.rotate(sprite, angle)

        shadow_w = max(7, 13 - lift)
        pygame.draw.ellipse(surface, (15, 48, 50), (int(self.x + 9 - shadow_w / 2), int(self.y + 17), shadow_w, 2))
        draw_x = int(self.x + 9 - sprite.get_width() / 2)
        draw_y = int(self.y + 9 - sprite.get_height() / 2 - lift + sink + breathe)
        surface.blit(sprite, (draw_x, draw_y))
