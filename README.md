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
