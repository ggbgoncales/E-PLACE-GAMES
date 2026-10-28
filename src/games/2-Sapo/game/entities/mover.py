import pygame
import random
from settings import VW, WATER_DARK, WOOD_DARK, WOOD, WOOD_LIGHT, GATOR_DARK, GATOR, GATOR_LIGHT, GOLD, INK, WHITE, pixel_rect

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

    def draw_log(self, surface):
        r = self.rect
        pixel_rect(surface, WATER_DARK, (r.x + 2, r.y + 3, r.w, r.h - 1))
        pixel_rect(surface, WOOD_DARK, (r.x, r.y + 2, r.w, r.h - 4))
        pixel_rect(surface, WOOD, (r.x + 2, r.y, r.w - 4, r.h - 3))
        pixel_rect(surface, WOOD_LIGHT, (r.x + 5, r.y + 2, max(2, r.w - 12), 2))
        pixel_rect(surface, WOOD_DARK, (r.x, r.y + 4, 3, r.h - 8))
        pixel_rect(surface, WOOD_DARK, (r.right - 3, r.y + 4, 3, r.h - 8))
        pixel_rect(surface, WOOD_LIGHT, (r.right - 2, r.y + 5, 1, 4))
        for xx in range(r.x + 10, r.right - 7, 14):
            pixel_rect(surface, WOOD_DARK, (xx, r.y + 4, 2, 6))
            pixel_rect(surface, WOOD_LIGHT, (xx + 2, r.y + 3, 3, 1))

    def draw_gator(self, surface):
        r = self.rect
        right = self.speed > 0
        pixel_rect(surface, WATER_DARK, (r.x + 2, r.y + 4, r.w, 8))
        pixel_rect(surface, GATOR_DARK, (r.x + 4, r.y + 3, r.w - 8, 9))
        pixel_rect(surface, GATOR, (r.x + 7, r.y + 1, r.w - 14, 9))
        pixel_rect(surface, GATOR_LIGHT, (r.x + 10, r.y + 2, max(2, r.w - 24), 2))
        hx = r.right - 16 if right else r.x
        pixel_rect(surface, GATOR, (hx, r.y, 16, 11))
        pixel_rect(surface, GATOR_LIGHT, (hx + 2, r.y + 1, 11, 3))
        ex = hx + 11 if right else hx + 4
        pixel_rect(surface, GOLD, (ex, r.y, 3, 3))
        pixel_rect(surface, INK, (ex + (1 if right else 0), r.y + 1, 1, 1))
        pixel_rect(surface, INK, (hx + 2, r.y + 7, 12, 1))
        for tx in range(hx + 4, hx + 13, 4):
            pixel_rect(surface, WHITE, (tx, r.y + 8, 1, 2))
        for xx in range(r.x + 12, r.right - 17, 8):
            pygame.draw.polygon(surface, GATOR_DARK, [(xx, r.y + 2), (xx + 3, r.y - 2), (xx + 6, r.y + 2)])
        if right:
            pygame.draw.polygon(surface, GATOR_DARK, [(r.x + 7, r.y + 3), (r.x - 5, r.y + 7), (r.x + 7, r.y + 10)])
        else:
            pygame.draw.polygon(surface, GATOR_DARK, [(r.right - 7, r.y + 3), (r.right + 5, r.y + 7), (r.right - 7, r.y + 10)])

    def draw(self, surface):
        if self.kind == "log":
            self.draw_log(surface)
        else:
            self.draw_gator(surface)

