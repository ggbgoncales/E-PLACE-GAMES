import math
import random
import pygame
from settings import (VW, WATER_DARK, WATER_LIGHT, WATER_FOAM, WOOD_DARK, WOOD, WOOD_LIGHT,
                      GATOR_DARK, GATOR, GATOR_LIGHT, GOLD, INK, WHITE,
                      SHELL_DARK, SHELL, SHELL_LIGHT, SKIN_DARK, SKIN,
                      SNAKE_DARK, SNAKE, SNAKE_LIGHT, RED, pixel_rect)

DIVE_CYCLE = 5.0        # tartaruga: 3.0s em cima, 0.8s afundando (aviso), 1.2s submersa
TURTLE_W = 18           # largura de cada tartaruga do grupo
LOOP_MARGIN = 80        # quanto fora da tela os objetos andam antes de dar a volta

# ---------------- jacare (sprite estilo cartoon) ----------------
OUT=(10,28,18);D=(36,100,30);G=(78,156,40);L=(122,196,58);H=(176,228,96)
B=(214,232,120);BS=(168,196,78);EYE=(236,150,30);K=(16,16,16);WT=(255,255,240)


def build_gator_sprite(frame=0):
    W_,H_=62,22
    m=pygame.Surface((W_,H_),pygame.SRCALPHA)   # mascara/cores, virado pra ESQUERDA
    f=frame
    # pernas (coxas arredondadas) atras do corpo
    for cx in (20,42):
        pygame.draw.ellipse(m,D,(cx-4+f,12,9,8)); pygame.draw.rect(m,D,(cx-4+f,17,7,3))
    # rabo (afina para a direita)
    pygame.draw.polygon(m,G,[(44,8),(61,13),(61,14),(44,17)])
    # corpo
    pygame.draw.ellipse(m,G,(12,5,40,13))
    # cabeca + focinho
    pygame.draw.ellipse(m,G,(8,5,16,11))
    pygame.draw.rect(m,G,(1,10,14,5),border_radius=2)
    # escamas grandes nas costas
    SC=[]
    for i,x in enumerate(range(18,56,6)):
        r=3 if x<44 else 2
        y=6 if x<44 else (9 if x<50 else 11)
        SC.append((x,y,r)); pygame.draw.circle(m,L,(x,y),r)
    # contorno de cada escama (fica destacada igual a referencia)
    for x,y,r in SC:
        pygame.draw.circle(m,D,(x,y+1),r,1)
        pygame.draw.circle(m,L,(x,y),r-1)
        m.set_at((x-1,y-r+1),H)
    # pernas da frente (por cima)
    for cx in (17,39):
        pygame.draw.ellipse(m,D,(cx-1-f,10,10,9))
        pygame.draw.ellipse(m,G,(cx-f,11,8,7)); pygame.draw.rect(m,G,(cx+1-f,15,5,4))
        pygame.draw.arc(m,L,(cx+1-f,12,6,5),0.3,2.6,1)
    # ---- sombreamento ----
    px=pygame.PixelArray(m)
    for x in range(W_):
        col=[y for y in range(H_) if m.get_at((x,y)).a]
        if not col: continue
        t,b=min(col),max(col)
        for y in col:
            c=m.get_at((x,y))[:3]
            if c in (L,D,H): continue
            if y<=t+1: px[x,y]=L
            elif y==t+2 and 12<x<48: px[x,y]=L
    del px
    # brilho nas costas
    for x in range(20,44):
        if x%5: m.set_at((x,8),H)
    for x,y in ((18,5),(24,5),(30,5),(36,5),(42,5)): m.set_at((x,y),H)
    # barriga
    for x in range(4,48):
        for y in (14,15):
            if m.get_at((x,y)).a and m.get_at((x,y))[:3] not in (D,OUT) and not (14<x<26 or 36<x<48):
                m.set_at((x,y),B if y==15 else BS if x%4==0 else B)
    # boca: linha e dentes
    for x in range(2,15): m.set_at((x,13),OUT)
    for x in (3,6,9,12): m.set_at((x,12),WT)
    for x in (5,8,11): m.set_at((x,14),WT)
    m.set_at((15,12),OUT);m.set_at((16,12),OUT)
    # narina
    m.set_at((3,10),OUT); m.set_at((4,10),OUT)
    # olho laranja grande
    pygame.draw.circle(m,OUT,(14,8),3)
    pygame.draw.circle(m,EYE,(14,8),2)
    m.set_at((14,7),K);m.set_at((14,8),K);m.set_at((14,9),K)
    m.set_at((13,7),(255,230,150))
    # sobrancelha
    for x in (13,14,15,16): m.set_at((x,4),OUT)
    # garrinhas
    for cx in (17,39):
        for d in (0,2,4): m.set_at((cx+1-f+d,19),OUT)
    # ---- contorno automatico ----
    o=m.copy()
    for x in range(W_):
        for y in range(H_):
            if m.get_at((x,y)).a==0:
                for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W_ and 0<=yy<H_ and m.get_at((xx,yy)).a and m.get_at((xx,yy))[:3]!=OUT:
                        o.set_at((x,y),OUT);break
    return o


class Mover:
    def __init__(self, x, y, width, speed, kind, dive=False, loop=None):
        self.x = float(x)
        self.y = y
        self.width = width
        self.speed = speed
        self.kind = kind
        self.dive = dive
        # comprimento da "esteira" da faixa: todos os objetos da mesma faixa
        # usam o mesmo valor, entao o espacamento entre eles nunca muda
        self.loop = loop or (VW + 2 * LOOP_MARGIN)
        if kind == "snake":
            self.rect = pygame.Rect(int(x), y + 6, width, 10)
        else:
            self.rect = pygame.Rect(int(x), y + 4, width, 14)
        self.anim = random.random() * DIVE_CYCLE

    # ---------------- estado da tartaruga ----------------
    @property
    def dive_phase(self):
        return (self.anim % DIVE_CYCLE) if self.dive else 0.0

    @property
    def sinking(self):
        return self.dive and 3.0 <= self.dive_phase < 3.8

    @property
    def submerged(self):
        return self.dive and self.dive_phase >= 3.8

    @property
    def safe(self):
        """Pode ficar em cima? Troncos sim; tartarugas so na superficie."""
        if self.kind == "log":
            return True
        if self.kind == "turtle":
            return not self.submerged
        return False

    def update(self, dt):
        self.anim += dt
        self.x += self.speed * dt
        if self.speed > 0 and self.x > VW + LOOP_MARGIN:
            self.x -= self.loop
        elif self.speed < 0 and self.x < -LOOP_MARGIN:
            self.x += self.loop
        self.rect.x = int(self.x)

    # ---------------- desenhos ----------------
    def draw_log(self, surface):
        r = self.rect
        pixel_rect(surface, WATER_DARK, (r.x + 2, r.y + 3, r.w, r.h - 1))
        pixel_rect(surface, WOOD_DARK, (r.x, r.y + 2, r.w, r.h - 4))
        pixel_rect(surface, WOOD, (r.x + 2, r.y, r.w - 4, r.h - 3))
        pixel_rect(surface, WOOD_LIGHT, (r.x + 5, r.y + 2, max(2, r.w - 12), 2))
        pixel_rect(surface, WOOD_DARK, (r.x, r.y + 4, 3, r.h - 8))
        pixel_rect(surface, WOOD_DARK, (r.right - 3, r.y + 4, 3, r.h - 8))
        pixel_rect(surface, WOOD_LIGHT, (r.right - 2, r.y + 5, 1, 4))
        for xx in range(r.x + 10, r.right - 7, 14):
            pixel_rect(surface, WOOD_DARK, (xx, r.y + 4, 2, 6))
            pixel_rect(surface, WOOD_LIGHT, (xx + 2, r.y + 3, 3, 1))

    _gator_cache = {}

    def draw_gator(self, surface):
        r = self.rect
        right = self.speed > 0
        frame = int(self.anim * 4) % 2
        key = (frame, right)
        img = Mover._gator_cache.get(key)
        if img is None:
            img = build_gator_sprite(frame)          # desenhado virado pra esquerda
            if right:
                img = pygame.transform.flip(img, True, False)
            Mover._gator_cache[key] = img
        x = r.centerx - img.get_width() // 2
        y = r.bottom - img.get_height() + 2
        surface.blit(img, (x, y))
        # agua batendo no corpo (espuma animada)
        wy = r.bottom - 2
        for k in range(4, img.get_width() - 4, 3):
            if (k + int(self.anim * 8)) % 6 < 3:
                pygame.draw.line(surface, (120, 210, 240), (x + k, wy), (x + k + 2, wy))
        for k in range(8, img.get_width() - 8, 9):
            o = int(self.anim * 6) % 4
            pygame.draw.line(surface, (210, 245, 255), (x + k + o, wy + 1), (x + k + 3 + o, wy + 1))

    def draw_one_turtle(self, surface, tx, ty, right, swim, blink):
        """Tartaruga vista de cima: casco oval, cabeca na frente e 4 nadadeiras."""
        pygame.draw.ellipse(surface, WATER_DARK, (tx + 1, ty + 3, 16, 11))
        f = 1 if swim else 0
        pixel_rect(surface, SKIN_DARK, (tx + 2 - f, ty + 1, 4, 3))
        pixel_rect(surface, SKIN_DARK, (tx + 12 + f, ty + 1, 4, 3))
        pixel_rect(surface, SKIN_DARK, (tx + 2 + f, ty + 11, 4, 3))
        pixel_rect(surface, SKIN_DARK, (tx + 12 - f, ty + 11, 4, 3))
        pixel_rect(surface, SKIN, (tx + 3 - f, ty + 2, 2, 1))
        pixel_rect(surface, SKIN, (tx + 13 + f, ty + 2, 2, 1))
        hx = tx + 15 if right else tx - 3
        pixel_rect(surface, SKIN_DARK, (hx, ty + 5, 5, 5))
        pixel_rect(surface, SKIN, (hx + 1, ty + 6, 3, 3))
        pixel_rect(surface, INK, (hx + (3 if right else 1), ty + 6, 1, 1))
        pixel_rect(surface, INK, (hx + (3 if right else 1), ty + 8, 1, 1))
        shell = SHELL_LIGHT if blink else SHELL
        pygame.draw.ellipse(surface, SHELL_DARK, (tx + 2, ty + 2, 14, 11))
        pygame.draw.ellipse(surface, shell, (tx + 3, ty + 3, 12, 9))
        pixel_rect(surface, SHELL_DARK, (tx + 8, ty + 3, 1, 9))
        pixel_rect(surface, SHELL_DARK, (tx + 4, ty + 7, 10, 1))
        pixel_rect(surface, SHELL_LIGHT, (tx + 5, ty + 4, 2, 2))
        pixel_rect(surface, SHELL_LIGHT, (tx + 10, ty + 4, 2, 2))

    def draw_turtle(self, surface):
        r = self.rect
        n = max(1, r.w // TURTLE_W)
        if self.submerged:
            for i in range(n):
                tx = r.x + i * TURTLE_W
                pygame.draw.ellipse(surface, WATER_LIGHT, (tx + 3, r.y + 4, 12, 7), 1)
                if int(self.anim * 6 + i) % 2:
                    pixel_rect(surface, WATER_FOAM, (tx + 8, r.y + 2, 2, 2))
            return
        sink = 2 if self.sinking else 0
        blink = self.sinking and int(self.anim * 10) % 2
        swim = int(self.anim * 4) % 2
        right = self.speed > 0
        for i in range(n):
            self.draw_one_turtle(surface, r.x + i * TURTLE_W, r.y - 1 + sink, right, (swim + i) % 2, blink)

    def draw_snake(self, surface):
        """Cobra completa: rabo fino na ponta, corpo ondulando e cabeca."""
        r = self.rect
        right = self.speed > 0
        n = r.w // 3                      # quantidade de gomos
        cy = r.y + 5
        pts = []
        for i in range(n + 1):
            t = i / n                     # 0 = ponta do rabo, 1 = pescoco
            wy = math.sin(self.anim * 9 + i * 0.7) * 2.2
            if right:
                x = r.x + i * (r.w - 8) / n
            else:
                x = r.right - i * (r.w - 8) / n
            esp = 1 + int(t * 3.2)        # rabo fino -> corpo grosso
            pts.append((x, cy + wy, esp))
        # contorno e depois o corpo por cima
        for x, y, esp in pts:
            pygame.draw.circle(surface, SNAKE_DARK, (int(x), int(y)), esp + 1)
        for i, (x, y, esp) in enumerate(pts):
            cor = SNAKE_LIGHT if i % 3 == 0 else SNAKE
            pygame.draw.circle(surface, cor, (int(x), int(y)), esp)
        # ponta do rabo (chocalho)
        tx, ty, _ = pts[0]
        pixel_rect(surface, GOLD, (int(tx) - 1, int(ty) - 1, 2, 2))
        # cabeca
        nx, ny, _ = pts[-1]
        hx = int(nx) + (2 if right else -10)
        hy = int(ny) - 4
        pygame.draw.ellipse(surface, SNAKE_DARK, (hx - 1, hy - 1, 11, 10))
        pygame.draw.ellipse(surface, SNAKE, (hx, hy, 9, 8))
        pixel_rect(surface, SNAKE_LIGHT, (hx + 2, hy + 1, 4, 2))
        # olho
        ex = hx + (6 if right else 2)
        pixel_rect(surface, GOLD, (ex, hy + 2, 2, 2))
        pixel_rect(surface, INK, (ex + (1 if right else 0), hy + 2, 1, 2))
        # lingua piscando
        if int(self.anim * 5) % 2:
            lx = hx + 9 if right else hx - 4
            pixel_rect(surface, RED, (lx, hy + 5, 4, 1))
            pixel_rect(surface, RED, (lx + (3 if right else 0), hy + 4, 1, 1))
            pixel_rect(surface, RED, (lx + (3 if right else 0), hy + 6, 1, 1))

    def draw(self, surface):
        if self.kind == "log":
            self.draw_log(surface)
        elif self.kind == "turtle":
            self.draw_turtle(surface)
        elif self.kind == "snake":
            self.draw_snake(surface)
        else:
            self.draw_gator(surface)
