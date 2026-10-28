# Space Invaders

Jogo arcade espacial desenvolvido em Python com Pygame.

## Estrutura

```text
space_invaders/
├── main.py
├── README.md
├── requirements.txt
├── requirements
├── settings.py
└── game/
    ├── __init__.py
    └── app.py
```

## Instalação

```cmd
pip install -r requirements.txt
```

## Execução

```cmd
python main.py
```

## Controles

- WASD ou setas: movimentar
- Espaço: disparar
- Shift: impulso
- P: pausar
- Esc: voltar

## Alteração desta versão

A nave mantém o desenho detalhado, mas agora é renderizada em 62% do tamanho anterior. A hitbox e o escudo também foram reduzidos proporcionalmente.
