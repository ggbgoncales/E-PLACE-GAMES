"""
zip_extractor.py
================
Le a pasta games/imports/ e extrai qualquer .zip para dentro de games/.
Um zip chamado "game6.zip" vira a pasta games/game6/.
O zip continua em imports/ (nao apaga nada).
"""
import os
import zipfile


def extrair_zips(games_dir):
    imports_dir = os.path.join(games_dir, "imports")
    if not os.path.isdir(imports_dir):
        return
    for arquivo in os.listdir(imports_dir):
        if not arquivo.lower().endswith(".zip"):
            continue
        nome_jogo = os.path.splitext(arquivo)[0]
        destino = os.path.join(games_dir, nome_jogo)
        if os.path.isdir(destino) and os.path.exists(os.path.join(destino, "main.py")):
            continue
        caminho_zip = os.path.join(imports_dir, arquivo)
        try:
            with zipfile.ZipFile(caminho_zip, "r") as z:
                os.makedirs(destino, exist_ok=True)
                z.extractall(destino)
            _achatar_se_necessario(destino)
            print(f"[zip_extractor] Extraido: {arquivo} -> {nome_jogo}/")
        except Exception as e:
            print(f"[zip_extractor] Erro ao extrair {arquivo}: {e}")


def _achatar_se_necessario(destino):
    itens = os.listdir(destino)
    if len(itens) == 1:
        unico = os.path.join(destino, itens[0])
        if os.path.isdir(unico) and not os.path.exists(os.path.join(destino, "main.py")):
            for sub in os.listdir(unico):
                os.rename(os.path.join(unico, sub), os.path.join(destino, sub))
            os.rmdir(unico)


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extrair_zips(os.path.join(base, "games"))
