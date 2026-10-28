import math
import random
import pygame
from settings import WATER_FOAM, WATER_LIGHT

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

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.size, self.size))

class Ripple:
    def __init__(self, x, y, delay=0):
        self.x = x
        self.y = y
        self.age = -delay
        self.life = 0.75

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        if 0 <= self.age <= self.life:
            t = self.age / self.life
            width = int(4 + 24 * t)
            height = max(2, width // 4)
            color = WATER_FOAM if t < 0.7 else WATER_LIGHT
            pygame.draw.ellipse(surface, color, (int(self.x - width / 2), int(self.y - height / 2), width, height), 1)