"""Tests estadísticos para validar los números generados (Unidad 5).

Quality gate del pipeline: si el reporte no es aceptado, la simulación
no debe ejecutarse. Funciones puras sobre arrays de NumPy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats

NIVEL_SIGNIFICANCIA = 0.05
PARAMETROS_ESTIMADOS_GAMMA = 2
PARAMETROS_ESTIMADOS_NORMAL = 2


@dataclass(frozen=True)
class ResultadoTest:
    """Resultado de un test de hipótesis individual."""

    nombre: str
    serie: str
    estadistico: float
    p_valor: float
    aceptado: bool
    detalle: dict | None = None


@dataclass(frozen=True)
class ReporteValidacion:
    """Conjunto de tests sobre las series generadas."""

    aceptado: bool
    tests: tuple[ResultadoTest, ...]

    def a_dict(self) -> dict:
        return {
            "aceptado": self.aceptado,
            "tests": [asdict(t) for t in self.tests],
        }


def _momentos_gamma(datos: np.ndarray) -> tuple[float, float]:
    """Estima (alpha, beta) de una Gamma por método de los momentos."""
    media = float(np.mean(datos))
    varianza = float(np.var(datos))
    return media**2 / varianza, varianza / media


def test_chi_cuadrada_gamma(
    datos: np.ndarray, serie: str, n_bins: int = 12
) -> ResultadoTest:
    """Bondad de ajuste chi-cuadrada contra Gamma con bins equiprobables.

    Los límites de bin se toman de los cuantiles de la Gamma ajustada,
    así la frecuencia esperada es uniforme (n/k) y el test es válido.
    """
    alpha, beta = _momentos_gamma(datos)
    cuantiles = np.linspace(0.0, 1.0, n_bins + 1)
    limites = stats.gamma.ppf(cuantiles, a=alpha, scale=beta)
    limites[0], limites[-1] = -np.inf, np.inf

    observada, _ = np.histogram(datos, bins=limites)
    esperada = len(datos) / n_bins

    estadistico = float(np.sum((observada - esperada) ** 2 / esperada))
    grados_libertad = n_bins - 1 - PARAMETROS_ESTIMADOS_GAMMA
    p_valor = float(1.0 - stats.chi2.cdf(estadistico, df=grados_libertad))

    return ResultadoTest(
        nombre="chi_cuadrada_gamma",
        serie=serie,
        estadistico=estadistico,
        p_valor=p_valor,
        aceptado=p_valor > NIVEL_SIGNIFICANCIA,
        detalle={"alpha": alpha, "beta": beta, "bins": n_bins},
    )


def test_ks_gamma(datos: np.ndarray, serie: str) -> ResultadoTest:
    """Kolmogorov-Smirnov contra Gamma ajustada por momentos."""
    alpha, beta = _momentos_gamma(datos)
    estadistico, p_valor = stats.kstest(datos, "gamma", args=(alpha, 0, beta))
    return ResultadoTest(
        nombre="kolmogorov_smirnov_gamma",
        serie=serie,
        estadistico=float(estadistico),
        p_valor=float(p_valor),
        aceptado=p_valor > NIVEL_SIGNIFICANCIA,
        detalle={"alpha": alpha, "beta": beta},
    )


def test_ks_normal(datos: np.ndarray, serie: str) -> ResultadoTest:
    """Kolmogorov-Smirnov contra Normal con media y desvío muestrales."""
    media, desvio = float(np.mean(datos)), float(np.std(datos))
    estadistico, p_valor = stats.kstest(datos, "norm", args=(media, desvio))
    return ResultadoTest(
        nombre="kolmogorov_smirnov_normal",
        serie=serie,
        estadistico=float(estadistico),
        p_valor=float(p_valor),
        aceptado=p_valor > NIVEL_SIGNIFICANCIA,
        detalle={"media": media, "desvio": desvio},
    )


def test_autocorrelacion(
    datos: np.ndarray, serie: str, lags: int = 5
) -> ResultadoTest:
    """Independencia: autocorrelación dentro del IC 95% para cada lag."""
    intervalo = 1.96 / np.sqrt(len(datos))
    correlaciones = {}
    for lag in range(1, lags + 1):
        r = float(np.corrcoef(datos[:-lag], datos[lag:])[0, 1])
        correlaciones[f"lag_{lag}"] = r

    max_abs = max(abs(r) for r in correlaciones.values())
    return ResultadoTest(
        nombre="autocorrelacion",
        serie=serie,
        estadistico=max_abs,
        p_valor=float("nan"),
        aceptado=max_abs < intervalo,
        detalle={"intervalo_confianza": float(intervalo), **correlaciones},
    )


def validar_series_climaticas(
    precipitacion_anual: np.ndarray,
    fusion_anual: np.ndarray,
    afluente_mensual: np.ndarray,
) -> ReporteValidacion:
    """Corre la batería completa de tests sobre las tres series de entrada."""
    tests = (
        test_chi_cuadrada_gamma(precipitacion_anual, "precipitacion"),
        test_ks_gamma(precipitacion_anual, "precipitacion"),
        test_autocorrelacion(precipitacion_anual, "precipitacion"),
        test_ks_normal(fusion_anual, "fusion"),
        test_autocorrelacion(fusion_anual, "fusion"),
        test_ks_normal(afluente_mensual.ravel(), "afluente"),
    )
    return ReporteValidacion(
        aceptado=all(t.aceptado for t in tests),
        tests=tests,
    )
