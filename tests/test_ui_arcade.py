import unittest

import pygame

from tests import _util


class TestUiArcade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _util.entrar_na_raiz()
        pygame.init()
        pygame.display.set_mode((10, 10))
        from src.utils import ui_arcade
        cls.ui = ui_arcade

    def test_misturar_extremos_e_meio(self):
        self.assertEqual(self.ui.misturar((0, 0, 0), (100, 200, 50), 0), (0, 0, 0))
        self.assertEqual(self.ui.misturar((0, 0, 0), (100, 200, 50), 1), (100, 200, 50))
        self.assertEqual(self.ui.misturar((0, 0, 0), (100, 200, 50), 0.5), (50, 100, 25))

    def test_quebrar_texto_respeita_a_largura(self):
        fonte = self.ui.fonte(20)
        linhas = self.ui.quebrar_texto(fonte, "um texto bem comprido que precisa ser dividido em varias linhas", 150)
        self.assertGreater(len(linhas), 1)
        for linha in linhas:
            self.assertLessEqual(fonte.size(linha)[0], 150)
        self.assertEqual(" ".join(linhas), "um texto bem comprido que precisa ser dividido em varias linhas")

    def test_fonte_usa_os_arquivos_do_projeto(self):
        # Press Start 2P é larga: cada letra ocupa uma caixa quadrada.
        titulo = self.ui.fonte(16, True)
        self.assertEqual(titulo.size("AAAA")[0], 64)

    def test_lista_menu_devolve_um_retangulo_por_item(self):
        tela = pygame.Surface((800, 600))
        rects = self.ui.lista_menu(tela, ["A", "B", "C"], 1, self.ui.CIANO, self.ui.fonte(16, True), 400, 100, 300, 50, 10, 0.0)
        self.assertEqual(len(rects), 3)
        self.assertEqual(rects[1].y - rects[0].y, 60)

    def test_cabem_os_atalhos_na_largura_da_tela(self):
        itens = [("SETAS", "Navegar"), ("ENTER", "Confirmar"), ("F1", "Controles"), ("ESC", "Sair")]
        total = self.ui.medir_atalhos(self.ui.fonte(11, True), self.ui.fonte(22), itens)
        self.assertLess(total, 1280)


if __name__ == "__main__":
    unittest.main()
