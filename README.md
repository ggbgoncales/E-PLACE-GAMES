# Eplace - Launcher de Jogos

Launcher em Python/Pygame para reunir jogos arcade em uma única aplicação.

## Como rodar
```bash
pip install -r requirements.txt
python main.py
```

## Controles
| Tela | Teclas |
|---|---|
| Menu inicial | Setas cima/baixo, ENTER seleciona, H abre o Recordes, ESC sai |
| Escolher jogo | Setas cima/baixo, ENTER joga, H abre o Recordes, ESC volta |
| Recordes | R atualiza os recordes, ESC/BACKSPACE volta |
| Configurações | Setas mover/alterar, ENTER confirma, ESC volta |

## Recordes
O launcher lê os recordes salvos por Snake, Flappy Bird, Frogger, Space Invaders, Pong e Kombate. O Space Invaders salva o recorde em `src/games/Space Invaders/highscore.json`.

No Pong e no Kombate o recorde é o total de vitórias contra a CPU, salvo em `recorde.json` na pasta de cada jogo.

## Fontes
O visual retrô usa as fontes Press Start 2P e VT323 (licença OFL), em `assets/fonts/`.

## Adicionar um jogo novo
Crie uma pasta dentro de `src/games/` com um arquivo `main.py`. O launcher identifica automaticamente os jogos compatíveis.

## Testes
Os testes automáticos usam só a biblioteca padrão do Python (`unittest`) e rodam sem abrir janela:
```bash
python -m unittest discover -s tests -t .
```
Eles cobrem a descoberta de jogos do launcher, a leitura dos recordes, o recorde de vitórias do Pong e do Kombate, as regras de rounds e K.O. do Kombate e o módulo `score.py`.
