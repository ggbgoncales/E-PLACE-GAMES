"""Camada de controle universal do E-PLACE.

Prioriza o mapeamento padrao SDL GameController (Xbox, PlayStation, Switch e
varios controles genericos). Se o dispositivo nao tiver mapeamento SDL, usa
pygame.joystick com deteccao de layout por nome e fallback generico.

API mantida por compatibilidade: XboxController, connected, axis(), button(),
pressed_buttons e poll_keys(). Os indices de button() sao logicos:
0=sul/confirmar, 1=leste/voltar, 2=oeste, 3=norte, 4=L1/LB, 5=R1/RB,
7=Start/Options/Plus.
"""
import pygame
import re

try:
    from pygame._sdl2 import controller as _sdl_controller
except (ImportError, AttributeError):
    _sdl_controller = None


def _fonte_retro(tamanho, titulo):
    """Titulos em Press Start 2P e textos em VT323 (assets/fonts); sem os arquivos usa fonte do sistema."""
    import os
    nome = "PressStart2P-Regular.ttf" if titulo else "VT323-Regular.ttf"
    pasta = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        caminho = os.path.join(pasta, "assets", "fonts", nome)
        if os.path.exists(caminho):
            return pygame.font.Font(caminho, max(8, int(tamanho)))
        pasta = os.path.dirname(pasta)
    return pygame.font.SysFont("arial,helveticaneue,dejavusans", max(8, int(tamanho)), bold=titulo)


class XboxController:
    """Nome antigo preservado; a classe agora aceita controles universais."""
    DEADZONE = 0.22
    REFRESH_INTERVAL = 90  # frames; tambem reage a eventos de hot-plug

    # Botoes SDL GameController padronizados.
    _SDL_BUTTONS = {
        0: "CONTROLLER_BUTTON_A",
        1: "CONTROLLER_BUTTON_B",
        2: "CONTROLLER_BUTTON_X",
        3: "CONTROLLER_BUTTON_Y",
        4: "CONTROLLER_BUTTON_LEFTSHOULDER",
        5: "CONTROLLER_BUTTON_RIGHTSHOULDER",
        7: "CONTROLLER_BUTTON_START",
        11: "CONTROLLER_BUTTON_DPAD_UP",
        12: "CONTROLLER_BUTTON_DPAD_DOWN",
        13: "CONTROLLER_BUTTON_DPAD_LEFT",
        14: "CONTROLLER_BUTTON_DPAD_RIGHT",
    }
    _SDL_AXES = {
        0: "CONTROLLER_AXIS_LEFTX",
        1: "CONTROLLER_AXIS_LEFTY",
    }

    def __init__(self):
        pygame.joystick.init()
        self.joystick = None
        self.sdl_controller = None
        self.device_name = ""
        self.guid = ""
        self.layout = "generic"
        self._held = set()
        self._repeat = {}
        self.pressed_buttons = set()
        self._previous_buttons = set()
        self._frames = 0
        self.refresh(force=True)

    @property
    def connected(self):
        try:
            if self.sdl_controller is not None and self.sdl_controller.get_init():
                return True
            if self.joystick is not None and self.joystick.get_init():
                return True
        except pygame.error:
            pass
        return False

    def _close_current(self):
        try:
            if self.sdl_controller is not None:
                self.sdl_controller.quit()
        except Exception:
            pass
        try:
            if self.joystick is not None:
                self.joystick.quit()
        except Exception:
            pass
        self.sdl_controller = None
        self.joystick = None

    def _classify(self, name):
        n = (name or "").lower()
        if any(s in n for s in ("playstation", "dualshock", "dualsense", "wireless controller", "sony")):
            return "playstation"
        if any(s in n for s in ("nintendo", "switch", "joy-con", "joy con", "pro controller")):
            return "nintendo"
        if any(s in n for s in ("xbox", "xinput", "x-box")):
            return "xbox"
        return "generic"

    def refresh(self, force=False):
        """Detecta conexoes/desconexoes sem exigir reiniciar o launcher."""
        try:
            pygame.joystick.init()
            if not force and self.connected:
                return
            self._close_current()
            count = pygame.joystick.get_count()
            if not count:
                return

            # Prefere o primeiro dispositivo reconhecido pelo SDL como gamepad.
            selected = 0
            if _sdl_controller is not None:
                try:
                    for i in range(count):
                        if _sdl_controller.is_controller(i):
                            selected = i
                            break
                except Exception:
                    pass

            if _sdl_controller is not None:
                try:
                    if _sdl_controller.is_controller(selected):
                        self.sdl_controller = _sdl_controller.Controller(selected)
                        self.sdl_controller.init()
                except Exception:
                    self.sdl_controller = None

            # Mantem Joystick para leitura de nome, GUID, D-pad e fallback.
            try:
                self.joystick = pygame.joystick.Joystick(selected)
                self.joystick.init()
                self.device_name = self.joystick.get_name() or "Controle"
                try:
                    self.guid = self.joystick.get_guid()
                except Exception:
                    self.guid = ""
            except pygame.error:
                self.joystick = None
                self.device_name = "Controle"
            self.layout = self._classify(self.device_name)
            self._held.clear()
            self._repeat.clear()
            self._previous_buttons.clear()
            self.pressed_buttons.clear()
        except pygame.error:
            self._close_current()

    def handle_event(self, event):
        """Pode ser chamado com eventos JOYDEVICEADDED/REMOVED pelo launcher."""
        if event.type in (getattr(pygame, "JOYDEVICEADDED", -1),
                          getattr(pygame, "JOYDEVICEREMOVED", -2)):
            self.refresh(force=True)

    def _raw_axis(self, index):
        if not self.joystick:
            return 0.0
        try:
            if self.joystick.get_numaxes() > index:
                value = float(self.joystick.get_axis(index))
                if abs(value) >= self.DEADZONE:
                    return value
        except pygame.error:
            self._close_current()
        return 0.0

    def _dpad_axis(self, index):
        """Lê o direcional como hat ou como quatro botões (comum no DualSense BT)."""
        try:
            if self.sdl_controller is not None:
                negative = 13 if index == 0 else 11
                positive = 14 if index == 0 else 12
                if self.button(negative):
                    return -1.0
                if self.button(positive):
                    return 1.0
            if self.joystick:
                if self.joystick.get_numhats():
                    hx, hy = self.joystick.get_hat(0)
                    hat_value = hx if index == 0 else -hy
                    if hat_value:
                        return float(hat_value)
                # Mapeamento SDL/DirectInput frequente para D-pad em controles PS.
                if self.joystick.get_numbuttons() > 14:
                    negative = 13 if index == 0 else 11
                    positive = 14 if index == 0 else 12
                    if self.joystick.get_button(negative):
                        return -1.0
                    if self.joystick.get_button(positive):
                        return 1.0
        except pygame.error:
            self._close_current()
        return 0.0

    def axis(self, index):
        if not self.connected:
            self.refresh(force=True)
        if not self.connected:
            return 0.0
        try:
            if self.sdl_controller is not None:
                enum_name = self._SDL_AXES.get(index)
                enum = getattr(_sdl_controller, enum_name, None) if enum_name else None
                if enum is not None:
                    value = float(self.sdl_controller.get_axis(enum)) / 32767.0
                    if abs(value) >= self.DEADZONE:
                        return max(-1.0, min(1.0, value))
            value = self._raw_axis(index)
            if abs(value) >= self.DEADZONE:
                return value
            # Alguns drivers expõem o stick esquerdo em eixos alternativos.
            if self.joystick and self.joystick.get_numaxes() == 4:
                alt = self._raw_axis(index + 2)
                if abs(alt) >= self.DEADZONE:
                    return alt
            # O direcional digital precisa alimentar também os jogos que consultam axis().
            return self._dpad_axis(index)
        except pygame.error:
            self._close_current()
        return 0.0

    def _raw_button_index(self, logical_index):
        # Layouts comuns quando o SDL nao possui um mapeamento para o controle.
        maps = {
            "xbox": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 7: 7},
            # DualShock 4 / DualSense no Pygame em modo joystick: face 0-3,
            # L1=4, R1=5. No DualSense Bluetooth, OPTIONS=9 (em vez de 6).
            "playstation": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
                            7: (9 if self.joystick and self.joystick.get_numbuttons() >= 13 else 6)},
            "nintendo": {0: 1, 1: 0, 2: 3, 3: 2, 4: 4, 5: 5, 7: 9},
            "generic": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 7: 7},
        }
        return maps.get(self.layout, maps["generic"]).get(logical_index, logical_index)

    def button_icon(self, index):
        """Marcador para desenhar a imagem pequena do botao, nunca um glifo de fonte."""
        return f"\x1dBTN{int(index)}\x1d"

    def button(self, index):
        if not self.connected:
            self.refresh(force=True)
        if not self.connected:
            return False
        try:
            if self.sdl_controller is not None:
                enum_name = self._SDL_BUTTONS.get(index)
                enum = getattr(_sdl_controller, enum_name, None) if enum_name else None
                if enum is not None and self.sdl_controller.get_button(enum):
                    return True
            raw = self._raw_button_index(index)
            raw_pressed = bool(self.joystick and self.joystick.get_numbuttons() > raw
                               and self.joystick.get_button(raw))
            if raw_pressed:
                return True
            # R2/RT pode chegar como eixo analógico, principalmente no DualSense Bluetooth.
            if index == 5 and self.joystick and self.joystick.get_numaxes() > 5:
                trigger = float(self.joystick.get_axis(5))
                if trigger > 0.55:
                    return True
            if index == 5 and self.sdl_controller is not None:
                trigger_enum = getattr(_sdl_controller, "CONTROLLER_AXIS_TRIGGERRIGHT", None)
                if trigger_enum is not None:
                    trigger = float(self.sdl_controller.get_axis(trigger_enum)) / 32767.0
                    if trigger > 0.55:
                        return True
            return False
        except pygame.error:
            self._close_current()
            return False

    def poll_keys(self):
        """Converte direcional e botoes em eventos para o menu do launcher."""
        self._frames += 1
        if self._frames % self.REFRESH_INTERVAL == 0 and not self.connected:
            self.refresh(force=True)
        if not self.connected:
            return []
        keys = set()
        x, y = self.axis(0), self.axis(1)
        if x <= -self.DEADZONE: keys.add(pygame.K_LEFT)
        if x >= self.DEADZONE: keys.add(pygame.K_RIGHT)
        if y <= -self.DEADZONE: keys.add(pygame.K_UP)
        if y >= self.DEADZONE: keys.add(pygame.K_DOWN)

        try:
            if self.joystick and self.joystick.get_numhats():
                hx, hy = self.joystick.get_hat(0)
                if hx < 0: keys.add(pygame.K_LEFT)
                if hx > 0: keys.add(pygame.K_RIGHT)
                if hy < 0: keys.add(pygame.K_DOWN)
                if hy > 0: keys.add(pygame.K_UP)
        except pygame.error:
            pass

        # O botão norte é emitido como F2, um evento próprio para o atalho de
        # CONTROLES. Ele não depende do caractere Y do teclado e não interfere
        # nas ações de gameplay (por exemplo, triângulo = dash no Kombate).
        mapping = {0: pygame.K_SPACE, 1: pygame.K_ESCAPE,
                   7: pygame.K_RETURN, 2: pygame.K_x,
                   4: pygame.K_q, 5: pygame.K_e}
        now_buttons = set()
        for idx, key in mapping.items():
            if self.button(idx):
                now_buttons.add(idx)
                keys.add(key)
                # Botão oeste: Quadrado (PS), X (Xbox) ou Y (Nintendo) abre Recordes.
                if idx == 2:
                    keys.add(pygame.K_h)
        if self.button(3):
            now_buttons.add(3)
        newly_pressed = now_buttons - self._previous_buttons
        self.pressed_buttons = newly_pressed
        self._previous_buttons = now_buttons

        events = []
        if 3 in newly_pressed:
            events.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2))
        for key in keys:
            if key not in self._held:
                events.append(pygame.event.Event(pygame.KEYDOWN, key=key))
                self._repeat[key] = 0.0
            else:
                self._repeat[key] = self._repeat.get(key, 0.0) + 1 / 60
                if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT) and self._repeat[key] >= 0.18:
                    events.append(pygame.event.Event(pygame.KEYDOWN, key=key))
                    self._repeat[key] = 0.0
        for key in self._held - keys:
            self._repeat.pop(key, None)
        self._held = keys
        return events


# Alias mais descritivo para novos usos; imports antigos continuam funcionando.
UniversalController = XboxController


_ICON_CACHE = {}
def _controller_button_image(layout, index):
    """Gera um pequeno ícone gráfico de botão, sem depender de glifos Unicode."""
    key = (layout, int(index))
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    size = 24
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    if layout == "playstation" and index in (0, 1, 2, 3, 7):
        # Ícones gráficos do DualSense: X, bola, quadrado, triângulo e OPTIONS.
        color = (120, 225, 255)
        if index == 0:  # X
            pygame.draw.line(surf, color, (5, 5), (19, 19), 3)
            pygame.draw.line(surf, color, (19, 5), (5, 19), 3)
        elif index == 1:  # Bola
            pygame.draw.circle(surf, color, (12, 12), 8, 3)
        elif index == 2:  # Quadrado
            pygame.draw.rect(surf, color, (4, 4, 16, 16), 3, border_radius=1)
        elif index == 3:  # Triângulo
            pygame.draw.polygon(surf, color, [(12, 3), (21, 20), (3, 20)], 3)
        else:  # OPTIONS: três traços horizontais
            for yy in (6, 12, 18):
                pygame.draw.line(surf, color, (4, yy), (20, yy), 3)
    else:
        labels = {
            "xbox": {0: "A", 1: "B", 2: "X", 3: "Y", 4: "LB", 5: "RB", 7: "MENU"},
            "nintendo": {0: "B", 1: "A", 2: "Y", 3: "X", 4: "L", 5: "R", 7: "+"},
            "generic": {0: "A", 1: "B", 2: "X", 3: "Y", 4: "L1", 5: "R1", 7: "START"},
        }
        label = labels.get(layout, labels["generic"]).get(index, "")
        font_size = 13 if len(label) <= 2 else 10
        font = pygame.font.SysFont("arial", font_size, bold=True)
        color = (245, 250, 255) if layout != "generic" else (205, 225, 240)
        glyph = font.render(label, True, color)
        surf.blit(glyph, glyph.get_rect(center=(size // 2, size // 2)))

    _ICON_CACHE[key] = surf
    return surf

def draw_controller_text(surface, font, value, color, pos, controller, anchor="topleft", icon_size=24):
    """Renderiza uma legenda com imagens inline; pos/anchor seguem pygame.Rect.

    Aceita tanto um objeto Font quanto um tamanho numerico, evitando que uma
    tela de jogo que passe SMALL/FONT (int/float) derrube o loop de desenho.
    """
    if not hasattr(font, "render"):
        font = pygame.font.SysFont(None, max(8, int(float(font) * 1.35)))
    parts = re.split(r"(\x1dBTN\d+\x1d)", str(value))
    items=[]
    for part in parts:
        m=re.fullmatch(r"\x1dBTN(\d+)\x1d", part)
        if m:
            image = _controller_button_image(getattr(controller, "layout", "generic"), int(m.group(1)))
            if icon_size and image.get_size() != (int(icon_size), int(icon_size)):
                image = pygame.transform.smoothscale(image, (int(icon_size), int(icon_size)))
            items.append(("img", image))
        elif part:
            items.append(("txt", font.render(part, True, color)))
    gap=4; total=sum(x.get_width() for _,x in items)+gap*max(0,len(items)-1)
    height=max([x.get_height() for _,x in items] or [font.get_height()])
    rect=pygame.Rect(0,0,total,height); setattr(rect, anchor, pos)
    x=rect.left
    for kind,img in items:
        y=rect.centery-img.get_height()//2
        surface.blit(img,(x,y)); x += img.get_width()+gap
    return rect


def draw_controls_table(surface, rows, title="CONTROLES", footer="F1 / ESC: VOLTAR", colors=None):
    """Desenha uma tabela fixa com comandos de PlayStation, Xbox e Switch.

    rows: sequencia de (acao, playstation, xbox, nintendo). Os botoes PS sao
    desenhados geometricamente; Xbox e Switch usam letras/nomes legiveis.
    """
    colors = colors or {}
    w, h = surface.get_size()
    panel_w = min(w - 36, 900)
    panel_h = min(h - 36, max(270, 150 + len(rows) * 38))
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((14, 17, 40, 242))
    x0, y0 = (w - panel_w) // 2, (h - panel_h) // 2
    surface.blit(panel, (x0, y0))
    try:
        from utils import ui_arcade as _ui
        _ui.brilho(surface, pygame.Rect(x0, y0, panel_w, panel_h), _ui.CIANO, intensidade=50, raio=14, camadas=3)
    except ImportError:
        pass
    pygame.draw.rect(surface, (24, 231, 255), (x0, y0, panel_w, panel_h), 3, border_radius=14)
    title_font = _fonte_retro(max(18, min(30, w // 34)) * 0.55, True)
    head_font = _fonte_retro(max(13, min(19, w // 52)) * 1.4, False)
    row_font = _fonte_retro(max(12, min(18, w // 55)) * 1.4, False)
    title_img = title_font.render(title, True, (232, 236, 255))
    surface.blit(title_img, title_img.get_rect(center=(w // 2, y0 + 30)))
    inner_left = x0 + 22
    action_w = int(panel_w * .36)
    col_w = (panel_w - 44 - action_w) / 3
    headers = (("AÇÃO", inner_left + action_w / 2),
               ("PLAYSTATION", inner_left + action_w + col_w / 2),
               ("XBOX", inner_left + action_w + col_w * 1.5),
               ("NINTENDO SWITCH", inner_left + action_w + col_w * 2.5))
    hy = y0 + 69
    for label, cx in headers:
        img = head_font.render(label, True, (255, 205, 100))
        surface.blit(img, img.get_rect(center=(int(cx), hy)))
    row_top = y0 + 91
    row_h = min(39, max(27, (panel_h - 132) // max(1, len(rows))))
    for i, row in enumerate(rows):
        action, ps, xbox, switch = (list(row) + [""] * 4)[:4]
        yy = row_top + i * row_h
        if i % 2 == 0:
            pygame.draw.rect(surface, (22, 27, 60), (x0 + 12, yy - 2, panel_w - 24, row_h), border_radius=5)
        vals = (action, ps, xbox, switch)
        centers = [inner_left + action_w / 2,
                   inner_left + action_w + col_w / 2,
                   inner_left + action_w + col_w * 1.5,
                   inner_left + action_w + col_w * 2.5]
        img = row_font.render(str(action), True, (238, 246, 255))
        surface.blit(img, img.get_rect(center=(int(centers[0]), yy + row_h // 2)))
        _draw_table_control(surface, centers[1], yy + row_h // 2, str(ps), "playstation", row_font)
        _draw_table_control(surface, centers[2], yy + row_h // 2, str(xbox), "xbox", row_font)
        _draw_table_control(surface, centers[3], yy + row_h // 2, str(switch), "nintendo", row_font)
    foot = _fonte_retro(max(11, min(15, w // 65)) * 1.4, False).render(footer, True, (105, 220, 230))
    surface.blit(foot, foot.get_rect(center=(w // 2, y0 + panel_h - 19)))


def _draw_table_control(surface, cx, cy, token, platform, font):
    """Renderiza um botao/descricao numa celula da tabela."""
    token = token.strip()
    if not token:
        return
    color = (110, 225, 255) if platform == "playstation" else (245, 250, 255)
    upper = token.upper()
    if (platform == "xbox" and upper in ("MENU", "START", "OPTIONS")):
        icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        for yy in (6, 12, 18): pygame.draw.line(icon, color, (4, yy), (20, yy), 3)
        surface.blit(icon, icon.get_rect(center=(int(cx), int(cy))))
    elif platform == "playstation" and upper in ("X", "O", "SQUARE", "QUADRADO", "TRIANGLE", "TRIANGULO", "OPTIONS", "L1", "R1", "L2", "R2"):
        s = 24
        icon = pygame.Surface((s, s), pygame.SRCALPHA)
        if upper == "X":
            pygame.draw.line(icon, color, (5, 5), (19, 19), 3)
            pygame.draw.line(icon, color, (19, 5), (5, 19), 3)
        elif upper == "O": pygame.draw.circle(icon, color, (12, 12), 8, 3)
        elif upper in ("SQUARE", "QUADRADO"): pygame.draw.rect(icon, color, (4, 4, 16, 16), 3)
        elif upper in ("TRIANGLE", "TRIANGULO"): pygame.draw.polygon(icon, color, [(12, 3), (21, 20), (3, 20)], 3)
        elif upper == "OPTIONS":
            for yy in (6, 12, 18): pygame.draw.line(icon, color, (4, yy), (20, yy), 3)
        else:
            label = font.render(upper, True, color); icon.blit(label, label.get_rect(center=(12, 12)))
        surface.blit(icon, icon.get_rect(center=(int(cx), int(cy))))
    else:
        label = font.render(token, True, color)
        surface.blit(label, label.get_rect(center=(int(cx), int(cy))))
