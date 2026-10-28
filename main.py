"""
Eplace - Launcher de Jogos (minimalista)
========================================
Tela inicial: imagem de fundo (assets/ui/background.png) + menu central
(Jogar / Configuracoes / Sair) com animacao subindo/descendo.

Tela de jogos: fundo preto + lista dos jogos na LATERAL (game1..game5)
com animacao subindo/descendo, estilo "menu de emulador".

Rode com:  python main.py
"""

from src.jogador import GestorJogador
from src.utils.zip_extractor import extrair_zips
import pygame
import os
import sys
import json
import math
import subprocess

# Janela sem borda do tamanho do monitor (nao troca a resolucao = nao pisca)
os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"


# ---------------------------------------------------------------------------
# Caminhos / Constantes
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
GAMES_DIR = os.path.join(SRC_DIR, "games")
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")
UI_DIR = os.path.join(BASE_DIR, "assets", "ui")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# fundos opcionais
BG_HOME = os.path.join(UI_DIR, "background.png")
BG_JOGOS = os.path.join(UI_DIR, "background_jogos.png")

LARGURA, ALTURA = 1280, 720
FPS = 60

PRETO = (0, 0, 0)
BRANCO = (245, 245, 245)
CINZA = (120, 120, 120)
DESTAQUE = (255, 255, 255)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CONFIG_PADRAO = {"tela_cheia": False, "volume": 70, "titulo": "EPLACE"}


def carregar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                base = dict(CONFIG_PADRAO)
                base.update(json.load(f))
                return base
        except Exception:
            pass
    return dict(CONFIG_PADRAO)


def salvar_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Erro ao salvar config:", e)


# ---------------------------------------------------------------------------
# Jogos
# ---------------------------------------------------------------------------
def listar_jogos():
    jogos = []
    if not os.path.isdir(GAMES_DIR):
        return jogos
    for nome in sorted(os.listdir(GAMES_DIR)):
        caminho = os.path.join(GAMES_DIR, nome)
        if not os.path.isdir(caminho) or nome == "imports":
            continue
        main_jogo = os.path.join(caminho, "main.py")

        # Procura a imagem da capa
        capa_path = None
        for ext in [".png", ".jpg", ".jpeg"]:
            p = os.path.join(COVERS_DIR, nome + ext)
            if os.path.exists(p):
                capa_path = p
                break

        if os.path.exists(main_jogo):
            jogos.append({
                "id": nome,
                "titulo": nome_bonito(nome),
                "caminho": caminho,
                "main": main_jogo,
                "capa": capa_path  # Adicionado aqui
            })
    return jogos


def nome_bonito(nome):
    if nome.lower().startswith("game") and nome[4:].isdigit():
        return "Game " + nome[4:]
    return nome[:1].upper() + nome[1:]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class Eplace:
    def __init__(self):
        # ... outras variáveis que já estão no seu código ...
        self.jogo_idx = 0
        self.capas_cache = {}  # Adicione esta linha aqui
        pygame.init()
        pygame.display.set_caption("Eplace - Launcher")
        self.cfg = carregar_config()

        self.gestor = GestorJogador(os.path.join(BASE_DIR, "data"))

        self.janela = None
        self.tela = pygame.Surface((LARGURA, ALTURA))   # tudo e desenhado aqui
        self._aplicar_tela()
        self.clock = pygame.time.Clock()

        self.f_titulo = pygame.font.SysFont("Arial", 60, bold=True)
        self.f_menu = pygame.font.SysFont("Arial", 44, bold=True)
        self.f_item = pygame.font.SysFont("Arial", 34, bold=True)
        self.f_pequena = pygame.font.SysFont("Arial", 18)

        self.cena = "home"
        self.rodando = True
        self.t = 0.0                       # tempo pra animacao

        self.menu_idx = 0
        self.menu_itens = ["Jogar", "Configuracoes", "Sair"]
        self.config_idx = 0

        # HOME: guarda a imagem original da logo pra animar em tempo real
        self.bg_home_img = None
        if os.path.exists(BG_HOME):
            try:
                self.bg_home_img = pygame.image.load(BG_HOME).convert()
            except Exception:
                self.bg_home_img = None

        if self.bg_home_img:
            iw, ih = self.bg_home_img.get_size()
            # escala base 'fit' (logo inteira visivel, sem animacao)
            self.home_esc_base = min(LARGURA / iw, ALTURA / ih)
            nw, nh = int(iw * self.home_esc_base), int(ih * self.home_esc_base)
            self.home_esc = self.home_esc_base
            self.home_offx = (LARGURA - nw) // 2
            self.home_offy = (ALTURA - nh) // 2
        else:
            self.home_esc_base = 1.0
            self.home_esc = 1.0
            self.home_offx = 0
            self.home_offy = 0

        self.bg_jogos = self._carregar_bg(BG_JOGOS)

        # posicao dos 3 botoes NA ARTE ORIGINAL (coords da imagem 1254x1254)
        # [x, y, largura, altura] -> ARCADE, OPCOES, SAIR
        self.botoes_orig = [
            [324, 737, 623, 114],   # Jogar   (ARCADE)
            [324, 875, 623, 108],   # Config  (OPCOES)
            [324, 1007, 623, 108],  # Sair    (SAIR)
        ]

        # estado da transicao (logo indo pro canto = marca dagua)
        self.trans_ativa = False
        self.trans_t = 0.0
        self.TRANS_DUR = 0.7            # duracao da transicao (segundos)
        self.trans_reversa = False     # False = home->jogos | True = jogos->home

        extrair_zips(GAMES_DIR)
        self.jogos = listar_jogos()
        self.jogo_idx = 0

    def _carregar_bg(self, caminho):
        """Carrega imagem no modo 'cover' (preenche a tela, corta o excesso)."""
        if not os.path.exists(caminho):
            return None
        try:
            img = pygame.image.load(caminho).convert()
            iw, ih = img.get_size()
            escala = max(LARGURA / iw, ALTURA / ih)
            nw, nh = int(iw * escala), int(ih * escala)
            img = pygame.transform.smoothscale(img, (nw, nh))
            x = (nw - LARGURA) // 2
            y = (nh - ALTURA) // 2
            recorte = pygame.Surface((LARGURA, ALTURA))
            recorte.blit(img, (0, 0), (x, y, LARGURA, ALTURA))
            return recorte
        except Exception:
            return None

    def _carregar_bg_fit(self, caminho):
        """Carrega no modo 'fit' (imagem inteira visivel, bordas pretas).
        Retorna (surface_tela_cheia, escala, offx, offy) pra posicionar o seletor.
        """
        if not os.path.exists(caminho):
            return None, 1.0, 0, 0
        try:
            img = pygame.image.load(caminho).convert()
            iw, ih = img.get_size()
            escala = min(LARGURA / iw, ALTURA / ih)
            nw, nh = int(iw * escala), int(ih * escala)
            img = pygame.transform.smoothscale(img, (nw, nh))
            offx = (LARGURA - nw) // 2
            offy = (ALTURA - nh) // 2
            base = pygame.Surface((LARGURA, ALTURA))
            base.fill(PRETO)
            base.blit(img, (offx, offy))
            return base, escala, offx, offy
        except Exception:
            return None, 1.0, 0, 0

    # ------------------------------------------------------------------ loop
    def run(self):
        while self.rodando:
            dt = self.clock.get_time() / 1000.0
            self.t += dt
            # avanca a transicao
            if self.cena == "transicao":
                self.trans_t += dt
                if self.trans_t >= self.TRANS_DUR:
                    # reversa termina na HOME, normal termina em JOGOS
                    self.cena = "home" if self.trans_reversa else "jogos"
            self.eventos()
            self.desenhar()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # -------------------------------------------------------------- eventos
    def eventos(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.rodando = False
            elif e.type == pygame.KEYDOWN:
                if self.cena == "home":
                    self._ev_home(e)
                elif self.cena == "jogos":
                    self._ev_jogos(e)
                elif self.cena == "config":
                    self._ev_config(e)

    def _ev_home(self, e):
        if e.key in (pygame.K_UP, pygame.K_w):
            self.menu_idx = (self.menu_idx - 1) % len(self.menu_itens)
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_itens)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            escolha = self.menu_itens[self.menu_idx]
            if escolha == "Jogar":
                self.jogos = listar_jogos()
                self.trans_ativa = True
                self.trans_reversa = False
                self.trans_t = 0.0
                self.cena = "transicao"
            elif escolha == "Configuracoes":
                self.cena = "config"
            elif escolha == "Sair":
                self.rodando = False
        elif e.key == pygame.K_ESCAPE:
            self.rodando = False

    def _ev_jogos(self, e):
        if e.key in (pygame.K_UP, pygame.K_w):
            if self.jogos:
                self.jogo_idx = (self.jogo_idx - 1) % len(self.jogos)
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            if self.jogos:
                self.jogo_idx = (self.jogo_idx + 1) % len(self.jogos)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.iniciar_jogo()
        elif e.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
            # volta pra home com a animacao reversa (logo cresce do canto)
            self.trans_ativa = True
            self.trans_reversa = True
            self.trans_t = 0.0
            self.cena = "transicao"

    def _ev_config(self, e):
        opcoes = ["tela_cheia", "volume", "voltar"]
        if e.key in (pygame.K_UP, pygame.K_w):
            self.config_idx = (self.config_idx - 1) % len(opcoes)
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            self.config_idx = (self.config_idx + 1) % len(opcoes)
        elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            alvo = opcoes[self.config_idx]
            direcao = 1 if e.key in (pygame.K_RIGHT, pygame.K_d) else -1
            if alvo == "tela_cheia":
                self.cfg["tela_cheia"] = not self.cfg["tela_cheia"]
                self._aplicar_tela()
            elif alvo == "volume":
                self.cfg["volume"] = max(
                    0, min(100, self.cfg["volume"] + direcao * 5))
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            if opcoes[self.config_idx] == "voltar":
                salvar_config(self.cfg)
                self.cena = "home"
        elif e.key == pygame.K_ESCAPE:
            salvar_config(self.cfg)
            self.cena = "home"

    def _aplicar_tela(self):
        if self.cfg.get("tela_cheia"):
            tamanho = pygame.display.get_desktop_sizes()[0]
            self.janela = pygame.display.set_mode(tamanho, pygame.NOFRAME)
        else:
            self.janela = pygame.display.set_mode((LARGURA, ALTURA))

    def _apresentar(self):
        """Amplia a tela 1280x720 para a janela, sem distorcer."""
        jw, jh = self.janela.get_size()
        if (jw, jh) == (LARGURA, ALTURA):
            self.janela.blit(self.tela, (0, 0))
        else:
            esc = min(jw / LARGURA, jh / ALTURA)
            img = pygame.transform.smoothscale(
                self.tela, (int(LARGURA * esc), int(ALTURA * esc)))
            self.janela.fill(PRETO)
            self.janela.blit(img, img.get_rect(center=(jw // 2, jh // 2)))
        pygame.display.flip()

    # --------------------------------------------------------------- jogos
    def iniciar_jogo(self):
        if not self.jogos:
            return
        jogo = self.jogos[self.jogo_idx]

        # Tela de "carregando" (o launcher NAO fecha, entao nada pisca)
        self.tela.fill(PRETO)
        txt = self.f_menu.render(
            f"Abrindo {jogo['titulo']}...", True, (235, 235, 235))
        self.tela.blit(txt, txt.get_rect(center=(LARGURA // 2, ALTURA // 2)))
        self._apresentar()

        env = os.environ.copy()
        env["SDL_VIDEO_WINDOW_POS"] = "0,0"
        env["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
        try:
            proc = subprocess.Popen([sys.executable, jogo["main"]],
                                    cwd=jogo["caminho"], env=env)
            # espera o jogo fechar, mantendo o launcher "vivo" por tras
            while proc.poll() is None:
                pygame.event.pump()
                self.clock.tick(15)
        except Exception as ex:
            print("Erro ao iniciar o jogo:", ex)

        # Jogo fechou: volta direto para a tela inicial
        pygame.event.clear()
        self.clock.tick()
        self.trans_ativa = False
        self.menu_idx = 0
        self.cena = "home"

    def _recarregar_imagens(self):
        """Recarrega as imagens depois de reabrir a janela."""
        if os.path.exists(BG_HOME):
            try:
                self.bg_home_img = pygame.image.load(BG_HOME).convert()
            except Exception:
                self.bg_home_img = None
        self.bg_jogos = self._carregar_bg(BG_JOGOS)

    # ------------------------------------------------------------- desenho
    def _bob(self, fase=0.0):
        """deslocamento vertical suave (sobe/desce)."""
        return math.sin(self.t * 3.0 + fase) * 6

    def desenhar(self):
        if self.cena == "home":
            self._draw_home()
        elif self.cena == "transicao":
            self._draw_transicao()
        elif self.cena == "jogos":
            self._draw_jogos()
        elif self.cena == "config":
            self._draw_config()
        self._apresentar()

    def _fundo(self, bg):
        if bg:
            self.tela.blit(bg, (0, 0))
        else:
            self.tela.fill(PRETO)

    def _texto_sombra(self, texto, fonte, cor, centro):
        """Desenha texto com sombra pra ficar legivel sobre a arte."""
        sombra = fonte.render(texto, True, PRETO)
        self.tela.blit(sombra, sombra.get_rect(
            center=(centro[0] + 2, centro[1] + 2)))
        img = fonte.render(texto, True, cor)
        rect = img.get_rect(center=centro)
        self.tela.blit(img, rect)
        return rect

    def _botao_tela(self, i, esc, ox, oy):
        """Converte o botao i (coords da arte) para o retangulo na tela."""
        x, y, w, h = self.botoes_orig[i]
        return pygame.Rect(int(ox + x * esc), int(oy + y * esc),
                           int(w * esc), int(h * esc))

    def _desenhar_logo(self, esc, ox, oy, alpha=255):
        """Desenha a arte E-PLACE (sem animacao) na escala/posicao dadas."""
        if not self.bg_home_img:
            return
        iw, ih = self.bg_home_img.get_size()
        nw, nh = max(1, int(iw * esc)), max(1, int(ih * esc))
        img = pygame.transform.smoothscale(self.bg_home_img, (nw, nh))
        if alpha < 255:
            img = img.copy()
            img.set_alpha(alpha)
        self.tela.blit(img, (ox, oy))

    # ---- HOME: logo E-PLACE fixa + seletor fixo sobre os botoes ----
    def _draw_home(self):
        self.tela.fill(PRETO)
        esc, ox, oy = self.home_esc_base, self.home_offx, self.home_offy
        self._desenhar_logo(esc, ox, oy)

        rect = self._botao_tela(self.menu_idx, esc, ox, oy)
        sel = rect.inflate(18, 12)

        for k, alfa in ((10, 40), (6, 80), (2, 160)):
            s = pygame.Surface((sel.w + k * 2, sel.h + k * 2), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, alfa),
                             s.get_rect(), width=3, border_radius=14)
            self.tela.blit(s, (sel.x - k, sel.y - k))
        pygame.draw.rect(self.tela, DESTAQUE, sel, width=4, border_radius=14)

        self._rodape("SETAS mover   |   ENTER selecionar   |   ESC sair")

    # ---- TRANSICAO: logo desliza pro canto sup. esquerdo (marca dagua) ----
    def _marca_dagua_alvo(self):
        """Escala/posicao final da logo como marca dagua no canto sup. esq."""
        esc = self.home_esc_base * 0.28          # bem menor
        ox, oy = 20, 20                          # canto superior esquerdo
        return esc, ox, oy

    def _draw_transicao(self):
        self.tela.fill(PRETO)
        p = min(1.0, self.trans_t / self.TRANS_DUR)
        # easing suave (ease-in-out)
        p = p * p * (3 - 2 * p)

        # na reversa, o progresso vai de 1 -> 0 (do canto de volta pro centro)
        if self.trans_reversa:
            p = 1.0 - p
            # na volta, tambem mostra a lista de jogos "saindo" ao fundo? nao,
            # mantemos so a logo pra ficar limpo, igual a ida.

        e0, x0, y0 = self.home_esc_base, self.home_offx, self.home_offy   # centro
        e1, x1, y1 = self._marca_dagua_alvo()                            # canto

        esc = e0 + (e1 - e0) * p
        ox = int(x0 + (x1 - x0) * p)
        oy = int(y0 + (y1 - y0) * p)
        alpha = int(255 + (110 - 255) * p)       # 255 no centro, 110 no canto

        self._desenhar_logo(esc, ox, oy, alpha)

    # ---- JOGOS (lista na lateral, animada, fundo preto) ----
    def _draw_jogos(self):
        self._fundo(self.bg_jogos)

        # logo como marca dagua no canto superior esquerdo
        e1, x1, y1 = self._marca_dagua_alvo()
        self._desenhar_logo(e1, x1, y1, alpha=110)

        if not self.jogos:
            aviso = self.f_menu.render("Nenhum jogo em /games", True, CINZA)
            self.tela.blit(aviso, aviso.get_rect(
                center=(LARGURA // 2, ALTURA // 2)))
            self._rodape("ESC voltar")
            return

        x_dir = LARGURA - 90
        centro_y = ALTURA // 2
        espaco = 74

        # Exibir capa do jogo selecionado
        jogo_atual = self.jogos[self.jogo_idx]
        caminho_capa = jogo_atual.get("capa")

        if caminho_capa:
            if caminho_capa not in self.capas_cache:
                try:
                    img = pygame.image.load(caminho_capa).convert_alpha()
                    # Redimensiona para um tamanho fixo (ex: 500x350)
                    img = pygame.transform.smoothscale(img, (500, 350))
                    self.capas_cache[caminho_capa] = img
                except:
                    self.capas_cache[caminho_capa] = None

            capa_img = self.capas_cache[caminho_capa]
            if capa_img:
                rect = capa_img.get_rect(
                    center=(LARGURA // 2 - 150, ALTURA // 2))
                self.tela.blit(capa_img, rect)
                pygame.draw.rect(self.tela, DESTAQUE, rect,
                                 width=3, border_radius=4)

        for i, jogo in enumerate(self.jogos):
            offset = i - self.jogo_idx
            sel = (offset == 0)
            y = centro_y + offset * espaco
            if y < -40 or y > ALTURA + 40:
                continue

            if sel:
                dy = self._bob()
                cor = DESTAQUE
                fonte = self.f_menu
            else:
                dy = 0
                fade = max(60, 160 - abs(offset) * 35)
                cor = (fade, fade, fade)
                fonte = self.f_item

            txt = fonte.render(jogo["titulo"], True, cor)
            rect = txt.get_rect(midright=(x_dir, y + dy))
            self.tela.blit(txt, rect)

            if sel:
                pygame.draw.rect(self.tela, DESTAQUE,
                                 (rect.right + 12, rect.centery - 14, 5, 28),
                                 border_radius=2)

        self._rodape(
            "SETAS cima/baixo   |   ENTER jogar   |   BACKSPACE / ESC voltar (animado)")

    def _draw_config(self):
        self._fundo(None)
        titulo = self.f_titulo.render("CONFIGURACOES", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 120)))

        opcoes = [
            ("Tela cheia",
             "LIGADO" if self.cfg["tela_cheia"] else "DESLIGADO"),
            ("Volume", f"{self.cfg['volume']}%"),
            ("Voltar", ""),
        ]
        cx = LARGURA // 2
        base_y = 300
        for i, (label, valor) in enumerate(opcoes):
            sel = (i == self.config_idx)
            dy = self._bob(i) if sel else 0
            cor = DESTAQUE if sel else CINZA
            texto = label if not valor else f"{label}:  {valor}"
            fonte = self.f_menu if sel else self.f_item
            txt = fonte.render(texto, True, cor)
            self.tela.blit(txt, txt.get_rect(
                center=(cx, base_y + i * 78 + dy)))

        self._rodape(
            "SETAS mover / alterar   |   ENTER confirmar   |   ESC voltar")

    def _rodape(self, texto):
        t = self.f_pequena.render(texto, True, CINZA)
        self.tela.blit(t, (24, ALTURA - 34))


if __name__ == "__main__":
    Eplace().run()
