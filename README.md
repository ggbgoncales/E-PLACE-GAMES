# E-PLACE - Coleção de Mini-Games em Python/Pygame

Launcher em Pygame que reúne vários mini-games feitos em Python com Orientação a Objetos. Projeto Prático Integrado de OO e Desenvolvimento de Aplicativos (4º semestre).

O launcher abre uma tela inicial (Jogar / Configurações / Sair) e lista os jogos disponíveis em `src/games/`. Cada jogo é independente e também pode ser executado sozinho.

## Jogos incluídos

| Jogo           | Pasta                    | Descrição                                                    |
|----------------|--------------------------|--------------------------------------------------------------|
| Ping Pong      | `src/games/Ping pong`    | Jogador contra CPU ou dois jogadores locais                  |
| Sapo           | `src/games/sapo`         | Atravesse o cenário pulando entre obstáculos, com recorde    |
| Cobrinha       | `src/games/Cobrinha`     | Snake clássico com pausa e tela cheia                        |
| Flappy Bird    | `src/games/Flappy_bird`  | Versão "Skyward" com cenário completo, loja e save           |
| Space Invaders | `src/games/Space Invaders` | Arcade espacial com impulso e pausa                        |
| Kombate        | `src/games/Kombate`      | Luta 2D 1v1, modo contra CPU e 2 jogadores locais            |

## Requisitos

- Windows, Linux ou macOS com tela (os jogos abrem uma janela gráfica)
- Python 3.10 ou superior
- Pygame (instalado pelo `requirements.txt`)

## Como rodar (passo a passo)

### 1. Baixar o projeto

```bash
git clone https://github.com/ggbgoncales/E-PLACE-GAMES.git
cd E-PLACE-GAMES
```

Também é possível usar o botão **Code -> Download ZIP** no GitHub e extrair a pasta.

### 2. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

No Windows, se o comando `python` não for reconhecido, use `py` no lugar:

```bash
py -m pip install -r requirements.txt
```

### 3. Executar o launcher

```bash
python main.py
```

(ou `py main.py` no Windows)

### Ambiente virtual (opcional, recomendado)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
python -m pip install -r requirements.txt
python main.py
```

## Problemas comuns

| Sintoma                                              | Solução                                                                                       |
|------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `Python was not found` (abre a Microsoft Store)      | Instale o Python em python.org marcando "Add python.exe to PATH", ou use `py` no lugar de `python` |
| `pip` não é reconhecido                              | Use `python -m pip ...` (ou `py -m pip ...`)                                                  |
| Erro ao instalar o `pygame` (Python muito novo)      | Rode `python -m pip install pygame-ce` e tente de novo; o código usa `import pygame` do mesmo jeito |
| `fatal: not a git repository`                        | O terminal precisa estar dentro da pasta do projeto (`cd E-PLACE-GAMES`)                      |
| Janela não abre em servidor/SSH sem tela             | Os jogos precisam de ambiente gráfico; rode em uma máquina com monitor                        |

## Controles

### Launcher

| Tela            | Teclas                                                       |
|-----------------|--------------------------------------------------------------|
| Menu inicial    | Setas ou W/S para navegar, Enter ou Espaço seleciona, Esc sai |
| Escolher jogo   | Setas ou W/S para navegar, Enter ou Espaço joga, Esc volta   |
| Configurações   | Setas ou A/D/W/S para alterar, Enter confirma, Esc volta     |

### Jogos

| Jogo           | Controles                                                                                     |
|----------------|-----------------------------------------------------------------------------------------------|
| Ping Pong      | Menu: `1` contra CPU, `2` dois jogadores. J1: W/S. J2: setas cima/baixo. `P` pausa, `R` reinicia, Esc sai |
| Sapo           | Setas ou WASD para pular, `P` pausa, Enter/Espaço inicia, `R` reinicia                        |
| Cobrinha       | Setas ou WASD para mover, `P` ou Esc pausa, Enter/Espaço inicia, `F11` tela cheia             |
| Flappy Bird    | Espaço, W ou seta cima para voar. Menus: setas/WASD, Enter/Espaço seleciona, Esc volta        |
| Space Invaders | WASD ou setas para mover, Espaço atira, Shift impulso, `P` pausa, Esc volta                   |
| Kombate        | Ver tabela abaixo                                                                             |

#### Kombate

| Ação       | Jogador 1  | Jogador 2  |
|------------|------------|------------|
| Andar      | A / D      | Setas      |
| Pular      | W          | Seta cima  |
| Agachar    | S          | Seta baixo |
| Soco       | F          | K          |
| Chute      | G          | L          |
| Especial 1 | R          | I          |
| Especial 2 | T          | O          |
| Dash       | Shift esq. | Shift dir. |

`Esc` pausa e `F1` mostra hitboxes/hurtboxes. Detalhes de combos e personagens em `src/games/Kombate/README.md`.

## Estrutura do projeto

```text
E-PLACE-GAMES/
├── main.py                 Launcher (telas, menu, execução dos jogos)
├── requirements.txt        Dependências (pygame)
├── README.md
├── assets/
│   ├── DiagramaUML.png     Diagrama UML do projeto
│   ├── covers/             Capas opcionais dos jogos
│   └── ui/                 Fundos do launcher
├── src/
│   ├── jogador.py          GestorJogador: jogador atual e pontuações
│   ├── utils/
│   │   ├── score.py        Leitura/gravação de recordes
│   │   └── zip_extractor.py  Extrai jogos em .zip de src/games/imports/
│   └── games/
│       ├── Ping pong/
│       ├── sapo/
│       ├── Cobrinha/
│       ├── Flappy_bird/
│       ├── Space Invaders/
│       ├── Kombate/
│       └── imports/        Coloque aqui um .zip para adicionar um jogo
└── data/                   Dados locais gerados em execução (ignorados pelo Git)
```

Os jogos mais estruturados seguem o padrão `main.py` + `settings.py` + pacote `game/` (classes de entidades, interface e lógica separadas).

## Arquivos gerados em execução

- `config.json`: configurações do launcher (tela cheia, volume). Criado automaticamente.
- `data/*.json`: pontuações do launcher.
- `savegame.json` (Flappy Bird) e `recorde.json` (Sapo): progresso e recordes de cada jogo.

## Adicionar um jogo novo

- **Pasta:** crie uma pasta em `src/games/` com um `main.py` dentro. Ela aparece sozinha na lista.
- **ZIP:** coloque o `.zip` do jogo em `src/games/imports/`. Ele é extraído automaticamente ao abrir o launcher.

## Roteiro sugerido para o code review

1. Rodar o launcher e abrir cada jogo para validar que tudo inicia sem erro.
2. Ler `main.py` (launcher) e `src/jogador.py` para entender o fluxo geral.
3. Comparar a estrutura dos jogos (`Kombate`, `Ping pong`, `Flappy_bird`) com o diagrama em `assets/DiagramaUML.png`.
4. Verificar separação de responsabilidades (entidades, lógica, interface) e uso de OO.
5. Registrar sugestões de melhoria (legibilidade, duplicação, tratamento de erros, testes).

## Equipe

Projeto desenvolvido em grupo na disciplina de OO e Desenvolvimento de Aplicativos (Unimax, 4º semestre).
