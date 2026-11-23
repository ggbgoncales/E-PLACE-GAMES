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

A única dependência é o **Pygame** (`pygame>=2.5.0`, listado em `requirements.txt`).

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
| Escolher jogo | `↑` `↓` navegam · `ENTER` joga · `H` abre Recordes · `ESC` volta |
| Recordes | `R` atualiza · `ESC` ou `BACKSPACE` volta |
| Configurações | `←` `→` `↑` `↓` movem e alteram · `ENTER` confirma · `ESC` volta |

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
- **Arquivo não encontrado**: verifique se o terminal está na pasta que contém o `main.py`.
- **A janela fecha rápido**: execute pelo terminal para ver a mensagem de erro.
