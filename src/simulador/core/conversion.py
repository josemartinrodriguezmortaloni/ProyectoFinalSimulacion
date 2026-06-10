"""Conversión física: variables climáticas → volumen de entrada (hm³/mes).

También define las estrategias de distribución mensual de las variables
anuales (asignación uniforme o estacional). Funciones puras.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

M3_POR_HM3 = 1_000_000.0
MM_POR_METRO = 1_000.0
SEGUNDOS_POR_MES = 2_592_000.0  # 30 días

# Mes 0 = enero. Pesos con media 1 (suman 12): la fusión nival pica en
# verano (deshielo dic-feb) y la lluvia sigue las tormentas estivales.
PESOS_FUSION_MENDOZA = np.array(
    [2.0, 1.8, 1.2, 0.7, 0.4, 0.25, 0.2, 0.25, 0.5, 1.0, 1.6, 2.1]
)
PESOS_LLUVIA_MENDOZA = np.array(
    [1.8, 1.6, 1.3, 0.8, 0.5, 0.3, 0.3, 0.4, 0.7, 1.1, 1.5, 1.7]
)


@dataclass(frozen=True)
class ParametrosCuenca:
    """Geometría de la cuenca aportante usada en la conversión."""

    area_m2: float
    segundos_por_mes: float = SEGUNDOS_POR_MES


def distribuir_uniforme(valor_anual: float) -> np.ndarray:
    """Reparte un total anual en 12 cuotas mensuales iguales."""
    return np.full(12, valor_anual / 12.0)


def distribuir_estacional(valor_anual: float, pesos: np.ndarray) -> np.ndarray:
    """Reparte un total anual según pesos mensuales (deben sumar 12)."""
    return valor_anual * pesos / 12.0


def volumen_entrada_hm3(
    lluvia_mm_mes: float,
    nieve_mm_mes: float,
    caudal_m3s: float,
    cuenca: ParametrosCuenca,
) -> float:
    """Volumen total de agua que ingresa al sistema en un mes (hm³).

    Lluvia y nieve se convierten por lámina sobre el área de la cuenca;
    el caudal afluente se integra en el tiempo del mes.
    """
    lamina_m = (lluvia_mm_mes + nieve_mm_mes) / MM_POR_METRO
    volumen_precipitacion_m3 = lamina_m * cuenca.area_m2
    volumen_afluente_m3 = caudal_m3s * cuenca.segundos_por_mes
    return (volumen_precipitacion_m3 + volumen_afluente_m3) / M3_POR_HM3


def entradas_mensuales_hm3(
    lluvia_mensual_mm: np.ndarray,
    nieve_mensual_mm: np.ndarray,
    afluente_mensual_m3s: np.ndarray,
    cuenca: ParametrosCuenca,
) -> np.ndarray:
    """Vectoriza `volumen_entrada_hm3` para los 12 meses de un año."""
    lamina_m = (lluvia_mensual_mm + nieve_mensual_mm) / MM_POR_METRO
    volumen_m3 = (
        lamina_m * cuenca.area_m2
        + afluente_mensual_m3s * cuenca.segundos_por_mes
    )
    return volumen_m3 / M3_POR_HM3
