# E-Place — Python Offline Arcade

Coletânea de **seis mini-games arcade 2D** em Python e Pygame, reunidos em um launcher que funciona **sem internet**. Projeto acadêmico, com visual retrô inspirado nos fliperamas.

> Clássicos. Desafios. Diversão.

## Os jogos

| Jogo | Em uma frase |
|---|---|
| **Snake** | Cobra neon com combos, comida especial e três dificuldades. |
| **Pong** | Contra a CPU ou em dois jogadores. Vence quem chegar a 7 pontos. |
| **Frogger** | Atravesse o rio em fases infinitas, com vidas e tempo limite. |
| **Space Invaders** | Atirador espacial com ondas, power-ups e alvos elite. |
| **Flappy Bird** | Passe pelos canos, junte moedas e personalize o pássaro na loja. |
| **Kombate** | Luta 1 contra 1 com seis lutadores, quatro arenas e combos. |

## Requisitos

- Python 3.10 ou superior
- [Pygame](https://www.pygame.org/) 2.5 ou superior (`requirements.txt`)

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Cada jogo também roda sozinho, a partir da própria pasta, por exemplo:

```bash
cd "src/games/Snake"
python main.py
```

## Controles do launcher

| Tela | Teclas |
|---|---|
| Menu inicial | `↑` `↓` navegam, `ENTER` seleciona, `H` abre os Recordes, `ESC` sai |
| Escolher jogo | `←` `→` (ou `↑` `↓`) trocam de jogo, `ENTER` joga, `H` abre os Recordes, `ESC` volta |
| Recordes | `R` atualiza, `ESC` ou `BACKSPACE` volta |
| Opções | `←` `→` `↑` `↓` movem e alteram, `ENTER` confirma, `ESC` volta |

As opções (tela cheia, volume e som do menu) ficam em `config.json`, que o launcher cria quando você altera algo. Os controles de cada jogo estão na [documentação](#documentação).

## Controles USB e Bluetooth (gamepad)

O E-PLACE usa o mapeamento universal SDL/Pygame quando disponivel e possui
fallback para controles sem mapeamento. A compatibilidade inclui controles
Xbox, PlayStation (DualShock/DualSense), Nintendo Switch (Pro Controller e
controles reconhecidos pelo sistema) e modelos USB/Bluetooth genericos.
O teclado continua funcionando normalmente.

Antes de abrir o E-PLACE, conecte o controle por USB ou emparelhe-o nas
configuracoes Bluetooth do Windows. Se o controle for conectado depois, o
launcher tenta reconhece-lo automaticamente. O suporte depende de o Windows
reconhecer o dispositivo como controle de jogo e de o driver disponibilizar
seus botoes/eixos ao Pygame.

### Launcher
- Analógico esquerdo ou direcional: navegar
- Botao inferior (A / Cross / B, conforme o controle): confirmar
- Botao direito (B / Circle / A, conforme o controle): voltar
- Start / Options / Plus: confirmar

### Jogos
- Snake: direcional/analógico para virar; botao inferior para iniciar; botao direito para pausar/voltar
- Flappy Bird: botao inferior para voar; direcional para navegar nos menus
- Frogger: direcional/analógico para mover; botao inferior para iniciar; botao direito para sair
- Space Invaders: analógico para mover; botao inferior para disparar; RB/R1 para impulso
- Ping Pong: analógico vertical para mover a raquete; botao inferior inicia contra CPU;
  botao oeste inicia versus local; botao direito volta
- Kombate: analógico para mover; botao inferior soco; botao oeste chute;
  L1/LB e R1/RB especiais; botao norte dash; botao direito pausa/volta.
  O teclado do segundo jogador continua disponivel.

Observacao: controles genericos variam bastante entre fabricantes. O E-PLACE
usa o padrao SDL sempre que o dispositivo fornece um mapeamento conhecido;
caso contrario, aplica um layout generico que pode variar conforme o driver.

## Recordes

A tela de Recordes do launcher (tecla `H`) lista a melhor marca de cada jogo.

| Jogo | Onde é salvo |
|---|---|
| Snake | `~/.cobra_neon_recorde.txt` (pasta do usuário) |
| Frogger | `src/games/Frogger/recorde.json` |
| Flappy Bird | `src/games/Flappy bird/savegame.json` |
| Space Invaders | `src/games/Space Invaders/highscore.json` |
| Pong | `src/games/Ping pong/recorde.json` — total de vitórias contra a CPU |
| Kombate | `src/games/Kombate/recorde.json` — total de vitórias contra a CPU |

Esses arquivos são gerados ao jogar e não vão para o repositório (`.gitignore`).

## Estrutura do projeto

```text
.
├── main.py               # Launcher: menu, lista de jogos, recordes e opções
├── requirements.txt
├── assets/
│   ├── covers/           # Capas dos jogos (nome do arquivo = nome da pasta do jogo)
│   ├── fonts/            # Press Start 2P e VT323 (licença OFL)
│   ├── sounds/
│   └── ui/               # Fundo do menu
├── src/
│   ├── jogador.py
│   ├── utils/            # score.py e zip_extractor.py
│   └── games/            # Um jogo por pasta, cada um com seu main.py
├── tests/                # Testes automáticos (unittest)
├── .github/workflows/    # GitHub Actions: testes e build da documentação
└── eplace-docs/          # Site de documentação (Docusaurus)
```

### Adicionar um jogo novo

1. Crie uma pasta em `src/games/` com um `main.py`.
2. (Opcional) Coloque a capa em `assets/covers/` com o mesmo nome da pasta (`.png`, `.jpg` ou `.jpeg`).
3. Abra o launcher: o jogo aparece na lista automaticamente.

Também dá para colocar um `.zip` em `src/games/imports/`: `game6.zip` vira `src/games/game6/`. O zip precisa ter um `main.py` na raiz.

## Testes

Os testes usam só a biblioteca padrão do Python (`unittest`) e rodam sem abrir janela:

```bash
python -m unittest discover -s tests -t .
```

Eles cobrem a descoberta de jogos do launcher, a leitura dos recordes, o recorde de vitórias do Pong e do Kombate, as regras de rounds e K.O. do Kombate e o módulo `score.py`. A cada push e pull request, o GitHub Actions roda esses testes (`.github/workflows/tests.yml`).

## Documentação

O site de documentação, feito com [Docusaurus](https://docusaurus.io/), fica em `eplace-docs/` e traz a instalação, a estrutura do projeto e uma página por jogo, com controles, regras e capturas de tela.

Para ver localmente (precisa de Node.js 20 ou superior):

```bash
cd eplace-docs
npm install
npm start
```

O site abre em `http://localhost:3000/E-PLACE-GAMES/`. Para gerar a versão final: `npm run build`.

### Publicação no GitHub Pages

O workflow `.github/workflows/docs.yml` compila o site a cada alteração em `eplace-docs/`. Para publicar:

1. Um administrador do repositório ativa **Settings → Pages → Source: GitHub Actions**.
2. Em **Actions → Documentação → Run workflow**, rode o fluxo manualmente.

O endereço fica em `https://ggbgoncales.github.io/E-PLACE-GAMES/`. Se o repositório mudar de dono ou nome, ajuste `url`, `baseUrl`, `organizationName` e `projectName` em `eplace-docs/docusaurus.config.js`.

## Equipe

- Arley Silvestre
- Bruno Campos de Moraes
- Cassiane da Silva Costa
- Guilherme Barbosa
- Julio Cezar Oliveira Galzano
- Leticia Conti Ramos

## Créditos e licenças

- Fontes **Press Start 2P** e **VT323**, licença [SIL Open Font License 1.1](https://openfontlicense.org/). Os textos das licenças estão em `assets/fonts/`.
- Demais códigos e imagens: projeto acadêmico da equipe.
