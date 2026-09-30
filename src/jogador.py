import os
import json


class GestorJogador:
    def __init__(self, data_dir):
        self.ficheiro_pontuacoes = os.path.join(data_dir, "highscore.json")
        self.jogador_atual = "Convidado"
        self.pontuacoes = self._carregar_pontuacoes()

    def _carregar_pontuacoes(self):
        if os.path.exists(self.ficheiro_pontuacoes):
            try:
                with open(self.ficheiro_pontuacoes, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def obter_pontuacao(self, jogo_id):
        return self.pontuacoes.get(jogo_id, 0)

    def registar_pontuacao(self, jogo_id, pontuacao):
        # Atualiza apenas se for um novo recorde
        atual = self.obter_pontuacao(jogo_id)
        if pontuacao > atual:
            self.pontuacoes[jogo_id] = pontuacao
            self._salvar_pontuacoes()

    def _salvar_pontuacoes(self):
        try:
            with open(self.ficheiro_pontuacoes, "w", encoding="utf-8") as f:
                json.dump(self.pontuacoes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Erro ao guardar pontuações:", e)
