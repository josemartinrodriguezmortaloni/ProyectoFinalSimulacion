"""Tests del núcleo funcional: conversión, generación, estadística y KPIs."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from simulador.core import conversion, estadistica, generacion, kpis
from simulador.persistencia import esquemas


# ----------------------------------------------------------- conversión
class TestConversion:
    CUENCA = conversion.ParametrosCuenca(area_m2=5_600_000_000)

    def test_volumen_entrada_coincide_con_ejemplo_de_clase(self) -> None:
        """Mismo ejemplo que el encabezado de la simulación original."""
        volumen = conversion.volumen_entrada_hm3(
            lluvia_mm_mes=230 / 12,
            nieve_mm_mes=150 / 12,
            caudal_m3s=30.0,
            cuenca=self.CUENCA,
        )
        # 107.33 (lluvia) + 70.0 (nieve) + 77.76 (afluente) hm³
        assert volumen == pytest.approx(255.09, abs=0.01)

    def test_distribuir_uniforme_conserva_el_total(self) -> None:
        mensual = conversion.distribuir_uniforme(240.0)
        assert mensual.sum() == pytest.approx(240.0)
        assert np.allclose(mensual, 20.0)

    def test_distribuir_estacional_conserva_el_total(self) -> None:
        mensual = conversion.distribuir_estacional(
            240.0, conversion.PESOS_FUSION_MENDOZA
        )
        assert mensual.sum() == pytest.approx(240.0)
        assert mensual[0] > mensual[6]  # verano > invierno

    def test_pesos_estacionales_tienen_media_uno(self) -> None:
        assert conversion.PESOS_FUSION_MENDOZA.sum() == pytest.approx(12.0)
        assert conversion.PESOS_LLUVIA_MENDOZA.sum() == pytest.approx(12.0)

    def test_entradas_mensuales_vectorizada_equivale_a_escalar(self) -> None:
        lluvia = np.full(12, 19.0)
        nieve = np.full(12, 12.0)
        afluente = np.full(12, 30.0)
        vector = conversion.entradas_mensuales_hm3(
            lluvia, nieve, afluente, self.CUENCA
        )
        escalar = conversion.volumen_entrada_hm3(19.0, 12.0, 30.0, self.CUENCA)
        assert np.allclose(vector, escalar)


# ----------------------------------------------------------- generación
class TestGeneracion:
    def test_series_reproducibles_con_mismo_seed(self) -> None:
        series_a = generacion.generar_series_climaticas(
            np.random.default_rng(7), n_anios=5
        )
        series_b = generacion.generar_series_climaticas(
            np.random.default_rng(7), n_anios=5
        )
        pd.testing.assert_frame_equal(series_a, series_b)

    def test_formato_largo_y_esquema(self) -> None:
        series = generacion.generar_series_climaticas(
            np.random.default_rng(0), n_anios=3
        )
        assert len(series) == 3 * 12
        esquemas.validar_esquema(series, esquemas.ESQUEMA_SERIES, "series")

    def test_rangos_fisicos(self) -> None:
        series = generacion.generar_series_climaticas(
            np.random.default_rng(1), n_anios=50
        )
        assert (series["afluente_m3s"] >= 0).all()
        assert (series["demanda_hm3"] >= 0).all()
        assert series["fusion_anual_mm"].between(50, 300).all()
        assert series["precipitacion_anual_mm"].between(0, 600).all()


# ----------------------------------------------------------- estadística
class TestEstadistica:
    def test_gate_acepta_series_bien_generadas(self) -> None:
        rng = np.random.default_rng(42)
        params = generacion.ParametrosClimaticos()
        reporte = estadistica.validar_series_climaticas(
            generacion.generar_precipitacion_anual(rng, 500, params),
            generacion.generar_fusion_anual(rng, 500, params),
            generacion.generar_afluentes_mensuales(rng, 500, params),
        )
        assert reporte.aceptado

    def test_chi_cuadrada_rechaza_distribucion_incorrecta(self) -> None:
        uniformes = np.random.default_rng(0).uniform(0, 600, 500)
        resultado = estadistica.test_chi_cuadrada_gamma(uniformes, "uniforme")
        assert not resultado.aceptado

    def test_autocorrelacion_detecta_dependencia(self) -> None:
        rng = np.random.default_rng(3)
        ruido = rng.normal(0, 1, 500)
        correlacionada = np.cumsum(ruido)  # paseo aleatorio: muy dependiente
        resultado = estadistica.test_autocorrelacion(correlacionada, "paseo")
        assert not resultado.aceptado

    def test_reporte_serializable(self) -> None:
        rng = np.random.default_rng(11)
        resultado = estadistica.test_ks_normal(rng.normal(0, 1, 200), "x")
        reporte = estadistica.ReporteValidacion(
            aceptado=resultado.aceptado, tests=(resultado,)
        )
        assert "tests" in reporte.a_dict()


# ----------------------------------------------------------------- KPIs
class TestKpis:
    @staticmethod
    def _resultados_sinteticos() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "mes": range(4),
                "Total Satisfaccion Riego": [1.0, 0.8, 0.6, 0.4],
                "Total Energia GWh": [10.0, 10.0, 10.0, 10.0],
                "Total Ingresos Energia": [1000.0] * 4,
                "Total Porcentaje de Llenado Completo": [0.7, 0.45, 0.25, 0.6],
                "Total Riego Entregado": [100.0] * 4,
                "Potrerillos Satisfaccion Riego": [0.9, 0.9, 0.9, 0.9],
            }
        )

    def test_calcular_kpis(self) -> None:
        indicadores = kpis.calcular_kpis(self._resultados_sinteticos())
        assert indicadores.energia_total_gwh == pytest.approx(40.0)
        assert indicadores.meses_crisis == 1  # 0.25 < 0.30
        assert indicadores.meses_alerta == 1  # 0.45 en [0.30, 0.50)
        assert indicadores.satisfaccion_por_dique == {
            "Potrerillos": pytest.approx(0.9)
        }

    def test_puntuar_corridas_ordena_por_score(self) -> None:
        tabla = pd.DataFrame(
            {
                "id_corrida": ["a", "b"],
                "horizonte_meses": [120, 120],
                "satisfaccion_riego_media": [0.9, 0.5],
                "energia_total_gwh": [100.0, 100.0],
                "meses_crisis": [0, 24],
                "meses_alerta": [0, 0],
            }
        )
        ranking = kpis.puntuar_corridas(tabla, kpis.PesosScore())
        assert ranking.iloc[0]["id_corrida"] == "a"
        assert ranking.iloc[0]["score"] > ranking.iloc[1]["score"]


# ------------------------------------------------------------- esquemas
class TestEsquemas:
    def test_columna_faltante_lanza_error(self) -> None:
        incompleto = pd.DataFrame({"mes": [0]})
        with pytest.raises(esquemas.EsquemaInvalidoError, match="faltan columnas"):
            esquemas.validar_esquema(
                incompleto, esquemas.ESQUEMA_ESCENARIO, "escenario"
            )

    def test_columna_no_numerica_lanza_error(self) -> None:
        invalido = pd.DataFrame(
            {"mes": [0], "entrada_agua_hm3": ["mucha"], "temperatura_c": [20.0]}
        )
        with pytest.raises(esquemas.EsquemaInvalidoError, match="no numéricas"):
            esquemas.validar_esquema(
                invalido, esquemas.ESQUEMA_ESCENARIO, "escenario"
            )
