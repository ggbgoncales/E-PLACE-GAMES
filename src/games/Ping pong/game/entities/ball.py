import math
import random

import pygame

from settings import (
    BALL_ACCELERATION,
    BALL_MAX_SPEED,
    BALL_SIZE,
    BALL_START_SPEED,
    FOREGROUND_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.position = pygame.Vector2()
        self.velocity = pygame.Vector2()
        self.reset(random.choice((-1, 1)))

    def reset(self, horizontal_direction=None):
        direction = horizontal_direction or random.choice((-1, 1))
        angle = math.radians(random.uniform(-35, 35))
        self.position.update(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.velocity.update(
            math.cos(angle) * BALL_START_SPEED * direction,
            math.sin(angle) * BALL_START_SPEED,
        )
        self._sync_rect()

    def update(self, dt):
        self.position += self.velocity * dt
        self._sync_rect()

        if self.rect.top <= 0 and self.velocity.y < 0:
            self.rect.top = 0
            self.position.y = self.rect.centery
            self.velocity.y *= -1
        elif self.rect.bottom >= SCREEN_HEIGHT and self.velocity.y > 0:
            self.rect.bottom = SCREEN_HEIGHT
            self.position.y = self.rect.centery
            self.velocity.y *= -1

    def bounce_from_paddle(self, paddle, direction):
        offset = (self.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
        speed = min(self.velocity.length() * BALL_ACCELERATION, BALL_MAX_SPEED)
        angle = math.radians(offset * 58)
        self.velocity.x = math.cos(angle) * speed * direction
        self.velocity.y = math.sin(angle) * speed

        if direction > 0:
            self.rect.left = paddle.rect.right
        else:
            self.rect.right = paddle.rect.left
        self.position.update(self.rect.center)

    def _sync_rect(self):
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen):
        pygame.draw.ellipse(screen, FOREGROUND_COLOR, self.rect)
