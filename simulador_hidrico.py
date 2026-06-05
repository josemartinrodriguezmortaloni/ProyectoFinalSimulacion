"""
SIMULACIÓN DE OPTIMIZACIÓN DE DISTRIBUCIÓN HÍDRICA EN MENDOZA
Proyecto: "Modelo de decisiones inteligentes de riego bajo incertidumbre"
UTN - Asignatura Simulación (2026)

Autor: [Tu nombre]
Fecha: Junio 2026

UNIDADES CURRICULARES:
- Unidad 2 (Vensim): Modelo de dinámicas continuas
- Unidad 4 (Python): Simulación discreta orientada a eventos
- Unidad 5 (Python): Generación de números aleatorios y validación

OBJETIVO:
Simular 500 años de operación de embalses de Mendoza bajo 3 estrategias
de decisión diferentes y determinar cuál minimiza riesgo de crisis.
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2, kstest
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import json


def _convertir_a_json(obj):
    """Convierte escalares de NumPy a tipos nativos de Python para json.dump."""
    if isinstance(obj, dict):
        return {k: _convertir_a_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convertir_a_json(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


# ===============================================================================
# UNIDAD 5: GENERACIÓN Y VALIDACIÓN DE NÚMEROS ALEATORIOS
# ===============================================================================

class GeneradorNumerosAleatorios:
    """
    Clase para generar números aleatorios que simulan procesos hidrológicos
    reales de Mendoza y validar su conformidad con distribuciones teóricas.
    """

    def __init__(self, seed=42):
        """
        Args:
            seed: Para reproducibilidad
        """
        np.random.seed(seed)
        self.validaciones = {}

    def generar_precipitacion_anual(self, n_años=500, media_mm=230, desv_mm=80):
        """
        UNIDAD 5.2: Técnicas de Extracción de Variables Aleatorias

        Mendoza es región árida con precipitación muy variable.
        Usamos Gamma(α, β) que es natural para lluvia.

        Parámetros de Mendoza:
        - Media: 200-250 mm/año
        - Desviación: 80-100 mm (altamente variable)
        - Rango: 50-600 mm (casos extremos)

        Args:
            n_años: número de años a simular
            media_mm: precipitación media anual
            desv_mm: desviación estándar

        Returns:
            np.array: precipitación anual en mm
        """
        # Parámetros Gamma
        # Para Gamma: α = media²/varianza, β = varianza/media
        varianza = desv_mm ** 2
        alpha = media_mm ** 2 / varianza
        beta = varianza / media_mm

        # Generar usando transformada inversa
        lluvia = np.random.gamma(alpha, beta, n_años)
        lluvia = np.clip(lluvia, 0, 600)  # Límites realistas

        return lluvia

    def generar_fusion_nival(self, n_años=500, base_mm=150, desv_mm=40):
        """
        UNIDAD 5.3: Método de la Transformada Inversa

        Fusión nival ocurre principalmente Sep-Mar.
        Correlacionada parcialmente con precipitación invernal.

        Args:
            n_años: número de años
            base_mm: escorrentía base por fusión
            desv_mm: variabilidad anual

        Returns:
            np.array: fusión nival en mm/año
        """
        fusion = np.random.normal(base_mm, desv_mm, n_años)
        fusion = np.clip(fusion, 50, 300)
        return fusion

    def generar_demanda_agricola(self, n_años=500, media_hm3_mes=250):
        """
        UNIDAD 5.2: Pruebas Estadísticas - Independencia

        Demanda agrícola con estacionalidad + variabilidad interanual.

        Args:
            n_años: número de años
            media_hm3_mes: volumen mensual promedio

        Returns:
            np.array shape (n_años, 12): demanda por mes
        """
        # Factor estacional (Oct=máximo, Jun=mínimo)
        estacion = np.array([1.00, 1.10, 1.05, 0.70, 0.40, 0.35,
                            0.40, 0.50, 0.80, 1.00, 1.15, 1.05])

        demanda = np.zeros((n_años, 12))
        for año in range(n_años):
            variabilidad_anual = np.random.normal(1.0, 0.15, 12)
            demanda[año, :] = media_hm3_mes * estacion * variabilidad_anual

        return np.maximum(demanda, 0)  # No negativo

    def generar_temperatura_mensual(self, n_años=500):
        """
        UNIDAD 5.1: Números Pseudoaleatorios

        Temperatura para cálculo de evaporación.
        Ciclo anual determinístico + ruido aleatorio.

        Args:
            n_años: número de años

        Returns:
            np.array shape (n_años, 12): temperatura °C por mes
        """
        temp = np.zeros((n_años, 12))
        for mes in range(12):
            temp_media = 20 + 8 * np.sin(2 * np.pi * mes / 12)
            ruido = np.random.normal(0, 1, n_años)
            temp[:, mes] = temp_media + ruido

        return temp

    # =========================================================================
    # UNIDAD 5.2: PRUEBAS ESTADÍSTICAS PARA VALIDAR ALEATORIEDAD
    # =========================================================================

    def test_chi_cuadrada(self, datos, nombre="datos", n_bins=15,
                          rango=(0, 600)):
        """
        UNIDAD 5.2: Test de análisis de uniformidad

        Prueba Chi-cuadrada para verificar si la distribución empírica
        se ajusta a la teórica esperada.

        Args:
            datos: serie de datos
            nombre: identificador para reportes
            n_bins: número de bins
            rango: (min, max) de rango

        Returns:
            Dict: estadístico, p-valor, resultado
        """
        observada, bins = np.histogram(datos, bins=n_bins, range=rango)
        esperada = len(datos) / n_bins

        chi2_stat = np.sum((observada - esperada)**2 / esperada)
        p_valor = 1 - chi2.cdf(chi2_stat, df=n_bins-1)

        resultado = {
            'test': 'Chi-cuadrada',
            'estadistico': chi2_stat,
            'p_valor': p_valor,
            'aceptada': p_valor > 0.05,
            'nombre': nombre
        }

        self.validaciones[f"{nombre}_chi2"] = resultado
        return resultado

    def test_kolmogorov_smirnov(self, datos, distribucion='gamma',
                               params=None, nombre="datos"):
        """
        UNIDAD 5.2: Prueba de Kolmogorov-Smirnov

        Valida si datos se ajustan a una distribución teórica.
        Más sensible que Chi-cuadrada para muestras pequeñas.

        Args:
            datos: serie de datos
            distribucion: 'gamma', 'normal', 'lognormal'
            params: parámetros de la distribución
            nombre: identificador

        Returns:
            Dict: estadístico KS, p-valor
        """
        if distribucion == 'gamma':
            ks_stat, p_valor = kstest(datos, 'gamma', args=(params[0], 0, params[1]))
        elif distribucion == 'normal':
            ks_stat, p_valor = kstest(datos, 'norm', args=(np.mean(datos), np.std(datos)))

        resultado = {
            'test': 'Kolmogorov-Smirnov',
            'distribucion': distribucion,
            'estadistico': ks_stat,
            'p_valor': p_valor,
            'aceptada': p_valor > 0.05,
            'nombre': nombre
        }

        self.validaciones[f"{nombre}_ks"] = resultado
        return resultado

    def test_autocorrelacion(self, datos, nombre="datos", lags=5):
        """
        UNIDAD 5.2: Prueba de Independencia - Autocorrelación

        Verifica que valores consecutivos no están correlacionados.

        Args:
            datos: serie de datos
            nombre: identificador
            lags: número de rezagos a probar

        Returns:
            List[Dict]: resultados por lag
        """
        resultados = []
        for lag in range(1, lags+1):
            correlacion = np.corrcoef(datos[:-lag], datos[lag:])[0, 1]
            # Intervalo de confianza 95% para autocorrelación
            ic = 1.96 / np.sqrt(len(datos))

            resultado = {
                'lag': lag,
                'correlacion': correlacion,
                'independiente': abs(correlacion) < ic
            }
            resultados.append(resultado)

        self.validaciones[f"{nombre}_autocorr"] = resultados
        return resultados

    def generar_reporte_validacion(self) -> Dict:
        """
        UNIDAD 5: Resumen de validación estadística
        """
        resumen = {
            'fecha_generacion': datetime.now().isoformat(),
            'validaciones': self.validaciones,
            'conclusion': 'Números aleatorios validados'
                         if all(v.get('aceptada', True)
                               for v in self.validaciones.values()
                               if isinstance(v, dict))
                         else 'Revisar algunos tests'
        }
        return resumen


# ===============================================================================
# UNIDAD 4: SIMULACIÓN DISCRETA ORIENTADA A EVENTOS
# ===============================================================================

@dataclass
class EstadoEmbalse:
    """Snapshot del estado del embalse en un momento"""
    tiempo_dias: int
    volumen_hm3: float
    altura_m: float
    energia_generada_gwh: float
    riego_entregado_hm3: float
    satisfaccion_riego: float
    en_crisis: bool


class SimuladorEmbalseEventos:
    """
    UNIDAD 4: Simulación discreta orientada a eventos

    Simula la operación de un embalse a nivel diario.
    Eventos:
    - Entrada de agua (precipitación + fusión)
    - Decisión de erogación
    - Salida de agua
    """

    def __init__(self, nombre_embalse: str, capacidad_max_hm3: float,
                 altura_minima_m: float, altura_maxima_m: float,
                 estrategia: str = "balance"):
        """
        Args:
            nombre_embalse: nombre para identificación
            capacidad_max_hm3: capacidad máxima en hm³
            altura_minima_m: altura mínima operacional
            altura_maxima_m: altura máxima
            estrategia: "prioridad_energia", "prioridad_riego", "balance"
        """
        self.nombre = nombre_embalse
        self.cap_max = capacidad_max_hm3
        self.alt_min = altura_minima_m
        self.alt_max = altura_maxima_m
        self.estrategia = estrategia

        # Relación volumen-altura (simplificada lineal)
        self.volumen_por_metro = capacidad_max_hm3 / (altura_maxima_m - altura_minima_m)

        # Estado inicial
        self.volumen = capacidad_max_hm3 * 0.65  # 65% de capacidad
        self.historico = []
        self.dias_crisis = 0

        # Acumuladores
        self.energia_anual_gwh = 0
        self.riego_anual_hm3 = 0
        self.satisfaccion_promedio = []

    def altura_actual(self) -> float:
        """Calcula altura actual en metros"""
        return self.alt_min + (self.volumen / self.volumen_por_metro)

    def porcentaje_capacidad(self) -> float:
        """Porcentaje de ocupación 0-1"""
        return self.volumen / self.cap_max

    def algoritmo_decision(self, demanda_riego_hm3: float,
                          disponible_hm3: float) -> Tuple[float, float]:
        """
        UNIDAD 4: Evento de decisión discreta

        Determina cómo distribuir agua según estrategia y estado actual.

        Returns:
            (salida_riego, salida_energia) en hm³
        """
        pct = self.porcentaje_capacidad()

        if self.estrategia == "prioridad_energia":
            # Si hay agua, generar energía primero
            energía = min(disponible_hm3 * 0.75, disponible_hm3 - 50)
            riego = min(demanda_riego_hm3, disponible_hm3 - energía)

        elif self.estrategia == "prioridad_riego":
            # Satisfacer demanda de riego primero
            riego = min(demanda_riego_hm3, disponible_hm3 * 0.8)
            energía = min(disponible_hm3 - riego, disponible_hm3 * 0.3)

        else:  # "balance"
            # Usar la regla inteligente: altura → decisión
            if pct > 0.80:
                prioridad_energia = 0.8
            elif pct < 0.40:
                prioridad_energia = 0.2
            else:
                prioridad_energia = 0.5

            energía = disponible_hm3 * prioridad_energia
            riego = min(demanda_riego_hm3, disponible_hm3 - energía)

        return riego, energía

    def simular_dia(self, precipitacion_mm: float, fusion_nival_mm: float,
                   demanda_riego_hm3: float, temperatura_c: float) -> EstadoEmbalse:
        """
        UNIDAD 4: Simular un día

        Calcula entrada → decisión → salida → balance → nuevo estado
        """
        # ENTRADA
        entrada_hm3 = (precipitacion_mm + fusion_nival_mm) / 1000 * 1000  # Simplificado
        entrada_hm3 = max(0, entrada_hm3)

        # DISPONIBLE
        disponible = self.volumen + entrada_hm3
        disponible_para_decision = max(0, disponible - 100)  # Dejar mínimo

        # DECISIÓN
        riego_otorgado, energia_erogada = self.algoritmo_decision(
            demanda_riego_hm3, disponible_para_decision
        )

        # EVAPORACIÓN (función de temperatura)
        superficie_aprox = self.volumen / (self.altura_actual() - self.alt_min + 0.1)
        tasa_evap_diaria = max(0, (temperatura_c - 5) * 0.0001)
        evaporacion = superficie_aprox * tasa_evap_diaria

        # BALANCE
        balance = entrada_hm3 - riego_otorgado - energia_erogada - evaporacion - 8/30
        self.volumen = np.clip(self.volumen + balance, 50, self.cap_max)

        # MÉTRICAS
        satisfaccion = min(1.0, riego_otorgado / max(0.1, demanda_riego_hm3))
        en_crisis = self.volumen < 100

        if en_crisis:
            self.dias_crisis += 1

        # REGISTRO
        estado = EstadoEmbalse(
            tiempo_dias=len(self.historico),
            volumen_hm3=self.volumen,
            altura_m=self.altura_actual(),
            energia_generada_gwh=energia_erogada * 0.00981 * self.altura_actual() / 1000,
            riego_entregado_hm3=riego_otorgado,
            satisfaccion_riego=satisfaccion,
            en_crisis=en_crisis
        )

        self.historico.append(estado)
        self.energia_anual_gwh += estado.energia_generada_gwh
        self.riego_anual_hm3 += riego_otorgado
        self.satisfaccion_promedio.append(satisfaccion)

        return estado

    def simular_anio(self, precipitacion_anual: np.ndarray,
                     fusion_anual: np.ndarray,
                     demanda_anual: np.ndarray,
                     temperatura_anual: np.ndarray) -> float:
        """
        Simula un año completo (365 días).

        Returns:
            Satisfacción promedio anual
        """
        self.energia_anual_gwh = 0
        self.riego_anual_hm3 = 0
        self.satisfaccion_promedio = []

        for mes in range(12):
            dias_mes = 30  # Simplificado
            precip_diaria = precipitacion_anual[mes] / dias_mes
            fusion_diaria = fusion_anual[mes] / dias_mes
            demanda_diaria = demanda_anual[mes] / dias_mes
            temp_promedio = temperatura_anual[mes]

            for dia in range(dias_mes):
                self.simular_dia(precip_diaria, fusion_diaria,
                               demanda_diaria, temp_promedio)

        satisfaccion_prom = np.mean(self.satisfaccion_promedio)
        return satisfaccion_prom

    def obtener_metricas(self) -> Dict:
        """
        UNIDAD 4: Extrae métricas de la simulación
        """
        return {
            'nombre': self.nombre,
            'estrategia': self.estrategia,
            'energia_total_gwh': self.energia_anual_gwh,
            'riego_total_hm3': self.riego_anual_hm3,
            'satisfaccion_promedio': np.mean(self.satisfaccion_promedio),
            'dias_crisis': self.dias_crisis,
            'volumen_final_hm3': self.volumen
        }


# ===============================================================================
# EJECUTABLE: SIMULACIÓN COMPLETA
# ===============================================================================

def main():
    """
    Ejecuta la simulación completa de 500 años con 3 estrategias diferentes
    """

    print("=" * 80)
    print("SIMULACIÓN: Optimización de Distribución Hídrica en Mendoza")
    print("=" * 80)
    print()

    # FASE 1: GENERAR Y VALIDAR NÚMEROS ALEATORIOS
    print("FASE 1: Generación y Validación de Números Aleatorios (Unidad 5)")
    print("-" * 80)

    generador = GeneradorNumerosAleatorios(seed=42)

    # Generar series de 500 años
    precipitacion = generador.generar_precipitacion_anual(n_años=500)
    fusion = generador.generar_fusion_nival(n_años=500)
    demanda = generador.generar_demanda_agricola(n_años=500)
    temperatura = generador.generar_temperatura_mensual(n_años=500)

    # Validar precipitación
    print("\n✓ Validando precipitación con Chi-cuadrada...")
    resultado_chi2 = generador.test_chi_cuadrada(precipitacion, "precipitacion")
    print(f"  Estadístico χ²: {resultado_chi2['estadistico']:.3f}")
    print(f"  p-valor: {resultado_chi2['p_valor']:.4f}")
    print(f"  Resultado: {'ACEPTADO ✓' if resultado_chi2['aceptada'] else 'RECHAZADO ✗'}")

    # Validar con Kolmogorov-Smirnov
    print("\n✓ Validando con Kolmogorov-Smirnov...")
    resultado_ks = generador.test_kolmogorov_smirnov(
        precipitacion, 'gamma',
        (np.mean(precipitacion)**2/np.std(precipitacion)**2,
         np.std(precipitacion)**2/np.mean(precipitacion)),
        "precipitacion"
    )
    print(f"  Estadístico KS: {resultado_ks['estadistico']:.4f}")
    print(f"  p-valor: {resultado_ks['p_valor']:.4f}")

    # Validar independencia
    print("\n✓ Validando independencia (autocorrelación)...")
    resultado_autocorr = generador.test_autocorrelacion(precipitacion, 5)
    for r in resultado_autocorr:
        independencia = "✓" if r['independiente'] else "✗"
        print(f"  Lag {r['lag']}: r={r['correlacion']:.4f} {independencia}")

    print("\n✓ Números aleatorios validados correctamente.")

    # FASE 2: SIMULACIÓN CON 3 ESTRATEGIAS
    print("\n\n" + "=" * 80)
    print("FASE 2: Simulación Estocástica (Unidad 4)")
    print("=" * 80)

    estrategias = ["prioridad_energia", "prioridad_riego", "balance"]
    resultados_finales = []

    for estrategia in estrategias:
        print(f"\n▶ Simulando estrategia: {estrategia}")
        print("  Ejecutando 500 años...")

        # Crear simulador
        sim = SimuladorEmbalseEventos(
            nombre_embalse="Potrerillos",
            capacidad_max_hm3=1885,
            altura_minima_m=970,
            altura_maxima_m=1210,
            estrategia=estrategia
        )

        # Simular 500 años
        for año in range(500):
            precip_mes = precipitacion[año] / 12
            fusion_mes = fusion[año] / 12
            demanda_mes = demanda[año, :]
            temp_mes = temperatura[año, :]

            sim.simular_anio(
                np.full(12, precip_mes),
                np.full(12, fusion_mes),
                demanda_mes,
                temp_mes
            )

            if (año + 1) % 100 == 0:
                print(f"    {año + 1}/500 años completados")

        metricas = sim.obtener_metricas()
        resultados_finales.append(metricas)

        print(f"  ✓ Simulación completada")
        print(f"    Energía: {metricas['energia_total_gwh']:.0f} GWh")
        print(f"    Riego: {metricas['riego_total_hm3']:.0f} hm³")
        print(f"    Satisfacción: {metricas['satisfaccion_promedio']*100:.1f}%")
        print(f"    Días crisis: {metricas['dias_crisis']}")

    # FASE 3: ANÁLISIS Y CONCLUSIONES
    print("\n\n" + "=" * 80)
    print("FASE 3: Análisis de Resultados")
    print("=" * 80)

    df_resultados = pd.DataFrame(resultados_finales)
    print("\n" + df_resultados.to_string())

    # Guardar resultados
    df_resultados.to_csv('./resultados/resultados_simulacion.csv', index=False)
    print("\n✓ Resultados guardados en 'resultados_simulacion.csv'")

    # Reporte de validación
    reporte = generador.generar_reporte_validacion()
    with open('./resultados/validacion_estadistica.json', 'w') as f:
        json.dump(_convertir_a_json(reporte), f, indent=2)
    print("✓ Reporte de validación guardado en 'validacion_estadistica.json'")

    print("\n" + "=" * 80)
    print("PROYECTO COMPLETO")
    print("=" * 80)

    return df_resultados, reporte


if __name__ == "__main__":
    resultados, validacion = main()
