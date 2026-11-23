---
id: snake
title: Snake
description: Regras, controles e conceitos de programação do Snake (Cobra Neon).
---

<div className="eyebrow">MINI-GAME / GAME_01</div>

# 🐍 Snake

<p className="lead">Cresça, marque pontos e não deixe a cobra se enroscar. Versão neon com combos, comida especial e três dificuldades. Dentro do jogo o título aparece como **Cobra Neon**.</p>

![Snake em partida, com painel de pontos, recorde e modo](/img/jogos/snake.jpg)

## Objetivo

Movimente a cobra pelo cenário para coletar frutas e aumentar seu tamanho. A partida termina ao bater na parede ou no próprio corpo.

## Controles

| Ação | Teclas |
|---|---|
| Mover | `↑` `↓` `←` `→` ou `W` `A` `S` `D` |
| Iniciar / jogar de novo | `ENTER` ou `ESPAÇO` (ou clique nos botões do menu) |
| Pausar | `P` ou `ESC` |
| Ligar/desligar som | `M` |
| Tela cheia | `F11` |

## Regras

- Cada fruta vale **10 × combo**. O combo sobe até ×5 quando você come em sequência.
- A cada 50 pontos pode surgir uma **comida especial dourada**, que vale 35 × combo.
- A velocidade aumenta conforme a pontuação cresce.
- Três dificuldades: **Tranquilo**, **Clássico** e **Insano**.
- O recorde é salvo automaticamente.

## Conceitos de programação

Movimento em grade, detecção de colisões, geração de itens em células livres, sistema de combo, partículas e controle de estado (menu, jogo, pausa e fim de jogo).
