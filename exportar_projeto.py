import os

RAIZ = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(RAIZ, "projeto_completo.txt")

EXTENSOES = {".py", ".json", ".txt", ".md", ".cfg", ".ini"}
IGNORAR_PASTAS = {"__pycache__", ".git", ".venv", "venv", ".idea", ".vscode"}
IGNORAR_ARQUIVOS = {"projeto_completo.txt", "exportar_projeto.py"}

with open(SAIDA, "w", encoding="utf-8") as out:
    # 1) Arvore de pastas (inclui imagens/sons so pelo nome)
    out.write("=== ESTRUTURA ===\n")
    for pasta, subpastas, arquivos in os.walk(RAIZ):
        subpastas[:] = sorted(s for s in subpastas if s not in IGNORAR_PASTAS)
        nivel = os.path.relpath(pasta, RAIZ).count(os.sep)
        nome = os.path.basename(pasta) if pasta != RAIZ else "."
        out.write("    " * nivel + nome + "/\n")
        for a in sorted(arquivos):
            out.write("    " * (nivel + 1) + a + "\n")

    # 2) Conteudo dos arquivos de codigo/texto
    out.write("\n\n=== ARQUIVOS ===\n")
    for pasta, subpastas, arquivos in os.walk(RAIZ):
        subpastas[:] = sorted(s for s in subpastas if s not in IGNORAR_PASTAS)
        for a in sorted(arquivos):
            if a in IGNORAR_ARQUIVOS or os.path.splitext(a)[1].lower() not in EXTENSOES:
                continue
            caminho = os.path.join(pasta, a)
            rel = os.path.relpath(caminho, RAIZ)
            out.write(f"\n\n########## {rel} ##########\n")
            try:
                with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[erro ao ler: {e}]")

print("Gerado:", SAIDA)
