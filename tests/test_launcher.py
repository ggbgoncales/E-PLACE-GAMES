import json
import os
import tempfile
import unittest

from tests import _util


class TestLauncher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _util.entrar_na_raiz()
        import main
        cls.main = main

    def test_encontra_os_seis_jogos(self):
        jogos = self.main.listar_jogos()
        nomes = sorted(j["id"] for j in jogos)
        self.assertEqual(nomes, ["Flappy bird", "Frogger", "Kombate", "Ping pong", "Snake", "Space Invaders"])
        for jogo in jogos:
            self.assertTrue(os.path.exists(jogo["main"]), jogo["id"])

    def test_todos_os_jogos_tem_capa(self):
        for jogo in self.main.listar_jogos():
            self.assertIsNotNone(jogo["capa"], f"sem capa: {jogo['id']}")

    def test_pasta_imports_e_ignorada(self):
        self.assertNotIn("imports", [j["id"] for j in self.main.listar_jogos()])

    def test_nome_bonito(self):
        self.assertEqual(self.main.nome_bonito("game6"), "Game 6")
        self.assertEqual(self.main.nome_bonito("snake"), "Snake")
        self.assertEqual(self.main.nome_bonito("Ping pong"), "Pong")
        self.assertEqual(self.main.nome_bonito("Flappy bird"), "Flappy Bird")

    def test_ordem_da_lista_segue_a_documentacao(self):
        titulos = [j["titulo"] for j in self.main.listar_jogos()]
        self.assertEqual(titulos, ["Snake", "Pong", "Frogger", "Space Invaders", "Flappy Bird", "Kombate"])

    def test_titulos_dos_jogos_na_lista(self):
        titulos = sorted(j["titulo"] for j in self.main.listar_jogos())
        self.assertEqual(titulos, ["Flappy Bird", "Frogger", "Kombate", "Pong", "Snake", "Space Invaders"])

    def test_config_padrao_quando_arquivo_nao_existe(self):
        antigo = self.main.CONFIG_PATH
        self.main.CONFIG_PATH = os.path.join(tempfile.gettempdir(), "nao-existe-eplace.json")
        try:
            cfg = self.main.carregar_config()
        finally:
            self.main.CONFIG_PATH = antigo
        self.assertEqual(cfg, self.main.CONFIG_PADRAO)

    def test_config_mescla_valores_salvos(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "config.json")
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"volume": 10}, f)
            antigo = self.main.CONFIG_PATH
            self.main.CONFIG_PATH = caminho
            try:
                cfg = self.main.carregar_config()
            finally:
                self.main.CONFIG_PATH = antigo
        self.assertEqual(cfg["volume"], 10)
        self.assertEqual(cfg["tela_cheia"], self.main.CONFIG_PADRAO["tela_cheia"])

    def test_ler_json_tolera_arquivo_ausente_ou_invalido(self):
        app = self.main.Eplace.__new__(self.main.Eplace)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(app._ler_json(os.path.join(d, "nada.json"), "recorde"), 0)
            ruim = os.path.join(d, "ruim.json")
            with open(ruim, "w", encoding="utf-8") as f:
                f.write("{nao e json")
            self.assertEqual(app._ler_json(ruim, "recorde"), 0)
            bom = os.path.join(d, "bom.json")
            with open(bom, "w", encoding="utf-8") as f:
                json.dump({"recorde": 42}, f)
            self.assertEqual(app._ler_json(bom, "recorde"), 42)

    def test_recordes_listam_os_seis_jogos_em_ordem(self):
        app = self.main.Eplace.__new__(self.main.Eplace)
        recordes = app._carregar_recordes()
        self.assertEqual(sorted(n for n, _, _ in recordes),
                         ["Flappy Bird", "Frogger", "Kombate", "Pong", "Snake", "Space Invaders"])
        valores = [v for _, v, _ in recordes]
        self.assertEqual(valores, sorted(valores, reverse=True))
        unidades = {n: u for n, _, u in recordes}
        self.assertEqual(unidades["Pong"], "vitorias")
        self.assertEqual(unidades["Kombate"], "vitorias")


if __name__ == "__main__":
    unittest.main()
