"""
app.py - telas do jogo (menu, controles, selecao, luta, pausa) + sons e efeitos.
"""
import os
import random
import sys

os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"

import pygame

from settings import LARGURA, ALTURA, FPS, TITULO, CONTROLES, NIVEL_CPU, CHAO_Y
from game.characters import PERSONAGENS
from game.match import Partida
from game.fighter import Fighter
from game.input import Teclado
from game.ai import NIVEIS as NIVEIS_CPU, nivel_valido
from game.fx import Particulas, Tremor, Sons, glow
from game import render
from game.mapas import MAPAS, Mapa
from game.render import texto

DESC_NIVEL = {
    1: "Para aprender: a CPU quase nao defende e pensa devagar.",
    2: "Defende as vezes e ataca sem pressa.",
    3: "Equilibrado: defende metade dos golpes e usa antiaereo.",
    4: "Reage rapido, defende bem e emenda combos.",
    5: "Sem piedade: defende quase tudo e pune cada erro.",
}


class App:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.gpu = self._abrir_tela()
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.fontes = {
            "logo": render.make_font(124), "titulo": render.make_font(92),
            "grande": render.make_font(54), "media": render.make_font(28),
            "pequena": render.make_font(20), "mini": render.make_font(16, bold=False),
        }
        self.vinheta = pygame.Surface((1, 1), pygame.SRCALPHA)
        self._escala = None
        self._veus = {}
        self.ambiente = render.Ambiente()
        self.mapas = [Mapa(m) for m in MAPAS]               # os 4 mapas (fundo + animacao)
        self.mapa_idx = 0
        self.thumbs = []
        for m in self.mapas:
            prev = m.fundo.copy()
            m.anim.desenhar(prev, 0)
            self.thumbs.append(pygame.transform.smoothscale(prev, (256, 144)).convert())
        self.particulas = Particulas()
        self.tremor = Tremor()
        self.sons = Sons()
        self.teclado = {1: Teclado(1), 2: Teclado(2)}
        self.t = 0
        self.debug = False
        self.nivel = nivel_valido(NIVEL_CPU)
        self.menu_idx = 0
        self.pausa_idx = 0
        self.vs_cpu = True
        self.partida = None
        self.demo = None
        self.flash = 0
        self._som_golpe = {1: False, 2: False}
        self._fase_ant = None
        self.preview = {}
        for ch in PERSONAGENS:
            f = Fighter(ch, 1)
            f.reset(0, 1)
            self.preview[ch.key] = f
        self.cena = "menu"

    # ================================================================ loop
    def run(self):
        while True:
            self.t += 1
            eventos = pygame.event.get()
            for e in eventos:
                if e.type == pygame.QUIT:
                    self.sair()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                    self.debug = not self.debug
            getattr(self, "cena_" + self.cena)(eventos)
            self.apresentar()
            self.clock.tick(FPS)

    def sair(self):
        pygame.quit()
        sys.exit()

    def _abrir_tela(self):
        """Tela cheia ampliada pela PLACA DE VIDEO (SCALED + vsync): rapido e sem trocar
        a resolucao do monitor (nao pisca). Se nao der, usa o metodo antigo (CPU)."""
        flags = pygame.SCALED | pygame.FULLSCREEN
        for vsync in (1, 0):
            try:
                self.janela = pygame.display.set_mode((LARGURA, ALTURA), flags, vsync=vsync)
                self.tela = self.janela
                return True
            except Exception:
                continue
        tamanho = pygame.display.get_desktop_sizes()[0]
        self.janela = pygame.display.set_mode(tamanho, pygame.NOFRAME)
        self.tela = pygame.Surface((LARGURA, ALTURA))
        return False

    def apresentar(self):
        if self.gpu:
            ox, oy = self.tremor.offset()
            if ox or oy:
                self.tela.scroll(ox, oy)                    # tremida de tela
            pygame.display.flip()
            return
        jw, jh = self.janela.get_size()
        esc = min(jw / LARGURA, jh / ALTURA)
        tam = (int(LARGURA * esc), int(ALTURA * esc))
        if self._escala is None or self._escala.get_size() != tam:
            self._escala = pygame.Surface(tam).convert()
        img = pygame.transform.smoothscale(self.tela, tam, self._escala)
        ox, oy = self.tremor.offset()
        self.janela.fill((0, 0, 0))
        self.janela.blit(img, img.get_rect(center=(jw // 2 + ox, jh // 2 + oy)))
        pygame.display.flip()

    @staticmethod
    def _teclas(eventos):
        return [e.key for e in eventos if e.type == pygame.KEYDOWN]

    def _veu(self, alpha, cor=(8, 4, 12)):
        chave = (alpha, cor)
        veu = self._veus.get(chave)
        if veu is None:
            veu = pygame.Surface((LARGURA, ALTURA))
            veu.fill(cor)
            veu.set_alpha(alpha)
            veu = veu.convert()
            veu.set_alpha(alpha)
            self._veus[chave] = veu
        self.tela.blit(veu, (0, 0))

    def _cenario(self):
        self.mapas[self.mapa_idx].desenhar(self.tela, self.t)

    def _botao(self, rotulo, centro, sel, largura=520):
        r = pygame.Rect(0, 0, largura, 54)
        r.center = centro
        if sel:
            glow(self.tela, (110, 25, 20), r.center, largura // 2 + 30, 0.9)
            pts = [(r.x + 18, r.y), (r.right, r.y), (r.right - 18, r.bottom), (r.x, r.bottom)]
            pygame.draw.polygon(self.tela, (200, 40, 35), pts)
            pygame.draw.polygon(self.tela, (255, 190, 120), pts, 2)
            texto(self.tela, rotulo, self.fontes["media"], (255, 255, 255), centro)
        else:
            texto(self.tela, rotulo, self.fontes["media"], (205, 190, 195), centro)

    # ================================================================ demo (fundo do menu)
    def _atualizar_demo(self):
        if self.demo is None or self.demo.fase == "fim":
            a, b = random.sample(PERSONAGENS, 2)
            self.demo = Partida(a, b, cpu1=True, cpu2=True, nivel=4)
            self.demo.fase, self.demo.fase_t = "luta", 0
        self.demo.update()
        self.demo.combate.eventos.clear()
        self._cenario()
        render.desenhar_objetos(self.tela, self.demo.combate, self.t)
        for f in sorted((self.demo.f1, self.demo.f2), key=lambda f: f.estado == "attack"):
            render.desenhar_lutador(self.tela, f, self.t)
        render.desenhar_efeitos(self.tela, self.demo.combate)

    # ================================================================ menu
    def _itens_menu(self):
        return ["1 JOGADOR  (VS CPU)", "2 JOGADORES", "DIFICULDADE", "CONTROLES", "SAIR"]

    def cena_menu(self, eventos):
        itens = self._itens_menu()
        for k in self._teclas(eventos):
            if k in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % len(itens)
                self.sons.tocar("menu")
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % len(itens)
                self.sons.tocar("menu")
            elif k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and self.menu_idx == 2:
                passo = 1 if k in (pygame.K_RIGHT, pygame.K_d) else -1
                self.nivel = max(1, min(5, self.nivel + passo))
                self.sons.tocar("menu")
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_f):
                escolha = self.menu_idx
                if escolha in (0, 1):
                    self.sons.tocar("ok")
                    self.vs_cpu = escolha == 0
                    self.abrir_selecao()
                elif escolha == 2:
                    self.nivel = self.nivel % 5 + 1
                    self.sons.tocar("menu")
                elif escolha == 3:
                    self.sons.tocar("ok")
                    self.cena = "controles"
                else:
                    self.sair()
            elif k == pygame.K_ESCAPE:
                self.sair()                                   # volta ao launcher

        self._atualizar_demo()
        self._veu(150)
        pulso = 0.85 + 0.15 * abs(((self.t % 120) / 60) - 1)
        glow(self.tela, (int(150 * pulso), 25, 20), (LARGURA // 2, 150), 330, 0.9)
        texto(self.tela, "KOMBATE", self.fontes["logo"], (240, 60, 45), (LARGURA // 2, 150), contorno=5)
        texto(self.tela, "-  TORNEIO DOS MANEQUINS  -", self.fontes["media"], (255, 210, 150), (LARGURA // 2, 232))
        for i, item in enumerate(itens):
            y = 325 + i * 64
            if i == 2:                                        # medidor de dificuldade
                sel = i == self.menu_idx
                self._botao("", (LARGURA // 2, y), sel)
                texto(self.tela, "CPU", self.fontes["media"], (255, 255, 255) if sel else (205, 190, 195),
                      (LARGURA // 2 - 200, y), "midleft")
                render.medidor_dificuldade(self.tela, (LARGURA // 2 - 10, y - 18), self.nivel, self.fontes,
                                           0.5, nome=False)
                texto(self.tela, NIVEIS_CPU[self.nivel]["nome"], self.fontes["pequena"],
                      render.CORES_NIVEL[self.nivel], (LARGURA // 2 + 130, y), "midleft")
                if sel:
                    texto(self.tela, "<", self.fontes["media"], (255, 255, 255), (LARGURA // 2 - 90, y))
                    texto(self.tela, ">", self.fontes["media"], (255, 255, 255), (LARGURA // 2 + 72, y))
            else:
                self._botao(item, (LARGURA // 2, y), i == self.menu_idx)
        texto(self.tela, "Setas / W S escolhem   -   ENTER confirma   -   ESC volta ao launcher",
              self.fontes["pequena"], (200, 185, 190), (LARGURA // 2, ALTURA - 34), contorno=1)

    # ================================================================ controles
    def cena_controles(self, eventos):
        if any(k in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE) for k in self._teclas(eventos)):
            self.sons.tocar("menu")
            self.cena = "menu"
        self._cenario()
        self._veu(205)
        texto(self.tela, "CONTROLES", self.fontes["grande"], (240, 60, 45), (LARGURA // 2, 62))
        linhas = [("Andar", "esquerda", "direita"), ("Pular", "cima", None), ("Agachar", "baixo", None),
                  ("Soco", "soco", None), ("Chute", "chute", None), ("Especial 1", "especial1", None),
                  ("Especial 2", "especial2", None), ("Dash", "dash", None)]
        texto(self.tela, "JOGADOR 1", self.fontes["media"], (255, 90, 80), (640, 128))
        texto(self.tela, "JOGADOR 2", self.fontes["media"], (90, 170, 255), (960, 128))
        for i, (nome, a, b) in enumerate(linhas):
            y = 176 + i * 42
            if i % 2 == 0:
                faixa = pygame.Surface((860, 40), pygame.SRCALPHA)
                faixa.fill((255, 255, 255, 14))
                self.tela.blit(faixa, (210, y - 20))
            texto(self.tela, nome, self.fontes["media"], (255, 255, 255), (240, y), "midleft")
            for col, slot in ((640, 1), (960, 2)):
                k = CONTROLES[slot][a].upper()
                if b:
                    k += " / " + CONTROLES[slot][b].upper()
                texto(self.tela, k, self.fontes["media"], (230, 225, 235), (col, y))
        dicas = ["DEFENDER: segure para TRAS (agachado + tras defende golpe BAIXO)",
                 "COMBO: acerte um soco/chute e aperte um ESPECIAL logo em seguida (soco -> chute tambem emenda)",
                 "COUNTER: acertar o oponente no meio do golpe dele causa mais dano",
                 "ESC na luta = pausa   |   F1 = mostrar hitboxes"]
        for i, d in enumerate(dicas):
            texto(self.tela, d, self.fontes["pequena"], (255, 215, 150) if i < 3 else (200, 190, 200),
                  (LARGURA // 2, 540 + i * 34), contorno=1)

    # ================================================================ selecao
    def abrir_selecao(self):
        self.sel = {1: 0, 2: 1}
        self.conf = {1: False, 2: False}
        self.sel_t = 0
        self.cena = "selecao"

    def _mover_cursor(self, slot, dx, dy):
        i = self.sel[slot]
        col, lin = (i % 3 + dx) % 3, (i // 3 + dy) % 2
        self.sel[slot] = lin * 3 + col
        self.sons.tocar("menu")

    def _confirmar(self, slot):
        self.conf[slot] = True
        self.sons.tocar("ok")
        f = self.preview[PERSONAGENS[self.sel[slot]].key]
        f.golpe, f.golpe_t, f.estado = f.char.golpes["chute"], 0, "attack"

    def cena_selecao(self, eventos):
        teclas = self._teclas(eventos)
        k1, k2 = self.teclado[1], self.teclado[2]
        direcoes = {"esquerda": (-1, 0), "direita": (1, 0), "cima": (0, -1), "baixo": (0, 1)}

        if self.vs_cpu:
            ativo = 1 if not self.conf[1] else 2
            for k in teclas:
                if self.conf[2]:
                    break
                for acao, (dx, dy) in direcoes.items():
                    if k in (k1.tecla(acao), k2.tecla(acao)):
                        self._mover_cursor(ativo, dx, dy)
                if k in (k1.tecla("soco"), pygame.K_RETURN, pygame.K_SPACE):
                    self._confirmar(ativo)
                    ativo = 2
        else:
            for k in teclas:
                for slot, tec in ((1, k1), (2, k2)):
                    if self.conf[slot]:
                        continue
                    for acao, (dx, dy) in direcoes.items():
                        if k == tec.tecla(acao):
                            self._mover_cursor(slot, dx, dy)
                    if k == tec.tecla("soco"):
                        self._confirmar(slot)
                if k == pygame.K_RETURN:
                    self._confirmar(1 if not self.conf[1] else 2)
        if pygame.K_ESCAPE in teclas:
            self.sons.tocar("menu")
            if self.conf[2]:
                self.conf[2] = False
            elif self.conf[1]:
                self.conf[1] = False
            else:
                self.cena = "menu"

        if self.conf[1] and self.conf[2]:
            self.sel_t += 1
            if self.vs_cpu and self.sel_t > 22:
                self.cena = "dificuldade"
                return
            if self.sel_t > 30:
                self.abrir_mapas()
                return
        else:
            self.sel_t = 0
        self._desenhar_selecao()

    def _desenhar_selecao(self):
        self._cenario()
        self._veu(195)
        if self.vs_cpu:
            titulo = "ESCOLHA SEU LUTADOR" if not self.conf[1] else "ESCOLHA O OPONENTE (CPU)"
        else:
            titulo = "ESCOLHAM SEUS LUTADORES"
        texto(self.tela, titulo, self.fontes["grande"], (255, 255, 255), (LARGURA // 2, 52))

        cw, chh, gap = 340, 248, 22
        x0 = (LARGURA - (cw * 3 + gap * 2)) // 2
        y0 = 100
        for i, ch in enumerate(PERSONAGENS):
            col, lin = i % 3, i // 3
            r = pygame.Rect(x0 + col * (cw + gap), y0 + lin * (chh + gap), cw, chh)
            marcado = [s for s in (1, 2) if self.sel[s] == i and not (self.vs_cpu and s == 2 and not self.conf[1])]
            card = pygame.Surface(r.size, pygame.SRCALPHA)
            topo = (*render.escurecer(ch.cor, 0.35 if marcado else 0.18), 235)
            for yy in range(r.h):
                k = yy / r.h
                pygame.draw.line(card, (int(topo[0] * (1 - k) + 14 * k), int(topo[1] * (1 - k) + 10 * k),
                                        int(topo[2] * (1 - k) + 18 * k), 235), (0, yy), (r.w, yy))
            self.tela.blit(card, r.topleft)
            pygame.draw.rect(self.tela, render.escurecer(ch.cor, 0.8) if sum(ch.cor) > 250 else (110, 90, 150),
                             r, 2, border_radius=6)

            f = self.preview[ch.key]
            f.t = self.t
            if f.estado == "attack":
                f.golpe_t += 1
                if f.golpe_t > f.golpe.total:
                    f.estado, f.golpe = "idle", None
            else:
                f.estado = "idle"
            clip = self.tela.get_clip()
            self.tela.set_clip(r)
            if marcado:
                glow(self.tela, render.escurecer(ch.cor, 0.5 if sum(ch.cor) > 250 else 1.4), (r.x + 80, r.bottom - 110), 110)
            render.desenhar_lutador(self.tela, f, self.t, ox=r.x + 80, oy=r.bottom - 14 - CHAO_Y)
            self.tela.set_clip(clip)

            tx = r.x + 160
            texto(self.tela, ch.nome, self.fontes["media"], render.cor_texto(ch.cor), (tx, r.y + 30), "midleft")
            texto(self.tela, ch.arquetipo, self.fontes["pequena"], (240, 230, 230), (tx, r.y + 60), "midleft", contorno=1)
            for j, (rot, val) in enumerate((("VIDA", ch.max_hp / 1250), ("VELOC.", ch.vel_andar / 5.4))):
                yy = r.y + 94 + j * 26
                texto(self.tela, rot, self.fontes["mini"], (210, 205, 210), (tx, yy), "midleft", contorno=0)
                pygame.draw.rect(self.tela, (40, 32, 46), (tx + 64, yy - 6, 104, 12), border_radius=5)
                pygame.draw.rect(self.tela, render.cor_texto(ch.cor), (tx + 64, yy - 6, int(104 * val), 12), border_radius=5)
            for j, nome in enumerate((ch.golpes["especial1"].nome, ch.golpes["especial2"].nome)):
                pygame.draw.circle(self.tela, render.cor_texto(ch.cor), (tx + 4, r.y + 152 + j * 22), 4)
                texto(self.tela, nome, self.fontes["mini"], (225, 215, 235),
                      (tx + 14, r.y + 152 + j * 22), "midleft", contorno=0)

            for slot in marcado:
                cor = (255, 70, 60) if slot == 1 else (70, 160, 255)
                rot = "P1" if slot == 1 else ("CPU" if self.vs_cpu else "P2")
                pisca = self.conf[slot] or (self.t // 8) % 2 == 0
                off = 0 if slot == 1 else 7
                if pisca:
                    pygame.draw.rect(self.tela, cor, r.inflate(8 + off * 2, 8 + off * 2), 4, border_radius=10)
                tag = pygame.Rect(0, 0, 84, 28)
                tag.bottomright = (r.right - 10 - (0 if slot == 1 else 92), r.bottom - 10)
                pygame.draw.rect(self.tela, cor, tag, border_radius=8)
                texto(self.tela, rot + (" OK" if self.conf[slot] else ""), self.fontes["pequena"],
                      (255, 255, 255), tag.center, contorno=0)

        ativo = 2 if (self.vs_cpu and self.conf[1]) else 1
        ch = PERSONAGENS[self.sel[ativo]]
        texto(self.tela, ch.descricao, self.fontes["media"], (255, 220, 150), (LARGURA // 2, 662))
        if self.vs_cpu:
            dica = "Setas/WASD movem  -  F ou ENTER confirma  -  ESC volta"
        else:
            dica = "P1: WASD + F     P2: Setas + K     ESC volta"
        texto(self.tela, dica, self.fontes["pequena"], (200, 190, 195), (LARGURA // 2, 700), contorno=1)
        if self.conf[1] and self.conf[2] and not self.vs_cpu:
            k = min(1.0, self.sel_t / 12)
            texto(self.tela, "PREPARE-SE!", self.fontes["titulo"], (255, 220, 70), (LARGURA // 2, 360),
                  contorno=4, escala=2.0 - k)

    # ================================================================ dificuldade
    def cena_dificuldade(self, eventos):
        k1 = self.teclado[1]
        for k in self._teclas(eventos):
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_DOWN, pygame.K_s):
                self.nivel = max(1, self.nivel - 1)
                self.sons.tocar("menu")
            elif k in (pygame.K_RIGHT, pygame.K_d, pygame.K_UP, pygame.K_w):
                self.nivel = min(5, self.nivel + 1)
                self.sons.tocar("menu")
            elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                self.nivel = k - pygame.K_0
                self.sons.tocar("menu")
            elif k in (pygame.K_RETURN, pygame.K_SPACE, k1.tecla("soco")):
                self.sons.tocar("ok")
                self.abrir_mapas()
                return
            elif k == pygame.K_ESCAPE:
                self.sons.tocar("menu")
                self.conf[2] = False
                self.sel_t = 0
                self.cena = "selecao"
                return
        self._desenhar_selecao()
        self._veu(175, (0, 0, 0))
        cx = LARGURA // 2
        painel = pygame.Rect(0, 0, 760, 420)
        painel.center = (cx, ALTURA // 2)
        pygame.draw.rect(self.tela, (18, 12, 22), painel, border_radius=18)
        pygame.draw.rect(self.tela, render.CORES_NIVEL[self.nivel], painel, 3, border_radius=18)
        c1, c2 = PERSONAGENS[self.sel[1]], PERSONAGENS[self.sel[2]]
        texto(self.tela, "DIFICULDADE DA CPU", self.fontes["grande"], (255, 255, 255), (cx, painel.y + 52))
        texto(self.tela, f"{c1.nome}  vs  {c2.nome} (CPU)", self.fontes["pequena"], (220, 205, 215),
              (cx, painel.y + 98), contorno=1)
        render.medidor_dificuldade(self.tela, (cx, painel.y + 180), self.nivel, self.fontes, 1.6, tempo=self.t)
        seta = (255, 255, 255) if (self.t // 20) % 2 else (180, 170, 180)
        if self.nivel > 1:
            texto(self.tela, "<", self.fontes["titulo"], seta, (painel.x + 90, painel.y + 190))
        if self.nivel < 5:
            texto(self.tela, ">", self.fontes["titulo"], seta, (painel.right - 90, painel.y + 190))
        texto(self.tela, DESC_NIVEL[self.nivel], self.fontes["pequena"], (240, 225, 200),
              (cx, painel.y + 300), contorno=1)
        texto(self.tela, "< >  ou  1-5  ajusta     ENTER / F  luta!     ESC  volta", self.fontes["pequena"],
              (190, 180, 190), (cx, painel.bottom - 36), contorno=1)

    # ================================================================ mapas
    def abrir_mapas(self):
        self.mapa_t = 0
        self.cena = "mapa"

    def cena_mapa(self, eventos):
        k1, k2 = self.teclado[1], self.teclado[2]
        n = len(self.mapas)
        self.mapa_t += 1
        for k in self._teclas(eventos):
            if k in (pygame.K_LEFT, pygame.K_a, k2.tecla("esquerda")):
                self.mapa_idx = (self.mapa_idx - 1) % n
                self.sons.tocar("menu")
            elif k in (pygame.K_RIGHT, pygame.K_d, k2.tecla("direita")):
                self.mapa_idx = (self.mapa_idx + 1) % n
                self.sons.tocar("menu")
            elif pygame.K_1 <= k <= pygame.K_0 + n:
                self.mapa_idx = k - pygame.K_1
                self.sons.tocar("menu")
            elif k in (pygame.K_RETURN, pygame.K_SPACE, k1.tecla("soco"), k2.tecla("soco")):
                self.sons.tocar("ok")
                self.iniciar_luta(PERSONAGENS[self.sel[1]], PERSONAGENS[self.sel[2]])
                return
            elif k == pygame.K_ESCAPE:
                self.sons.tocar("menu")
                if self.vs_cpu:
                    self.cena = "dificuldade"
                else:
                    self.conf[2] = False
                    self.sel_t = 0
                    self.cena = "selecao"
                return

        info = self.mapas[self.mapa_idx].info
        self._cenario()                                    # previa ao vivo do mapa escolhido
        faixa = pygame.Surface((LARGURA, 150), pygame.SRCALPHA)
        for i in range(150):
            pygame.draw.line(faixa, (0, 0, 0, int(200 * (1 - i / 150))), (0, i), (LARGURA, i))
        self.tela.blit(faixa, (0, 0))
        rodape = pygame.Surface((LARGURA, 270), pygame.SRCALPHA)
        for i in range(270):
            pygame.draw.line(rodape, (0, 0, 0, int(225 * min(1.0, i / 90))), (0, i), (LARGURA, i))
        self.tela.blit(rodape, (0, ALTURA - 270))
        cx = LARGURA // 2
        texto(self.tela, "ESCOLHA O MAPA", self.fontes["grande"], (255, 255, 255), (cx, 50))
        texto(self.tela, info["nome"], self.fontes["titulo"], info["cor"], (cx, 300), contorno=4,
              escala=1.0 + 0.25 * max(0.0, 1 - self.mapa_t / 10))
        texto(self.tela, info["desc"], self.fontes["media"], (240, 230, 225), (cx, 368))

        tw, th, gap = 256, 144, 26
        x0 = (LARGURA - (tw * n + gap * (n - 1))) // 2
        y0 = ALTURA - th - 52
        for i, (m, thumb) in enumerate(zip(self.mapas, self.thumbs)):
            r = pygame.Rect(x0 + i * (tw + gap), y0, tw, th)
            sel = i == self.mapa_idx
            if sel:
                r = r.move(0, -10)
                glow(self.tela, render.escurecer(m.info["cor"], 0.5), r.center, 190, 0.9)
            self.tela.blit(thumb, r.topleft)
            if not sel:
                self._escurecer_rect(r)
            pygame.draw.rect(self.tela, m.info["cor"] if sel else (90, 80, 95), r, 4 if sel else 2, border_radius=4)
            texto(self.tela, f"{i + 1}  {m.info['nome']}", self.fontes["mini"],
                  (255, 255, 255) if sel else (180, 170, 180), (r.centerx, r.bottom + 16), contorno=1)
        texto(self.tela, "< >  ou  1-4  escolhe     ENTER / F  luta!     ESC  volta", self.fontes["pequena"],
              (200, 190, 200), (cx, 105), contorno=1)

    def _escurecer_rect(self, r):
        v = pygame.Surface(r.size)
        v.set_alpha(120)
        self.tela.blit(v, r.topleft)

    # ================================================================ luta
    def iniciar_luta(self, c1, c2):
        self.chars = (c1, c2)
        self.partida = Partida(c1, c2, cpu1=False, cpu2=self.vs_cpu, nivel=self.nivel)
        self.particulas = Particulas()
        self._fase_ant = None
        self.cena = "luta"

    def _processar_fx(self):
        p = self.partida
        P = self.particulas
        for tipo, x, y, forca in p.combate.eventos:
            if tipo == "hit":
                forte = forca >= 45
                P.faiscas(x, y, (255, 240, 150), n=12 + int(forca / 4), vel=8 + forca / 10)
                P.faiscas(x, y, (255, 255, 255), n=6, vel=6)
                self.tremor.add(3 + forca / 9)
                self.sons.tocar("forte" if forte else "soco", 1.0 if forte else 0.8)
                if forte:
                    self.flash = 3
            elif tipo == "bloqueio":
                P.faiscas(x, y, (140, 210, 255), n=10, vel=7)
                self.sons.tocar("bloqueio", 0.7)
            elif tipo == "armadura":
                P.faiscas(x, y, (255, 180, 60), n=14, vel=8)
                self.tremor.add(4)
                self.sons.tocar("bloqueio")
                self.sons.tocar("soco", 0.5)
            elif tipo == "agarrao":
                P.faiscas(x, y, (255, 100, 90), n=26, vel=12)
                P.poeira(x, CHAO_Y, 14, 1.6)
                self.tremor.add(14)
                self.flash = 4
                self.sons.tocar("agarrao")
            elif tipo == "explosao":
                P.fogo(x, CHAO_Y - 20)
                self.tremor.add(13)
                self.sons.tocar("explosao")
            elif tipo == "counter":
                P.texto("COUNTER!", x, y, (255, 120, 60))
            elif tipo == "cancel":
                P.faiscas(x, y, (200, 230, 255), n=8, vel=5)
            elif tipo == "tiro":
                self.sons.tocar("tiro", 0.7)
        p.combate.eventos.clear()

        for f in (p.f1, p.f2):
            if f.estado == "attack" and f.golpe_t == 1:
                if not self._som_golpe[f.slot]:
                    self._som_golpe[f.slot] = True
                    self.sons.tocar("whoosh", 0.6)
            else:
                self._som_golpe[f.slot] = False
            if f.pousou:
                caiu = f.estado in ("knockdown", "ko")
                P.poeira(f.x, CHAO_Y, 14 if caiu else 6, 1.5 if caiu else 0.8)
                if caiu:
                    self.tremor.add(6)
                    self.sons.tocar("soco", 0.5)
                f.pousou = False
            if f.estado == "dash" and f.t == 1:
                P.poeira(f.x, CHAO_Y, 6, 1.0)
            if f.estado == "jump" and f.t == 1:
                self.sons.tocar("pulo", 0.5)
                P.poeira(f.x, CHAO_Y, 4, 0.6)

        if p.fase != self._fase_ant:
            if p.fase == "intro":
                self.sons.tocar("sino", 0.8)
            elif p.fase == "luta":
                self.sons.tocar("sino", 1.0)
            elif p.fase == "ko":
                self.sons.tocar("ko" if p.motivo == "K.O.!" else "sino")
                if p.motivo == "K.O.!":
                    self.tremor.add(16)
                    self.flash = 6
            self._fase_ant = p.fase

    def cena_luta(self, eventos):
        p = self.partida
        teclas = self._teclas(eventos)
        if p.fase == "fim" and p.fase_t > 30:
            if pygame.K_RETURN in teclas or pygame.K_SPACE in teclas:
                self.sons.tocar("ok")
                self.iniciar_luta(*self.chars)
                return
            if pygame.K_ESCAPE in teclas:
                self.sons.tocar("menu")
                self.abrir_selecao()
                return
        elif p.fase != "fim" and pygame.K_ESCAPE in teclas:
            self.pausa_idx = 0
            self.sons.tocar("menu")
            self.cena = "pausa"
            self._desenhar_luta()
            return

        estado = pygame.key.get_pressed()
        cmd1 = self.teclado[1].ler(eventos, estado)
        cmd2 = None if self.vs_cpu else self.teclado[2].ler(eventos, estado)
        p.update(cmd1, cmd2)
        self._processar_fx()
        self.particulas.update()
        self._desenhar_luta()

    def _desenhar_luta(self):
        p, s = self.partida, self.tela
        self._cenario()
        render.desenhar_objetos(s, p.combate, self.t)
        venc = None
        if p.fase == "fim" and p.vencedor not in (None, "empate"):
            venc = p.vencedor
        elif p.fase == "ko" and p.fase_t > 45:
            venc = p.vencedor_round
        for f in sorted((p.f1, p.f2), key=lambda f: f.estado == "attack"):
            render.desenhar_lutador(s, f, self.t, self.debug, vitoria=(f is venc and f.estado == "idle"))
        render.desenhar_efeitos(s, p.combate)
        self.particulas.draw(s)
        if self.flash > 0:
            self.flash -= 1
            self._veu(70, (255, 255, 255))
        render.desenhar_hud(s, p, self.fontes, self.t)
        self.particulas.draw_textos(s, self.fontes["grande"], texto)

        g, cx = self.fontes["titulo"], LARGURA // 2
        if p.fase == "intro":
            if p.fase_t < 40:
                k = min(1.0, p.fase_t / 14)
                texto(s, f"ROUND {p.round}", g, (255, 220, 80), (cx, 300), contorno=4, escala=2.2 - 1.2 * k,
                      alpha=int(255 * k))
            else:
                k = min(1.0, (p.fase_t - 40) / 6)
                glow(s, (140, 40, 10), (cx, 300), 260, 1.0 - k * 0.5)
                texto(s, "LUTE!", self.fontes["logo"], (255, 90, 50), (cx, 300), contorno=5, escala=1.8 - 0.8 * k)
        elif p.fase == "ko":
            k = min(1.0, p.fase_t / 10)
            cor = (240, 40, 35) if p.motivo == "K.O.!" else (255, 220, 80)
            glow(s, (120, 15, 10), (cx, 270), 300, 0.8)
            texto(s, p.motivo, self.fontes["logo"], cor, (cx, 270), contorno=6, escala=2.5 - 1.5 * k)
            if p.fase_t > 35:
                v = p.vencedor_round
                msg = f"{v.char.nome} VENCE O ROUND" if v else "EMPATE"
                texto(s, msg, self.fontes["grande"], (255, 255, 255), (cx, 375), contorno=3)
        elif p.fase == "fim":
            self._veu(110, (0, 0, 0))
            k = min(1.0, p.fase_t / 15)
            if p.vencedor == "empate":
                texto(s, "EMPATE!", g, (255, 255, 255), (cx, 260), contorno=4)
            else:
                v = p.vencedor
                quem = "CPU" if (self.vs_cpu and v is p.f2) else f"JOGADOR {v.slot}"
                glow(s, render.escurecer(v.char.cor, 0.6 if sum(v.char.cor) > 250 else 1.5), (cx, 260), 320, 0.9)
                texto(s, f"{v.char.nome} VENCEU!", g, render.cor_texto(v.char.cor), (cx, 260), contorno=5,
                      escala=1.6 - 0.6 * k)
                texto(s, quem, self.fontes["grande"], (255, 255, 255), (cx, 350), contorno=3)
            if p.fase_t > 30:
                texto(s, "ENTER  revanche        ESC  trocar lutadores", self.fontes["media"],
                      (235, 225, 225), (cx, 450))
        if self.debug:
            texto(s, "DEBUG: hurtbox verde / hitbox vermelha (F1)", self.fontes["mini"],
                  (120, 255, 160), (cx, ALTURA - 20), contorno=1)

    # ================================================================ pausa
    def cena_pausa(self, eventos):
        cpu = self.partida.cpus.get(2) if self.partida else None
        itens = ["CONTINUAR", "TROCAR LUTADORES", "MENU PRINCIPAL", "SAIR DO JOGO"]
        if cpu:
            itens.insert(1, "DIFICULDADE")
        for k in self._teclas(eventos):
            if cpu and itens[self.pausa_idx] == "DIFICULDADE" and k in (pygame.K_LEFT, pygame.K_a,
                                                                         pygame.K_RIGHT, pygame.K_d):
                passo = 1 if k in (pygame.K_RIGHT, pygame.K_d) else -1
                self.nivel = max(1, min(5, self.nivel + passo))
                cpu.set_nivel(self.nivel)
                self.sons.tocar("menu")
                continue
            if k in (pygame.K_UP, pygame.K_w):
                self.pausa_idx = (self.pausa_idx - 1) % len(itens)
                self.sons.tocar("menu")
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.pausa_idx = (self.pausa_idx + 1) % len(itens)
                self.sons.tocar("menu")
            elif k == pygame.K_ESCAPE:
                self.cena = "luta"
                return
            elif k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_f):
                escolha = itens[self.pausa_idx]
                if escolha == "DIFICULDADE":
                    self.nivel = self.nivel % 5 + 1
                    cpu.set_nivel(self.nivel)
                    self.sons.tocar("menu")
                    continue
                self.sons.tocar("ok")
                if escolha == "CONTINUAR":
                    self.cena = "luta"
                elif escolha == "TROCAR LUTADORES":
                    self.abrir_selecao()
                elif escolha == "MENU PRINCIPAL":
                    self.cena = "menu"
                else:
                    self.sair()
                return
        self._desenhar_luta()
        self._veu(165, (0, 0, 0))
        texto(self.tela, "PAUSA", self.fontes["titulo"], (255, 255, 255), (LARGURA // 2, 190), contorno=4)
        for i, item in enumerate(itens):
            y = 300 + i * 64
            sel = i == self.pausa_idx
            if item == "DIFICULDADE":
                self._botao("", (LARGURA // 2, y), sel, 520)
                render.medidor_dificuldade(self.tela, (LARGURA // 2 - 60, y - 18), self.nivel, self.fontes,
                                           0.5, nome=False)
                texto(self.tela, NIVEIS_CPU[self.nivel]["nome"], self.fontes["pequena"],
                      render.CORES_NIVEL[self.nivel], (LARGURA // 2 + 70, y), "midleft")
                texto(self.tela, "CPU", self.fontes["media"], (255, 255, 255), (LARGURA // 2 - 230, y), "midleft")
            else:
                self._botao(item, (LARGURA // 2, y), sel, 440)
