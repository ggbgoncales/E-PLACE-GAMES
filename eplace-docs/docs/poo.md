---
id: poo
title: Programação orientada a objetos
description: Exemplos de POO tirados do código do E-Place.
---

<div className="eyebrow">DESENVOLVIMENTO / CONCEITOS</div>

# Programação orientada a objetos

<p className="lead">Os exemplos abaixo são trechos reais do código do E-Place. Cada um mostra um conceito de POO e onde encontrá-lo no projeto.</p>

---

## Classe e objeto

Uma **classe** descreve como é uma coisa do jogo. Um **objeto** é uma coisa criada a partir dela. No Pong, a raquete é a classe `Paddle`, e o jogo cria duas raquetes com posição e cor diferentes.

```python title="src/games/Ping pong/game/entities/paddle.py"
class Paddle:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.speed = PADDLE_SPEED

    def move(self, direction, dt):
        self.rect.y += round(direction * self.speed * dt)
```

```python title="src/games/Ping pong/game/game.py"
self.left_paddle = Paddle(PADDLE_MARGIN, paddle_y, ACCENT_COLOR)
self.right_paddle = Paddle(SCREEN_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH, paddle_y, SECONDARY_COLOR)
```

O `__init__` é o construtor: guarda o estado de cada raquete em atributos (`rect`, `color`, `speed`). Os métodos (`move`, `draw`) são o que a raquete sabe fazer.

---

## Encapsulamento

Cada objeto cuida dos próprios dados e esconde os detalhes de como trabalha. A classe `GestorJogador` guarda as pontuações. Quem a usa chama `registar_pontuacao` e não precisa saber como o arquivo é lido ou gravado. Os métodos com `_` no começo são de uso interno da classe.

```python title="src/jogador.py"
class GestorJogador:
    def __init__(self, data_dir):
        self.ficheiro_pontuacoes = os.path.join(data_dir, "highscore.json")
        self.pontuacoes = self._carregar_pontuacoes()

    def registar_pontuacao(self, jogo_id, pontuacao):
        # Atualiza apenas se for um novo recorde
        if pontuacao > self.obter_pontuacao(jogo_id):
            self.pontuacoes[jogo_id] = pontuacao
            self._salvar_pontuacoes()
```

A regra "só grava se for recorde" fica dentro da classe. Nenhum jogo precisa repeti-la.

---

## Composição

Um objeto pode ser feito de outros objetos. Uma `Partida` do Kombate **tem** dois lutadores, um gerenciador de combate e, se for contra a máquina, uma CPU para cada lado.

```python title="src/games/Kombate/game/match.py"
class Partida:
    def __init__(self, char1, char2, cpu1=False, cpu2=True, nivel=NIVEL_CPU):
        self.f1 = Fighter(char1, 1)
        self.f2 = Fighter(char2, 2)
        self.combate = CombatManager()
        self.cpus = {1: CPU(self.f1, nivel) if cpu1 else None,
                     2: CPU(self.f2, nivel) if cpu2 else None}
```

Cada peça tem uma responsabilidade só: `Fighter` cuida do lutador, `CombatManager` dos golpes e `CPU` das decisões da máquina. A `Partida` só junta tudo. O Pong faz o mesmo: o `Game` tem duas `Paddle` e uma `Ball`.

---

## Herança

Uma classe pode **herdar** de outra e mudar só o que for diferente. No Kombate, `AnimNeonP` herda de `AnimNeon`, a animação do cenário neon, e acrescenta o relâmpago.

```python title="src/games/Kombate/game/mapas.py"
class AnimNeonP(AnimNeon):
    def __init__(self):
        super().__init__()
        self.carros = []                       # a pintura já tem os carros

    def desenhar(self, s, t):
        if (t // 4) % 160 == 0:                # relâmpago de vez em quando
            glow(s, (60, 60, 90), (900, 60), 500, 1.0)
        super().desenhar(s, t)
```

O `super()` chama o código da classe-mãe. Assim a animação nova reaproveita tudo o que a antiga já fazia.

---

## Polimorfismo

Classes diferentes podem ter um método com o mesmo nome e cada uma o faz do seu jeito. Os quatro cenários do Kombate têm uma animação própria, mas todas respondem a `desenhar(s, t)`. A classe `Mapa` chama esse método sem saber qual é o cenário.

```python title="src/games/Kombate/game/mapas.py"
class Mapa:
    """Mapa pronto para usar: fundo + vinheta + animacao."""

    def __init__(self, info):
        self.fundo = ...
        self.anim = info["anim"]()      # AnimTemploP, AnimNeonP, AnimColiseuP ou AnimFabricaP

    def desenhar(self, s, t):
        s.blit(self.fundo, (0, 0))
        self.anim.desenhar(s, t)        # cada animação desenha do seu jeito
```

Para criar um quinto cenário, basta escrever uma classe nova com o método `desenhar`. A `Mapa` não muda.

---

## Classes só para guardar dados

Quando uma classe serve para agrupar informações, o Python oferece o `@dataclass`, que gera o construtor sozinho. Os golpes do Kombate são descritos assim, e cada golpe é um objeto `Move` com uma lista de objetos `Hit`.

```python title="src/games/Kombate/game/characters.py"
@dataclass
class Hit:
    start: int                  # primeiro frame ativo do golpe
    end: int                    # último frame ativo
    box: tuple                  # (ox, oy, w, h)
    dano: float
    knockback: float = 6.0
    knockdown: bool = False

@dataclass
class Move:
    nome: str
    total: int                  # duração total (frames)
    hits: list = field(default_factory=list)
```

Para criar um golpe novo, escreve-se um `Move` com os valores. Não é preciso mexer na lógica da luta.

---

## Propriedades

Uma `@property` faz um método ser lido como se fosse um atributo. No Flappy Bird, o retângulo de colisão do pássaro é calculado a partir da posição dele.

```python title="src/games/Flappy bird/game/app.py"
class Bird:
    def flap(self):
        self.vel = FLAP_FORCE

    @property
    def rect(self):
        return pygame.Rect(self.pos.x - 13, self.pos.y - 12, 26, 24)
```

Quem usa escreve `bird.rect`, e o valor está sempre atualizado com a posição atual.

---

## Onde ver cada conceito

| Conceito | Exemplo | Arquivo |
|---|---|---|
| Classe e objeto | `Paddle`, `Ball` | `src/games/Ping pong/game/entities/` |
| Encapsulamento | `GestorJogador` | `src/jogador.py` |
| Composição | `Partida` | `src/games/Kombate/game/match.py` |
| Herança | `AnimNeonP(AnimNeon)` | `src/games/Kombate/game/mapas.py` |
| Polimorfismo | `Mapa.desenhar` | `src/games/Kombate/game/mapas.py` |
| Dataclass | `Hit`, `Move` | `src/games/Kombate/game/characters.py` |
| Propriedade | `Bird.rect` | `src/games/Flappy bird/game/app.py` |
