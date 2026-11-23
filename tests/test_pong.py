import importlib
import json
import os
import tempfile
import unittest

import pygame

from tests import _util


class TestPong(unittest.TestCase):
    def setUp(self):
        _util.entrar_no_jogo("Ping pong")
        pygame.init()
        self.modulo = importlib.import_module("game.game")
        self.tmp = tempfile.TemporaryDirectory()
        self.modulo.RECORDE_FILE = os.path.join(self.tmp.name, "recorde.json")
        self.settings = importlib.import_module("settings")
        self.jogo = self.modulo.Game(pygame.Surface((self.settings.SCREEN_WIDTH, self.settings.SCREEN_HEIGHT)))

    def tearDown(self):
        self.tmp.cleanup()

    def _vencer(self, lado):
        self.jogo.start_match(self.jogo.mode)
        if lado == "esquerda":
            self.jogo.left_score = self.settings.WINNING_SCORE
        else:
            self.jogo.right_score = self.settings.WINNING_SCORE
        self.jogo._after_point(1)

    def test_vence_quem_chega_ao_placar(self):
        self.jogo.start_match("cpu")
        self.jogo.left_score = self.settings.WINNING_SCORE - 1
        self.jogo._after_point(1)
        self.assertEqual(self.jogo.state, self.modulo.Game.PLAYING)
        self.jogo.left_score += 1
        self.jogo._after_point(1)
        self.assertEqual(self.jogo.state, self.modulo.Game.GAME_OVER)
        self.assertIn("Jogador 1", self.jogo.winner)

    def test_vitoria_contra_cpu_salva_recorde(self):
        self.jogo.mode = "cpu"
        self._vencer("esquerda")
        self.assertEqual(self.jogo.vitorias, 1)
        with open(self.modulo.RECORDE_FILE, encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"recorde": 1})
        self.assertEqual(self.modulo.carregar_vitorias(), 1)

    def test_derrota_para_cpu_nao_conta(self):
        self.jogo.mode = "cpu"
        self._vencer("direita")
        self.assertEqual(self.jogo.vitorias, 0)
        self.assertIn("CPU", self.jogo.winner)
        self.assertFalse(os.path.exists(self.modulo.RECORDE_FILE))

    def test_dois_jogadores_nao_contam_recorde(self):
        self.jogo.mode = "versus"
        self._vencer("esquerda")
        self.assertEqual(self.jogo.vitorias, 0)
        self.assertFalse(os.path.exists(self.modulo.RECORDE_FILE))

    def test_recorde_acumula_entre_partidas(self):
        self.jogo.mode = "cpu"
        self._vencer("esquerda")
        self._vencer("esquerda")
        self.assertEqual(self.modulo.carregar_vitorias(), 2)

    def test_arquivo_invalido_vira_zero(self):
        with open(self.modulo.RECORDE_FILE, "w") as f:
            f.write("lixo")
        self.assertEqual(self.modulo.carregar_vitorias(), 0)


if __name__ == "__main__":
    unittest.main()
