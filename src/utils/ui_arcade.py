"""Componentes visuais do launcher: fundo arcade, painéis, botões e atalhos de teclado.

Tudo é desenhado com primitivas do Pygame (sem imagens extras), para manter o launcher leve
e com o mesmo visual neon retrô em todas as telas.
"""
import math
import random

import pygame

# --- Paleta (a mesma do logo e da documentação) -----------------------------------------
CIANO = (24, 231, 255)
ROSA = (255, 69, 230)
ROXO = (138, 91, 255)
VERDE = (84, 255, 139)
AMARELO = (255, 205, 0)
VERMELHO = (255, 70, 80)
AZUL = (59, 130, 246)

TEXTO = (232, 236, 255)      # texto principal
TEXTO2 = (167, 176, 214)     # texto secundário
TEXTO3 = (112, 122, 165)     # texto de apoio (ainda legível sobre o fundo escuro)
LINHA = (48, 56, 100)
PAINEL = (14, 17, 40)
PAINEL2 = (22, 27, 60)
FUNDO_TOPO = (8, 9, 28)
FUNDO_BASE = (2, 2, 10)


def misturar(a, b, k):
    """Mistura duas cores: k=0 devolve a, k=1 devolve b."""
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class FundoArcade:
    """Fundo com degradê, estrelas piscando, chão em perspectiva e linhas de varredura."""

    def __init__(self, largura, altura):
        self.w, self.h = largura, altura
        self.horizonte = int(altura * 0.68)
        rng = random.Random(7)
        self.estrelas = [
            (rng.randrange(largura), rng.randrange(0, self.horizonte), rng.random() * 6.28, rng.choice((1, 1, 2, 2, 3)))
            for _ in range(80)
        ]
        self.base = pygame.Surface((largura, altura))
        for y in range(altura):
            self.base.fill(misturar(FUNDO_TOPO, FUNDO_BASE, y / altura), (0, y, largura, 1))
        # brilho suave na linha do horizonte
        brilho = pygame.Surface((largura, 140), pygame.SRCALPHA)
        for i in range(140):
            alfa = int(34 * (1 - abs(i - 70) / 70))
            pygame.draw.line(brilho, (*ROSA, max(0, alfa)), (0, i), (largura, i))
        self.base.blit(brilho, (0, self.horizonte - 70))
        self.scan = pygame.Surface((largura, altura), pygame.SRCALPHA)
        for y in range(0, altura, 3):
            pygame.draw.line(self.scan, (0, 0, 0, 34), (0, y), (largura, y))

    def desenhar(self, tela, t):
        tela.blit(self.base, (0, 0))
        for x, y, fase, r in self.estrelas:
            piscar = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.6 + fase))
            tela.fill(misturar(FUNDO_TOPO, (205, 220, 255), piscar * 0.8), (x, y, r, r))

        hz, vx = self.horizonte, self.w // 2
        for i in range(-16, 17):                         # linhas que convergem no horizonte
            pygame.draw.line(tela, misturar(FUNDO_BASE, CIANO, 0.16), (vx + i * 9, hz), (vx + i * 120, self.h))
        deslocamento = (t * 0.30) % 1.0
        for i in range(10):                              # linhas horizontais que "correm" para a frente
            p = (i + deslocamento) / 10.0
            y = hz + int((self.h - hz) * (p ** 2.0))
            pygame.draw.line(tela, misturar(FUNDO_BASE, ROSA, 0.07 + 0.22 * p), (0, y), (self.w, y))
        pygame.draw.line(tela, misturar(FUNDO_BASE, ROSA, 0.55), (0, hz), (self.w, hz))
        tela.blit(self.scan, (0, 0))


_FONTES = {}


def fonte(tamanho, titulo=False):
    """Press Start 2P (titulo=True) ou VT323, de assets/fonts; cai para uma fonte do sistema se faltar."""
    import os
    chave = (int(tamanho), bool(titulo))
    if chave not in _FONTES:
        nome = "PressStart2P-Regular.ttf" if titulo else "VT323-Regular.ttf"
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts", nome)
        try:
            _FONTES[chave] = pygame.font.Font(caminho, max(8, int(tamanho)))
        except (OSError, pygame.error):
            _FONTES[chave] = pygame.font.SysFont("arial,helveticaneue,dejavusans", max(8, int(tamanho)), bold=titulo)
    return _FONTES[chave]


# --- Texto ------------------------------------------------------------------------------
def texto(tela, fonte, conteudo, cor, pos, ancora="topleft", sombra=False):
    img = fonte.render(str(conteudo), True, cor)
    rect = img.get_rect(**{ancora: pos})
    if sombra:
        sombra_img = fonte.render(str(conteudo), True, (0, 0, 0))
        tela.blit(sombra_img, rect.move(2, 2))
    tela.blit(img, rect)
    return rect


def quebrar_texto(fonte, conteudo, largura):
    """Quebra um texto em linhas que cabem na largura dada."""
    linhas, atual = [], ""
    for palavra in conteudo.split():
        teste = f"{atual} {palavra}".strip()
        if fonte.size(teste)[0] <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


# --- Formas -----------------------------------------------------------------------------
def painel(tela, rect, borda=LINHA, fundo=PAINEL, raio=14, largura_borda=2, alfa=236):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*fundo, alfa), s.get_rect(), border_radius=raio)
    pygame.draw.rect(s, borda, s.get_rect(), width=largura_borda, border_radius=raio)
    tela.blit(s, rect.topleft)


def brilho(tela, rect, cor, intensidade=70, raio=14, camadas=4, passo=7, espessura=3):
    """Aura neon ao redor de um retângulo. `passo` e `espessura` permitem usar em telas de baixa resolução."""
    for k in range(camadas, 0, -1):
        r = rect.inflate(k * passo, k * passo)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*cor, max(6, int(intensidade / k))), s.get_rect(), width=espessura,
                         border_radius=raio + k * max(1, passo // 2))
        tela.blit(s, r.topleft)


def triangulo(tela, centro, tamanho, cor, direcao="direita"):
    x, y = centro
    t = tamanho
    pontos = {
        "direita": [(x - t // 2, y - t), (x - t // 2, y + t), (x + t, y)],
        "esquerda": [(x + t // 2, y - t), (x + t // 2, y + t), (x - t, y)],
    }[direcao]
    pygame.draw.polygon(tela, cor, pontos)


# --- Ícones dos botões ------------------------------------------------------------------
def icone(tela, nome, centro, cor, fundo):
    x, y = centro
    if nome == "jogar":
        pygame.draw.polygon(tela, cor, [(x - 12, y - 16), (x - 12, y + 16), (x + 16, y)])
    elif nome == "opcoes":
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(tela, cor, (x + math.cos(a) * 9, y + math.sin(a) * 9),
                             (x + math.cos(a) * 17, y + math.sin(a) * 17), 6)
        pygame.draw.circle(tela, cor, (x, y), 13)
        pygame.draw.circle(tela, fundo, (x, y), 6)
    elif nome == "sair":
        pygame.draw.arc(tela, cor, (x - 15, y - 15, 30, 30), math.radians(-60), math.radians(240), 4)
        pygame.draw.line(tela, cor, (x, y - 19), (x, y - 2), 4)


def botao_menu(tela, rect, rotulo, cor, selecionado, fonte, nome_icone, t):
    """Botão do menu principal: apagado quando solto, aceso e com seta quando selecionado."""
    fundo = misturar(PAINEL, cor, 0.22 if selecionado else 0.07)
    if selecionado:
        brilho(tela, rect, cor, intensidade=90 + int(30 * math.sin(t * 5)), raio=16)
    painel(tela, rect, borda=cor if selecionado else misturar(LINHA, cor, 0.25), fundo=fundo, raio=16,
           largura_borda=3 if selecionado else 2)
    cor_texto = TEXTO if selecionado else misturar(TEXTO3, cor, 0.35)
    icone(tela, nome_icone, (rect.x + 58, rect.centery), cor if selecionado else misturar(TEXTO3, cor, 0.4), fundo)
    texto(tela, fonte, rotulo, cor_texto, (rect.x + 108, rect.centery), "midleft")
    if selecionado:
        vai_e_vem = int(4 * math.sin(t * 7))
        triangulo(tela, (rect.right - 36 - vai_e_vem, rect.centery), 8, cor, "esquerda")


def fundo_item(tela, rect, cor, selecionado, t, raio=14, seta=True, passo=7, espessura=2):
    """Forma de um item de menu (sem texto): apagado quando solto, aceso e com seta quando selecionado."""
    fundo = misturar(PAINEL, cor, 0.22 if selecionado else 0.07)
    if selecionado:
        brilho(tela, rect, cor, intensidade=90 + int(30 * math.sin(t * 5)), raio=raio, passo=passo,
               espessura=espessura + 1)
    painel(tela, rect, borda=cor if selecionado else misturar(LINHA, cor, 0.25), fundo=fundo, raio=raio,
           largura_borda=espessura + 1 if selecionado else espessura)
    if selecionado and seta:
        vai_e_vem = int(math.sin(t * 7) * rect.h * 0.06)
        triangulo(tela, (rect.right - int(rect.h * 0.55) - vai_e_vem, rect.centery), max(3, int(rect.h * 0.13)), cor, "esquerda")
    return fundo


def lista_menu(tela, itens, indice, cor, fonte_item, centro_x, y0, largura, altura, folga, t, cores=None,
               alinhar="centro", raio=14):
    """Lista vertical de botões. Devolve os retângulos, para quem quiser desenhar algo por cima."""
    rects = []
    for i, rotulo in enumerate(itens):
        x = centro_x - largura // 2 if alinhar == "centro" else centro_x
        rect = pygame.Rect(x, y0 + i * (altura + folga), largura, altura)
        sel = i == indice
        c = cores[i] if cores else cor
        fundo_item(tela, rect, c, sel, t, raio=raio)
        cor_texto = TEXTO if sel else misturar(TEXTO3, c, 0.35)
        if alinhar == "centro":
            texto(tela, fonte_item, rotulo, cor_texto, rect.center, "center")
        else:
            texto(tela, fonte_item, rotulo, cor_texto, (rect.x + 26, rect.centery), "midleft")
        rects.append(rect)
    return rects


def modal(tela, rect, titulo, cor, fonte_titulo, linhas=(), fonte_linha=None, cor_linha=TEXTO2, escurecer=170, raio=18):
    """Caixa central para pausa, fim de jogo etc.: escurece o fundo, desenha o painel e o título."""
    if escurecer:
        veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        veu.fill((0, 0, 8, escurecer))
        tela.blit(veu, (0, 0))
    brilho(tela, rect, cor, intensidade=60, raio=raio, camadas=3)
    painel(tela, rect, borda=cor, fundo=PAINEL, raio=raio, largura_borda=3)
    y = rect.y + 20 + fonte_titulo.get_height() // 2
    texto(tela, fonte_titulo, titulo, cor, (rect.centerx, y), "center", sombra=True)
    y += fonte_titulo.get_height() // 2 + 16
    for linha in linhas:
        r = texto(tela, fonte_linha or fonte_titulo, linha, cor_linha, (rect.centerx, y), "midtop")
        y = r.bottom + 6
    return y


# --- Atalhos de teclado -----------------------------------------------------------------
def _chip(tela, f_tecla, f_texto, tecla, legenda, x, y):
    img_tecla = f_tecla.render(tecla, True, TEXTO)
    w_tecla = max(30, img_tecla.get_width() + 18)
    rect = pygame.Rect(x, y, w_tecla, 28)
    pygame.draw.rect(tela, PAINEL2, rect, border_radius=6)
    pygame.draw.rect(tela, TEXTO3, rect, width=2, border_radius=6)
    pygame.draw.line(tela, TEXTO3, (rect.x + 4, rect.bottom + 1), (rect.right - 4, rect.bottom + 1), 2)
    tela.blit(img_tecla, img_tecla.get_rect(center=rect.center))
    img_legenda = f_texto.render(legenda, True, TEXTO2)
    tela.blit(img_legenda, img_legenda.get_rect(midleft=(rect.right + 10, rect.centery)))
    return rect.right + 10 + img_legenda.get_width() + 30


def medir_atalhos(f_tecla, f_texto, itens):
    total = 0
    for tecla, legenda in itens:
        total += max(30, f_tecla.size(tecla)[0] + 18) + 10 + f_texto.size(legenda)[0] + 30
    return total - 30


def rodape_atalhos(tela, f_tecla, f_texto, itens, y, largura, fundo=False):
    """Faixa de atalhos centralizada, no estilo de teclas ("[ENTER] Jogar").
    Com fundo=True desenha uma barra escura atrás, para ler bem sobre cenários claros."""
    total = medir_atalhos(f_tecla, f_texto, itens)
    x = (largura - total) // 2
    if fundo:
        painel(tela, pygame.Rect(x - 18, y - 8, total + 36, 46), borda=LINHA, fundo=PAINEL, raio=12, alfa=225)
    for tecla, legenda in itens:
        x = _chip(tela, f_tecla, f_texto, tecla, legenda, x, y)


def etiqueta(tela, fonte, conteudo, cor, x, y):
    """Pílula pequena de classificação (gênero, nº de jogadores...). Devolve o x seguinte."""
    img = fonte.render(conteudo, True, cor)
    rect = pygame.Rect(x, y, img.get_width() + 22, 30)
    pygame.draw.rect(tela, misturar(PAINEL, cor, 0.14), rect, border_radius=15)
    pygame.draw.rect(tela, misturar(PAINEL, cor, 0.7), rect, width=2, border_radius=15)
    tela.blit(img, img.get_rect(center=rect.center))
    return rect.right + 10


# Cores do medidor de dificuldade, do mais facil (verde) ao mais dificil (vermelho).
_ESCALA_NIVEL = [(70, 210, 110), (170, 220, 70), (250, 200, 50), (250, 120, 45), (220, 50, 70)]


def cor_nivel(indice, total):
    """Cor do nivel `indice` (0 a total-1) na escala verde -> vermelho, qualquer que seja o total de niveis."""
    pos = 0 if total <= 1 else indice / (total - 1) * (len(_ESCALA_NIVEL) - 1)
    a = int(pos)
    b = min(a + 1, len(_ESCALA_NIVEL) - 1)
    return misturar(_ESCALA_NIVEL[a], _ESCALA_NIVEL[b], pos - a)


def seletor_dificuldade(tela, rect, rotulo, nome, indice, total, cor, selecionado, t):
    """Botao de dificuldade igual em todos os jogos: rotulo a esquerda e, a direita, um seletor em
    "pilula" com setas, segmentos de nivel (verde -> vermelho) e o nome do nivel.
    `indice` vai de 0 a total-1; o jogo escolhe os seus proprios niveis e nomes."""
    fundo_item(tela, rect, cor, selecionado, t, raio=14)
    cy = rect.centery
    cor_nome = cor_nivel(indice, total)
    texto(tela, fonte(12, True), rotulo, TEXTO if selecionado else misturar(TEXTO3, cor, 0.35),
          (rect.x + 24, cy), "midleft")

    f_nome = fonte(11, True)
    larg_nome = f_nome.size(nome)[0]
    seg_w, seg_h, gap = 14, 16, 4
    larg_seg = total * seg_w + (total - 1) * gap
    pad, seta_w = 14, 8
    larg = pad + seta_w + 12 + larg_seg + 14 + larg_nome + 12 + seta_w + pad
    trilho = pygame.Rect(0, 0, larg, 36)
    trilho.midright = (rect.right - 14, cy)
    pygame.draw.rect(tela, misturar((6, 8, 18), cor, 0.10), trilho, border_radius=18)
    pygame.draw.rect(tela, misturar(LINHA, cor_nome, 0.75 if selecionado else 0.35), trilho, width=2, border_radius=18)

    cor_seta = TEXTO if selecionado else TEXTO3
    triangulo(tela, (trilho.x + pad + 2, cy), 6, cor_seta, "esquerda")
    triangulo(tela, (trilho.right - pad - 3, cy), 6, cor_seta, "direita")

    x0 = trilho.x + pad + seta_w + 12
    for i in range(total):
        r = pygame.Rect(x0 + i * (seg_w + gap), cy - seg_h // 2, seg_w, seg_h)
        if i <= indice:
            c = cor_nivel(i, total)
            pygame.draw.rect(tela, c, r, border_radius=5)
            pygame.draw.rect(tela, misturar(c, (255, 255, 255), 0.45), (r.x + 3, r.y + 2, r.w - 6, 3), border_radius=2)
        else:
            pygame.draw.rect(tela, (38, 42, 66), r, border_radius=5)
    texto(tela, f_nome, nome, cor_nome, (x0 + larg_seg + 14, cy), "midleft")
