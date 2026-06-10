"""CLI del pipeline: un subcomando por fase + `pipeline` que encadena todo.

Uso típico:
    uv run simular pipeline --seed 42
    uv run simular generar --seed 7 --anios 500
    uv run simular validar --corrida ultima
    uv run simular convertir --corrida ultima --asignacion estacional
    uv run simular simular --corrida ultima
    uv run simular analizar --corrida ultima
    uv run simular analizar --todas
    uv run simular eventos          # simulador discreto legacy (Unidad 4)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from simulador.aggregate import SimulacionHidrica
from simulador.config import ConfigPipeline
from simulador.core.kpis import PesosScore
from simulador.fases import analizar, convertir, generar, simular, validar
from simulador.persistencia.repositorio import RepositorioArtefactos

CODIGO_GATE_RECHAZADO = 1


def _config_desde_args(args: argparse.Namespace) -> ConfigPipeline:
    base = ConfigPipeline()
    cambios: dict[str, object] = {}
    if getattr(args, "asignacion", None):
        cambios["asignacion"] = args.asignacion
    if getattr(args, "horizonte_meses", None):
        cambios["horizonte_meses"] = args.horizonte_meses
    if getattr(args, "raiz", None):
        cambios["raiz_artefactos"] = Path(args.raiz)
    return replace(base, **cambios) if cambios else base


def _repo(config: ConfigPipeline) -> RepositorioArtefactos:
    return RepositorioArtefactos(config.raiz_artefactos)


def _cmd_generar(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    generar.ejecutar(_repo(config), seed=args.seed, n_anios=args.anios)
    return 0


def _cmd_validar(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    repo = _repo(config)
    reporte = validar.ejecutar(repo, repo.resolver_id(args.corrida))
    return 0 if reporte.aceptado else CODIGO_GATE_RECHAZADO


def _cmd_convertir(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    repo = _repo(config)
    convertir.ejecutar(repo, repo.resolver_id(args.corrida), config)
    return 0


def _cmd_simular(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    repo = _repo(config)
    simular.ejecutar(repo, repo.resolver_id(args.corrida), config)
    return 0


def _cmd_analizar(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    repo = _repo(config)
    if args.todas:
        riego, energia, crisis = config.pesos_score
        analizar.ejecutar_global(
            repo, PesosScore(riego=riego, energia=energia, crisis=crisis)
        )
    else:
        analizar.ejecutar(repo, repo.resolver_id(args.corrida))
    return 0


def _cmd_pipeline(args: argparse.Namespace) -> int:
    config = _config_desde_args(args)
    repo = _repo(config)

    print("=" * 70)
    print("PIPELINE: generar → validar → convertir → simular → analizar")
    print("=" * 70)

    print("\n[1/5] Generación de series")
    id_corrida = generar.ejecutar(repo, seed=args.seed, n_anios=args.anios)

    print("\n[2/5] Validación estadística (gate)")
    reporte = validar.ejecutar(repo, id_corrida)
    if not reporte.aceptado:
        print("✗ Pipeline detenido: las series no superan los tests.")
        return CODIGO_GATE_RECHAZADO

    print("\n[3/5] Conversión a escenarios por dique")
    convertir.ejecutar(repo, id_corrida, config)

    print("\n[4/5] Simulación PySD del modelo Vensim")
    simular.ejecutar(repo, id_corrida, config)

    print("\n[5/5] Análisis de KPIs")
    analizar.ejecutar(repo, id_corrida)

    print(f"\n✓ Pipeline completo. Artefactos en {config.raiz_artefactos}/{id_corrida}/")
    return 0


def _cmd_eventos(_args: argparse.Namespace) -> int:
    """Modo legacy: simulador discreto por eventos (Unidad 4)."""
    SimulacionHidrica().ejecutar()
    return 0


def _agregar_arg_corrida(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--corrida",
        default="ultima",
        help="ID de la corrida (default: 'ultima', la más reciente)",
    )


def _agregar_arg_raiz(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--raiz", default=None, help="Directorio raíz de artefactos"
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simular",
        description="Pipeline de simulación hídrica de Mendoza (PySD + Vensim)",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_generar = subparsers.add_parser("generar", help="Fase 1: generar series")
    parser_generar.add_argument("--seed", type=int, default=42)
    parser_generar.add_argument("--anios", type=int, default=500)
    _agregar_arg_raiz(parser_generar)
    parser_generar.set_defaults(func=_cmd_generar)

    parser_validar = subparsers.add_parser(
        "validar", help="Fase 2: gate estadístico (exit 1 si rechaza)"
    )
    _agregar_arg_corrida(parser_validar)
    _agregar_arg_raiz(parser_validar)
    parser_validar.set_defaults(func=_cmd_validar)

    parser_convertir = subparsers.add_parser(
        "convertir", help="Fase 3: escenarios por dique"
    )
    _agregar_arg_corrida(parser_convertir)
    _agregar_arg_raiz(parser_convertir)
    parser_convertir.add_argument(
        "--asignacion", choices=sorted(convertir.ASIGNACIONES), default=None
    )
    parser_convertir.add_argument("--horizonte-meses", type=int, default=None)
    parser_convertir.set_defaults(func=_cmd_convertir)

    parser_simular = subparsers.add_parser(
        "simular", help="Fase 4: correr el .mdl con PySD"
    )
    _agregar_arg_corrida(parser_simular)
    _agregar_arg_raiz(parser_simular)
    parser_simular.set_defaults(func=_cmd_simular)

    parser_analizar = subparsers.add_parser(
        "analizar", help="Fase 5: KPIs y ranking global"
    )
    _agregar_arg_corrida(parser_analizar)
    _agregar_arg_raiz(parser_analizar)
    parser_analizar.add_argument(
        "--todas", action="store_true", help="Ranking global de todas las corridas"
    )
    parser_analizar.set_defaults(func=_cmd_analizar)

    parser_pipeline = subparsers.add_parser(
        "pipeline", help="Todas las fases encadenadas"
    )
    parser_pipeline.add_argument("--seed", type=int, default=42)
    parser_pipeline.add_argument("--anios", type=int, default=500)
    parser_pipeline.add_argument(
        "--asignacion", choices=sorted(convertir.ASIGNACIONES), default=None
    )
    parser_pipeline.add_argument("--horizonte-meses", type=int, default=None)
    _agregar_arg_raiz(parser_pipeline)
    parser_pipeline.set_defaults(func=_cmd_pipeline)

    parser_eventos = subparsers.add_parser(
        "eventos", help="Simulador discreto legacy (Unidad 4)"
    )
    parser_eventos.set_defaults(func=_cmd_eventos)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
