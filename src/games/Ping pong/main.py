import os as _os, sys as _sys
_SRC_DIR = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))
if _SRC_DIR not in _sys.path: _sys.path.insert(0, _SRC_DIR)
import os
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
import pygame
from gamepad import XboxController

from game.game import Game
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE


def main():
    pygame.init()
    controller = XboxController()
    pygame.display.set_caption(TITLE)
    # Tela cheia: o jogo desenha em 1280x720 e e ampliado para o monitor
    display = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    game = Game(screen)
    game.controller = controller

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get() + controller.poll_keys():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()

        dw, dh = display.get_size()
        esc = min(dw / SCREEN_WIDTH, dh / SCREEN_HEIGHT)
        img = pygame.transform.smoothscale(screen, (int(SCREEN_WIDTH * esc), int(SCREEN_HEIGHT * esc)))
        display.fill((0, 0, 0))
        display.blit(img, img.get_rect(center=(dw // 2, dh // 2)))
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
