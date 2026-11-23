---
id: estrutura
title: Estrutura do projeto
description: Organização de pastas e funcionamento do launcher do E-Place.
---

<div className="eyebrow">DESENVOLVIMENTO / ARQUITETURA</div>

# Estrutura do projeto

<p className="lead">O E-Place é um **launcher** que descobre e executa jogos independentes. Cada jogo vive na própria pasta, com seu `main.py`.</p>

## Estrutura de pastas

```text
Eplace Games/
├── main.py               # Launcher: menu, lista de jogos, recordes, configurações
├── config.json           # Tela cheia, volume, som do menu
├── requirements.txt      # pygame>=2.5.0
├── README.md
├── assets/
│   ├── covers/           # Capas dos jogos (nome do arquivo = nome da pasta do jogo)
│   ├── ui/               # background.png do menu
│   └── sounds/           # eplace_menu.wav, menu_click.wav
├── data/
│   └── highscore.json    # Pontuações globais
├── tests/                # Testes automáticos (unittest)
├── eplace-docs/          # Este site (Docusaurus)
└── src/
    ├── jogador.py        # GestorJogador
    ├── utils/
    │   ├── score.py          # Leitura e gravação de recordes
    │   └── zip_extractor.py  # Importa jogos de games/imports/*.zip
    └── games/
        ├── Snake/             # main.py (arquivo único)
        ├── Ping pong/         # main.py + game/ (entities, ui)
        ├── Frogger/           # main.py + game/ (entities)
        ├── Space Invaders/    # main.py + game/app.py
        ├── Flappy bird/       # main.py + game/app.py
        ├── Kombate/           # main.py + game/ (lutadores, IA, mapas) + assets/
        └── imports/           # Coloque aqui .zip de jogos novos
```

## Como o launcher funciona

- Lista toda subpasta de `src/games/` que tenha um `main.py` (a pasta `imports` é ignorada).
- Usa como capa a imagem de `assets/covers/` com o mesmo nome da pasta do jogo (`.png`, `.jpg` ou `.jpeg`).
- Inicia o jogo escolhido em um **processo separado** (`subprocess`), usando o `main.py` da pasta dele.
- Ao abrir, extrai automaticamente os `.zip` de `src/games/imports/`.

## Adicionar um jogo novo

1. Crie uma pasta em `src/games/` com um `main.py`.
2. (Opcional) Coloque uma capa em `assets/covers/` com o mesmo nome da pasta.
3. Abra o launcher: o jogo aparece na lista automaticamente.

Também é possível usar um `.zip`: `game6.zip` colocado em `src/games/imports/` vira a pasta `src/games/game6/`. O zip precisa ter um `main.py` na raiz.

## Janela e game loop

Os jogos desenham em uma superfície de tamanho fixo e a ampliam para o monitor, mantendo a proporção. O launcher usa 1280×720 a 60 FPS.

```python
import pygame

pygame.init()
tela_real = pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.NOFRAME)
tela = pygame.Surface((1280, 720))        # resolução interna do jogo
relogio = pygame.time.Clock()
rodando = True

while rodando:
    dt = relogio.tick(60) / 1000.0
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # atualize o estado (dt) e desenhe em "tela" aqui

    dw, dh = tela_real.get_size()
    esc = min(dw / 1280, dh / 720)
    img = pygame.transform.smoothscale(tela, (int(1280 * esc), int(720 * esc)))
    tela_real.fill((0, 0, 0))
    tela_real.blit(img, img.get_rect(center=(dw // 2, dh // 2)))
    pygame.display.flip()

pygame.quit()
```

## Testes

O projeto tem 27 testes automáticos (`unittest`, sem dependências extras), que rodam sem abrir janela:

```bash
python -m unittest discover -s tests -t .
```

Eles cobrem a descoberta de jogos do launcher, a leitura dos recordes, o recorde de vitórias do Pong e do Kombate, as regras de rounds e K.O. do Kombate e o módulo `score.py`.

## Boas práticas adotadas

- Cada mini-game tem a lógica em módulos próprios.
- Constantes (cores, tamanhos, velocidades) ficam em `settings.py` ou no topo do arquivo.
- Cada jogo documenta como iniciar e quais teclas usa.
