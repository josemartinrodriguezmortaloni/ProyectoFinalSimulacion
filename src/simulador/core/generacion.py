"""Generación de series climáticas pseudoaleatorias (Unidad 5).

Funciones puras: reciben un `numpy.random.Generator` explícito, por lo
que la reproducibilidad queda garantizada por el seed del llamador.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MESES_POR_ANIO = 12


@dataclass(frozen=True)
class ParametrosClimaticos:
    """Parámetros de las distribuciones del clima mendocino."""

    media_precipitacion_mm: float = 230.0
    desv_precipitacion_mm: float = 80.0
    max_precipitacion_mm: float = 600.0
    media_fusion_mm: float = 300.0
    desv_fusion_mm: float = 80.0
    min_fusion_mm: float = 50.0
    max_fusion_mm: float = 600.0
    media_afluente_m3s: float = 60.0
    desv_afluente_m3s: float = 20.0
    media_demanda_hm3: float = 250.0
    desv_relativa_demanda: float = 0.15
    estacionalidad_demanda: tuple[float, ...] = (
        1.00, 1.10, 1.05, 0.70, 0.40, 0.35,
        0.40, 0.50, 0.80, 1.00, 1.15, 1.05,
    )


def generar_precipitacion_anual(
    rng: np.random.Generator, n_anios: int, params: ParametrosClimaticos
) -> np.ndarray:
    """Precipitación anual (mm) con distribución Gamma ajustada por momentos."""
    varianza = params.desv_precipitacion_mm**2
    alpha = params.media_precipitacion_mm**2 / varianza
    beta = varianza / params.media_precipitacion_mm
    lluvia = rng.gamma(alpha, beta, n_anios)
    return np.clip(lluvia, 0.0, params.max_precipitacion_mm)


def generar_fusion_anual(
    rng: np.random.Generator, n_anios: int, params: ParametrosClimaticos
) -> np.ndarray:
    """Fusión nival anual (mm) con distribución Normal acotada."""
    fusion = rng.normal(params.media_fusion_mm, params.desv_fusion_mm, n_anios)
    return np.clip(fusion, params.min_fusion_mm, params.max_fusion_mm)


def generar_afluentes_mensuales(
    rng: np.random.Generator, n_anios: int, params: ParametrosClimaticos
) -> np.ndarray:
    """Caudal afluente mensual (m³/s), matriz (n_anios, 12)."""
    afluentes = rng.normal(
        params.media_afluente_m3s,
        params.desv_afluente_m3s,
        (n_anios, MESES_POR_ANIO),
    )
    return np.maximum(afluentes, 0.0)


def generar_demanda_mensual(
    rng: np.random.Generator, n_anios: int, params: ParametrosClimaticos
) -> np.ndarray:
    """Demanda agrícola mensual (hm³), estacional con ruido multiplicativo."""
    estacion = np.asarray(params.estacionalidad_demanda)
    ruido = rng.normal(1.0, params.desv_relativa_demanda, (n_anios, MESES_POR_ANIO))
    demanda = params.media_demanda_hm3 * estacion * ruido
    return np.maximum(demanda, 0.0)


def generar_temperatura_mensual(
    rng: np.random.Generator, n_anios: int
) -> np.ndarray:
    """Temperatura media mensual (°C): ciclo anual senoidal + ruido N(0,1)."""
    meses = np.arange(MESES_POR_ANIO)
    ciclo = 20.0 + 8.0 * np.sin(2.0 * np.pi * meses / MESES_POR_ANIO)
    ruido = rng.normal(0.0, 1.0, (n_anios, MESES_POR_ANIO))
    return ciclo + ruido


def generar_series_climaticas(
    rng: np.random.Generator,
    n_anios: int,
    params: ParametrosClimaticos | None = None,
) -> pd.DataFrame:
    """Genera todas las series en formato largo: una fila por (anio, mes).

    Las variables anuales (precipitación y fusión) se repiten en las 12
    filas de su año; la distribución mensual la decide la fase de
    conversión según la estrategia de asignación elegida.

    Returns:
        DataFrame con el esquema ``ESQUEMA_SERIES``.
    """
    parametros = params or ParametrosClimaticos()

    precipitacion = generar_precipitacion_anual(rng, n_anios, parametros)
    fusion = generar_fusion_anual(rng, n_anios, parametros)
    afluente = generar_afluentes_mensuales(rng, n_anios, parametros)
    demanda = generar_demanda_mensual(rng, n_anios, parametros)
    temperatura = generar_temperatura_mensual(rng, n_anios)

    anios = np.repeat(np.arange(n_anios), MESES_POR_ANIO)
    meses = np.tile(np.arange(MESES_POR_ANIO), n_anios)

    return pd.DataFrame(
        {
            "anio": anios,
            "mes": meses,
            "precipitacion_anual_mm": np.repeat(precipitacion, MESES_POR_ANIO),
            "fusion_anual_mm": np.repeat(fusion, MESES_POR_ANIO),
            "afluente_m3s": afluente.ravel(),
            "demanda_hm3": demanda.ravel(),
            "temperatura_c": temperatura.ravel(),
        }
    )
