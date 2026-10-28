# Flappy Bird: Skyward

Jogo arcade original em Python/Pygame, com customização e progresso local.

## Estrutura

```text
flappy_bird/
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

- Espaço, W ou seta para cima: voar
- Setas ou WASD: navegar pelos menus
- Enter ou Espaço: selecionar/comprar/equipar
- Esc: voltar

## Recursos

- Loja de chapéus: boné, cartola, coroa e chapéu de mago
- Efeitos: clássico, faíscas, arco-íris e estrelas
- Moedas adquiridas ao passar por canos
- Recorde, itens e moedas salvos em `savegame.json`
- Cenário em camadas, partículas, animações e dificuldade progressiva
- Tudo desenhado pelo próprio código, sem arquivos externos

## Versão profissional ampliada

- 8 chapéus, incluindo pirata, aurora e headset
- 6 rastros, incluindo fogo e gelo
- 5 cores de pássaro
- Loja com três categorias e catálogo com rolagem
- Canos móveis após os primeiros pontos
- Velocidade progressiva, abertura menor e geração mais rápida
- Bônus de moeda a cada sequência de cinco canos
- Indicador de nível e aviso de canos móveis
