---
id: flappy-bird
title: Flappy Bird
description: Regras, controles e conceitos de programação do Flappy Bird.
---

<div className="eyebrow">MINI-GAME / GAME_05</div>

# 🐤 Flappy Bird

<p className="lead">Mantenha o pássaro no ar, passe pelos canos, junte moedas e personalize o seu bichinho na loja.</p>

![Flappy Bird com o pássaro entre os canos](/img/jogos/flappy.jpg)

## Objetivo

Controle a altura do pássaro para passar pelos vãos entre os canos sem colidir. Cada cano ultrapassado vale 1 ponto e rende moedas.

## Controles

| Ação | Teclas |
|---|---|
| Bater asas | `ESPAÇO`, `↑` ou `W` |
| Menu: navegar e escolher | `↑` `↓` (ou `W` `S`) e `ENTER` ou `ESPAÇO` |
| Loja: trocar de aba | `←` `→` (ou `A` `D`) |
| Loja: escolher item | `↑` `↓` e `ENTER` para comprar ou equipar |
| Jogar de novo (fim de jogo) | `ESPAÇO` ou `ENTER` |
| Voltar ao menu | `ESC` |

## Regras

- Cada cano passado dá 1 moeda; a cada 5 seguidos você ganha 1 moeda extra.
- O **nível** sobe a cada 10 pontos.
- A **loja** tem 3 abas: chapéus, efeitos e skins do pássaro.
- Moedas, itens comprados e melhor pontuação ficam salvos em `savegame.json`.

## Conceitos de programação

Gravidade simulada, impulso vertical, geração de obstáculos, colisões, pontuação, economia de moedas, persistência de dados em JSON e partículas de efeito.
