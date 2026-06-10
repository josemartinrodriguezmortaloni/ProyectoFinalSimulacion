"""Entry point: delega en el CLI del pipeline.

`uv run simular pipeline` corre todo; `uv run simular eventos` mantiene
el simulador discreto original (Unidad 4).
"""
from __future__ import annotations

import sys

from simulador.cli import main as main_cli


def main() -> None:
    sys.exit(main_cli())


if __name__ == "__main__":
    main()
