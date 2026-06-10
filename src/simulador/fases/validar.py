"""Fase 2: validación estadística de las series (quality gate).

Si el reporte rechaza, el pipeline debe cortar: no tiene sentido
simular con números que no superan los tests de la Unidad 5.
"""
from __future__ import annotations

from simulador.core.estadistica import ReporteValidacion, validar_series_climaticas
from simulador.persistencia.repositorio import RepositorioArtefactos


def ejecutar(repo: RepositorioArtefactos, id_corrida: str) -> ReporteValidacion:
    """Corre la batería de tests y persiste el reporte JSON."""
    series = repo.leer_series(id_corrida)

    por_anio = series.groupby("anio")
    precipitacion = por_anio["precipitacion_anual_mm"].first().to_numpy()
    fusion = por_anio["fusion_anual_mm"].first().to_numpy()
    afluente = series["afluente_m3s"].to_numpy()

    reporte = validar_series_climaticas(precipitacion, fusion, afluente)
    repo.escribir_validacion(id_corrida, reporte.a_dict())

    for test in reporte.tests:
        marca = "✓" if test.aceptado else "✗"
        p_valor = f"p={test.p_valor:.4f}" if test.p_valor == test.p_valor else "IC 95%"
        print(f"  {marca} {test.nombre} [{test.serie}] {p_valor}")

    veredicto = "ACEPTADO" if reporte.aceptado else "RECHAZADO"
    print(f"{'✓' if reporte.aceptado else '✗'} Gate de validación: {veredicto}")
    return reporte
