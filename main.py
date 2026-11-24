"""
E-Place - Launcher de Jogos (minimalista)
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
from src.gamepad import XboxController

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
MUSIC_MENU = os.path.join(BASE_DIR, "assets", "sounds", "eplace_menu.wav")

LARGURA, ALTURA = 1280, 720
FPS = 60

PRETO = (0, 0, 0)
BRANCO = (245, 245, 245)
CINZA = (120, 120, 120)
DESTAQUE = (255, 255, 255)


def fonte_retro(tamanho, titulo):
    """Titulos em Press Start 2P e textos em VT323 (assets/fonts). Sem os arquivos, usa fonte do sistema."""
    import os
    nome = "PressStart2P-Regular.ttf" if titulo else "VT323-Regular.ttf"
    pasta = os.path.abspath(os.path.dirname(__file__))
    for _ in range(8):
        caminho = os.path.join(pasta, "assets", "fonts", nome)
        if os.path.exists(caminho):
            return pygame.font.Font(caminho, max(8, int(tamanho)))
        pasta = os.path.dirname(pasta)
    return pygame.font.SysFont("arial,helveticaneue,dejavusans", int(tamanho), bold=titulo)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CONFIG_PADRAO = {"tela_cheia": False, "volume": 70, "som_menu": True, "titulo": "EPLACE"}


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


# Nomes exibidos no launcher quando diferem do nome da pasta do jogo.
NOMES_DOS_JOGOS = {"Ping pong": "Pong", "Flappy bird": "Flappy Bird"}


def nome_bonito(nome):
    if nome in NOMES_DOS_JOGOS:
        return NOMES_DOS_JOGOS[nome]
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
        self.controle = XboxController()
        pygame.display.set_caption("E-Place - Launcher")
        self.cfg = carregar_config()
        self.som_botao = None
        self._iniciar_musica_menu()
        try:
            caminho_som = os.path.join(BASE_DIR, "assets", "sounds", "menu_click.wav")
            if os.path.exists(caminho_som) and pygame.mixer.get_init():
                self.som_botao = pygame.mixer.Sound(caminho_som)
                self._atualizar_volume_som_botao()
        except pygame.error:
            self.som_botao = None

        self.gestor = GestorJogador(os.path.join(BASE_DIR, "data"))

        self.janela = None
        self.tela = pygame.Surface((LARGURA, ALTURA))   # tudo e desenhado aqui
        self._aplicar_tela()
        self.clock = pygame.time.Clock()

        self.f_titulo = fonte_retro(40, True)
        self.f_menu = fonte_retro(28, True)
        self.f_item = fonte_retro(22, True)
        self.f_pequena = fonte_retro(24, False)

        self.cena = "home"
        self.origem_recordes = "home"
        self.recordes = []
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

        # Transicao curta de fade para Configuracoes e Recordes.
        self.trans_tela_ativa = False
        self.trans_tela_t = 0.0
        self.TRANS_TELA_DUR = 0.42
        self.trans_tela_destino = None
        self.trans_tela_trocou = False

        extrair_zips(GAMES_DIR)
        self.jogos = listar_jogos()
        self.jogo_idx = 0

    def _atualizar_volume_som_botao(self):
        try:
            if self.som_botao:
                # Volume dos efeitos e independente do volume da musica.
                self.som_botao.set_volume(0.45)
        except pygame.error:
            pass

    def _tocar_som_botao(self):
        """Reproduz um clique curto ao navegar ou selecionar itens do menu."""
        try:
            if self.cfg.get("som_menu", True) and self.som_botao:
                self.som_botao.play()
        except pygame.error:
            pass

    def _aplicar_som_menu(self):
        """Liga/desliga somente os efeitos de navegacao do launcher."""
        try:
            if not pygame.mixer.get_init():
                return
            if self.cfg.get("som_menu", True):
                self._atualizar_volume_som_botao()
            elif self.som_botao:
                self.som_botao.stop()
        except pygame.error:
            pass

    def _iniciar_musica_menu(self):
        """Inicia a trilha do menu independentemente dos efeitos de navegacao."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            if os.path.exists(MUSIC_MENU):
                pygame.mixer.music.load(MUSIC_MENU)
                self._atualizar_volume_musica()
                pygame.mixer.music.play(-1)
        except pygame.error as erro:
            # O launcher continua funcionando mesmo em computadores sem áudio.
            print("Não foi possível iniciar a música do menu:", erro)

    def _atualizar_volume_musica(self):
        """Aplica imediatamente o volume escolhido nas configurações (0 a 100)."""
        try:
            volume = max(0, min(100, int(self.cfg.get("volume", 70))))
            if pygame.mixer.get_init():
                # Este controle altera apenas a trilha de fundo.
                pygame.mixer.music.set_volume(volume / 100.0)
        except (pygame.error, TypeError, ValueError):
            pass

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

            if self.trans_tela_ativa:
                self.trans_tela_t += dt
                metade = self.TRANS_TELA_DUR / 2
                if not self.trans_tela_trocou and self.trans_tela_t >= metade:
                    self.cena = self.trans_tela_destino
                    self.trans_tela_trocou = True
                if self.trans_tela_t >= self.TRANS_TELA_DUR:
                    self.trans_tela_ativa = False
                    self.trans_tela_destino = None
            self.eventos()
            self.desenhar()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # -------------------------------------------------------------- eventos
    def eventos(self):
        eventos = pygame.event.get()
        eventos.extend(self.controle.poll_keys())
        for e in eventos:
            if e.type == pygame.QUIT:
                self.rodando = False
            elif e.type == pygame.KEYDOWN and not self.trans_tela_ativa:
                if (self.cena in ("home", "jogos", "config", "recordes") and
                        e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                                  pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
                                  pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE,
                                  pygame.K_ESCAPE, pygame.K_h, pygame.K_r)):
                    self._tocar_som_botao()
                if self.cena == "home":
                    self._ev_home(e)
                elif self.cena == "jogos":
                    self._ev_jogos(e)
                elif self.cena == "config":
                    self._ev_config(e)
                elif self.cena == "recordes":
                    self._ev_recordes(e)

    def _ev_home(self, e):
        if e.key == pygame.K_h:
            self._abrir_recordes("home")
        elif e.key in (pygame.K_UP, pygame.K_w):
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
                self._iniciar_transicao_tela("config")
            elif escolha == "Sair":
                self.rodando = False
        elif e.key == pygame.K_ESCAPE:
            self.rodando = False

    def _ev_jogos(self, e):
        if e.key == pygame.K_h:
            self._abrir_recordes("jogos")
        elif e.key in (pygame.K_UP, pygame.K_w):
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

    def _iniciar_transicao_tela(self, destino):
        """Faz fade-out, troca a tela no escuro e faz fade-in."""
        if self.trans_tela_ativa:
            return
        self.trans_tela_ativa = True
        self.trans_tela_t = 0.0
        self.trans_tela_destino = destino
        self.trans_tela_trocou = False

    def _abrir_recordes(self, origem):
        self.origem_recordes = origem
        self.recordes = self._carregar_recordes()
        self._iniciar_transicao_tela("recordes")

    def _ev_recordes(self, e):
        if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_h):
            self._iniciar_transicao_tela(self.origem_recordes)
        elif e.key == pygame.K_r:
            self.recordes = self._carregar_recordes()

    def _ler_json(self, caminho, chave, padrao=0):
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            return max(0, int(dados.get(chave, padrao)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def _carregar_recordes(self):
        cobrinha = os.path.join(os.path.expanduser("~"), ".cobra_neon_recorde.txt")
        try:
            with open(cobrinha, "r", encoding="utf-8") as arquivo:
                recorde_cobrinha = max(0, int(arquivo.read().strip()))
        except (OSError, ValueError):
            recorde_cobrinha = 0

        base_jogos = GAMES_DIR
        dados = [
            ("Snake", recorde_cobrinha, "pontos"),
            ("Flappy Bird", self._ler_json(os.path.join(base_jogos, "Flappy bird", "savegame.json"), "best"), "pontos"),
            ("Frogger", self._ler_json(os.path.join(base_jogos, "Frogger", "recorde.json"), "recorde"), "pontos"),
            ("Space Invaders", self._ler_json(os.path.join(base_jogos, "Space Invaders", "highscore.json"), "recorde"), "pontos"),
            ("Pong", self._ler_json(os.path.join(base_jogos, "Ping pong", "recorde.json"), "recorde"), "vitorias"),
            ("Kombate", self._ler_json(os.path.join(base_jogos, "Kombate", "recorde.json"), "recorde"), "vitorias"),
        ]
        return sorted(dados, key=lambda item: item[1] if item[1] is not None else -1, reverse=True)

    def _ev_config(self, e):
        opcoes = ["tela_cheia", "volume", "som_menu", "voltar"]
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
                self._atualizar_volume_musica()
                salvar_config(self.cfg)
            elif alvo == "som_menu":
                self.cfg["som_menu"] = not self.cfg.get("som_menu", True)
                self._aplicar_som_menu()
                salvar_config(self.cfg)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            alvo = opcoes[self.config_idx]
            if alvo == "som_menu":
                self.cfg["som_menu"] = not self.cfg.get("som_menu", True)
                self._aplicar_som_menu()
                salvar_config(self.cfg)
            elif alvo == "voltar":
                salvar_config(self.cfg)
                self._iniciar_transicao_tela("home")
        elif e.key == pygame.K_ESCAPE:
            salvar_config(self.cfg)
            self._iniciar_transicao_tela("home")

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
        # Permite que os jogos importem o modulo compartilhado de controle.
        env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
        # O launcher continua aberto em segundo plano, mas a musica do menu
        # deve ficar pausada enquanto o jogo estiver em primeiro plano.
        musica_pausada = False
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                musica_pausada = True
        except pygame.error:
            pass

        try:
            proc = subprocess.Popen([sys.executable, jogo["main"]],
                                    cwd=jogo["caminho"], env=env)
            # espera o jogo fechar, mantendo o launcher "vivo" por tras
            while proc.poll() is None:
                pygame.event.pump()
                self.clock.tick(15)
        except Exception as ex:
            print("Erro ao iniciar o jogo:", ex)
        finally:
            # Retoma a trilha do ponto em que foi pausada ao voltar ao menu.
            if musica_pausada:
                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.unpause()
                except pygame.error:
                    pass

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
        elif self.cena == "recordes":
            self._draw_recordes()

        # Camada de fade por cima da cena atual; a troca ocorre no preto.
        if self.trans_tela_ativa:
            progresso = min(1.0, self.trans_tela_t / self.TRANS_TELA_DUR)
            metade = 0.5
            if progresso < metade:
                fase = progresso / metade
            else:
                fase = (1.0 - progresso) / metade
            # smoothstep para evitar uma variacao brusca de opacidade
            fase = max(0.0, min(1.0, fase))
            fase = fase * fase * (3.0 - 2.0 * fase)
            camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            camada.fill((0, 0, 0, int(255 * fase)))
            self.tela.blit(camada, (0, 0))

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

        self._rodape("SETAS / ANALOGICO mover   |   A selecionar   |   B voltar   |   QUADRADO / X / Y recordes")

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

        x_dir = LARGURA - 70
        centro_y = ALTURA // 2
        espaco = 74

        # Capa em destaque, centralizada e preservando a proporcao original.
        jogo_atual = self.jogos[self.jogo_idx]
        caminho_capa = jogo_atual.get("capa")
        if caminho_capa:
            if caminho_capa not in self.capas_cache:
                try:
                    original = pygame.image.load(caminho_capa).convert_alpha()
                    iw, ih = original.get_size()
                    # Capas quadradas: manter a proporcao e limitar ao mesmo espaco.
                    escala = min(378 / iw, 378 / ih)
                    tamanho = (max(1, int(iw * escala)), max(1, int(ih * escala)))
                    self.capas_cache[caminho_capa] = pygame.transform.smoothscale(original, tamanho)
                except (pygame.error, OSError):
                    self.capas_cache[caminho_capa] = None

            capa_img = self.capas_cache[caminho_capa]
            if capa_img:
                centro_capa = (570, centro_y)
                rect = capa_img.get_rect(center=centro_capa)

                # Moldura quadrada, acompanhando o formato 1:1 das capas.
                margem = 9
                moldura = rect.inflate(margem * 2, margem * 2)
                sombra = moldura.move(7, 9)
                pygame.draw.rect(self.tela, (0, 0, 0), sombra, border_radius=8)
                pygame.draw.rect(self.tela, (12, 19, 36), moldura, border_radius=8)
                pygame.draw.rect(self.tela, (35, 225, 190), moldura, width=3, border_radius=8)
                externa = moldura.inflate(8, 8)
                pygame.draw.rect(self.tela, (90, 120, 255), externa, width=2, border_radius=10)

                self.tela.blit(capa_img, rect)
                pygame.draw.rect(self.tela, (235, 245, 255), rect, width=1)

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
            "DIRECIONAL / ANALOGICO mover   |   A jogar   |   B voltar")

    def _draw_recordes(self):
        self._fundo(self.bg_jogos)
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        camada.fill((3, 5, 18, 220))
        self.tela.blit(camada, (0, 0))

        titulo = self.f_titulo.render("RECORDES", True, (90, 220, 255))
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 82)))
        subtitulo = self.f_pequena.render("RECORDES PESSOAIS DOS JOGOS", True, (170, 190, 220))
        self.tela.blit(subtitulo, subtitulo.get_rect(center=(LARGURA // 2, 128)))

        medalhas = [(255, 205, 70), (190, 205, 220), (205, 135, 85)]
        inicio_y = 190
        for i, (nome, pontos, detalhe) in enumerate(self.recordes):
            y = inicio_y + i * 72
            cartao = pygame.Rect(250, y - 27, 780, 56)
            pygame.draw.rect(self.tela, (13, 25, 48), cartao, border_radius=9)
            cor_borda = medalhas[i] if i < 3 and pontos is not None and pontos > 0 else (45, 75, 105)
            pygame.draw.rect(self.tela, cor_borda, cartao, width=2, border_radius=9)

            posicao = self.f_item.render(f"#{i + 1}", True, cor_borda)
            self.tela.blit(posicao, (cartao.x + 18, cartao.y + 9))
            nome_img = self.f_item.render(nome, True, BRANCO)
            self.tela.blit(nome_img, (cartao.x + 95, cartao.y + 9))

            if pontos is None:
                valor_txt = detalhe.upper()
                cor_valor = (145, 155, 175)
            elif pontos == 0:
                valor_txt = "SEM RECORDE"
                cor_valor = (145, 155, 175)
            else:
                unidade = "PTS" if detalhe == "pontos" else detalhe.upper()
                valor_txt = f"{pontos:,} {unidade}".replace(",", ".")
                cor_valor = (90, 235, 180)
            valor_img = self.f_pequena.render(valor_txt, True, cor_valor)
            self.tela.blit(valor_img, valor_img.get_rect(midright=(cartao.right - 20, cartao.centery)))

        self._rodape("R atualizar   |   ESC / BACKSPACE voltar")

    def _draw_config(self):
        self._fundo(None)
        titulo = self.f_titulo.render("CONFIGURACOES", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 120)))
        status_controle = (f"CONTROLE: {self.controle.device_name.upper()} CONECTADO"
                           if self.controle.connected else "CONTROLE: DESCONECTADO")
        cor_controle = (70, 230, 160) if self.controle.connected else (150, 150, 150)
        status_img = self.f_pequena.render(status_controle, True, cor_controle)
        self.tela.blit(status_img, status_img.get_rect(center=(LARGURA // 2, 185)))

        opcoes = [
            ("Tela cheia", "LIGADO" if self.cfg["tela_cheia"] else "DESLIGADO"),
            ("Volume da música", f"{self.cfg['volume']}%"),
            ("Sons de navegação", "LIGADOS" if self.cfg.get("som_menu", True) else "DESLIGADOS"),
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

            # Barra visual do volume: acompanha em tempo real as setas esquerda/direita.
            if i == 1:
                barra = pygame.Rect(cx - 150, base_y + 1 * 78 + 28, 300, 12)
                pygame.draw.rect(self.tela, (45, 55, 75), barra, border_radius=6)
                preenchido = barra.copy()
                preenchido.width = int(barra.width * self.cfg["volume"] / 100)
                if preenchido.width > 0:
                    pygame.draw.rect(self.tela, (0, 220, 255), preenchido, border_radius=6)
                x_knob = barra.x + int(barra.width * self.cfg["volume"] / 100)
                pygame.draw.circle(self.tela, (255, 255, 255), (x_knob, barra.centery), 9)

        self._rodape(
            "SETAS mover / alterar   |   ENTER alternar / selecionar   |   ESC voltar")

    def _rodape(self, texto):
        t = self.f_pequena.render(texto, True, CINZA)
        self.tela.blit(t, (24, ALTURA - 34))


if __name__ == "__main__":
    Eplace().run()
