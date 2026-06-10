"""Contratos de datos del pipeline: único punto de verdad de los CSV.

Las fases NO se importan entre sí: solo comparten estos esquemas. Si un
artefacto no cumple su esquema, la fase que lo lee falla temprano.
"""
from __future__ import annotations

import pandas as pd


class EsquemaInvalidoError(ValueError):
    """El DataFrame leído no cumple el contrato del artefacto."""


ESQUEMA_SERIES: tuple[str, ...] = (
    "anio",
    "mes",
    "precipitacion_anual_mm",
    "fusion_anual_mm",
    "afluente_m3s",
    "demanda_hm3",
    "temperatura_c",
)

ESQUEMA_ESCENARIO: tuple[str, ...] = (
    "mes",
    "entrada_agua_hm3",
    "temperatura_c",
)

# Columnas mínimas que la fase de análisis necesita de los resultados.
ESQUEMA_RESULTADOS: tuple[str, ...] = (
    "mes",
    "Total Satisfaccion Riego",
    "Total Energia GWh",
    "Total Ingresos Energia",
    "Total Porcentaje de Llenado Completo",
    "Total Riego Entregado",
)


def validar_esquema(
    artefacto: pd.DataFrame, columnas: tuple[str, ...], nombre: str
) -> None:
    """Valida presencia de columnas y que sean numéricas.

    Raises:
        EsquemaInvalidoError: Si faltan columnas o alguna no es numérica.
    """
    faltantes = set(columnas) - set(artefacto.columns)
    if faltantes:
        raise EsquemaInvalidoError(
            f"Artefacto '{nombre}': faltan columnas {sorted(faltantes)}"
        )

    no_numericas = [
        c for c in columnas if not pd.api.types.is_numeric_dtype(artefacto[c])
    ]
    if no_numericas:
        raise EsquemaInvalidoError(
            f"Artefacto '{nombre}': columnas no numéricas {no_numericas}"
        )
