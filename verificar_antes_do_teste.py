#!/usr/bin/env python3
"""Libera o teste somente se a pasta for igual a origin/main.

Uso:
    python verificar_antes_do_teste.py

Codigos de saida:
    0 = teste liberado
    1 = teste bloqueado
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REMOTE = "origin"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent


def configurar_terminal() -> None:
    """Permite mostrar os icones mesmo no console antigo do Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        reconfigure = getattr(fluxo, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def executar_git(*argumentos: str) -> subprocess.CompletedProcess[str]:
    """Executa Git na pasta deste arquivo e captura a resposta."""
    return subprocess.run(
        ["git", *argumentos],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def bloquear(motivo: str) -> int:
    print(f"\n🔴 TESTE BLOQUEADO: {motivo}")
    return 1


def main() -> int:
    configurar_terminal()
    print(f"Verificando {ROOT} contra {REMOTE}/{BRANCH}...")

    if executar_git("rev-parse", "--is-inside-work-tree").returncode != 0:
        return bloquear("esta pasta nao e um repositorio Git.")

    # Atualiza somente a referencia da main. Nenhum arquivo local e alterado.
    refspec = f"+refs/heads/{BRANCH}:refs/remotes/{REMOTE}/{BRANCH}"
    fetch = executar_git("fetch", "--quiet", REMOTE, refspec)
    if fetch.returncode != 0:
        detalhe = fetch.stderr.strip() or fetch.stdout.strip()
        if detalhe:
            print(f"Detalhe do Git: {detalhe}")
        return bloquear("nao foi possivel consultar a main no GitHub.")

    referencia = f"{REMOTE}/{BRANCH}"
    if executar_git("rev-parse", "--verify", referencia).returncode != 0:
        return bloquear(f"a referencia {referencia} nao foi encontrada.")

    # Compara arquivos rastreados (commitados, preparados ou modificados).
    diferencas = executar_git("diff", "--name-status", referencia, "--")
    if diferencas.returncode != 0:
        return bloquear("o Git nao conseguiu comparar os arquivos.")

    # Arquivos ignorados pelo .gitignore nao bloqueiam (por exemplo, .venv).
    nao_rastreados = executar_git("ls-files", "--others", "--exclude-standard")
    if nao_rastreados.returncode != 0:
        return bloquear("o Git nao conseguiu verificar arquivos novos.")

    itens = [linha for linha in diferencas.stdout.splitlines() if linha.strip()]
    itens += [f"?\t{linha}" for linha in nao_rastreados.stdout.splitlines() if linha.strip()]

    if itens:
        print("\nDiferencas encontradas:")
        for item in itens:
            print(f"  {item}")
        return bloquear(f"a pasta nao e igual a {referencia}.")

    print(f"\n🟢 TESTE LIBERADO: a pasta e igual a {referencia}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError:
        raise SystemExit(bloquear("Git nao esta instalado ou nao esta no PATH."))
    except KeyboardInterrupt:
        raise SystemExit(bloquear("verificacao cancelada."))
