from typing import Dict, Tuple

import numpy as np

from simulador.config import ConfigEmbalse
from simulador.models import EstadoEmbalse


class SimuladorEmbalseEventos:
    """
    Simulación discreta orientada a eventos de un embalse (Unidad 4).
    """

    def __init__(self, embalse: ConfigEmbalse, estrategia: str = "balance"):
        self.nombre = embalse.nombre
        self.cap_max = embalse.capacidad_max_hm3
        self.alt_min = embalse.altura_minima_m
        self.alt_max = embalse.altura_maxima_m
        self.estrategia = estrategia

        self.volumen_por_metro = embalse.capacidad_max_hm3 / (
            embalse.altura_maxima_m - embalse.altura_minima_m
        )

        self.volumen = embalse.capacidad_max_hm3 * 0.65
        self.historico: list[EstadoEmbalse] = []
        self.dias_crisis = 0

        self.energia_anual_gwh = 0.0
        self.riego_anual_hm3 = 0.0
        self.satisfaccion_promedio: list[float] = []

    def altura_actual(self) -> float:
        return self.alt_min + (self.volumen / self.volumen_por_metro)

    def porcentaje_capacidad(self) -> float:
        return self.volumen / self.cap_max

    def algoritmo_decision(
        self, demanda_riego_hm3: float, disponible_hm3: float
    ) -> Tuple[float, float]:
        pct = self.porcentaje_capacidad()

        if self.estrategia == "prioridad_energia":
            energía = min(disponible_hm3 * 0.75, disponible_hm3 - 50)
            riego = min(demanda_riego_hm3, disponible_hm3 - energía)

        elif self.estrategia == "prioridad_riego":
            riego = min(demanda_riego_hm3, disponible_hm3 * 0.8)
            energía = min(disponible_hm3 - riego, disponible_hm3 * 0.3)

        else:
            if pct > 0.80:
                prioridad_energia = 0.8
            elif pct < 0.40:
                prioridad_energia = 0.2
            else:
                prioridad_energia = 0.5

            energía = disponible_hm3 * prioridad_energia
            riego = min(demanda_riego_hm3, disponible_hm3 - energía)

        return riego, energía

    def simular_dia(
        self,
        precipitacion_mm: float,
        fusion_nival_mm: float,
        demanda_riego_hm3: float,
        temperatura_c: float,
    ) -> EstadoEmbalse:
        entrada_hm3 = max(0, (precipitacion_mm + fusion_nival_mm) / 1000 * 1000)

        disponible = self.volumen + entrada_hm3
        disponible_para_decision = max(0, disponible - 100)

        riego_otorgado, energia_erogada = self.algoritmo_decision(
            demanda_riego_hm3, disponible_para_decision
        )

        superficie_aprox = self.volumen / (self.altura_actual() - self.alt_min + 0.1)
        tasa_evap_diaria = max(0, (temperatura_c - 5) * 0.0001)
        evaporacion = superficie_aprox * tasa_evap_diaria

        balance = (
            entrada_hm3 - riego_otorgado - energia_erogada - evaporacion - 8 / 30
        )
        self.volumen = np.clip(self.volumen + balance, 50, self.cap_max)

        satisfaccion = min(1.0, riego_otorgado / max(0.1, demanda_riego_hm3))
        en_crisis = self.volumen < 100

        if en_crisis:
            self.dias_crisis += 1

        estado = EstadoEmbalse(
            tiempo_dias=len(self.historico),
            volumen_hm3=self.volumen,
            altura_m=self.altura_actual(),
            energia_generada_gwh=(
                energia_erogada * 0.00981 * self.altura_actual() / 1000
            ),
            riego_entregado_hm3=riego_otorgado,
            satisfaccion_riego=satisfaccion,
            en_crisis=en_crisis,
        )

        self.historico.append(estado)
        self.energia_anual_gwh += estado.energia_generada_gwh
        self.riego_anual_hm3 += riego_otorgado
        self.satisfaccion_promedio.append(satisfaccion)

        return estado

    def simular_anio(
        self,
        precipitacion_anual: np.ndarray,
        fusion_anual: np.ndarray,
        demanda_anual: np.ndarray,
        temperatura_anual: np.ndarray,
    ) -> float:
        self.energia_anual_gwh = 0.0
        self.riego_anual_hm3 = 0.0
        self.satisfaccion_promedio = []

        for mes in range(12):
            dias_mes = 30
            precip_diaria = precipitacion_anual[mes] / dias_mes
            fusion_diaria = fusion_anual[mes] / dias_mes
            demanda_diaria = demanda_anual[mes] / dias_mes
            temp_promedio = temperatura_anual[mes]

            for _ in range(dias_mes):
                self.simular_dia(
                    precip_diaria, fusion_diaria, demanda_diaria, temp_promedio
                )

        return float(np.mean(self.satisfaccion_promedio))

    def obtener_metricas(self) -> Dict:
        return {
            "nombre": self.nombre,
            "estrategia": self.estrategia,
            "energia_total_gwh": self.energia_anual_gwh,
            "riego_total_hm3": self.riego_anual_hm3,
            "satisfaccion_promedio": float(np.mean(self.satisfaccion_promedio)),
            "dias_crisis": self.dias_crisis,
            "volumen_final_hm3": self.volumen,
        }
