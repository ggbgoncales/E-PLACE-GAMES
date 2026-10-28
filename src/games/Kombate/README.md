# Kombate - prototipo de luta 1v1 (Pygame)

Jogo de luta 2D com camera lateral travada, 6 manequins, modo VS CPU e 2 jogadores locais.

## Rodar
    python3 main.py        (ou pelo launcher E-PLACE)

## Controles
| Acao        | Jogador 1 | Jogador 2   |
|-------------|-----------|-------------|
| Andar       | A / D     | Setas       |
| Pular       | W         | Seta cima   |
| Agachar     | S         | Seta baixo  |
| Soco        | F         | K           |
| Chute       | G         | L           |
| Especial 1  | R         | I           |
| Especial 2  | T         | O           |
| Dash        | Shift esq | Shift dir   |

- Segurar para TRAS = defender (agachado + tras defende golpe baixo)
- Agachado + soco/chute = golpes baixos; soco/chute no ar = chute aereo (overhead)
- COMBO: acerte um soco/chute e aperte um especial logo depois (cancel). Soco -> chute tambem emenda.
- COUNTER: acertar o oponente durante o golpe dele = +25% de dano e mais tempo de combo
- ESC = pausa | F1 = mostra hitboxes (vermelho) e hurtboxes (verde)
- Dificuldade da CPU: medidor de 5 niveis (menu, tela antes da luta e pausa)

## Arquitetura
    Kombate/
    ├── main.py              ponto de entrada
    ├── settings.py          constantes (arena, gravidade, dano, controles, nivel da CPU)
    └── game/
        ├── characters.py    DADOS: Hit, Move, Character e os 6 personagens
        ├── fighter.py       PlayerController: Comandos, estados, fisica, bloqueio
        ├── combat.py        CombatManager: hitbox x hurtbox, dano, projeteis, minas
        ├── ai.py            CPU: State Machine IDLE / APPROACH / ATTACK / RETREAT
        ├── match.py         Partida: rounds, tempo, K.O., vencedor
        ├── input.py         teclado -> Comandos
        ├── modelo.py        manequim articulado (esqueleto + IK + sombreamento)
        ├── render.py        arena animada, HUD, medidor de dificuldade, efeitos
        ├── fx.py            particulas, tremida de tela, brilhos e sons sintetizados
        └── app.py           telas: menu, controles, selecao, luta, pausa

Fluxo de um frame:
Teclado/CPU -> Comandos -> Fighter.update() (PlayerController)
-> CombatManager.separar() (pushbox) -> CombatManager.update() (acertos) -> render

A CPU gera os MESMOS Comandos que o teclado, entao a fisica e igual para todos.
fighter.py, combat.py, ai.py e match.py nao usam pygame (testaveis sem tela).

## Personagens
| Personagem | Arquetipo  | Especial 1                          | Especial 2                          |
|------------|------------|-------------------------------------|-------------------------------------|
| RUBRO      | Balanceado | Bola de Energia (projetil reto)     | Gancho Ascendente (antiaereo, invulneravel no inicio) |
| COLOSSO    | Grappler   | Agarrao Esmagador (imbloqueavel)    | Punho Blindado (hiper-armadura)     |
| FAISCA     | Zoner      | Disparo Alto (passa por cima de quem agacha) | Disparo Rasteiro (defender agachado) |
| VULTO      | Rushdown   | Investida Fantasma (atravessa projetil) | Rajada Relampago (5 acertos)     |
| LANCEIRO   | Mid-Range  | Estocada Longa                      | Varredura de Lanca (baixa)          |
| SOMBRA     | Trapper    | Plantar Mina (maximo 2)             | Detonar minas                       |

## Como ajustar / colocar a arte final
- Golpes, dano, alcance e frames: game/characters.py
- Dano geral: DANO_GLOBAL | Ritmo: VELOCIDADE_GOLPES e VELOCIDADE_ANDAR (settings.py)
- Dificuldade padrao: NIVEL_CPU (1 a 5)
- Arte: troque desenhar_lutador() em game/modelo.py por sprites
  (use f.estado, f.golpe, f.golpe_t e f.facing para escolher o quadro).


### Sprites (todos os personagens)
- Os 6 lutadores usam sprites em assets/sprites/<nome>/ (12 poses em PNG + quadros.json).
- O alcance dos golpes foi ajustado a arte (PONTA_SPRITE em game/characters.py).
- Se apagar a pasta de um personagem, ele volta a ser desenhado como manequim (game/modelo.py).

### Mapas
- 4 mapas em game/mapas.py: Templo da Lua, Cidade Neon, Coliseu e Fabrica Abandonada.
- A tela de mapa aparece depois da selecao (2 jogadores) ou da dificuldade (vs CPU).
- Setas ou 1-4 escolhem, ENTER luta, ESC volta.

### Cenarios pintados e animacao de andar
- Os 4 mapas usam artes pintadas em assets/mapas/*.jpg, com fogo pulsando, chuva, brasas, poeira,
  faiscas e neblina animados por cima (game/mapas.py). Sem a imagem, o mapa volta ao desenho antigo.
- Cada lutador tem um ciclo de caminhada (andar_01.png, andar_02.png...) listado em "ciclo_andar"
  no quadros.json. Andar para tras toca o mesmo ciclo ao contrario.
- Rubro e Colosso tambem tem quadros de pulo (pulo_sobe / pulo_desce).
- Troca de pose com transicao suave (a pose anterior some em 4 quadros).
