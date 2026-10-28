import json
import math
import random
from pathlib import Path

import pygame

from settings import WIDTH, HEIGHT, FPS, TITLE, GRAVITY, FLAP_FORCE, PIPE_SPEED, PIPE_GAP, SAVE_FILE

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
Vec=pygame.Vector2
WHITE=(250,252,255); INK=(20,36,58); SKY=(69,190,242); BLUE=(35,126,222)
CYAN=(55,236,239); YELLOW=(255,213,55); ORANGE=(255,130,45); GREEN=(53,196,104)
DARK_GREEN=(18,119,67); RED=(245,76,91); PINK=(255,100,176); PURPLE=(132,92,246)

screen=pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption(TITLE)
clock=pygame.time.Clock()
FONT_BIG=pygame.font.SysFont("arialblack",48)
FONT_TITLE=pygame.font.SysFont("arialblack",30)
FONT=pygame.font.SysFont("segoeui",21,bold=True)
SMALL=pygame.font.SysFont("segoeui",15,bold=True)
TINY=pygame.font.SysFont("consolas",12)


def clamp(v,a,b): return max(a,min(b,v))

def text(surf,value,font,color,pos,anchor="topleft",shadow=True):
    img=font.render(str(value),True,color); rect=img.get_rect(); setattr(rect,anchor,pos)
    if shadow:
        sh=font.render(str(value),True,(9,25,40)); sr=sh.get_rect(); setattr(sr,anchor,(pos[0]+2,pos[1]+3)); surf.blit(sh,sr)
    surf.blit(img,rect); return rect

def panel(surf,rect,fill=(255,255,255,220),border=(255,255,255,245),radius=18):
    layer=pygame.Surface(rect.size,pygame.SRCALPHA)
    pygame.draw.rect(layer,fill,layer.get_rect(),border_radius=radius)
    pygame.draw.rect(layer,border,layer.get_rect(),2,border_radius=radius)
    surf.blit(layer,rect.topleft)

def glow(surf,color,pos,r):
    layer=pygame.Surface((r*6,r*6),pygame.SRCALPHA); c=r*3
    for i in range(4,0,-1): pygame.draw.circle(layer,(*color,10+i*6),(c,c),r+i*r//2)
    surf.blit(layer,(pos[0]-c,pos[1]-c),special_flags=pygame.BLEND_ADD)

class SaveData:
    def __init__(self):
        self.path=Path(SAVE_FILE)
        self.data={"coins":0,"best":0,"hat":"none","effect":"classic","owned_hats":["none"],"owned_effects":["classic"],"skin":"gold","owned_skins":["gold"]}
        try:
            if self.path.exists(): self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
        except Exception: pass
    def save(self):
        try: self.path.write_text(json.dumps(self.data,indent=2),encoding="utf-8")
        except Exception: pass

class Particle:
    def __init__(self,pos,vel,color,life,size,kind="circle"):
        self.pos=Vec(pos); self.vel=Vec(vel); self.color=color; self.life=life; self.max=life; self.size=size; self.kind=kind
    def update(self,dt):
        self.life-=dt; self.pos+=self.vel*dt; self.vel.y+=80*dt; return self.life>0
    def draw(self,surf):
        a=clamp(self.life/self.max,0,1); s=max(1,int(self.size*a))
        if self.kind=="star":
            pts=[]
            for i in range(10):
                ang=-math.pi/2+i*math.pi/5; rad=s if i%2==0 else s*.45
                pts.append((self.pos.x+math.cos(ang)*rad,self.pos.y+math.sin(ang)*rad))
            pygame.draw.polygon(surf,self.color,pts)
        else: pygame.draw.circle(surf,self.color,self.pos,s)

class Cloud:
    def __init__(self,x=None):
        self.x=x if x is not None else random.randrange(WIDTH); self.y=random.randrange(70,470); self.speed=random.uniform(8,24); self.scale=random.uniform(.6,1.35)
    def update(self,dt):
        self.x-=self.speed*dt
        if self.x<-110: self.x=WIDTH+80; self.y=random.randrange(60,440)
    def draw(self,s):
        x,y=self.x,self.y; k=self.scale; c=(255,255,255,145)
        layer=pygame.Surface((130,65),pygame.SRCALPHA)
        pygame.draw.ellipse(layer,c,(10,30,105,27)); pygame.draw.circle(layer,c,(42,31),23); pygame.draw.circle(layer,c,(73,24),29); pygame.draw.circle(layer,c,(99,34),19)
        layer=pygame.transform.smoothscale(layer,(int(130*k),int(65*k))); s.blit(layer,(x,y))

class Pipe:
    def __init__(self,x,gap_y):
        self.x=x; self.gap_y=gap_y; self.base_gap_y=gap_y; self.passed=False; self.w=82
        self.phase=random.uniform(0,math.tau); self.age=0; self.motion=0
    def update(self,dt,speed):
        self.x-=speed*dt; self.age+=dt
        if self.motion: self.gap_y=self.base_gap_y+math.sin(self.age*1.35+self.phase)*self.motion
        return self.x>-self.w-20
    def rects(self,gap):
        return pygame.Rect(self.x,0,self.w,self.gap_y-gap/2),pygame.Rect(self.x,self.gap_y+gap/2,self.w,HEIGHT)
    def draw_one(self,surf,rect,top):
        body=pygame.Rect(rect)
        pygame.draw.rect(surf,(24,145,73),body,border_radius=8)
        pygame.draw.rect(surf,(72,220,116),(body.x+7,body.y,body.w-22,body.h),border_radius=7)
        pygame.draw.rect(surf,(136,247,158),(body.x+12,body.y,12,body.h),border_radius=6)
        pygame.draw.rect(surf,(10,90,48),body,4,border_radius=8)
        for by in range(body.top+36,body.bottom-20,72):
            pygame.draw.circle(surf,(190,255,205),(body.x+body.w-12,by),3); pygame.draw.circle(surf,(8,80,42),(body.x+body.w-12,by),3,1)
        cap_y=body.bottom-30 if top else body.top
        cap=pygame.Rect(body.x-8,cap_y,body.w+16,30)
        pygame.draw.rect(surf,(27,160,80),cap,border_radius=7); pygame.draw.rect(surf,(85,230,126),(cap.x+8,cap.y+4,cap.w-25,cap.h-8),border_radius=5); pygame.draw.rect(surf,(9,83,44),cap,4,border_radius=7)
    def draw(self,surf,gap):
        a,b=self.rects(gap); self.draw_one(surf,a,True); self.draw_one(surf,b,False)

class Bird:
    def __init__(self,hat,effect,skin="gold"):
        self.pos=Vec(140,HEIGHT*.43); self.vel=0; self.radius=18; self.angle=0; self.hat=hat; self.effect=effect; self.skin=skin; self.anim=0
    def flap(self): self.vel=FLAP_FORCE
    def update(self,dt):
        self.anim+=dt; self.vel+=GRAVITY*dt; self.pos.y+=self.vel*dt; self.angle=clamp(-self.vel*.075-8,-72,26)
    @property
    def rect(self): return pygame.Rect(self.pos.x-13,self.pos.y-12,26,24)
    def draw_hat(self,s,x,y):
        if self.hat=="cap":
            pygame.draw.arc(s,RED,(x-15,y-28,29,21),math.pi,math.pi*2,8); pygame.draw.rect(s,RED,(x-2,y-20,20,5),border_radius=2)
        elif self.hat=="tophat":
            pygame.draw.rect(s,(27,31,48),(x-11,y-34,22,21),border_radius=3); pygame.draw.rect(s,(27,31,48),(x-16,y-16,32,6),border_radius=2); pygame.draw.rect(s,PURPLE,(x-11,y-19,22,5))
        elif self.hat=="crown":
            pygame.draw.polygon(s,YELLOW,[(x-15,y-15),(x-13,y-34),(x-4,y-23),(x,y-37),(x+7,y-23),(x+15,y-34),(x+13,y-15)]); pygame.draw.rect(s,ORANGE,(x-15,y-18,30,6),border_radius=2)
        elif self.hat=="wizard":
            pygame.draw.polygon(s,PURPLE,[(x-16,y-14),(x+13,y-14),(x+2,y-43)]); pygame.draw.ellipse(s,PURPLE,(x-19,y-18,38,8)); pygame.draw.circle(s,YELLOW,(x+2,y-29),3)
        elif self.hat=="pirate":
            pygame.draw.arc(s,(25,28,39),(x-16,y-31,32,24),math.pi,math.pi*2,9); pygame.draw.circle(s,WHITE,(x,y-24),4); pygame.draw.line(s,WHITE,(x-6,y-18),(x+6,y-30),2)
        elif self.hat=="halo":
            pygame.draw.ellipse(s,YELLOW,(x-16,y-31,32,8),3); glow(s,YELLOW,(x,y-27),4)
        elif self.hat=="headphones":
            pygame.draw.arc(s,(35,45,65),(x-16,y-29,32,27),math.pi,math.pi*2,5); pygame.draw.rect(s,CYAN,(x-18,y-18,7,14),border_radius=3); pygame.draw.rect(s,CYAN,(x+11,y-18,7,14),border_radius=3)
    def draw(self,surf):
        bird=pygame.Surface((76,76),pygame.SRCALPHA); x=y=38
        # wing behind body
        wing_y=39+int(math.sin(self.anim*16)*5)
        pygame.draw.ellipse(bird,(232,153,35),(12,wing_y-8,28,19)); pygame.draw.ellipse(bird,(123,73,23),(12,wing_y-8,28,19),2)
        # body with outlines and highlight; cores customizaveis
        palettes={"gold":((255,190,43),(255,224,98),(108,66,22)),"blue":((55,166,245),(120,220,255),(22,70,125)),"rose":((255,105,165),(255,180,210),(125,38,78)),"mint":((65,220,155),(150,255,205),(20,105,72)),"night":((55,58,88),(125,115,210),(16,18,38))}
        body_col,light_col,outline=palettes.get(self.skin,palettes["gold"])
        pygame.draw.ellipse(bird,body_col,(18,18,43,39)); pygame.draw.ellipse(bird,outline,(18,18,43,39),3)
        pygame.draw.ellipse(bird,light_col,(22,21,21,13))
        pygame.draw.ellipse(bird,WHITE,(39,20,19,20)); pygame.draw.ellipse(bird,INK,(48,25,7,9)); pygame.draw.circle(bird,WHITE,(50,26),2)
        pygame.draw.polygon(bird,ORANGE,[(54,34),(72,40),(54,45)]); pygame.draw.lines(bird,(110,55,20),True,[(54,34),(72,40),(54,45)],2)
        pygame.draw.ellipse(bird,(255,245,205),(29,43,25,10))
        self.draw_hat(bird,x,y)
        bird=pygame.transform.rotate(bird,self.angle)
        surf.blit(bird,bird.get_rect(center=self.pos))

class Game:
    HATS=[("none","Sem chapéu",0),("cap","Boné",25),("tophat","Cartola",60),("crown","Coroa",120),("wizard","Mago",180),("pirate","Pirata",220),("halo","Aurora",260),("headphones","Headset",300)]
    EFFECTS=[("classic","Clássico",0),("spark","Faíscas",50),("rainbow","Arco-íris",100),("stars","Estrelas",160),("fire","Fogo",220),("ice","Gelo",260)]
    SKINS=[("gold","Dourado",0),("blue","Azul celeste",80),("rose","Rosa",100),("mint","Menta",130),("night","Noturno",200)]
    def __init__(self):
        self.save=SaveData(); self.state="menu"; self.menu_idx=0; self.shop_tab=0; self.shop_idx=0; self.streak=0
        self.clouds=[Cloud() for _ in range(7)]; self.particles=[]; self.reset()
    def reset(self):
        self.bird=Bird(self.save.data["hat"],self.save.data["effect"],self.save.data.get("skin","gold")); self.pipes=[]; self.score=0; self.started=False; self.spawn=0; self.speed=PIPE_SPEED; self.gap=PIPE_GAP; self.flash=0
    def emit(self,amount=7):
        effect=self.bird.effect
        colors=([RED,ORANGE,YELLOW] if effect=="fire" else ([WHITE,CYAN,BLUE] if effect=="ice" else ([YELLOW] if effect in ("classic","spark") else ([RED,ORANGE,YELLOW,GREEN,CYAN,PURPLE] if effect=="rainbow" else [WHITE,CYAN,PURPLE]))))
        for i in range(amount):
            self.particles.append(Particle(self.bird.pos+Vec(-16,random.uniform(-6,6)),Vec(random.uniform(-100,-45),random.uniform(-45,45)),colors[i%len(colors)],random.uniform(.35,.75),random.uniform(3,7),"star" if effect=="stars" else "circle"))
    def flap(self):
        if self.state=="play":
            if not self.started: self.started=True
            self.bird.flap(); self.emit(10 if self.bird.effect!="classic" else 5)
    def background(self):
        # rich vertical sky gradient
        for y in range(HEIGHT):
            t=y/HEIGHT; col=(int(58+65*t),int(178+40*t),int(239+10*t)); pygame.draw.line(screen,col,(0,y),(WIDTH,y))
        glow(screen,(255,232,130),(390,105),55); pygame.draw.circle(screen,(255,239,157),(390,105),34)
        for c in self.clouds: c.draw(screen)
        # distant hills
        pygame.draw.polygon(screen,(74,174,137),[(0,590),(60,520),(125,575),(195,505),(275,575),(350,520),(480,580),(480,720),(0,720)])
        pygame.draw.polygon(screen,(55,151,113),[(0,626),(76,565),(153,622),(242,550),(337,620),(418,568),(480,615),(480,720),(0,720)])
        pygame.draw.rect(screen,(209,181,91),(0,664,WIDTH,56)); pygame.draw.rect(screen,(112,204,95),(0,652,WIDTH,18)); pygame.draw.rect(screen,(47,135,71),(0,652,WIDTH,6))
        for x in range(0,WIDTH,32): pygame.draw.ellipse(screen,(232,205,112),(x,684,24,8))
    def update_common(self,dt):
        for c in self.clouds: c.update(dt)
        self.particles=[p for p in self.particles if p.update(dt)]
    def update_play(self,dt):
        self.update_common(dt); self.flash=max(0,self.flash-dt)
        if not self.started: return
        self.bird.update(dt); self.spawn-=dt
        self.speed=PIPE_SPEED+min(125,self.score*3.0); self.gap=max(118,PIPE_GAP-self.score*.85)
        if self.spawn<=0:
            pipe=Pipe(WIDTH+40,random.randint(190,485)); pipe.motion=min(34,max(0,self.score-6)*2.5); self.pipes.append(pipe); self.spawn=max(1.16,1.43-self.score*.008)
        self.pipes=[p for p in self.pipes if p.update(dt,self.speed)]
        if self.bird.effect!="classic" and random.random()<.55: self.emit(1)
        for p in self.pipes:
            if not p.passed and p.x+p.w<self.bird.pos.x:
                p.passed=True; self.score+=1; self.streak+=1; self.save.data["coins"]+=1+(1 if self.streak%5==0 else 0)
                for _ in range(14): self.particles.append(Particle((self.bird.pos.x,self.bird.pos.y),Vec(random.uniform(-110,110),random.uniform(-130,20)),YELLOW,.65,6,"star"))
            a,b=p.rects(self.gap)
            if self.bird.rect.colliderect(a) or self.bird.rect.colliderect(b): self.streak=0; self.game_over()
        if self.bird.pos.y>646 or self.bird.pos.y<-25: self.game_over()
    def game_over(self):
        self.save.data["best"]=max(self.save.data["best"],self.score); self.save.save(); self.state="over"; self.flash=.18
    def draw_score(self):
        text(screen,self.score,FONT_BIG,WHITE,(WIDTH//2,78),"center")
    def draw_menu(self):
        self.background(); t=pygame.time.get_ticks()/1000
        self.bird.pos=Vec(WIDTH*.5,270+math.sin(t*2.3)*8); self.bird.anim=t; self.bird.angle=-4; self.bird.draw(screen)
        text(screen,"FLAPPY",FONT_BIG,WHITE,(WIDTH//2,85),"center")
        text(screen,"BIRD",FONT_BIG,YELLOW,(WIDTH//2,137),"center")
        text(screen,"SKYWARD EDITION",SMALL,WHITE,(WIDTH//2,181),"center")
        panel(screen,pygame.Rect(75,365,330,190),(10,35,58,205),(255,255,255,90))
        items=("JOGAR","CUSTOMIZAR","SAIR")
        for i,item in enumerate(items):
            r=pygame.Rect(104,389+i*51,272,40)
            if i==self.menu_idx: pygame.draw.rect(screen,(255,198,45),r,border_radius=12); pygame.draw.rect(screen,WHITE,r,2,border_radius=12)
            text(screen,item,FONT,INK if i==self.menu_idx else WHITE,r.center,"center")
        pygame.draw.circle(screen,YELLOW,(34,34),16); text(screen,self.save.data["coins"],SMALL,WHITE,(58,34),"midleft")
        text(screen,f"RECORDE {self.save.data['best']}",SMALL,WHITE,(WIDTH-18,27),"topright")
        text(screen,"ESPAÇO / ENTER",TINY,WHITE,(WIDTH//2,606),"center")
    def draw_play(self):
        self.background()
        for p in self.pipes: p.draw(screen,self.gap)
        for p in self.particles: p.draw(screen)
        self.bird.draw(screen); self.draw_score()
        level=1+self.score//10
        text(screen,f"NÍVEL {level}",TINY,WHITE,(18,24))
        if self.score>=6: text(screen,"CANOS MÓVEIS",TINY,YELLOW,(WIDTH-18,24),"topright")
        if not self.started:
            panel(screen,pygame.Rect(95,395,290,86),(7,34,55,185),(255,255,255,80))
            text(screen,"ESPAÇO PARA VOAR",FONT,WHITE,(WIDTH//2,423),"center"); text(screen,"Passe pelos canos e ganhe moedas",TINY,WHITE,(WIDTH//2,458),"center")
    def draw_over(self):
        self.draw_play(); shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); shade.fill((4,18,35,135)); screen.blit(shade,(0,0))
        panel(screen,pygame.Rect(62,185,356,300),(248,252,255,240),(255,255,255,255))
        text(screen,"FIM DE JOGO",FONT_TITLE,INK,(WIDTH//2,220),"center")
        pygame.draw.circle(screen,YELLOW,(150,305),47); text(screen,self.score,FONT_TITLE,INK,(150,303),"center"); text(screen,"PONTOS",TINY,INK,(150,342),"center",False)
        pygame.draw.circle(screen,CYAN,(330,305),47); text(screen,self.save.data["best"],FONT_TITLE,INK,(330,303),"center"); text(screen,"RECORDE",TINY,INK,(330,342),"center",False)
        text(screen,f"+ {self.score} MOEDAS",SMALL,ORANGE,(WIDTH//2,382),"center")
        pygame.draw.rect(screen,YELLOW,(111,416,258,44),border_radius=13); text(screen,"JOGAR NOVAMENTE",FONT,INK,(240,437),"center")
        text(screen,"ESC para o menu",TINY,INK,(WIDTH//2,472),"center",False)
    def current_shop(self): return self.HATS if self.shop_tab==0 else (self.EFFECTS if self.shop_tab==1 else self.SKINS)
    def draw_shop_preview(self,item_id):
        preview=Bird(item_id if self.shop_tab==0 else self.save.data["hat"],item_id if self.shop_tab==1 else self.save.data["effect"],item_id if self.shop_tab==2 else self.save.data.get("skin","gold"))
        preview.pos=Vec(WIDTH//2,245); preview.anim=pygame.time.get_ticks()/1000; preview.draw(screen)
        if self.shop_tab==1:
            old=self.bird; self.bird=preview; self.emit(2); self.bird=old
    def draw_shop(self):
        self.background(); panel(screen,pygame.Rect(24,26,432,650),(8,30,52,225),(255,255,255,100))
        text(screen,"CUSTOMIZAÇÃO",FONT_TITLE,WHITE,(WIDTH//2,59),"center")
        tabs=("CHAPÉUS","EFEITOS","CORES")
        for i,name in enumerate(tabs):
            r=pygame.Rect(38+i*136,91,128,38); pygame.draw.rect(screen,YELLOW if i==self.shop_tab else (25,65,89),r,border_radius=10); text(screen,name,SMALL,INK if i==self.shop_tab else WHITE,r.center,"center")
        items=self.current_shop(); item_id,name,price=items[self.shop_idx]; self.draw_shop_preview(item_id)
        text(screen,name,FONT_TITLE,WHITE,(WIDTH//2,310),"center")
        owned_key="owned_hats" if self.shop_tab==0 else ("owned_effects" if self.shop_tab==1 else "owned_skins")
        select_key="hat" if self.shop_tab==0 else ("effect" if self.shop_tab==1 else "skin")
        owned=item_id in self.save.data[owned_key]
        selected=item_id==self.save.data[select_key]
        status="EQUIPADO" if selected else ("EQUIPAR" if owned else f"COMPRAR  {price}")
        pygame.draw.rect(screen,YELLOW,(100,349,280,46),border_radius=14); text(screen,status,FONT,INK,(240,372),"center")
        start=max(0,min(self.shop_idx-2,len(items)-5))
        for row,i in enumerate(range(start,min(len(items),start+5))):
            _,label,cost=items[i]; y=426+row*40; active=i==self.shop_idx
            if active: pygame.draw.rect(screen,(32,108,145),(58,y-5,364,34),border_radius=9)
            text(screen,label,SMALL,WHITE,(78,y+4)); text(screen,"GRÁTIS" if cost==0 else cost,SMALL,YELLOW,(397,y+4),"topright")
        pygame.draw.circle(screen,YELLOW,(50,650),14); text(screen,self.save.data["coins"],SMALL,WHITE,(72,650),"midleft"); text(screen,"ESC VOLTAR",TINY,WHITE,(WIDTH-44,650),"midright")
    def buy_or_equip(self):
        items=self.current_shop(); item_id,_,price=items[self.shop_idx]; owned_key="owned_hats" if self.shop_tab==0 else ("owned_effects" if self.shop_tab==1 else "owned_skins"); sel="hat" if self.shop_tab==0 else ("effect" if self.shop_tab==1 else "skin")
        if item_id in self.save.data[owned_key]: self.save.data[sel]=item_id
        elif self.save.data["coins"]>=price:
            self.save.data["coins"]-=price; self.save.data[owned_key].append(item_id); self.save.data[sel]=item_id
        self.save.save()
    def event(self,e):
        if e.type!=pygame.KEYDOWN: return
        if self.state=="menu":
            if e.key in (pygame.K_UP,pygame.K_w): self.menu_idx=(self.menu_idx-1)%3
            elif e.key in (pygame.K_DOWN,pygame.K_s): self.menu_idx=(self.menu_idx+1)%3
            elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                if self.menu_idx==0: self.reset(); self.state="play"
                elif self.menu_idx==1: self.state="shop"
                else: pygame.quit(); raise SystemExit
            elif e.key==pygame.K_ESCAPE: pygame.quit(); raise SystemExit
        elif self.state=="play":
            if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w): self.flap()
            elif e.key==pygame.K_ESCAPE: self.state="menu"
        elif self.state=="over":
            if e.key in (pygame.K_SPACE,pygame.K_RETURN): self.reset(); self.state="play"
            elif e.key==pygame.K_ESCAPE: self.state="menu"
        elif self.state=="shop":
            if e.key in (pygame.K_LEFT,pygame.K_a): self.shop_tab=(self.shop_tab-1)%3; self.shop_idx=0
            elif e.key in (pygame.K_RIGHT,pygame.K_d): self.shop_tab=(self.shop_tab+1)%3; self.shop_idx=0
            elif e.key in (pygame.K_UP,pygame.K_w): self.shop_idx=(self.shop_idx-1)%len(self.current_shop())
            elif e.key in (pygame.K_DOWN,pygame.K_s): self.shop_idx=(self.shop_idx+1)%len(self.current_shop())
            elif e.key in (pygame.K_RETURN,pygame.K_SPACE): self.buy_or_equip()
            elif e.key==pygame.K_ESCAPE: self.bird=Bird(self.save.data["hat"],self.save.data["effect"],self.save.data.get("skin","gold")); self.state="menu"
    def run(self):
        while True:
            dt=min(clock.tick(FPS)/1000,.033)
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); return
                self.event(e)
            if self.state=="play": self.update_play(dt); self.draw_play()
            else:
                self.update_common(dt)
                if self.state=="menu": self.draw_menu()
                elif self.state=="shop": self.draw_shop()
                else: self.draw_over()
            pygame.display.flip()
