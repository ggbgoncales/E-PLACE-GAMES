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
E-PLACE-GAMES/
├── main.py                 # Launcher: menu, lista de jogos, recordes e opções
├── requirements.txt        # pygame-ce>=2.5.0
├── README.md
├── assets/
│   ├── covers/             # Capas dos jogos (nome do arquivo = nome da pasta)
│   ├── fonts/              # Press Start 2P e VT323 (licença OFL)
│   ├── sounds/             # Música e cliques do menu
│   └── ui/                 # Logo e fundo do menu
├── src/
│   ├── gamepad.py          # XboxController: teclado e controle (compartilhado)
│   ├── jogador.py          # GestorJogador
│   ├── utils/
│   │   ├── ui_arcade.py    # Menus, botões e seletor de dificuldade (compartilhado)
│   │   ├── score.py        # Leitura e gravação de recordes
│   │   └── zip_extractor.py  # Importa jogos de games/imports/*.zip
│   └── games/              # Um jogo por pasta, cada um com seu main.py
│       ├── Snake/          # main.py (arquivo único)
│       ├── Ping pong/      # main.py + game/ (entities, ui)
│       ├── Frogger/        # main.py + game/ (entities)
│       ├── Space Invaders/ # main.py + game/app.py
│       ├── Flappy bird/    # main.py + game/app.py
│       ├── Kombate/        # main.py + game/ (lutadores, IA, mapas) + assets/
│       └── imports/        # Coloque aqui .zip de jogos novos
├── uml/                    # Diagramas UML (.mmd e .png)
├── tests/                  # Testes automáticos (unittest)
├── eplace-docs/            # Este site (Docusaurus)
└── .github/workflows/      # Testes e build da documentação
```

`config.json` e a pasta `data/` são criados ao usar o launcher e não vão para o repositório.

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

O projeto tem 35 testes automáticos (`unittest`, sem dependências extras), que rodam sem abrir janela:

```bash
python -m unittest discover -s tests -t .
```

Eles cobrem a descoberta de jogos do launcher, a leitura dos recordes, o recorde de vitórias do Pong e do Kombate, as regras de rounds e K.O. do Kombate e o módulo `score.py`. A cada push e pull request, o GitHub Actions roda esses testes.

## Diagramas UML

Os diagramas são escritos em Mermaid (`uml/*.mmd`) e exportados para PNG. Para atualizar, abra o `.mmd` no VS Code com uma extensão Mermaid e exporte de novo.

**Launcher:** a classe `Eplace` e o que ela usa (configuração, jogos, controle, fundo, pontuações).

![Diagrama de classes do launcher](/img/uml/launcher.png)

**Jogos:** a classe principal de cada jogo e as classes que cada um agrupa.

![Diagrama de classes dos seis jogos](/img/uml/jogos.png)

**Kombate:** telas, regras da luta, IA e dados dos personagens.

![Diagrama de classes do Kombate](/img/uml/kombate.png)

## Boas práticas adotadas

- Cada mini-game tem a lógica em módulos próprios.
- Constantes (cores, tamanhos, velocidades) ficam em `settings.py` ou no topo do arquivo.
- Cada jogo documenta como iniciar e quais teclas usa.

**Sequência:** o que acontece do clique em Jogar até a volta ao launcher. O launcher abre cada jogo em um processo próprio e espera ele fechar. Os recordes ficam em arquivos de cada jogo e o launcher os lê de novo ao abrir a tela de Recordes.

![Diagrama de sequência: launcher, processo do jogo e arquivo de recorde](/img/uml/sequencia.png)

Para ver os exemplos de classes, herança e polimorfismo usados no código, veja [Programação orientada a objetos](/poo).
