"""Run the full local research team; optionally select the Bytez experiment."""

from __future__ import annotations

import argparse


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--provider", choices=("ollama", "bytez"), default="ollama")
    args, remaining = parser.parse_known_args()
    if args.provider == "bytez":
        from examples.run_bytez_glm47 import main as run
    else:
        from examples.run_ollama_qwen3 import main as run
    run(remaining)

if __name__ == "__main__":
    main()
