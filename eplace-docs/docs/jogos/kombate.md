---
id: kombate
title: Kombate
description: Regras, controles, lutadores e arquitetura do Kombate, o jogo de luta do E-Place.
---

<div className="eyebrow">MINI-GAME / GAME_06</div>

# 🥊 Kombate

<p className="lead">Luta 2D 1 contra 1 com seis lutadores, quatro arenas e combos. Enfrente a CPU ou chame um amigo.</p>

![Kombate: luta entre Rubro e Colosso no Templo da Lua](/img/jogos/kombate.jpg)

## Objetivo

Derrote o oponente zerando a barra de vida antes do fim do tempo. Cada round dura **99 segundos** e vence quem ganhar **2 rounds** (melhor de 3).

## Modos

- **VS CPU**, com medidor de dificuldade de 5 níveis (no menu, na tela antes da luta e na pausa).
- **2 jogadores locais** no mesmo teclado.

## Controles

| Ação | Jogador 1 | Jogador 2 |
|---|---|---|
| Andar | `A` / `D` | `←` / `→` |
| Pular | `W` | `↑` |
| Agachar | `S` | `↓` |
| Soco | `F` | `K` |
| Chute | `G` | `L` |
| Especial 1 | `R` | `I` |
| Especial 2 | `T` | `O` |
| Dash | `SHIFT` esquerdo ou toque duplo | `SHIFT` direito ou toque duplo |

Pausa: `ESC`. Depuração: `F1` mostra hitboxes (vermelho) e hurtboxes (verde).

## Mecânicas

- **Defesa:** segurar para trás defende; agachado + para trás defende golpe baixo. Defender muitos golpes seguidos **quebra a guarda** e deixa o lutador tonto por cerca de 0,8 s.
- **Combo:** acerte um soco ou chute e aperte um especial logo depois (cancel). Soco → chute também emenda.
- **Counter:** acertar o oponente durante o golpe dele causa +25% de dano.
- **Arremesso:** soco + chute juntos, colado ao oponente. Não pode ser defendido.
- **Recarga:** cada especial tem cooldown, mostrado por ícones no HUD.

## Lutadores

| Lutador | Estilo | Especial 1 | Especial 2 |
|---|---|---|---|
| RUBRO | Balanceado | Bola de Energia | Gancho Ascendente |
| COLOSSO | Agarrador | Agarrão Esmagador | Punho Blindado |
| FAISCA | Zoner | Disparo Alto | Disparo Rasteiro |
| VULTO | Ataque rápido | Investida Fantasma | Rajada Relâmpago |
| LANCEIRO | Médio alcance | Estocada Longa | Varredura de Lança |
| SOMBRA | Armadilhas | Plantar Mina | Detonar minas |

## Arenas

Quatro mapas pintados e animados: **Templo da Lua**, **Cidade Neon**, **Coliseu** e **Fábrica Abandonada**. Na tela de mapa, use `←` `→` ou `1` a `4` para escolher, `ENTER` para lutar e `ESC` para voltar.

## Arquitetura

```text
Kombate/
├── main.py              # ponto de entrada
├── settings.py          # constantes: arena, gravidade, dano, controles, nível da CPU
└── game/
    ├── characters.py    # dados: Hit, Move, Character e os 6 personagens
    ├── fighter.py       # estados, física e bloqueio
    ├── combat.py        # hitbox x hurtbox, dano, projéteis, minas
    ├── ai.py            # CPU: máquina de estados
    ├── match.py         # rounds, tempo, K.O. e vencedor
    ├── input.py         # teclado para comandos
    ├── modelo.py        # manequim articulado (fallback de sprites)
    ├── render.py        # arena animada, HUD e efeitos
    ├── fx.py            # partículas, tremida de tela e sons sintetizados
    ├── mapas.py         # os 4 mapas
    └── app.py           # telas: menu, controles, seleção, luta e pausa
```

A CPU gera os **mesmos comandos** do teclado, então a física é igual para todos. Os módulos `fighter.py`, `combat.py`, `ai.py` e `match.py` não dependem do Pygame e podem ser testados sem tela.

:::note Recorde
O recorde do Kombate é o total de vitórias do jogador 1 contra a CPU, salvo em `recorde.json` e mostrado na tela de Recordes do launcher.
:::

## Conceitos de programação

Máquina de estados (a CPU alterna entre IDLE, APPROACH, ATTACK e RETREAT), hitboxes e hurtboxes, frames de golpe, separação entre dados dos personagens e lógica de luta, e CPU que usa a mesma interface de comandos do jogador.
