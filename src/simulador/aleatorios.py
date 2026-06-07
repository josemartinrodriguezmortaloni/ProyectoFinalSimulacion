from datetime import datetime
from typing import Dict, List

import numpy as np
from scipy.stats import chi2, kstest


class GeneradorNumerosAleatorios:
    """
    Genera números aleatorios que simulan procesos hidrológicos de Mendoza
    y valida su conformidad con distribuciones teóricas (Unidad 5).
    """

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.validaciones: dict = {}

    def generar_precipitacion_anual(
        self, n_años: int = 500, media_mm: float = 230, desv_mm: float = 80
    ) -> np.ndarray:
        varianza = desv_mm ** 2
        alpha = media_mm ** 2 / varianza
        beta = varianza / media_mm

        lluvia = np.random.gamma(alpha, beta, n_años)
        return np.clip(lluvia, 0, 600)

    def generar_fusion_nival(
        self, n_años: int = 500, base_mm: float = 150, desv_mm: float = 40
    ) -> np.ndarray:
        fusion = np.random.normal(base_mm, desv_mm, n_años)
        return np.clip(fusion, 50, 300)

    def generar_afluentes_mensuales(
        self, n_años: int = 500, media_m3s: float = 30, desv_m3s: float = 10
    ) -> np.ndarray:
        afluentes = np.random.normal(media_m3s, desv_m3s, (n_años, 12))
        return np.maximum(afluentes, 0)

    def generar_demanda_agricola(
        self, n_años: int = 500, media_hm3_mes: float = 250
    ) -> np.ndarray:
        estacion = np.array([
            1.00, 1.10, 1.05, 0.70, 0.40, 0.35,
            0.40, 0.50, 0.80, 1.00, 1.15, 1.05,
        ])

        demanda = np.zeros((n_años, 12))
        for año in range(n_años):
            variabilidad_anual = np.random.normal(1.0, 0.15, 12)
            demanda[año, :] = media_hm3_mes * estacion * variabilidad_anual

        return np.maximum(demanda, 0)

    def generar_temperatura_mensual(self, n_años: int = 500) -> np.ndarray:
        temp = np.zeros((n_años, 12))
        for mes in range(12):
            temp_media = 20 + 8 * np.sin(2 * np.pi * mes / 12)
            ruido = np.random.normal(0, 1, n_años)
            temp[:, mes] = temp_media + ruido

        return temp

    def test_chi_cuadrada(
        self,
        datos: np.ndarray,
        nombre: str = "datos",
        n_bins: int = 15,
        rango: tuple[float, float] = (0, 600),
    ) -> Dict:
        observada, _ = np.histogram(datos, bins=n_bins, range=rango)
        esperada = len(datos) / n_bins

        chi2_stat = np.sum((observada - esperada) ** 2 / esperada)
        p_valor = 1 - chi2.cdf(chi2_stat, df=n_bins - 1)

        resultado = {
            "test": "Chi-cuadrada",
            "estadistico": chi2_stat,
            "p_valor": p_valor,
            "aceptada": p_valor > 0.05,
            "nombre": nombre,
        }

        self.validaciones[f"{nombre}_chi2"] = resultado
        return resultado

    def test_kolmogorov_smirnov(
        self,
        datos: np.ndarray,
        distribucion: str = "gamma",
        params: tuple | None = None,
        nombre: str = "datos",
    ) -> Dict:
        if distribucion == "gamma":
            ks_stat, p_valor = kstest(datos, "gamma", args=(params[0], 0, params[1]))
        elif distribucion == "normal":
            ks_stat, p_valor = kstest(
                datos, "norm", args=(np.mean(datos), np.std(datos))
            )
        else:
            raise ValueError(f"Distribución no soportada: {distribucion}")

        resultado = {
            "test": "Kolmogorov-Smirnov",
            "distribucion": distribucion,
            "estadistico": ks_stat,
            "p_valor": p_valor,
            "aceptada": p_valor > 0.05,
            "nombre": nombre,
        }

        self.validaciones[f"{nombre}_ks"] = resultado
        return resultado

    def test_autocorrelacion(
        self, datos: np.ndarray, nombre: str = "datos", lags: int = 5
    ) -> List[Dict]:
        resultados = []
        for lag in range(1, lags + 1):
            correlacion = np.corrcoef(datos[:-lag], datos[lag:])[0, 1]
            ic = 1.96 / np.sqrt(len(datos))

            resultados.append({
                "lag": lag,
                "correlacion": correlacion,
                "independiente": abs(correlacion) < ic,
            })

        self.validaciones[f"{nombre}_autocorr"] = resultados
        return resultados

    def generar_reporte_validacion(self) -> Dict:
        return {
            "fecha_generacion": datetime.now().isoformat(),
            "validaciones": self.validaciones,
            "conclusion": (
                "Números aleatorios validados"
                if all(
                    v.get("aceptada", True)
                    for v in self.validaciones.values()
                    if isinstance(v, dict)
                )
                else "Revisar algunos tests"
            ),
        }
