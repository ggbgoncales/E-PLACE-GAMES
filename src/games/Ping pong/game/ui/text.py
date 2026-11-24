import pygame


_font_cache = {}


def _fonte(tamanho, titulo):
    """Titulos em Press Start 2P e textos em VT323 (assets/fonts)."""
    import os
    nome = "PressStart2P-Regular.ttf" if titulo else "VT323-Regular.ttf"
    pasta = os.path.abspath(os.path.dirname(__file__))
    for _ in range(10):
        caminho = os.path.join(pasta, "assets", "fonts", nome)
        if os.path.exists(caminho):
            return pygame.font.Font(caminho, max(8, int(tamanho)))
        pasta = os.path.dirname(pasta)
    return pygame.font.SysFont('arial,helveticaneue,dejavusans', int(tamanho), bold=titulo)


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        if size >= 26:
            _font_cache[key] = _fonte(size * 0.55, True)
        else:
            _font_cache[key] = _fonte(size * 1.3, False)
    return _font_cache[key]


def draw_text(screen, text, size, color, center, bold=False):
    surface = get_font(size, bold).render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)
    return rect
