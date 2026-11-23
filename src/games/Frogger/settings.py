import pygame

# Mundo 360 px de altura logica e largura no formato do monitor
# -> menos zoom, mais faixas, tela cheia sem borda
pygame.display.init()
_DW, _DH = pygame.display.get_desktop_sizes()[0]
VH = 360
VW = max(480, int(VH * _DW / _DH))
TILE = 20
FPS = 60

# Paleta pixel art
INK = (18, 31, 30)
WHITE = (248, 248, 224)
CREAM = (250, 235, 162)
GOLD = (255, 211, 63)
RED = (218, 66, 68)
GRASS_DARK, GRASS, GRASS_LIGHT = (40, 105, 57), (56, 132, 67), (86, 157, 73)
FLOWER = (244, 147, 184)
WATER_DARK, WATER, WATER_LIGHT, WATER_FOAM = (19, 77, 119), (26, 105, 158), (66, 159, 194), (157, 220, 226)
SAND_DARK, SAND, SAND_LIGHT = (159, 143, 78), (203, 189, 109), (230, 216, 137)
WOOD_DARK, WOOD, WOOD_LIGHT = (72, 42, 27), (116, 69, 36), (176, 107, 53)
FROG_OUTLINE, FROG_GREEN, FROG_LIGHT = (86, 144, 73), (148, 193, 59), (170, 207, 72)
FROG_BELLY, FROG_EYE, TONGUE = (224, 224, 25), (253, 253, 245), (239, 102, 129)
GATOR_DARK, GATOR, GATOR_LIGHT = (34, 75, 42), (56, 116, 58), (78, 145, 68)
# tartaruga: casco marrom-esverdeado e pele verde-oliva
SHELL_DARK, SHELL, SHELL_LIGHT = (58, 52, 24), (112, 104, 42), (164, 152, 70)
SKIN_DARK, SKIN = (64, 104, 52), (118, 168, 84)
SNAKE_DARK, SNAKE, SNAKE_LIGHT = (60, 40, 90), (120, 82, 170), (180, 150, 220)

# Layout das linhas (y do topo de cada linha de 20 px)
HUD_ROW = 0
GOAL_ROW = 20
RIVER_1 = [40, 60, 80, 100, 120, 140]
SAND_ROW = 160
RIVER_2 = [180, 200, 220, 240, 260, 280]
LANES = set(RIVER_1 + RIVER_2)
SAFE_ROWS = {SAND_ROW, 300, 320, 340}
START_Y = 337
GOAL_Y = GOAL_ROW - 3


def pixel_rect(surface, color, rect):
    pygame.draw.rect(surface, color, pygame.Rect(*rect))


# compatibilidade com versoes antigas do mover.py
TURTLE_DARK, TURTLE, TURTLE_LIGHT = SHELL_DARK, SHELL, SHELL_LIGHT
