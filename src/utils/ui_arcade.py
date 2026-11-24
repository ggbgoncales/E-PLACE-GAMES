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


def brilho(tela, rect, cor, intensidade=70, raio=14, camadas=4):
    """Aura neon ao redor de um retângulo."""
    for k in range(camadas, 0, -1):
        r = rect.inflate(k * 7, k * 7)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*cor, max(6, int(intensidade / k))), s.get_rect(), width=3, border_radius=raio + k * 3)
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


def rodape_atalhos(tela, f_tecla, f_texto, itens, y, largura):
    """Faixa de atalhos centralizada, no estilo de teclas ("[ENTER] Jogar")."""
    x = (largura - medir_atalhos(f_tecla, f_texto, itens)) // 2
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
