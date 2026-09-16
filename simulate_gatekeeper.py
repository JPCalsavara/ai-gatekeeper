#!/usr/bin/env python3
"""
Script de simulação local para testar o AI Quality Gatekeeper sem precisar abrir um PR no GitHub.
Permite testar dois cenários:
  1. clean: Código que cumpre as diretrizes e passa nos testes.
  2. violation: Código com falhas de teste e violações graves de diretrizes (SQL injection, credencial).
"""

import sys
import shutil
import argparse
from pathlib import Path
import gatekeeper

def setup_scenario(scenario: str):
    fixtures_dir = Path("tests/fixtures")
    if scenario == "clean":
        print("🔧 Configurando cenário: CLEAN (Sem violações e testes passando)")
        shutil.copy(fixtures_dir / "diff_clean.txt", Path("diff.txt"))
        shutil.copy(fixtures_dir / "tests_pass.log", Path("tests.log"))
    elif scenario == "violation":
        print("🔧 Configurando cenário: VIOLATION (Violações de diretrizes e falha em testes)")
        shutil.copy(fixtures_dir / "diff_violation.txt", Path("diff.txt"))
        shutil.copy(fixtures_dir / "tests_fail.log", Path("tests.log"))
    else:
        print(f"❌ Cenário desconhecido: {scenario}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Simulador local do AI Quality Gatekeeper")
    parser.add_argument(
        "--scenario",
        choices=["clean", "violation"],
        default="clean",
        help="Cenário de teste a ser preparado (clean ou violation)"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Executa o gatekeeper.py logo após preparar o cenário"
    )

    args = parser.parse_args()
    setup_scenario(args.scenario)
    print("✅ Arquivos diff.txt e tests.log gerados com sucesso!")

    if args.run:
        print("🚀 Executando Gatekeeper...")
        gatekeeper.main()

if __name__ == "__main__":
    main()
