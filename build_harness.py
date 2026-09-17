#!/usr/bin/env python3
"""
CLI utility to scan environment documentation and generate the local vector embedding index.
Outputs context_harness.json for semantic rule retrieval during Quality Gate execution.
"""

import argparse
import sys
from pathlib import Path
from context_harness import build_harness_index

def main():
    parser = argparse.ArgumentParser(description="Build local Context Harness vector index from documentation.")
    parser.add_argument(
        "--docs",
        nargs="+",
        default=["docs", "README.md"],
        help="Directories or markdown files to index (default: docs README.md)"
    )
    parser.add_argument(
        "--output",
        default="context_harness.json",
        help="Target output JSON path (default: context_harness.json)"
    )

    args = parser.parse_args()
    source_paths = [Path(p) for p in args.docs if Path(p).exists()]

    if not source_paths:
        print("[ERROR] None of the specified documentation paths exist.")
        sys.exit(1)

    print(f"[INFO] Scanning documentation from: {[str(p) for p in source_paths]}")
    try:
        count = build_harness_index(source_paths, Path(args.output))
        print(f"[SUCCESS] Context harness index generated with {count} chunks at {args.output}")
    except Exception as e:
        print(f"[ERROR] Failed to generate context harness index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
