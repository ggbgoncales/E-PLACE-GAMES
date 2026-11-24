import importlib
import os
import tempfile
import unittest

from tests import _util


class TestScore(unittest.TestCase):
    def setUp(self):
        _util.entrar_na_raiz()
        self.score = importlib.import_module("src.utils.score")
        self.tmp = tempfile.TemporaryDirectory()
        self.score.ARQUIVO_SCORE = os.path.join(self.tmp.name, "highscore.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_sem_arquivo_retorna_vazio(self):
        self.assertEqual(self.score.carregar_pontuacoes(), {})

    def test_salva_primeiro_recorde(self):
        self.score.salvar_pontuacao("Snake", 50)
        self.assertEqual(self.score.carregar_pontuacoes(), {"Snake": 50})

    def test_so_atualiza_quando_supera(self):
        self.score.salvar_pontuacao("Snake", 50)
        self.score.salvar_pontuacao("Snake", 30)
        self.assertEqual(self.score.carregar_pontuacoes()["Snake"], 50)
        self.score.salvar_pontuacao("Snake", 80)
        self.assertEqual(self.score.carregar_pontuacoes()["Snake"], 80)

    def test_jogos_sao_independentes(self):
        self.score.salvar_pontuacao("Snake", 50)
        self.score.salvar_pontuacao("Pong", 3)
        self.assertEqual(self.score.carregar_pontuacoes(), {"Snake": 50, "Pong": 3})


if __name__ == "__main__":
    unittest.main()
