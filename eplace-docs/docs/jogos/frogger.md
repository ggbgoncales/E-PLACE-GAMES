---
id: frogger
title: Frogger
description: Regras, controles e conceitos de programação do Frogger.
---

<div className="eyebrow">MINI-GAME / GAME_03</div>

# 🐸 Frogger

<p className="lead">Ajude o sapo a atravessar rios cheios de perigos. São fases infinitas, cada vez mais rápidas e difíceis.</p>

![Frogger na fase Lagoa Calma, com troncos e tartarugas no rio](/img/jogos/frogger.jpg)

## Objetivo

Atravesse o rio pulando em troncos e tartarugas até alcançar uma **vitória-régia** no topo da tela. Cair na água ou ser atingido custa uma vida, e o tempo da fase também conta.

## Controles

| Ação | Teclas |
|---|---|
| Pular uma casa | `↑` `↓` `←` `→` ou `W` `A` `S` `D` |
| Iniciar | `ENTER` ou `ESPAÇO` |
| Pausar / continuar | `P` |
| Jogar de novo (fim de jogo) | `R` ou `ENTER` |
| Sair | `ESC` |

## Regras

- Troncos e tartarugas são seguros; **jacarés, cobras e água não são**.
- Você começa com **4 vidas**. Ganha 1 vida extra a cada fase par (máximo de 6).
- Completar a fase dá bônus de **500 + 100 × fase + tempo restante × 10** pontos.
- A mosca vale **+200** pontos.

## Fases

| Fase | Cenário | Destaque |
|---|---|---|
| 1 | Lagoa Calma | Pule nos troncos e tartarugas até a vitória-régia. |
| 2 | Rio dos Troncos | Algumas tartarugas mergulham. |
| 3 | Pântano dos Jacarés | Jacarés no rio e cobra na margem do meio. |
| 4 | Correnteza | Tudo mais rápido. |
| 5 | Noite no Brejo | Escuridão total: só o sapo ilumina o caminho. |

Depois da fase 5 os cenários se repetem em ciclos mais rápidos e perigosos.

## Conceitos de programação

Movimentação por casas, objetos em movimento (`Mover`), colisões, plataformas que carregam o jogador, temporizador, fases geradas por configuração e dificuldade progressiva infinita.
