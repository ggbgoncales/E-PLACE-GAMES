"""Game 4 - jogo de exemplo (template). Substitua pelo seu jogo."""
import pygame, sys
pygame.init()
TELA = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Game 4")
clock = pygame.time.Clock()
fonte = pygame.font.SysFont("Arial", 48, bold=True)
fonte2 = pygame.font.SysFont("Arial", 22)
x, y, vel = 400, 300, 5
rodando = True
while rodando:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: rodando = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: rodando = False
    t = pygame.key.get_pressed()
    if t[pygame.K_LEFT]:  x -= vel
    if t[pygame.K_RIGHT]: x += vel
    if t[pygame.K_UP]:    y -= vel
    if t[pygame.K_DOWN]:  y += vel
    TELA.fill((18, 20, 28))
    txt = fonte.render("GAME 4", True, (0, 200, 255))
    TELA.blit(txt, txt.get_rect(center=(400, 80)))
    dica = fonte2.render("Setas movem  |  ESC sai", True, (150, 155, 168))
    TELA.blit(dica, dica.get_rect(center=(400, 140)))
    pygame.draw.rect(TELA, (255, 60, 90), (x - 25, y - 25, 50, 50), border_radius=8)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
sys.exit()
