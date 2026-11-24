import importlib
import os
import tempfile
import unittest

from tests import _util


class TestKombatePartida(unittest.TestCase):
    """Regras de luta (sem tela): rounds, tempo, K.O. e vencedor."""

    def setUp(self):
        _util.entrar_no_jogo("Kombate")
        characters = importlib.import_module("game.characters")
        match = importlib.import_module("game.match")
        self.settings = importlib.import_module("settings")
        self.partida = match.Partida(characters.PERSONAGENS[0], characters.PERSONAGENS[1], cpu1=False, cpu2=False)

    def _ir_para_luta(self):
        for _ in range(200):
            if self.partida.fase == "luta":
                return
            self.partida.update()
        self.fail("a partida nao saiu da intro")

    def _ganhar_round(self, vencedor, perdedor):
        self._ir_para_luta()
        perdedor.hp = 0
        for _ in range(600):
            self.partida.update()
            if self.partida.fase in ("luta", "fim") and self.partida.vencedor_round is None:
                return
            if self.partida.fase == "intro" or self.partida.fase == "fim":
                return
        self.fail("o round nao terminou")

    def test_comeca_na_intro_com_tempo_cheio(self):
        self.assertEqual(self.partida.fase, "intro")
        self.assertEqual(self.partida.round, 1)
        self.assertEqual(self.partida.segundos, self.settings.TEMPO_ROUND)

    def test_ko_da_vitoria_do_round(self):
        self._ir_para_luta()
        self.partida.f2.hp = 0
        self.partida.update()
        self.assertEqual(self.partida.fase, "ko")
        self.assertIs(self.partida.vencedor_round, self.partida.f1)
        self.assertEqual(self.partida.f1.vitorias, 1)
        self.assertEqual(self.partida.motivo, "K.O.!")

    def test_tempo_esgotado_vence_quem_tem_mais_vida(self):
        self._ir_para_luta()
        self.partida.f1.hp = 500   # os personagens tem vida maxima diferente: fixa os valores
        self.partida.f2.hp = 510
        self.partida.tempo = 1
        self.partida.update()
        self.assertEqual(self.partida.fase, "ko")
        self.assertIs(self.partida.vencedor_round, self.partida.f2)
        self.assertEqual(self.partida.motivo, "TEMPO!")

    def test_empate_no_round_ninguem_pontua(self):
        self._ir_para_luta()
        self.partida.f1.hp = self.partida.f2.hp = 500
        self.partida.tempo = 1
        self.partida.update()
        self.assertIsNone(self.partida.vencedor_round)
        self.assertEqual((self.partida.f1.vitorias, self.partida.f2.vitorias), (0, 0))

    def test_vence_a_partida_quem_ganha_dois_rounds(self):
        p = self.partida
        for _ in range(self.settings.ROUNDS_PARA_VENCER):
            self._ir_para_luta()
            p.f2.hp = 0
            for _ in range(800):
                p.update()
                if p.fase in ("intro", "fim"):
                    break
        self.assertEqual(p.fase, "fim")
        self.assertIs(p.vencedor, p.f1)
        self.assertEqual(p.f1.vitorias, self.settings.ROUNDS_PARA_VENCER)

    def test_todos_os_personagens_existem_e_tem_vida(self):
        characters = importlib.import_module("game.characters")
        self.assertEqual(len(characters.PERSONAGENS), 6)
        for c in characters.PERSONAGENS:
            self.assertGreater(c.max_hp, 0)


class TestKombateRecorde(unittest.TestCase):
    def setUp(self):
        _util.entrar_no_jogo("Kombate")
        self.app = importlib.import_module("game.app")
        self.tmp = tempfile.TemporaryDirectory()
        self.app.RECORDE_FILE = os.path.join(self.tmp.name, "recorde.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_sem_arquivo_e_zero(self):
        self.assertEqual(self.app.carregar_vitorias(), 0)

    def test_salva_e_le(self):
        self.app.salvar_vitorias(3)
        self.assertEqual(self.app.carregar_vitorias(), 3)
        self.app.salvar_vitorias(self.app.carregar_vitorias() + 1)
        self.assertEqual(self.app.carregar_vitorias(), 4)

    def test_arquivo_invalido_vira_zero(self):
        with open(self.app.RECORDE_FILE, "w") as f:
            f.write("{")
        self.assertEqual(self.app.carregar_vitorias(), 0)


if __name__ == "__main__":
    unittest.main()
