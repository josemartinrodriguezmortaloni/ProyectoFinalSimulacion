"""Entry point alternativo: `python src <comando>`.

Delega en el mismo CLI que `uv run simular`, así los dos caminos
ejecutan exactamente la misma aplicación.
"""
from __future__ import annotations

import sys

from simulador.cli import main as main_cli


def main() -> None:
    sys.exit(main_cli())


if __name__ == "__main__":
    main()
