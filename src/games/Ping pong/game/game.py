import json
import os

import pygame
from gamepad import XboxController, draw_controller_text, draw_controls_table

from game.entities.ball import Ball
from game.entities.paddle import Paddle
from game.ui.text import draw_text, get_font
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


RECORDE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorde.json")


def carregar_vitorias():
    """Vitorias do jogador contra a CPU (o 'recorde' do Pong)."""
    try:
        with open(RECORDE_FILE, "r", encoding="utf-8") as arquivo:
            return max(0, int(json.load(arquivo).get("recorde", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def salvar_vitorias(valor):
    try:
        with open(RECORDE_FILE, "w", encoding="utf-8") as arquivo:
            json.dump({"recorde": int(valor)}, arquivo)
    except OSError:
        pass


class Game:
    MENU = 'menu'
    PLAYING = 'playing'
    GAME_OVER = 'game_over'

    def __init__(self, screen):
        self.controller = None
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
        self.show_controls = False
        self.menu_idx = 0
        self.mode = 'cpu'
        self.paused = False
        self.left_score = 0
        self.right_score = 0
        self.winner = ''
        self.vitorias = carregar_vitorias()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.show_controls:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_F1, pygame.K_F2, pygame.K_TAB, pygame.K_y):
                self.show_controls = False
            return

        if self.state == self.MENU:
            # Y no Xbox, triangulo no PlayStation e X no Switch abre controles.
            if event.key in (pygame.K_y, pygame.K_F1, pygame.K_F2, pygame.K_TAB):
                self.show_controls = True
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % 4
                return
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % 4
                return
            if event.key == pygame.K_1:
                self.start_match('cpu'); return
            if event.key == pygame.K_2 or event.key == pygame.K_x:
                self.start_match('versus'); return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.menu_idx == 0: self.start_match('cpu')
                elif self.menu_idx == 1: self.start_match('versus')
                elif self.menu_idx == 2: self.show_controls = True
                else: pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.key == pygame.K_ESCAPE:
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
        eixo = self.controller.axis(1) if self.controller else 0.0
        left_direction = int(keys[pygame.K_s]) - int(keys[pygame.K_w]) + (1 if eixo > .35 else (-1 if eixo < -.35 else 0))
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
            if self.mode == 'cpu':
                self.vitorias += 1
                salvar_vitorias(self.vitorias)
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
            if self.show_controls:
                draw_controls_table(self.screen, [('P1 VS CPU', 'X', 'A', 'B'), ('P1 VS P2', 'SQUARE', 'X', 'Y'), ('VOLTAR / SAIR', 'O', 'B', 'A'), ('MOVER P1', 'D-PAD / ANALOGICO', 'D-PAD / ANALOG', 'D-PAD / ANALOG'), ('PAUSAR', 'OPTIONS', 'MENU', '+')], title="PONG - CONTROLES")
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
        draw_text(self.screen, 'PONG', 76, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, 125), True)
        draw_text(self.screen, 'ARCADE', 26, ACCENT_COLOR, (SCREEN_WIDTH // 2, 182), True)
        items = ('1  JOGADOR VS CPU', '2  JOGADORES', 'CONTROLES', 'SAIR')
        for i, item in enumerate(items):
            y = 280 + i * 48
            color = ACCENT_COLOR if i == self.menu_idx else FOREGROUND_COLOR
            if i == self.menu_idx:
                highlight = pygame.Rect(SCREEN_WIDTH // 2 - 245, y - 18, 490, 38)
                pygame.draw.rect(self.screen, (25, 52, 74), highlight, border_radius=9)
                pygame.draw.rect(self.screen, ACCENT_COLOR, highlight, 2, border_radius=9)
            draw_text(self.screen, item, 25, color, (SCREEN_WIDTH // 2, y), True)
        draw_text(self.screen, 'SETAS / D-PAD: NAVEGAR  |  X / A / B: CONFIRMAR', 16, MUTED_COLOR, (SCREEN_WIDTH // 2, 500), True)
        if self.controller:
            hint_font = get_font(16)
            draw_controller_text(self.screen, hint_font, f'ATALHO CONTROLES: {self.controller.button_icon(3)}', ACCENT_COLOR, (SCREEN_WIDTH // 2, 530), self.controller, 'center')

    def _draw_score(self):
        draw_text(self.screen, str(self.left_score), 64, ACCENT_COLOR, (SCREEN_WIDTH // 2 - 90, 65), True)
        draw_text(self.screen, str(self.right_score), 64, SECONDARY_COLOR, (SCREEN_WIDTH // 2 + 90, 65), True)
        mode_text = f'VS CPU  -  VITORIAS: {self.vitorias}' if self.mode == 'cpu' else '2 JOGADORES'
        draw_text(self.screen, mode_text, 17, MUTED_COLOR, (SCREEN_WIDTH // 2, 115), True)

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, title, 52, FOREGROUND_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 35), True)
        draw_text(self.screen, subtitle, 22, ACCENT_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))
