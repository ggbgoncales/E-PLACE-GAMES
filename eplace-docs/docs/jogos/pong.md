---
id: pong
title: Pong
description: Regras, controles e conceitos de programação do Pong.
---

<div className="eyebrow">MINI-GAME / GAME_02</div>

# 🏓 Pong

<p className="lead">Duas raquetes, uma bola e reflexos rápidos. Jogue contra a CPU ou contra um amigo no mesmo teclado.</p>

![Pong no modo dois jogadores, com placar no topo](/img/jogos/pong.jpg)

## Objetivo

Rebata a bola com sua raquete e faça-a passar pela raquete adversária. **O primeiro a chegar a 7 pontos vence.**

## Controles

| Ação | Teclas |
|---|---|
| Escolher modo (menu) | `1` Jogador vs CPU · `2` Dois jogadores |
| Jogador 1 | `W` sobe · `S` desce |
| Jogador 2 | `↑` sobe · `↓` desce |
| Pausar / continuar | `P` |
| Reiniciar partida | `R` |
| Voltar ao menu | `ESC` |
| Jogar de novo (fim de partida) | `ENTER` ou `ESPAÇO` |

:::note Modo contra a CPU
Nesse modo apenas a raquete esquerda é controlada por você. A direita é automática.
:::

## Recorde

Cada vitória contra a CPU soma 1 ao contador de vitórias, salvo em `recorde.json`. O número aparece no topo da partida ("VS CPU - VITORIAS") e na tela de Recordes do launcher.

## Conceitos de programação

Movimento e velocidade, colisão com raquetes e paredes, mudança de direção da bola, placar, pausa e reinício. O código separa as entidades (`Paddle`, `Ball`) da interface e das regras da partida.
