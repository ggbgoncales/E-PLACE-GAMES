import pygame

from game.entities.ball import Ball
from game.entities.paddle import Paddle
from game.ui.text import draw_text
from settings import (
    ACCENT_COLOR,
    BACKGROUND_COLOR,
    FOREGROUND_COLOR,
    MUTED_COLOR,
    PADDLE_MARGIN,
    PADDLE_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SECONDARY_COLOR,
    WINNING_SCORE,
)


class Game:
    MENU = 'menu'
    PLAYING = 'playing'
    GAME_OVER = 'game_over'

    def __init__(self, screen):
        self.screen = screen
        paddle_y = SCREEN_HEIGHT // 2 - 60
        self.left_paddle = Paddle(PADDLE_MARGIN, paddle_y, ACCENT_COLOR)
        self.right_paddle = Paddle(
            SCREEN_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH,
            paddle_y,
            SECONDARY_COLOR,
        )
        self.ball = Ball()
        self.state = self.MENU
        self.mode = 'cpu'
        self.paused = False
        self.left_score = 0
        self.right_score = 0
        self.winner = ''

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == self.MENU:
            if event.key == pygame.K_1:
                self.start_match('cpu')
            elif event.key == pygame.K_2:
                self.start_match('versus')
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key == pygame.K_ESCAPE:
            self.state = self.MENU
            self.paused = False
        elif event.key == pygame.K_r:
            self.start_match(self.mode)
        elif event.key == pygame.K_p and self.state == self.PLAYING:
            self.paused = not self.paused
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.state == self.GAME_OVER:
            self.start_match(self.mode)

    def start_match(self, mode):
        self.mode = mode
        self.left_score = 0
        self.right_score = 0
        self.left_paddle.center()
        self.right_paddle.center()
        self.ball.reset()
        self.winner = ''
        self.paused = False
        self.state = self.PLAYING

    def update(self, dt):
        if self.state != self.PLAYING or self.paused:
            return

        keys = pygame.key.get_pressed()
        left_direction = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.left_paddle.move(left_direction, dt)

        if self.mode == 'versus':
            right_direction = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.right_paddle.move(right_direction, dt)
        else:
            self._update_cpu(dt)

        self.ball.update(dt)
        self._handle_collisions()
        self._handle_score()

    def _update_cpu(self, dt):
        dead_zone = 18
        difference = self.ball.rect.centery - self.right_paddle.rect.centery
        direction = 0
        if difference > dead_zone:
            direction = 1
        elif difference < -dead_zone:
            direction = -1

        original_speed = self.right_paddle.speed
        self.right_paddle.speed *= 0.78
        self.right_paddle.move(direction, dt)
        self.right_paddle.speed = original_speed

    def _handle_collisions(self):
        if self.ball.velocity.x < 0 and self.ball.rect.colliderect(self.left_paddle.rect):
            self.ball.bounce_from_paddle(self.left_paddle, 1)
        elif self.ball.velocity.x > 0 and self.ball.rect.colliderect(self.right_paddle.rect):
            self.ball.bounce_from_paddle(self.right_paddle, -1)

    def _handle_score(self):
        if self.ball.rect.right < 0:
            self.right_score += 1
            self._after_point(-1)
        elif self.ball.rect.left > SCREEN_WIDTH:
            self.left_score += 1
            self._after_point(1)

    def _after_point(self, serve_direction):
        if self.left_score >= WINNING_SCORE:
            self.winner = 'Jogador 1 venceu!'
            self.state = self.GAME_OVER
        elif self.right_score >= WINNING_SCORE:
            self.winner = 'CPU venceu!' if self.mode == 'cpu' else 'Jogador 2 venceu!'
            self.state = self.GAME_OVER
        else:
            self.ball.reset(serve_direction)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_court()

        if self.state == self.MENU:
            self._draw_menu()
            return

        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        self.ball.draw(self.screen)
        self._draw_score()

        if self.paused:
            self._draw_overlay('PAUSADO', 'Pressione P para continuar')
        elif self.state == self.GAME_OVER:
            self._draw_overlay(self.winner, 'ENTER: jogar novamente  |  ESC: menu')

    def _draw_court(self):
        for y in range(12, SCREEN_HEIGHT, 34):
            pygame.draw.rect(
                self.screen,
                (45, 60, 82),
                (SCREEN_WIDTH // 2 - 2, y, 4, 18),
                border_radius=2,
            )
        pygame.draw.rect(self.screen, (32, 46, 66), self.screen.get_rect(), 4)

    def _draw_menu(self):
        draw_text(self.screen, 'PING PONG', 76, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, 150), True)
        draw_text(self.screen, 'PYGAME', 26, ACCENT_COLOR, (SCREEN_WIDTH // 2, 210), True)
        draw_text(self.screen, '1  Jogador vs CPU', 30, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, 320))
        draw_text(self.screen, '2  Dois jogadores', 30, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, 370))
        draw_text(self.screen, 'W/S  |  Setas  |  P pausa  |  R reinicia', 20, MUTED_COLOR, (SCREEN_WIDTH // 2, 475))
        draw_text(self.screen, 'ESC para sair', 18, MUTED_COLOR, (SCREEN_WIDTH // 2, 520))

    def _draw_score(self):
        draw_text(self.screen, str(self.left_score), 64, ACCENT_COLOR, (SCREEN_WIDTH // 2 - 90, 65), True)
        draw_text(self.screen, str(self.right_score), 64, SECONDARY_COLOR, (SCREEN_WIDTH // 2 + 90, 65), True)
        mode_text = 'VS CPU' if self.mode == 'cpu' else '2 JOGADORES'
        draw_text(self.screen, mode_text, 17, MUTED_COLOR, (SCREEN_WIDTH // 2, 115), True)

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, title, 52, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 35), True)
        draw_text(self.screen, subtitle, 22, ACCENT_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))
