"""settings.py - constantes globais do Kombate."""

TITULO = "Kombate"
LARGURA, ALTURA = 1280, 720          # resolucao virtual (ampliada para a tela)
FPS = 60

CHAO_Y = 640                         # linha do chao (pes dos lutadores)
ARENA_MIN_X = 60                     # paredes invisiveis da arena (camera travada)
ARENA_MAX_X = 1220
GRAVIDADE = 1.85                     # mais alta = pulo mais rapido

TEMPO_ROUND = 99                     # segundos
ROUNDS_PARA_VENCER = 2               # melhor de 3
MAX_ROUNDS = 5                       # evita loop infinito em empates

NIVEL_CPU = 3                        # 1 (muito facil) ate 5 (mestre)

VELOCIDADE_GOLPES = 0.50             # < 1 = golpes mais rapidos (multiplica os frames)
VELOCIDADE_ANDAR = 1.70              # > 1 = personagens andam/correm mais rapido

# Nomes de teclas aceitos por pygame.key.key_code()
CONTROLES = {
    1: {"esquerda": "a", "direita": "d", "cima": "w", "baixo": "s",
        "soco": "f", "chute": "g", "especial1": "r", "especial2": "t",
        "dash": "left shift"},
    2: {"esquerda": "left", "direita": "right", "cima": "up", "baixo": "down",
        "soco": "k", "chute": "l", "especial1": "i", "especial2": "o",
        "dash": "right shift"},
}

DANO_GLOBAL = 4.0
GUARDA_MAX = 100                     # defender muitos golpes seguidos quebra a guarda
DUPLO_TOQUE = 14                     # frames para o toque duplo (dash) ser reconhecido                    # multiplicador de dano de todos os golpes
