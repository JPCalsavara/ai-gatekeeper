#!/usr/bin/env python3
"""
Local simulation script to test the AI Quality Gatekeeper without opening a GitHub PR.
Supports two scenarios:
  1. clean: Code that adheres to guidelines and passes all unit tests.
  2. violation: Code with test failures and blocker guideline violations (SQL injection, credential leak).
"""

import sys
import shutil
import argparse
from pathlib import Path
import gatekeeper

def setup_scenario(scenario: str):
    fixtures_dir = Path("tests/fixtures")
    if scenario == "clean":
        print("[INFO] Setting up scenario: CLEAN (No violations, passing tests)")
        shutil.copy(fixtures_dir / "diff_clean.txt", Path("diff.txt"))
        shutil.copy(fixtures_dir / "tests_pass.log", Path("tests.log"))
    elif scenario == "violation":
        print("[INFO] Setting up scenario: VIOLATION (Guideline violations and test failures)")
        shutil.copy(fixtures_dir / "diff_violation.txt", Path("diff.txt"))
        shutil.copy(fixtures_dir / "tests_fail.log", Path("tests.log"))
    else:
        print(f"[ERROR] Unknown scenario: {scenario}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Local simulator for AI Quality Gatekeeper")
    parser.add_argument(
        "--scenario",
        choices=["clean", "violation"],
        default="clean",
        help="Test scenario to prepare (clean or violation)"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute gatekeeper.py immediately after preparing scenario"
    )

    args = parser.parse_args()
    setup_scenario(args.scenario)
    print("[SUCCESS] diff.txt and tests.log generated successfully.")

    if args.run:
        print("[RUN] Executing Gatekeeper...")
        gatekeeper.main()

if __name__ == "__main__":
    main()
