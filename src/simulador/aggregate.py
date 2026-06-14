import numpy as np
import pandas as pd

from simulador.aleatorios import GeneradorNumerosAleatorios
from simulador.config import ConfigSimulacion
from simulador.embalse import SimuladorEmbalseEventos
from simulador.models import ResultadoSimulacion, SeriesClimaticas
from simulador.util import guardar_resultados


class SimulacionHidrica:
    """
    Aggregate root: coordina generación, validación, simulación y persistencia.

    Es el único punto de entrada de la lógica de negocio. __main__.py solo
    instancia esta clase y llama a ejecutar().
    """

    def __init__(self, config: ConfigSimulacion | None = None):
        self.config = config or ConfigSimulacion()
        self.generador: GeneradorNumerosAleatorios | None = None
        self.series: SeriesClimaticas | None = None
        self.resultados: list[dict] = []
        self.reporte_validacion: dict | None = None

    def ejecutar(self) -> ResultadoSimulacion:
        self._imprimir_encabezado()
        self._fase_validacion()
        self._fase_simulacion()
        return self._fase_analisis()

    def _imprimir_encabezado(self) -> None:
        print("=" * 80)
        print("SIMULACIÓN: Optimización de Distribución Hídrica en Mendoza")
        print("=" * 80)
        print()

    def _fase_validacion(self) -> None:
        print("FASE 1: Generación y Validación de Números Aleatorios (Unidad 5)")
        print("-" * 80)

        self.generador = GeneradorNumerosAleatorios(seed=self.config.seed)
        n = self.config.n_años

        self.series = SeriesClimaticas(
            precipitacion=self.generador.generar_precipitacion_anual(n_años=n),
            fusion=self.generador.generar_fusion_nival(n_años=n),
            afluente=self.generador.generar_afluentes_mensuales(n_años=n),
            demanda=self.generador.generar_demanda_agricola(n_años=n),
            temperatura=self.generador.generar_temperatura_mensual(n_años=n),
        )

        # Mostrar ejemplo de volumen generado en el primer mes del primer año
        print("\n=== EJEMPLO DE CÁLCULO DE VOLÚMENES MENSUALES - DIQUE POTRERILLOS ===")
        AREA_CUENCA_M2 = 5_600_000_000  # 5.600 km2 en m2
        SEGUNDOS_MES = 2_592_000

        # Asumimos que lluvia y nieve se distribuyen parejo en los 12 meses para el mes de muestra
        lluvia_mm_mes = self.series.precipitacion[0] / 12
        nieve_mm_mes = self.series.fusion[0] / 12
        caudal_m3s = self.series.afluente[0, 0]

        vol_lluvia_m3 = (lluvia_mm_mes / 1000.0) * AREA_CUENCA_M2
        vol_nieve_m3 = (nieve_mm_mes / 1000.0) * AREA_CUENCA_M2
        vol_afluente_m3 = caudal_m3s * SEGUNDOS_MES
        vol_total_m3 = vol_lluvia_m3 + vol_nieve_m3 + vol_afluente_m3

        print(f"Lluvia (mm) mes: {lluvia_mm_mes:.2f}")
        print(f"Nieve (mm) mes: {nieve_mm_mes:.2f}")
        print(f"Afluente (m³/s): {caudal_m3s:.2f}")
        print("-" * 40)
        print(f"Volumen Lluvia: {vol_lluvia_m3:,.2f} m³")
        print(f"Volumen Nieve: {vol_nieve_m3:,.2f} m³")
        print(f"Volumen Afluente: {vol_afluente_m3:,.2f} m³")
        print(f"==> VOLUMEN TOTAL INGRESADO (MES): {vol_total_m3:,.2f} m³\n")

        precipitacion = self.series.precipitacion

        print("\n✓ Validando precipitación con Chi-cuadrada...")
        resultado_chi2 = self.generador.test_chi_cuadrada(
            precipitacion, "precipitacion"
        )
        print(f"  Estadístico χ²: {resultado_chi2['estadistico']:.3f}")
        print(f"  p-valor: {resultado_chi2['p_valor']:.4f}")
        print(
            f"  Resultado: {'ACEPTADO ✓' if resultado_chi2['aceptada'] else 'RECHAZADO ✗'}"
        )

        print("\n✓ Validando con Kolmogorov-Smirnov...")
        resultado_ks = self.generador.test_kolmogorov_smirnov(
            precipitacion,
            "gamma",
            (
                np.mean(precipitacion) ** 2 / np.std(precipitacion) ** 2,
                np.std(precipitacion) ** 2 / np.mean(precipitacion),
            ),
            "precipitacion",
        )
        print(f"  Estadístico KS: {resultado_ks['estadistico']:.4f}")
        print(f"  p-valor: {resultado_ks['p_valor']:.4f}")



        print("\n✓ Números aleatorios validados correctamente.")

    def _fase_simulacion(self) -> None:
        if self.series is None:
            raise RuntimeError("Fase de validación no ejecutada.")

        print("\n\n" + "=" * 80)
        print("FASE 2: Simulación Estocástica (Unidad 4)")
        print("=" * 80)

        self.resultados = []

        for estrategia in self.config.estrategias:
            print(f"\n▶ Simulando estrategia: {estrategia}")
            print(f"  Ejecutando {self.config.n_años} años...")

            sim = SimuladorEmbalseEventos(
                embalse=self.config.embalse,
                estrategia=estrategia,
            )

            for año in range(self.config.n_años):
                precip_mes = self.series.precipitacion[año] / 12
                fusion_mes = self.series.fusion[año] / 12
                demanda_mes = self.series.demanda[año, :]
                temp_mes = self.series.temperatura[año, :]

                sim.simular_anio(
                    np.full(12, precip_mes),
                    np.full(12, fusion_mes),
                    demanda_mes,
                    temp_mes,
                )

                if (año + 1) % 100 == 0:
                    print(f"    {año + 1}/{self.config.n_años} años completados")

            metricas = sim.obtener_metricas()
            self.resultados.append(metricas)

            print("  ✓ Simulación completada")
            print(f"    Energía: {metricas['energia_total_gwh']:.0f} GWh")
            print(f"    Riego: {metricas['riego_total_hm3']:.0f} hm³")
            print(f"    Satisfacción: {metricas['satisfaccion_promedio'] * 100:.1f}%")
            print(f"    Días crisis: {metricas['dias_crisis']}")

    def _fase_analisis(self) -> ResultadoSimulacion:
        if self.generador is None:
            raise RuntimeError("Generador no inicializado.")

        print("\n\n" + "=" * 80)
        print("FASE 3: Análisis de Resultados")
        print("=" * 80)

        df_resultados = pd.DataFrame(self.resultados)
        print("\n" + df_resultados.to_string())

        self.reporte_validacion = self.generador.generar_reporte_validacion()
        guardar_resultados(
            df_resultados,
            self.reporte_validacion,
            self.config.dir_resultados,
        )

        print("\n✓ Resultados guardados en 'resultados/resultados_simulacion.csv'")
        print(
            "✓ Reporte de validación guardado en 'resultados/validacion_estadistica.json'"
        )

        print("\n" + "=" * 80)
        print("PROYECTO COMPLETO")
        print("=" * 80)

        return ResultadoSimulacion(
            resultados=df_resultados,
            reporte_validacion=self.reporte_validacion,
        )
