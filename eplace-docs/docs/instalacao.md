---
id: instalacao
title: Instalação e execução
description: Como preparar o ambiente Python e executar o launcher do E-Place.
---

<div className="eyebrow">COMECE AQUI / SETUP</div>

# Instalação e execução

<p className="lead">Prepare o ambiente Python e execute o launcher do E-Place, que reúne todos os mini-games em uma única aplicação.</p>

## Pré-requisitos

- **Python 3.10 ou superior**.
- A pasta do projeto (`Eplace Games`) baixada ou clonada.
- Um terminal, ou o terminal integrado da sua IDE.

## 1. Crie um ambiente virtual e instale as dependências

A única dependência é o **Pygame CE** (`pygame-ce>=2.5.0`, listado em `requirements.txt`). O Pygame CE é um fork compatível do Pygame, com pacotes prontos para as versões recentes do Python (como a 3.14), e é usado com o mesmo `import pygame`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

:::tip Windows
No Windows, ative o ambiente com `.venv\Scripts\activate`. No macOS e no Linux, use `source .venv/bin/activate`.
:::

## 2. Execute o launcher

Na pasta que contém o `main.py`:

```bash
python main.py
```

O launcher abre o menu e inicia cada jogo em um processo próprio.

## Controles do launcher

| Tela | Teclas |
|---|---|
| Menu inicial | `↑` `↓` navegam · `ENTER` seleciona · `H` abre Recordes · `ESC` sai |
| Escolher jogo | `←` `→` (ou `↑` `↓`) trocam de jogo · `ENTER` joga · `H` abre Recordes · `ESC` volta |
| Recordes | `R` atualiza · `ESC` ou `BACKSPACE` volta |
| Configurações | `←` `→` `↑` `↓` movem e alteram · `ENTER` confirma · `ESC` volta |

## Controle USB e Bluetooth

O launcher e os seis jogos aceitam controles de videogame (Xbox, PlayStation, Nintendo Switch e modelos genéricos), além do teclado. O E-Place usa o mapeamento padrão do SDL e, se o controle não tiver um, aplica um layout genérico.

- Conecte o controle por USB ou emparelhe-o por Bluetooth antes de abrir o jogo. Se conectar depois, o launcher tenta reconhecê-lo sozinho.
- No launcher: o analógico esquerdo ou o direcional navega, o botão de baixo confirma e o botão da direita volta.
- Cada jogo tem uma tela de controles, aberta pelo botão de cima do controle ou pela tecla `F1`.

O suporte depende de o sistema operacional reconhecer o dispositivo como controle de jogo. Controles genéricos variam bastante entre fabricantes.

## Telas do launcher

![Tela inicial do launcher, com o logo E-Place e os botões Arcade, Opções e Sair](/img/launcher/home.jpg)

Na escolha de jogo, o launcher mostra a capa, o gênero, o número de jogadores, uma descrição curta e o seu recorde, com uma faixa de miniaturas para trocar de jogo.

![Escolha de jogo, com capa, ficha do jogo, recorde e miniaturas](/img/launcher/jogos.jpg)

A tela de Recordes mostra a melhor marca de cada jogo, e as Opções permitem ligar a tela cheia, ajustar o volume e os sons do menu.

![Tela de Recordes, com a melhor marca de cada jogo](/img/launcher/recordes.jpg)

## Configurações

As opções ficam salvas em `config.json`:

```json
{
  "tela_cheia": true,
  "volume": 100,
  "som_menu": true,
  "titulo": "EPLACE"
}
```

| Chave | Efeito |
|---|---|
| `tela_cheia` | Abre o launcher em tela cheia. |
| `volume` | Volume do launcher, de 0 a 100. |
| `som_menu` | Liga ou desliga a música do menu. |

## Rodar um jogo sozinho

Cada jogo pode ser executado direto da própria pasta, sem o launcher:

```bash
cd "src/games/Snake"
python main.py
```

## Se algo der errado

- **`ModuleNotFoundError: pygame`**: confira se o ambiente virtual está ativo e rode `pip install -r requirements.txt`.
- **Erro ao compilar o `pygame` (`SDL.h` not found)**: o pacote `pygame` não tem versão pronta para o seu Python. Desinstale-o e use o `pygame-ce` (`pip install -r requirements.txt`).
- **Arquivo não encontrado**: verifique se o terminal está na pasta que contém o `main.py`.
- **A janela fecha rápido**: execute pelo terminal para ver a mensagem de erro.
