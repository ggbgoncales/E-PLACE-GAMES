# Eplace - Launcher de Jogos

Launcher em Python/Pygame minimalista.
- **Tela inicial**: arte do E-PLACE como fundo + menu central (**Jogar / Configuracoes / Sair**) com animacao subindo/descendo.
- **Tela de jogos**: lista na lateral (`game1`..`game5`) com animacao e efeito de destaque.

## Como rodar
```bash
pip install -r requirements.txt
python main.py
```

## Controles
| Tela          | Teclas |
|---------------|--------|
| Menu inicial  | Setas cima/baixo, ENTER seleciona, ESC sai |
| Escolher jogo | Setas cima/baixo, ENTER joga, ESC volta |
| Configuracoes | Setas mover/alterar, ENTER confirma, ESC volta |

## Estrutura
```
Eplace/
├── main.py
├── requirements.txt
├── README.md
├── games/
│   ├── imports/          # coloque .zip aqui (extrai sozinho)
│   ├── game1/ ... game5/ # cada um com main.py + assets/
├── assets/
│   ├── covers/           # capas opcionais dos jogos
│   └── ui/
│       └── background.png  # fundo da tela inicial (arte E-PLACE)
└── utils/
    └── zip_extractor.py
```

## Adicionar um jogo novo
- **Pasta**: crie `games/game6/` com um `main.py` dentro. Aparece sozinho.
- **ZIP**: nomeie `game6.zip`, jogue em `games/imports/`. Extrai sozinho.

## Trocar o fundo da tela inicial
Substitua `assets/ui/background.png` pela imagem que quiser (1280x720 ideal).

## Mapeamento game1..game5 (backlog Jira)

| Pasta | Mini-game |
|---|---|
| `games/game1` | Snake |
| `games/game2` | Pong |
| `games/game3` | Space Invaders |
| `games/game4` | Flappy Bird |
| `games/game5` | Frogger |

## Fluxo de trabalho (branches)

- `main`: código estável.
- `feature/nome-da-tarefa`: cada tarefa em uma branch própria, criada a partir da `main` (ex: `feature/game1-snake`).
- Ao concluir, abrir um Pull Request para revisão antes do merge.

## Roadmap (Sprints)

| Sprint | Período | Objetivo |
|---|---|---|
| 1 - Planejamento | 6–19 ago | Formação de grupos e configuração do Jira |
| 2 - Estrutura | 26 ago – 16 set | Estrutura do projeto, menu, identidade visual |
| 3 - Snake e Pong | 16–30 set | Desenvolver os 2 primeiros mini-games (game1, game2) |
| 4 - Space I. / Flappy B. | 7–21 out | Desenvolver mais 2 mini-games (game3, game4) |
| 5 - Frogger | 28 out – 11 nov | 5º mini-game (game5), pontuação global, high score, ranking, integração |
| 6 - Testes e Polimento | 18 nov – 2 dez | Testes, correção de bugs, áudio, animações, entrega final |

## Equipe

- GB, AS, BM, CS, JG, LR
