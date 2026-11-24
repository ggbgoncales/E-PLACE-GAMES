"""
E-Place - Launcher de Jogos
===========================
Abertura com logo e menu (Arcade / Opcoes / Sair), escolha de jogo com capa e ficha,
tela de recordes e opcoes. O visual (fundo animado, botoes, paineis) fica em
src/utils/ui_arcade.py.

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
from src.utils import ui_arcade as ui

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
LOGO = os.path.join(UI_DIR, "logo.png")
MUSIC_MENU = os.path.join(BASE_DIR, "assets", "sounds", "eplace_menu.wav")

# Ficha de cada jogo na tela de escolha (chave = título exibido no launcher).
INFO_JOGOS = {
    "Snake": {"genero": "ARCADE", "jogadores": "1 JOGADOR", "cor": (84, 255, 139),
              "descricao": "Coma as frutas, faça combos e escape das paredes. Três dificuldades."},
    "Pong": {"genero": "ESPORTE", "jogadores": "1 OU 2 JOGADORES", "cor": (24, 231, 255),
             "descricao": "Rebata a bola e vença a CPU ou um amigo. Quem chegar a 7 pontos vence."},
    "Frogger": {"genero": "REFLEXO", "jogadores": "1 JOGADOR", "cor": (140, 230, 70),
                "descricao": "Atravesse o rio em fases infinitas, pulando em troncos e tartarugas."},
    "Space Invaders": {"genero": "AÇÃO", "jogadores": "1 JOGADOR", "cor": (138, 91, 255),
                       "descricao": "Pilote a nave, destrua inimigos e asteroides e sobreviva às ondas."},
    "Flappy Bird": {"genero": "ARCADE", "jogadores": "1 JOGADOR", "cor": (255, 205, 0),
                    "descricao": "Passe pelos canos, junte moedas e personalize o pássaro na loja."},
    "Kombate": {"genero": "LUTA", "jogadores": "1 OU 2 JOGADORES", "cor": (255, 70, 80),
                "descricao": "Luta 1 contra 1 com seis lutadores, quatro arenas e combos."},
}

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
# Ordem de exibição: a mesma da documentação; jogos novos (imports) vêm depois, em ordem alfabética.
ORDEM_JOGOS = ["Snake", "Ping pong", "Frogger", "Space Invaders", "Flappy bird", "Kombate"]


def _chave_de_ordem(nome):
    if nome in ORDEM_JOGOS:
        return (0, ORDEM_JOGOS.index(nome), "")
    return (1, 0, nome.lower())


def listar_jogos():
    jogos = []
    if not os.path.isdir(GAMES_DIR):
        return jogos
    for nome in sorted(os.listdir(GAMES_DIR), key=_chave_de_ordem):
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
        # Escala tipográfica das telas: títulos em Press Start 2P, textos em VT323
        self.f_h1 = fonte_retro(24, True)
        self.f_h2 = fonte_retro(16, True)
        self.f_btn = fonte_retro(22, True)
        self.f_titulo_jogo = fonte_retro(34, True)
        self.f_corpo = fonte_retro(28, False)
        self.f_corpo_g = fonte_retro(24, False)
        self.f_corpo_peq = fonte_retro(23, False)
        self.f_tecla = fonte_retro(11, True)
        self.f_valor = fonte_retro(22, True)

        self.cena = "home"
        self.origem_recordes = "home"
        self.recordes = []
        self.rodando = True
        self.t = 0.0                       # tempo pra animacao

        self.menu_idx = 0
        self.menu_itens = ["Jogar", "Configuracoes", "Sair"]
        self.config_idx = 0

        # Visual: fundo arcade animado e logo (PNG com fundo transparente)
        self.fundo = ui.FundoArcade(LARGURA, ALTURA)
        self.logo_img = None
        if os.path.exists(LOGO):
            try:
                self.logo_img = pygame.image.load(LOGO).convert_alpha()
            except pygame.error:
                self.logo_img = None
        self.recordes_cache = []

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
                self.recordes_cache = self._carregar_recordes()
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
        elif e.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            if self.jogos:
                self.jogo_idx = (self.jogo_idx - 1) % len(self.jogos)
        elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
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
        self.fundo.desenhar(self.tela, self.t)
        capa = self._capa(jogo, 260)
        ui.brilho(self.tela, capa.get_rect(center=(LARGURA // 2, 300)).inflate(16, 16), self._info_jogo(jogo)["cor"])
        self.tela.blit(capa, capa.get_rect(center=(LARGURA // 2, 300)))
        ui.texto(self.tela, self.f_h1, jogo["titulo"].upper(), ui.TEXTO, (LARGURA // 2, 480), "center", sombra=True)
        ui.texto(self.tela, self.f_corpo, "Abrindo o jogo...", ui.TEXTO2, (LARGURA // 2, 530), "center")
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
        self.capas_cache = {}

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

    # ---- Componentes comuns das telas ------------------------------------------------
    def _cabecalho(self, titulo, direita=None):
        """Faixa superior: logo, título da tela e (opcional) um texto à direita."""
        if self.logo_img:
            lh = 60
            lw = int(self.logo_img.get_width() * lh / self.logo_img.get_height())
            self.tela.blit(pygame.transform.smoothscale(self.logo_img, (lw, lh)), (32, 14))
        ui.texto(self.tela, self.f_h1, titulo, ui.TEXTO, (160, 44), "midleft", sombra=True)
        if direita:
            ui.texto(self.tela, self.f_corpo, direita[0], direita[1], (LARGURA - 40, 44), "midright")
        pygame.draw.line(self.tela, ui.LINHA, (32, 88), (LARGURA - 32, 88), 2)

    def _atalhos(self, itens):
        ui.rodape_atalhos(self.tela, self.f_tecla, self.f_corpo_peq, itens, ALTURA - 50, LARGURA)

    def _rodape(self, texto):
        t = self.f_corpo_peq.render(texto, True, ui.TEXTO2)
        self.tela.blit(t, (24, ALTURA - 34))

    def _capa(self, jogo, tamanho):
        """Capa do jogo redimensionada (com cache). Sem capa, desenha uma inicial."""
        chave = (jogo["id"], tamanho)
        if chave not in self.capas_cache:
            img = None
            if jogo.get("capa"):
                try:
                    original = pygame.image.load(jogo["capa"]).convert_alpha()
                    esc = min(tamanho / original.get_width(), tamanho / original.get_height())
                    img = pygame.transform.smoothscale(
                        original, (max(1, int(original.get_width() * esc)), max(1, int(original.get_height() * esc))))
                except (pygame.error, OSError):
                    img = None
            if img is None:
                img = pygame.Surface((tamanho, tamanho))
                img.fill(ui.PAINEL2)
                letra = self.f_h1.render(jogo["titulo"][:1].upper(), True, ui.TEXTO2)
                img.blit(letra, letra.get_rect(center=(tamanho // 2, tamanho // 2)))
            self.capas_cache[chave] = img
        return self.capas_cache[chave]

    def _info_jogo(self, jogo):
        padrao = {"genero": "JOGO", "jogadores": "1 JOGADOR", "descricao": "Jogo adicionado à coletânea.", "cor": ui.ROSA}
        info = dict(padrao)
        info.update(INFO_JOGOS.get(jogo["titulo"], {}))
        return info

    # ---- HOME ------------------------------------------------------------------------
    def _rects_home(self):
        largura, altura, folga = 480, 66, 18
        x = (LARGURA - largura) // 2
        y0 = 382
        return [pygame.Rect(x, y0 + i * (altura + folga), largura, altura) for i in range(3)]

    def _logo_home_rect(self):
        lw = 520
        lh = int(self.logo_img.get_height() * lw / self.logo_img.get_width()) if self.logo_img else 0
        return pygame.Rect((LARGURA - lw) // 2, 28, lw, lh)

    def _draw_home(self):
        self.fundo.desenhar(self.tela, self.t)
        if self.logo_img:
            r = self._logo_home_rect()
            img = pygame.transform.smoothscale(self.logo_img, r.size)
            self.tela.blit(img, (r.x, r.y + int(math.sin(self.t * 2.0) * 4)))
        cores = (ui.CIANO, ui.AMARELO, ui.VERMELHO)
        rotulos = ("ARCADE", "OPÇÕES", "SAIR")
        icones = ("jogar", "opcoes", "sair")
        for i, rect in enumerate(self._rects_home()):
            ui.botao_menu(self.tela, rect, rotulos[i], cores[i], i == self.menu_idx, self.f_btn, icones[i], self.t)
        self._atalhos([("SETAS", "Navegar"), ("ENTER", "Selecionar"), ("H", "Recordes"), ("ESC", "Sair")])

    # ---- TRANSICAO home <-> jogos: o logo desliza até o cabeçalho ---------------------
    def _draw_transicao(self):
        self.fundo.desenhar(self.tela, self.t)
        p = min(1.0, self.trans_t / self.TRANS_DUR)
        p = p * p * (3 - 2 * p)
        if self.trans_reversa:
            p = 1.0 - p
        if self.logo_img:
            r0 = self._logo_home_rect()
            lh = 60
            lw = int(self.logo_img.get_width() * lh / self.logo_img.get_height())
            r1 = pygame.Rect(32, 14, lw, lh)
            r = pygame.Rect(int(r0.x + (r1.x - r0.x) * p), int(r0.y + (r1.y - r0.y) * p),
                            max(1, int(r0.w + (r1.w - r0.w) * p)), max(1, int(r0.h + (r1.h - r0.h) * p)))
            self.tela.blit(pygame.transform.smoothscale(self.logo_img, r.size), r.topleft)
        # os botões do menu somem enquanto o logo sobe
        if p < 0.6:
            camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            cores = (ui.CIANO, ui.AMARELO, ui.VERMELHO)
            for i, rect in enumerate(self._rects_home()):
                ui.botao_menu(camada, rect, ("ARCADE", "OPÇÕES", "SAIR")[i], cores[i], False, self.f_btn,
                              ("jogar", "opcoes", "sair")[i], self.t)
            camada.set_alpha(int(255 * (1 - p / 0.6)))
            self.tela.blit(camada, (0, 0))

    # ---- JOGOS: capa grande + ficha do jogo + faixa de miniaturas ---------------------
    def _draw_jogos(self):
        self.fundo.desenhar(self.tela, self.t)
        self._cabecalho("ESCOLHA SEU JOGO",
                        (f"{self.jogo_idx + 1} / {len(self.jogos)}", ui.TEXTO2) if self.jogos else None)
        if not self.jogos:
            ui.texto(self.tela, self.f_h2, "Nenhum jogo em src/games", ui.TEXTO2, (LARGURA // 2, ALTURA // 2), "center")
            self._atalhos([("ESC", "Voltar")])
            return

        jogo = self.jogos[self.jogo_idx]
        info = self._info_jogo(jogo)
        cor = info["cor"]

        # Capa em destaque, com aura na cor do jogo
        moldura = pygame.Rect(90, 118, 400, 400)
        moldura.y += int(math.sin(self.t * 2.2) * 4)
        ui.brilho(self.tela, moldura, cor, intensidade=80, raio=18)
        ui.painel(self.tela, moldura, borda=cor, fundo=ui.PAINEL, raio=18, largura_borda=3)
        capa = self._capa(jogo, 376)
        self.tela.blit(capa, capa.get_rect(center=moldura.center))

        # Ficha do jogo
        x0, larg = 560, LARGURA - 560 - 60
        ui.texto(self.tela, self.f_corpo_peq, f"JOGO {self.jogo_idx + 1:02d}", cor, (x0, 122))
        ui.texto(self.tela, self.f_titulo_jogo, jogo["titulo"].upper(), ui.TEXTO, (x0, 150), sombra=True)
        x = x0
        y_tags = 214
        for rotulo, c in ((info["genero"], cor), (info["jogadores"], ui.TEXTO2), ("TECLADO E CONTROLE", ui.TEXTO2)):
            x = ui.etiqueta(self.tela, self.f_corpo_peq, rotulo, c, x, y_tags)
        y = 268
        for linha in ui.quebrar_texto(self.f_corpo, info["descricao"], larg)[:3]:
            ui.texto(self.tela, self.f_corpo, linha, ui.TEXTO2, (x0, y))
            y += 30

        # Recorde
        recorde = self._recorde_do_jogo(jogo)
        cartao = pygame.Rect(x0, 368, larg, 96)
        ui.painel(self.tela, cartao, borda=ui.LINHA, fundo=ui.PAINEL2)
        ui.texto(self.tela, self.f_corpo_peq, "SEU RECORDE", ui.TEXTO3, (cartao.x + 24, cartao.y + 12))
        if recorde and recorde[0] > 0:
            valor = f"{recorde[0]:,}".replace(",", ".")
            unidade = "PONTOS" if recorde[1] == "pontos" else recorde[1].upper()
            r = ui.texto(self.tela, self.f_valor, valor, ui.VERDE, (cartao.x + 24, cartao.y + 56), "midleft")
            ui.texto(self.tela, self.f_corpo, unidade, ui.TEXTO2, (r.right + 14, r.centery + 4), "midleft")
        else:
            ui.texto(self.tela, self.f_corpo, "Ainda sem recorde. Seja o primeiro!", ui.TEXTO2, (cartao.x + 24, cartao.y + 60), "midleft")

        # Botão principal
        botao = pygame.Rect(x0, 492, 320, 62)
        ui.botao_menu(self.tela, botao, "JOGAR", cor, True, self.f_btn, "jogar", self.t)

        # Faixa de miniaturas: onde estou e o que vem a seguir
        n = len(self.jogos)
        lado, folga = 74, 18
        total = n * lado + (n - 1) * folga
        xt = (LARGURA - total) // 2
        yt = 584
        for i, outro in enumerate(self.jogos):
            r = pygame.Rect(xt + i * (lado + folga), yt, lado, lado)
            sel = (i == self.jogo_idx)
            c = self._info_jogo(outro)["cor"]
            if sel:
                ui.brilho(self.tela, r, c, intensidade=70, raio=10, camadas=3)
            ui.painel(self.tela, r, borda=c if sel else ui.LINHA, fundo=ui.PAINEL, raio=10, largura_borda=3 if sel else 2)
            mini = self._capa(outro, lado - 10)
            if not sel:
                mini = mini.copy()
                mini.set_alpha(120)
            self.tela.blit(mini, mini.get_rect(center=r.center))
        ui.triangulo(self.tela, (xt - 28, yt + lado // 2), 8, ui.TEXTO3, "esquerda")
        ui.triangulo(self.tela, (xt + total + 28, yt + lado // 2), 8, ui.TEXTO3, "direita")

        self._atalhos([("SETAS", "Trocar jogo"), ("ENTER", "Jogar"), ("H", "Recordes"), ("ESC", "Voltar")])

    def _recorde_do_jogo(self, jogo):
        for nome, valor, unidade in self.recordes_cache:
            if nome == jogo["titulo"]:
                return (valor or 0, unidade)
        return None

    # ---- RECORDES -----------------------------------------------------------------
    def _draw_recordes(self):
        self.fundo.desenhar(self.tela, self.t)
        self._cabecalho("RECORDES", ("MELHOR MARCA DE CADA JOGO", ui.TEXTO2))
        por_titulo = {j["titulo"]: j for j in self.jogos}
        medalhas = [ui.AMARELO, (200, 212, 230), (214, 140, 90)]
        maior = max([v for _, v, _ in self.recordes if v] or [1])
        for i, (nome, pontos, unidade) in enumerate(self.recordes):
            y = 112 + i * 84
            cartao = pygame.Rect(180, y, LARGURA - 360, 72)
            tem = bool(pontos)
            cor = medalhas[i] if (i < 3 and tem) else ui.LINHA
            if i == 0 and tem:
                ui.brilho(self.tela, cartao, cor, intensidade=50, raio=14, camadas=3)
            ui.painel(self.tela, cartao, borda=cor, fundo=ui.PAINEL2 if tem else ui.PAINEL, raio=14)
            ui.texto(self.tela, self.f_btn, f"{i + 1}", cor if tem else ui.TEXTO3, (cartao.x + 40, cartao.centery), "center")
            jogo = por_titulo.get(nome)
            if jogo:
                mini = self._capa(jogo, 52)
                self.tela.blit(mini, mini.get_rect(center=(cartao.x + 108, cartao.centery)))
            ui.texto(self.tela, self.f_h2, nome.upper(), ui.TEXTO if tem else ui.TEXTO2, (cartao.x + 156, cartao.y + 22), "midleft")
            if tem:
                barra = pygame.Rect(cartao.x + 156, cartao.bottom - 22, 260, 8)
                pygame.draw.rect(self.tela, ui.LINHA, barra, border_radius=4)
                cheia = barra.copy()
                cheia.width = max(8, int(barra.width * pontos / maior))
                pygame.draw.rect(self.tela, ui.VERDE, cheia, border_radius=4)
                texto_unidade = "PONTOS" if unidade == "pontos" else unidade.upper()
                valor = f"{pontos:,}".replace(",", ".")
                r = ui.texto(self.tela, self.f_corpo_g, texto_unidade, ui.TEXTO2, (cartao.right - 24, cartao.centery + 12), "midright")
                ui.texto(self.tela, self.f_h2, valor, ui.VERDE, (cartao.right - 24, cartao.centery - 12), "midright")
            else:
                ui.texto(self.tela, self.f_corpo, "SEM RECORDE", ui.TEXTO3, (cartao.right - 24, cartao.centery), "midright")
        self._atalhos([("R", "Atualizar"), ("ESC", "Voltar")])

    # ---- OPCOES ---------------------------------------------------------------------
    def _draw_config(self):
        self.fundo.desenhar(self.tela, self.t)
        conectado = self.controle.connected
        status = (f"● CONTROLE: {self.controle.device_name.upper()}" if conectado else "○ SEM CONTROLE CONECTADO")
        self._cabecalho("OPÇÕES", (status, ui.VERDE if conectado else ui.TEXTO3))
        painel = pygame.Rect(240, 128, LARGURA - 480, 420)
        ui.painel(self.tela, painel, borda=ui.LINHA, fundo=ui.PAINEL, raio=18)

        linhas = [
            ("TELA CHEIA", "ligado" if self.cfg["tela_cheia"] else "desligado", "chave", self.cfg["tela_cheia"]),
            ("VOLUME DA MÚSICA", self.cfg["volume"], "barra", None),
            ("SONS DE NAVEGAÇÃO", "ligado" if self.cfg.get("som_menu", True) else "desligado", "chave", self.cfg.get("som_menu", True)),
            ("VOLTAR", "", "botao", None),
        ]
        altura_linha = 92
        for i, (rotulo, valor, tipo, ligado) in enumerate(linhas):
            r = pygame.Rect(painel.x + 20, painel.y + 20 + i * altura_linha, painel.w - 40, altura_linha - 12)
            sel = (i == self.config_idx)
            if sel:
                ui.brilho(self.tela, r, ui.CIANO, intensidade=50, raio=12, camadas=2)
                ui.painel(self.tela, r, borda=ui.CIANO, fundo=ui.PAINEL2, raio=12, largura_borda=3)
            ui.texto(self.tela, self.f_h2, rotulo, ui.TEXTO if sel else ui.TEXTO2, (r.x + 28, r.centery), "midleft")
            if tipo == "chave":
                pilula = pygame.Rect(0, 0, 124, 40)
                pilula.midright = (r.right - 28, r.centery)
                pygame.draw.rect(self.tela, ui.VERDE if ligado else ui.LINHA, pilula, border_radius=20)
                bolinha_x = pilula.right - 20 if ligado else pilula.x + 20
                pygame.draw.circle(self.tela, ui.TEXTO, (bolinha_x, pilula.centery), 14)
                ui.texto(self.tela, self.f_corpo_peq, "LIGADO" if ligado else "DESLIG.", (7, 8, 24) if ligado else ui.TEXTO2,
                         (pilula.x + 38 if ligado else pilula.right - 36, pilula.centery), "center")
            elif tipo == "barra":
                barra = pygame.Rect(0, 0, 260, 12)
                barra.midright = (r.right - 110, r.centery)
                pygame.draw.rect(self.tela, ui.LINHA, barra, border_radius=6)
                cheia = barra.copy()
                cheia.width = int(barra.width * valor / 100)
                if cheia.width > 0:
                    pygame.draw.rect(self.tela, ui.CIANO, cheia, border_radius=6)
                pygame.draw.circle(self.tela, ui.TEXTO, (barra.x + cheia.width, barra.centery), 12)
                ui.texto(self.tela, self.f_h2, f"{valor}%", ui.CIANO if sel else ui.TEXTO2, (r.right - 28, r.centery), "midright")
            if sel and tipo in ("chave", "barra"):
                ui.triangulo(self.tela, (r.x + 10, r.centery), 7, ui.CIANO, "direita")
        self._atalhos([("SETAS", "Selecionar"), ("SETAS", "Alterar"), ("ENTER", "Confirmar"), ("ESC", "Voltar")])


if __name__ == "__main__":
    Eplace().run()
