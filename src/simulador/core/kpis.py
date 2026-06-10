"""Cálculo de KPIs sobre los resultados del modelo de dinámica de sistemas.

Lee el DataFrame que devuelve PySD (columnas con los nombres reales de
Vensim) y produce indicadores agregados para el análisis de políticas.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

UMBRAL_CRISIS = 0.30
UMBRAL_ALERTA = 0.50

COLUMNA_SATISFACCION = "Total Satisfaccion Riego"
COLUMNA_ENERGIA = "Total Energia GWh"
COLUMNA_INGRESOS = "Total Ingresos Energia"
COLUMNA_LLENADO = "Total Porcentaje de Llenado Completo"
COLUMNA_RIEGO = "Total Riego Entregado"
SUFIJO_SATISFACCION_DIQUE = " Satisfaccion Riego"


@dataclass(frozen=True)
class KPIsSistema:
    """Indicadores agregados de una corrida completa."""

    satisfaccion_riego_media: float
    satisfaccion_riego_minima: float
    energia_total_gwh: float
    ingresos_totales_usd: float
    riego_total_hm3: float
    llenado_medio: float
    llenado_minimo: float
    meses_crisis: int
    meses_alerta: int
    satisfaccion_por_dique: dict[str, float]

    def a_dict(self) -> dict:
        return asdict(self)


def _satisfaccion_por_dique(resultados: pd.DataFrame) -> dict[str, float]:
    """Promedio de satisfacción de riego por embalse (excluye el total)."""
    columnas = [
        c
        for c in resultados.columns
        if c.endswith(SUFIJO_SATISFACCION_DIQUE) and not c.startswith("Total")
    ]
    return {
        c.removesuffix(SUFIJO_SATISFACCION_DIQUE): float(resultados[c].mean())
        for c in columnas
    }


def calcular_kpis(resultados: pd.DataFrame) -> KPIsSistema:
    """Agrega los resultados mensuales de PySD en KPIs de la corrida."""
    llenado = resultados[COLUMNA_LLENADO]
    satisfaccion = resultados[COLUMNA_SATISFACCION]

    return KPIsSistema(
        satisfaccion_riego_media=float(satisfaccion.mean()),
        satisfaccion_riego_minima=float(satisfaccion.min()),
        energia_total_gwh=float(resultados[COLUMNA_ENERGIA].sum()),
        ingresos_totales_usd=float(resultados[COLUMNA_INGRESOS].sum()),
        riego_total_hm3=float(resultados[COLUMNA_RIEGO].sum()),
        llenado_medio=float(llenado.mean()),
        llenado_minimo=float(llenado.min()),
        meses_crisis=int((llenado < UMBRAL_CRISIS).sum()),
        meses_alerta=int(
            ((llenado >= UMBRAL_CRISIS) & (llenado < UMBRAL_ALERTA)).sum()
        ),
        satisfaccion_por_dique=_satisfaccion_por_dique(resultados),
    )


@dataclass(frozen=True)
class PesosScore:
    """Ponderación del score multiobjetivo de una política hídrica."""

    riego: float = 0.5
    energia: float = 0.3
    crisis: float = 0.2


def puntuar_corridas(
    kpis_corridas: pd.DataFrame, pesos: PesosScore
) -> pd.DataFrame:
    """Agrega `energia_norm` y `score` a una tabla de KPIs de corridas.

    score = w_riego * satisfacción + w_energia * energía_normalizada
            - w_crisis * fracción de meses en crisis
    """
    puntuadas = kpis_corridas.copy()
    energia_max = puntuadas["energia_total_gwh"].max()
    puntuadas["energia_norm"] = puntuadas["energia_total_gwh"] / energia_max
    fraccion_crisis = puntuadas["meses_crisis"] / puntuadas["horizonte_meses"]

    puntuadas["score"] = (
        pesos.riego * puntuadas["satisfaccion_riego_media"]
        + pesos.energia * puntuadas["energia_norm"]
        - pesos.crisis * fraccion_crisis
    )
    return puntuadas.sort_values("score", ascending=False).reset_index(drop=True)
