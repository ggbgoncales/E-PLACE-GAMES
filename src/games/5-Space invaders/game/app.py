"""
NEON VOID - arcade espacial em um unico arquivo.
Requisito: pip install pygame
Execucao: python main.py

Controles:
  WASD / setas : mover
  Espaco       : disparar
  Shift        : impulso
  P            : pausar
  ESC          : voltar / sair
  Enter        : confirmar
"""

import math
import random
import sys
from array import array

try:
    import pygame
except ImportError:
    print("Pygame nao encontrado. Instale com: pip install pygame")
    raise

# ----------------------------- CONFIGURACAO -----------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
TITLE = "NEON VOID"
Vec = pygame.Vector2

BLACK = (2, 5, 15)
WHITE = (235, 250, 255)
CYAN = (35, 245, 255)
BLUE = (40, 110, 255)
PURPLE = (155, 65, 255)
PINK = (255, 55, 150)
RED = (255, 65, 80)
ORANGE = (255, 150, 55)
YELLOW = (255, 230, 90)
GREEN = (80, 255, 160)

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

FONT_BIG = pygame.font.SysFont("arialblack", 68)
FONT_TITLE = pygame.font.SysFont("arialblack", 38)
FONT = pygame.font.SysFont("segoeui", 22)
FONT_SMALL = pygame.font.SysFont("consolas", 16)
FONT_TINY = pygame.font.SysFont("consolas", 12)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def glow_circle(surface, color, pos, radius, strength=4):
    radius = max(1, int(radius))
    pad = radius * 4
    g = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
    c = (pad, pad)
    for i in range(strength, 0, -1):
        r = radius + i * radius // 2
        a = max(5, 30 // i)
        pygame.draw.circle(g, (*color, a), c, r)
    pygame.draw.circle(g, (*color, 230), c, radius)
    surface.blit(g, (int(pos[0] - pad), int(pos[1] - pad)), special_flags=pygame.BLEND_ADD)


def text(surf, value, font, color, pos, anchor="topleft", shadow=True):
    img = font.render(str(value), True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        sh = font.render(str(value), True, (0, 0, 0))
        sr = sh.get_rect()
        setattr(sr, anchor, (pos[0] + 3, pos[1] + 3))
        surf.blit(sh, sr)
    surf.blit(img, rect)
    return rect


def synth_tone(freq=440, duration=.08, volume=.2, slide=0):
    try:
        sample_rate = 44100
        n = int(duration * sample_rate)
        buf = array("h")
        for i in range(n):
            t = i / sample_rate
            f = freq + slide * (i / max(1, n))
            env = (1 - i / max(1, n)) ** 1.7
            val = int(32767 * volume * env * math.sin(2 * math.pi * f * t))
            buf.append(val); buf.append(val)
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


SND_SHOT = synth_tone(700, .055, .12, 260)
SND_HIT = synth_tone(130, .10, .15, -50)
SND_PICK = synth_tone(520, .16, .16, 650)
SND_BOOM = synth_tone(90, .24, .22, -60)


def play(sound):
    if sound:
        sound.play()


# ----------------------------- FUNDO ESPACIAL -----------------------------
class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(150):
            self.stars.append([random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                               random.choice((.25, .45, .8, 1.3)), random.randint(1, 3)])
        self.nebula = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(18):
            x, y = random.randrange(WIDTH), random.randrange(HEIGHT)
            r = random.randrange(60, 180)
            c = random.choice(((15, 45, 120, 7), (80, 15, 130, 6), (0, 100, 145, 5)))
            pygame.draw.circle(self.nebula, c, (x, y), r)

    def update(self, speed):
        for s in self.stars:
            s[1] += s[2] * speed
            if s[1] > HEIGHT:
                s[0], s[1] = random.uniform(0, WIDTH), -4

    def draw(self, surf):
        surf.fill(BLACK)
        surf.blit(self.nebula, (0, 0))
        for x, y, z, size in self.stars:
            col = (int(125 + 90*z), int(160 + 65*z), 255)
            pygame.draw.line(surf, col, (x, y), (x, y + size + z*3), max(1, size//2))


class Particle:
    def __init__(self, pos, vel, color, life, size):
        self.pos = Vec(pos); self.vel = Vec(vel)
        self.color = color; self.life = life; self.max_life = life; self.size = size

    def update(self, dt):
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= .985
        return self.life > 0

    def draw(self, surf):
        a = clamp(self.life / self.max_life, 0, 1)
        r = max(1, int(self.size * a))
        glow_circle(surf, self.color, self.pos, r, 2)


class FloatingText:
    def __init__(self, pos, value, color=WHITE):
        self.pos = Vec(pos); self.value = value; self.color = color; self.life = 1

    def update(self, dt):
        self.life -= dt; self.pos.y -= 42 * dt
        return self.life > 0

    def draw(self, surf):
        text(surf, self.value, FONT_SMALL, self.color, self.pos, "center")


# ----------------------------- ENTIDADES -----------------------------
class Bullet:
    def __init__(self, pos, vel, friendly=True, damage=1, color=CYAN, radius=4):
        self.pos = Vec(pos); self.vel = Vec(vel); self.friendly = friendly
        self.damage = damage; self.color = color; self.radius = radius

    def update(self, dt):
        self.pos += self.vel * dt
        return -40 < self.pos.x < WIDTH + 40 and -50 < self.pos.y < HEIGHT + 50

    def draw(self, surf):
        tail = self.pos - self.vel.normalize() * 16 if self.vel.length_squared() else self.pos
        pygame.draw.line(surf, self.color, tail, self.pos, max(2, self.radius))
        glow_circle(surf, self.color, self.pos, self.radius, 3)

    @property
    def rect(self):
        return pygame.Rect(self.pos.x-self.radius, self.pos.y-self.radius,
                           self.radius*2, self.radius*2)


class Player:
    def __init__(self):
        self.pos = Vec(WIDTH/2, HEIGHT-80)
        self.vel = Vec(); self.radius = 18
        self.hp = 100; self.max_hp = 100
        self.energy = 100; self.shield = 0
        self.cooldown = 0; self.invuln = 0
        self.weapon = 1; self.weapon_timer = 0

    def update(self, dt, particles):
        keys = pygame.key.get_pressed()
        direction = Vec(keys[pygame.K_d] - keys[pygame.K_a] + keys[pygame.K_RIGHT] - keys[pygame.K_LEFT],
                        keys[pygame.K_s] - keys[pygame.K_w] + keys[pygame.K_DOWN] - keys[pygame.K_UP])
        if direction.length_squared(): direction = direction.normalize()
        boosting = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.energy > 2
        speed = 355 if boosting else 235
        if boosting: self.energy -= 42 * dt
        else: self.energy = min(100, self.energy + 22 * dt)
        target = direction * speed
        self.vel = self.vel.lerp(target, min(1, 9*dt))
        self.pos += self.vel * dt
        self.pos.x = clamp(self.pos.x, 24, WIDTH-24)
        self.pos.y = clamp(self.pos.y, 55, HEIGHT-25)
        self.cooldown -= dt; self.invuln -= dt; self.weapon_timer -= dt
        if self.weapon_timer <= 0: self.weapon = 1
        if random.random() < .65:
            color = CYAN if boosting else BLUE
            particles.append(Particle(self.pos + Vec(random.uniform(-6,6), 23),
                                      Vec(random.uniform(-25,25), random.uniform(90,170)), color, .3, 5))

    def shoot(self, bullets):
        if self.cooldown > 0: return
        play(SND_SHOT)
        if self.weapon == 1:
            bullets.append(Bullet(self.pos + Vec(0,-24), Vec(0,-590)))
            self.cooldown = .16
        elif self.weapon == 2:
            for angle in (-7, 7):
                v = Vec(0,-620).rotate(angle)
                bullets.append(Bullet(self.pos + Vec(angle/3,-22), v, True, 1, CYAN, 4))
            self.cooldown = .13
        else:
            for angle in (-13, 0, 13):
                bullets.append(Bullet(self.pos + Vec(0,-24), Vec(0,-650).rotate(angle), True, 2, GREEN, 5))
            self.cooldown = .12

    def hit(self, damage):
        if self.invuln > 0: return False
        if self.shield > 0:
            self.shield -= damage
        else:
            self.hp -= damage
        self.invuln = .65
        play(SND_HIT)
        return True

    def draw(self, surf):
        if self.invuln > 0 and int(self.invuln*14) % 2: return
        x, y = int(self.pos.x), int(self.pos.y)
        keys = pygame.key.get_pressed()
        boost = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.energy > 2
        pulse = math.sin(pygame.time.get_ticks() * .02)

        # Nave compacta: aproximadamente 38 px de largura por 42 px de altura.
        flame = 12 + (7 if boost else 0) + int(pulse * 2)
        glow_circle(surf, BLUE, (x, y + 15), 7 if not boost else 10, 3)
        pygame.draw.polygon(surf, (30, 90, 255), [(x-4,y+13),(x,y+13+flame),(x+4,y+13)])
        pygame.draw.polygon(surf, CYAN, [(x-2,y+13),(x,y+19+flame//2),(x+2,y+13)])

        # Asas e fuselagem metálica.
        pygame.draw.polygon(surf, (25,38,60), [(x,y-20),(x-7,y-8),(x-20,y+13),(x-7,y+9),(x,y+18),(x+7,y+9),(x+20,y+13),(x+7,y-8)])
        pygame.draw.polygon(surf, (100,130,158), [(x-19,y+12),(x-7,y-7),(x-5,y+8),(x-10,y+12)])
        pygame.draw.polygon(surf, (100,130,158), [(x+19,y+12),(x+7,y-7),(x+5,y+8),(x+10,y+12)])
        pygame.draw.polygon(surf, (226,237,244), [(x,y-20),(x-6,y-4),(x-4,y+10),(x,y+15)])
        pygame.draw.polygon(surf, (125,151,176), [(x,y-20),(x+6,y-4),(x+4,y+10),(x,y+15)])
        pygame.draw.line(surf, WHITE, (x,y-18), (x,y+6), 1)

        # Cockpit e canhões.
        pygame.draw.ellipse(surf, (3,24,46), (x-5,y-11,10,16))
        pygame.draw.ellipse(surf, CYAN, (x-4,y-10,8,13))
        pygame.draw.ellipse(surf, WHITE, (x-2,y-9,3,7))
        pygame.draw.rect(surf, (180,205,220), (x-12,y-1,3,15), border_radius=1)
        pygame.draw.rect(surf, (180,205,220), (x+9,y-1,3,15), border_radius=1)
        pygame.draw.circle(surf, PINK, (x-15,y+10), 2)
        pygame.draw.circle(surf, PINK, (x+15,y+10), 2)

        if self.shield > 0:
            shield = pygame.Surface((58,58), pygame.SRCALPHA)
            r = 25 + int(pulse)
            pygame.draw.circle(shield, (40,205,255,25), (29,29), r)
            pygame.draw.circle(shield, (80,240,255,180), (29,29), r, 2)
            pygame.draw.arc(shield, WHITE, (4,4,50,50), .2, 1.5, 2)
            surf.blit(shield, (x-29,y-29), special_flags=pygame.BLEND_ADD)

    @property
    def rect(self):
        return pygame.Rect(self.pos.x-10, self.pos.y-13, 20, 27)


class Asteroid:
    def __init__(self, difficulty=1):
        self.radius = random.randint(16, 39)
        self.pos = Vec(random.randint(35, WIDTH-35), -self.radius-10)
        self.vel = Vec(random.uniform(-35,35), random.uniform(75,130) + difficulty*8)
        self.rot = random.random()*360; self.rot_speed = random.uniform(-80,80)
        self.hp = max(1, self.radius//13); self.max_hp = self.hp
        self.shape = []
        for i in range(12):
            a = i*30
            r = self.radius * random.uniform(.72,1.05)
            self.shape.append(Vec(math.cos(math.radians(a))*r, math.sin(math.radians(a))*r))

    def update(self, dt):
        self.pos += self.vel*dt; self.rot += self.rot_speed*dt
        return self.pos.y < HEIGHT+self.radius+30

    def draw(self, surf):
        pts = [self.pos + p.rotate(self.rot) for p in self.shape]
        pygame.draw.polygon(surf, (70,76,94), pts)
        pygame.draw.polygon(surf, (120,135,158), pts, 2)
        for off, r in ((Vec(-.3,-.25), .22), (Vec(.28,.2), .15), (Vec(.15,-.38), .1)):
            p = self.pos + off*self.radius
            pygame.draw.circle(surf, (46,51,67), p, max(2,int(self.radius*r)))

    @property
    def rect(self):
        return pygame.Rect(self.pos.x-self.radius*.72, self.pos.y-self.radius*.72,
                           self.radius*1.44, self.radius*1.44)


class Enemy:
    def __init__(self, level=1, elite=False):
        self.elite = elite
        self.pos = Vec(random.randint(60, WIDTH-60), -40)
        self.t = random.random()*10; self.base_x = self.pos.x
        self.hp = (8 + level*2) if elite else (2 + level//3)
        self.max_hp = self.hp
        self.speed = 55 + level*4; self.cooldown = random.uniform(.7,1.8)
        self.radius = 25 if elite else 17

    def update(self, dt, bullets, player):
        self.t += dt; self.pos.y += self.speed*dt
        self.pos.x = self.base_x + math.sin(self.t*2.1)*70
        self.cooldown -= dt
        if self.cooldown <= 0 and self.pos.y > 20:
            aim = player.pos-self.pos
            if aim.length_squared(): aim.scale_to_length(210 if not self.elite else 260)
            bullets.append(Bullet(self.pos+Vec(0,12), aim, False, 13 if self.elite else 9, PINK, 5))
            self.cooldown = .75 if self.elite else random.uniform(1.3,2.2)
        return self.pos.y < HEIGHT+60

    def draw(self, surf):
        x,y = self.pos; c = PURPLE if self.elite else RED
        pygame.draw.ellipse(surf, (110,115,135), (x-self.radius,y-8,self.radius*2,18))
        pygame.draw.ellipse(surf, (195,210,220), (x-self.radius*.55,y-17,self.radius*1.1,22))
        pygame.draw.arc(surf, c, (x-self.radius*.55,y-17,self.radius*1.1,22), math.pi, math.pi*2, 3)
        for ox in (-.55,0,.55): glow_circle(surf, c, (x+ox*self.radius,y+7), 3, 2)
        if self.hp < self.max_hp:
            pygame.draw.rect(surf, (25,30,45), (x-22,y-28,44,5))
            pygame.draw.rect(surf, c, (x-22,y-28,44*self.hp/self.max_hp,5))

    @property
    def rect(self):
        return pygame.Rect(self.pos.x-self.radius, self.pos.y-15, self.radius*2, 30)


class Powerup:
    COLORS = {"shield": CYAN, "repair": GREEN, "weapon": YELLOW}
    LABELS = {"shield": "S", "repair": "+", "weapon": "W"}
    def __init__(self, pos):
        self.kind = random.choice(("shield","repair","weapon"))
        self.pos = Vec(pos); self.t = 0

    def update(self, dt):
        self.t += dt; self.pos.y += 75*dt
        return self.pos.y < HEIGHT+30

    def draw(self, surf):
        c = self.COLORS[self.kind]
        glow_circle(surf,c,self.pos,12,3)
        pygame.draw.circle(surf,(15,28,45),self.pos,9)
        text(surf,self.LABELS[self.kind],FONT_TINY,c,self.pos,"center",False)

    @property
    def rect(self): return pygame.Rect(self.pos.x-13,self.pos.y-13,26,26)


# ----------------------------- JOGO -----------------------------
class Game:
    def __init__(self):
        self.stars = Starfield()
        self.highscore = 0
        self.state = "menu"
        self.menu_index = 0
        self.reset()

    def reset(self):
        self.player = Player(); self.bullets=[]; self.asteroids=[]; self.enemies=[]
        self.powerups=[]; self.particles=[]; self.floaters=[]
        self.score=0; self.combo=1; self.combo_time=0
        self.wave=1; self.wave_timer=0; self.spawn_timer=.4
        self.shake=0; self.paused=False; self.message="ONDA 1"; self.message_time=2

    def burst(self, pos, color, amount=18, power=150):
        for _ in range(amount):
            v = Vec(random.uniform(-1,1),random.uniform(-1,1))
            if v.length_squared(): v.scale_to_length(random.uniform(30,power))
            self.particles.append(Particle(pos,v,color,random.uniform(.25,.75),random.uniform(2,7)))

    def destroy(self, obj, reward):
        color = ORANGE if isinstance(obj, Asteroid) else PURPLE
        self.burst(obj.pos,color,24 if reward>100 else 14,210)
        play(SND_BOOM); self.shake=max(self.shake,8)
        gained=reward*self.combo; self.score+=gained
        self.floaters.append(FloatingText(obj.pos,f"+{gained}",YELLOW))
        self.combo=min(8,self.combo+1); self.combo_time=2.4
        if random.random()<.09: self.powerups.append(Powerup(obj.pos))

    def new_wave(self):
        self.wave += 1; self.wave_timer=0; self.spawn_timer=.2
        self.message=f"ONDA {self.wave}"; self.message_time=2
        if self.wave % 5 == 0:
            self.enemies.append(Enemy(self.wave, True)); self.message="ALVO ELITE"

    def update_play(self, dt):
        if self.paused: return
        self.stars.update(1.0 + self.wave*.03)
        self.player.update(dt,self.particles)
        keys=pygame.key.get_pressed()
        if keys[pygame.K_SPACE]: self.player.shoot(self.bullets)
        self.message_time-=dt; self.combo_time-=dt
        if self.combo_time<=0: self.combo=1
        self.wave_timer+=dt
        if self.wave_timer>18: self.new_wave()
        self.spawn_timer-=dt
        if self.spawn_timer<=0:
            if random.random()<.67: self.asteroids.append(Asteroid(self.wave))
            else: self.enemies.append(Enemy(self.wave))
            self.spawn_timer=max(.22,1.0-self.wave*.045)*random.uniform(.7,1.3)

        self.bullets=[b for b in self.bullets if b.update(dt)]
        self.asteroids=[a for a in self.asteroids if a.update(dt)]
        self.enemies=[e for e in self.enemies if e.update(dt,self.bullets,self.player)]
        self.powerups=[p for p in self.powerups if p.update(dt)]
        self.particles=[p for p in self.particles if p.update(dt)]
        self.floaters=[f for f in self.floaters if f.update(dt)]

        # tiros do jogador
        for b in self.bullets[:]:
            if not b.friendly: continue
            targets=self.asteroids+self.enemies
            for obj in targets:
                if b.rect.colliderect(obj.rect):
                    obj.hp-=b.damage
                    if b in self.bullets: self.bullets.remove(b)
                    self.burst(b.pos,b.color,4,70)
                    if obj.hp<=0:
                        if obj in self.asteroids: self.asteroids.remove(obj); self.destroy(obj,40+obj.radius)
                        elif obj in self.enemies: self.enemies.remove(obj); self.destroy(obj,250 if obj.elite else 90)
                    break

        # impactos no jogador
        for b in self.bullets[:]:
            if not b.friendly and b.rect.colliderect(self.player.rect):
                if self.player.hit(b.damage): self.burst(self.player.pos,RED,12,150); self.shake=10
                if b in self.bullets: self.bullets.remove(b)
        for obj in self.asteroids[:] + self.enemies[:]:
            if obj.rect.colliderect(self.player.rect):
                if self.player.hit(22): self.burst(self.player.pos,ORANGE,15,180); self.shake=12
                if obj in self.asteroids: self.asteroids.remove(obj)
                elif obj in self.enemies: self.enemies.remove(obj)
        for p in self.powerups[:]:
            if p.rect.colliderect(self.player.rect):
                play(SND_PICK); self.burst(p.pos,p.COLORS[p.kind],15,120)
                if p.kind=="shield": self.player.shield=min(50,self.player.shield+35)
                elif p.kind=="repair": self.player.hp=min(100,self.player.hp+30)
                else: self.player.weapon=min(3,self.player.weapon+1); self.player.weapon_timer=12
                self.floaters.append(FloatingText(p.pos,p.kind.upper(),p.COLORS[p.kind]))
                self.powerups.remove(p)
        if self.player.hp<=0:
            self.highscore=max(self.highscore,self.score); self.state="gameover"; play(SND_BOOM)

    def draw_hud(self,surf):
        panel=pygame.Surface((WIDTH,60),pygame.SRCALPHA); panel.fill((3,8,24,190)); surf.blit(panel,(0,0))
        text(surf,"INTEGRIDADE",FONT_TINY,(150,180,200),(18,10))
        pygame.draw.rect(surf,(30,40,57),(18,28,210,13),border_radius=6)
        hpw=210*max(0,self.player.hp)/100
        pygame.draw.rect(surf,GREEN if self.player.hp>35 else RED,(18,28,hpw,13),border_radius=6)
        text(surf,f"{max(0,int(self.player.hp))}%",FONT_TINY,WHITE,(123,34),"center",False)
        text(surf,"ENERGIA",FONT_TINY,(150,180,200),(250,10))
        pygame.draw.rect(surf,(30,40,57),(250,28,130,10),border_radius=5)
        pygame.draw.rect(surf,CYAN,(250,28,130*self.player.energy/100,10),border_radius=5)
        if self.player.shield>0: text(surf,f"ESCUDO {int(self.player.shield)}",FONT_TINY,CYAN,(400,20))
        text(surf,f"{self.score:08d}",FONT_TITLE,WHITE,(WIDTH-20,6),"topright")
        text(surf,f"ONDA {self.wave}   x{self.combo}",FONT_SMALL,YELLOW,(WIDTH-20,45),"bottomright")
        if self.player.weapon_timer>0:
            text(surf,f"ARMA NV.{self.player.weapon}  {self.player.weapon_timer:0.1f}s",FONT_TINY,YELLOW,(WIDTH/2,18),"midtop")

    def draw_play(self):
        world=pygame.Surface((WIDTH,HEIGHT)); self.stars.draw(world)
        for p in self.powerups: p.draw(world)
        for a in self.asteroids: a.draw(world)
        for e in self.enemies: e.draw(world)
        for b in self.bullets: b.draw(world)
        self.player.draw(world)
        for p in self.particles: p.draw(world)
        for f in self.floaters: f.draw(world)
        offset=(random.randint(-int(self.shake),int(self.shake)),random.randint(-int(self.shake),int(self.shake))) if self.shake>0 else (0,0)
        self.shake=max(0,self.shake-.55)
        screen.blit(world,offset); self.draw_hud(screen)
        if self.message_time>0: text(screen,self.message,FONT_BIG,CYAN,(WIDTH/2,HEIGHT/2),"center")
        if self.paused:
            shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); shade.fill((0,0,10,170)); screen.blit(shade,(0,0))
            text(screen,"PAUSADO",FONT_BIG,WHITE,(WIDTH/2,HEIGHT/2-20),"center")
            text(screen,"P para continuar",FONT,CYAN,(WIDTH/2,HEIGHT/2+42),"center")

    def draw_menu(self):
        self.stars.update(.45); self.stars.draw(screen)
        # planeta decorativo
        glow_circle(screen,BLUE,(760,155),72,4)
        pygame.draw.circle(screen,(25,67,125),(760,155),64)
        pygame.draw.arc(screen,(80,170,255),(695,120,130,55),0,math.pi,8)
        text(screen,"NEON",FONT_BIG,WHITE,(66,75))
        text(screen,"VOID",FONT_BIG,CYAN,(66,137))
        text(screen,"COMANDO ESTELAR",FONT_SMALL,(145,190,230),(71,213))
        items=("INICIAR MISSAO","COMO JOGAR","SAIR")
        for i,item in enumerate(items):
            y=305+i*55; selected=i==self.menu_index
            if selected:
                pygame.draw.rect(screen,(15,80,125),(58,y-7,286,42),border_radius=8)
                pygame.draw.rect(screen,CYAN,(58,y-7,5,42),border_radius=3)
            text(screen,item,FONT,CYAN if selected else (145,165,190),(78,y))
        text(screen,"W/S ou setas  |  ENTER",FONT_TINY,(105,130,160),(60,500))
        text(screen,"ARCADE PROTOCOL // v1.0",FONT_TINY,(70,100,130),(WIDTH-25,HEIGHT-20),"bottomright")

    def draw_help(self):
        self.stars.draw(screen)
        text(screen,"COMO JOGAR",FONT_TITLE,CYAN,(WIDTH/2,70),"center")
        rows=(("WASD / SETAS","Movimentar nave"),("ESPACO","Disparar"),("SHIFT","Impulso de velocidade"),("P","Pausar"),("ESC","Voltar"))
        for i,(key,desc) in enumerate(rows):
            y=145+i*55; pygame.draw.rect(screen,(12,24,45),(210,y-7,540,42),border_radius=7)
            text(screen,key,FONT_SMALL,YELLOW,(235,y+5)); text(screen,desc,FONT_SMALL,WHITE,(430,y+5))
        text(screen,"Colete S (escudo), + (reparo) e W (arma).",FONT_SMALL,GREEN,(WIDTH/2,450),"center")
        text(screen,"ESC para voltar",FONT_TINY,(145,165,190),(WIDTH/2,505),"center")

    def draw_gameover(self):
        self.stars.draw(screen)
        text(screen,"MISSAO ENCERRADA",FONT_TITLE,RED,(WIDTH/2,125),"center")
        text(screen,f"PONTUACAO  {self.score:08d}",FONT_TITLE,WHITE,(WIDTH/2,220),"center")
        text(screen,f"RECORDE  {self.highscore:08d}",FONT,CYAN,(WIDTH/2,276),"center")
        text(screen,f"ONDA ALCANCADA  {self.wave}",FONT_SMALL,YELLOW,(WIDTH/2,320),"center")
        text(screen,"ENTER para reiniciar",FONT,CYAN,(WIDTH/2,395),"center")
        text(screen,"ESC para o menu",FONT_SMALL,(150,170,195),(WIDTH/2,440),"center")

    def event(self,e):
        if e.type==pygame.KEYDOWN:
            if self.state=="menu":
                if e.key in (pygame.K_w,pygame.K_UP): self.menu_index=(self.menu_index-1)%3
                elif e.key in (pygame.K_s,pygame.K_DOWN): self.menu_index=(self.menu_index+1)%3
                elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                    if self.menu_index==0: self.reset(); self.state="play"
                    elif self.menu_index==1: self.state="help"
                    else: pygame.quit(); sys.exit()
                elif e.key==pygame.K_ESCAPE: pygame.quit(); sys.exit()
            elif self.state=="help" and e.key==pygame.K_ESCAPE: self.state="menu"
            elif self.state=="play":
                if e.key==pygame.K_p: self.paused=not self.paused
                elif e.key==pygame.K_ESCAPE: self.state="menu"
            elif self.state=="gameover":
                if e.key==pygame.K_RETURN: self.reset(); self.state="play"
                elif e.key==pygame.K_ESCAPE: self.state="menu"

    def run(self):
        while True:
            dt=min(clock.tick(FPS)/1000, .033)
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); return
                self.event(e)
            if self.state=="play": self.update_play(dt); self.draw_play()
            elif self.state=="menu": self.draw_menu()
            elif self.state=="help": self.draw_help()
            else: self.stars.update(.3); self.draw_gameover()
            pygame.display.flip()


