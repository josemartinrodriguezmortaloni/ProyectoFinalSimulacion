from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class EstadoEmbalse:
    """Snapshot del estado del embalse en un momento."""
    tiempo_dias: int
    volumen_hm3: float
    altura_m: float
    energia_generada_gwh: float
    riego_entregado_hm3: float
    satisfaccion_riego: float
    en_crisis: bool


@dataclass
class SeriesClimaticas:
    """Series hidrológicas generadas para toda la campaña."""
    precipitacion: np.ndarray
    fusion: np.ndarray
    demanda: np.ndarray
    temperatura: np.ndarray


@dataclass
class ResultadoSimulacion:
    """Resultado consolidado de la campaña completa."""
    resultados: pd.DataFrame
    reporte_validacion: dict
