---
id: recordes
title: Recordes
description: Como o launcher lê e mostra os recordes de cada jogo.
---

<div className="eyebrow">COMECE AQUI / RECORDES</div>

# Recordes

<p className="lead">A tela de Recordes do launcher lista a melhor pontuação de cada jogo, do maior para o menor.</p>

A tela de **Recordes** do launcher (tecla `H`) lista a melhor pontuação de cada jogo, em ordem decrescente. A tecla `R` atualiza a lista.

## Onde cada jogo salva

| Jogo | Arquivo | Chave |
|---|---|---|
| Snake | `~/.cobra_neon_recorde.txt` (pasta do usuário) | número simples |
| Frogger | `src/games/Frogger/recorde.json` | `recorde` |
| Flappy Bird | `src/games/Flappy bird/savegame.json` | `best` |
| Space Invaders | `src/games/Space Invaders/highscore.json` | `recorde` |
| Pong | `src/games/Ping pong/recorde.json` | `recorde` (vitórias) |
| Kombate | `src/games/Kombate/recorde.json` | `recorde` (vitórias) |

:::note Recorde do Pong e do Kombate
Nesses dois jogos o recorde é o **total de vitórias contra a CPU**, mostrado na tela de Recordes como "VITORIAS". Partidas de dois jogadores não contam.
:::

## Pontuação global

O módulo `src/utils/score.py` guarda pontuações por jogo em `data/highscore.json`. Ele só atualiza o valor quando a nova pontuação supera a anterior:

```python
def salvar_pontuacao(jogo, pontuacao):
    pontuacoes = carregar_pontuacoes()
    if jogo not in pontuacoes or pontuacao > pontuacoes[jogo]:
        pontuacoes[jogo] = pontuacao
    with open(ARQUIVO_SCORE, "w") as arquivo:
        json.dump(pontuacoes, arquivo, indent=4)
```
