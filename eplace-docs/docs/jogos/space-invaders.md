---
id: space-invaders
title: Space Invaders
description: Regras, controles e conceitos de programação do Space Invaders.
---

<div className="eyebrow">MINI-GAME / GAME_04</div>

# 👾 Space Invaders

<p className="lead">Pilote a nave pelo espaço, destrua inimigos e asteroides e sobreviva a ondas cada vez mais intensas.</p>

![Space Invaders com a nave entre asteroides e barras de integridade e energia](/img/jogos/space.jpg)

:::note Versão própria
Esta versão é um atirador espacial de movimento livre, não o formato clássico de fileiras de invasores com movimento só lateral.
:::

## Objetivo

Sobreviva o máximo possível e some pontos destruindo inimigos e asteroides. A nave tem **100 de vida**; o jogo termina quando ela chega a zero. A tela final mostra a onda alcançada.

## Controles

| Ação | Teclas |
|---|---|
| Mover a nave (livre, nas 4 direções) | `W` `A` `S` `D` ou `↑` `↓` `←` `→` |
| Atirar (segure para disparar) | `ESPAÇO` |
| Turbo (gasta energia) | `SHIFT` |
| Pausar | `P` |
| Menu / voltar | `ESC` |
| Menu: navegar e escolher | `↑` `↓` e `ENTER` ou `ESPAÇO` |
| Jogar de novo (fim de jogo) | `ENTER` |

## Regras

- A cada 18 segundos começa uma nova **onda**, com inimigos mais rápidos e resistentes.
- A cada 5 ondas surge um **alvo elite**.
- Inimigos e asteroides derrubados podem soltar power-ups: **S** (escudo), **+** (reparo) e **W** (arma).
- Acertos em sequência aumentam o multiplicador de **combo**.
- O recorde é salvo em `highscore.json`.

## Conceitos de programação

Vetores (`pygame.math.Vector2`), projéteis, colisão, barras de vida, energia e escudo, power-ups, ondas com dificuldade progressiva e partículas.
