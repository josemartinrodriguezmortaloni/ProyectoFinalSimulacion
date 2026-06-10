"""Fase 3: conversión de series climáticas en escenarios por dique.

Convierte mm y m³/s a hm³/mes (física de cuenca), distribuye los
totales anuales según la estrategia de asignación elegida y reparte el
volumen entre los diques según sus proporciones de cuenca.
"""
from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd

from simulador.config import ConfigPipeline
from simulador.core import conversion
from simulador.persistencia.repositorio import RepositorioArtefactos

MESES_POR_ANIO = 12


def _asignacion_uniforme(
    precipitacion_anual: float, fusion_anual: float, afluente_mensual: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reparte lluvia y nieve parejo; el afluente queda como se generó."""
    return (
        conversion.distribuir_uniforme(precipitacion_anual),
        conversion.distribuir_uniforme(fusion_anual),
        afluente_mensual,
    )


def _asignacion_estacional(
    precipitacion_anual: float, fusion_anual: float, afluente_mensual: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pesa lluvia, nieve y afluente con la estacionalidad mendocina."""
    return (
        conversion.distribuir_estacional(
            precipitacion_anual, conversion.PESOS_LLUVIA_MENDOZA
        ),
        conversion.distribuir_estacional(
            fusion_anual, conversion.PESOS_FUSION_MENDOZA
        ),
        # Pesos con media 1: modulan el caudal sin alterar el total anual.
        afluente_mensual * conversion.PESOS_FUSION_MENDOZA,
    )


Asignacion = Callable[
    [float, float, np.ndarray], tuple[np.ndarray, np.ndarray, np.ndarray]
]

# Registro de estrategias: agregar una nueva asignación = una entrada más.
ASIGNACIONES: dict[str, Asignacion] = {
    "uniforme": _asignacion_uniforme,
    "estacional": _asignacion_estacional,
}


class AsignacionDesconocidaError(ValueError):
    """La estrategia de asignación pedida no está registrada."""


def _entradas_totales_hm3(
    series: pd.DataFrame, asignacion: Asignacion, horizonte_meses: int, area_m2: float
) -> tuple[np.ndarray, np.ndarray]:
    """Calcula (entrada_total_hm3, temperatura) para el horizonte pedido."""
    cuenca = conversion.ParametrosCuenca(area_m2=area_m2)
    n_anios = math.ceil(horizonte_meses / MESES_POR_ANIO)

    entradas: list[np.ndarray] = []
    temperaturas: list[np.ndarray] = []
    for anio in range(n_anios):
        del_anio = series[series["anio"] == anio]
        lluvia, nieve, afluente = asignacion(
            float(del_anio["precipitacion_anual_mm"].iloc[0]),
            float(del_anio["fusion_anual_mm"].iloc[0]),
            del_anio["afluente_m3s"].to_numpy(),
        )
        entradas.append(
            conversion.entradas_mensuales_hm3(lluvia, nieve, afluente, cuenca)
        )
        temperaturas.append(del_anio["temperatura_c"].to_numpy())

    entrada_total = np.concatenate(entradas)[:horizonte_meses]
    temperatura = np.concatenate(temperaturas)[:horizonte_meses]
    return entrada_total, temperatura


def ejecutar(
    repo: RepositorioArtefactos,
    id_corrida: str,
    config: ConfigPipeline,
) -> list[str]:
    """Escribe un escenario CSV por dique y devuelve sus slugs."""
    if config.asignacion not in ASIGNACIONES:
        raise AsignacionDesconocidaError(
            f"Asignación '{config.asignacion}' no registrada. "
            f"Disponibles: {sorted(ASIGNACIONES)}"
        )

    series = repo.leer_series(id_corrida)
    anios_disponibles = series["anio"].nunique()
    anios_necesarios = math.ceil(config.horizonte_meses / MESES_POR_ANIO)
    if anios_disponibles < anios_necesarios:
        raise ValueError(
            f"El horizonte de {config.horizonte_meses} meses necesita "
            f"{anios_necesarios} años y la corrida tiene {anios_disponibles}."
        )

    entrada_total, temperatura = _entradas_totales_hm3(
        series,
        ASIGNACIONES[config.asignacion],
        config.horizonte_meses,
        config.area_cuenca_total_m2,
    )

    meses = np.arange(config.horizonte_meses)
    slugs: list[str] = []
    for dique in config.diques:
        escenario = pd.DataFrame(
            {
                "mes": meses,
                "entrada_agua_hm3": entrada_total * dique.proporcion_entrada,
                "temperatura_c": temperatura,
            }
        )
        repo.escribir_escenario(id_corrida, dique.slug, escenario)
        slugs.append(dique.slug)
        print(
            f"  ✓ {dique.nombre}: media "
            f"{escenario['entrada_agua_hm3'].mean():.1f} hm³/mes"
        )

    repo.actualizar_manifest(
        id_corrida,
        asignacion=config.asignacion,
        horizonte_meses=config.horizonte_meses,
        proporciones_diques={
            d.nombre: d.proporcion_entrada for d in config.diques
        },
    )
    print(f"✓ Escenarios generados ({config.asignacion}, {config.horizonte_meses} meses)")
    return slugs
