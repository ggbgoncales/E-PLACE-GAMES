import json
import os

ARQUIVO_SCORE = "data/hihgscore.json"

def carregar_pontuacoes():
    if not os.path.exists(ARQUIVO_SCORE):
        return {}
    with open(ARQUIVO_SCORE, "r") as arquivo:
        return json.load(arquivo)

def salvar_pontuacao(jogo, pontuacao):
    pontuacoes = carregar_pontuacoes()
    
    # Atualiza apenas se for um novo recorde para aquele jogo específico
    if jogo not in pontuacoes or pontuacao > pontuacoes[jogo]:
        pontuacoes[jogo] = pontuacao
        
    with open(ARQUIVO_SCORE, "w") as arquivo:
        json.dump(pontuacoes, arquivo, indent=4)