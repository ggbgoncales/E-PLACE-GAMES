import pygame

from settings import PADDLE_HEIGHT, PADDLE_SPEED, PADDLE_WIDTH, SCREEN_HEIGHT


class Paddle:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.speed = PADDLE_SPEED

    def move(self, direction, dt):
        self.rect.y += round(direction * self.speed * dt)
        self.rect.clamp_ip(pygame.Rect(0, 0, 10000, SCREEN_HEIGHT))

    def center(self):
        self.rect.centery = SCREEN_HEIGHT // 2

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=9)
