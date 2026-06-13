"""
Python model 'ProyectoGlobalSimulacion(PrimerModeloTerminado).py'
Translated using PySD
"""

from pathlib import Path
import numpy as np

from pysd.py_backend.functions import modulo, if_then_else
from pysd.py_backend.statefuls import Integ
from pysd import Component

__pysd_version__ = "3.14.3"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 120,
    "time_step": lambda: 1,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    The final time for the simulation.
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    The initial time for the simulation.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    The frequency with which output is stored.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Constant",
    comp_subtype="Normal",
)
def time_step():
    """
    The time step for the simulation.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="Salida Riego Potre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "potrerillos_demanda_riego": 1,
        "potrerillos_caudal_regulado": 1,
        "potrerillos_prioridad_energia": 1,
    },
)
def salida_riego_potre():
    return float(
        np.minimum(
            potrerillos_demanda_riego(),
            float(
                np.maximum(
                    0,
                    potrerillos_caudal_regulado()
                    * (1 - potrerillos_prioridad_energia()),
                )
            ),
        )
    )


@component.add(
    name="Agua Del Toro Salida Energia",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_caudal_regulado": 1, "agua_del_toro_salida_riego": 1},
)
def agua_del_toro_salida_energia():
    return float(
        np.maximum(0, agua_del_toro_caudal_regulado() - agua_del_toro_salida_riego())
    )


@component.add(
    name="Agua Del Toro Caudal Regulado",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_disponible": 1,
        "agua_del_toro_porcentaje_capacidad": 1,
        "agua_del_toro_entrada_agua": 1,
    },
)
def agua_del_toro_caudal_regulado():
    """
    Embalse en 65% (objetivo): libera exactamente el caudal entrante Embalse en 90% (muy lleno): libera hasta 50 hm³ extra para hacer espacio Embalse en 40% (bajo): libera hasta 50 hm³ menos para conservar agua
    """
    return float(
        np.minimum(
            agua_del_toro_disponible(),
            float(
                np.maximum(
                    0,
                    agua_del_toro_entrada_agua()
                    + (agua_del_toro_porcentaje_capacidad() - 0.65) * 40,
                )
            ),
        )
    )


@component.add(
    name="Nihuil Caudal Regulado",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "nihuil_disponible": 1,
        "nihuil_porcentaje_capacidad": 1,
        "nihuil_entrada_agua": 1,
    },
)
def nihuil_caudal_regulado():
    """
    Embalse en 65% (objetivo): libera exactamente el caudal entrante Embalse en 90% (muy lleno): libera hasta 50 hm³ extra para hacer espacio Embalse en 40% (bajo): libera hasta 50 hm³ menos para conservar agua
    """
    return float(
        np.minimum(
            nihuil_disponible(),
            float(
                np.maximum(
                    0,
                    nihuil_entrada_agua() + (nihuil_porcentaje_capacidad() - 0.65) * 30,
                )
            ),
        )
    )


@component.add(
    name="Salida Energia Potrerillos",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potrerillos_caudal_regulado": 1, "salida_riego_potre": 1},
)
def salida_energia_potrerillos():
    """
    Agua turbinada en la central hidroeléctrica de Potrerillos (315 MW instalados). Es lo que queda disponible después de satisfacer riego, limitado por la fracción de prioridad energética.
    """
    return float(np.maximum(0, potrerillos_caudal_regulado() - salida_riego_potre()))


@component.add(
    name="Potrerillos Caudal Regulado",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "potrerillos_disponible": 1,
        "potrerillos_porcentaje_capacidad": 1,
        "entrada_agua_potrerillos": 1,
    },
)
def potrerillos_caudal_regulado():
    """
    Embalse en 65% (objetivo): libera exactamente el caudal entrante Embalse en 90% (muy lleno): libera hasta 50 hm³ extra para hacer espacio Embalse en 40% (bajo): libera hasta 50 hm³ menos para conservar agua
    """
    return float(
        np.minimum(
            potrerillos_disponible(),
            float(
                np.maximum(
                    0,
                    entrada_agua_potrerillos()
                    + (potrerillos_porcentaje_capacidad() - 0.65) * 200,
                )
            ),
        )
    )


@component.add(
    name="Agua Del Toro Entrada Agua",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def agua_del_toro_entrada_agua():
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [95, 110, 90, 70, 55, 45, 40, 48, 68, 88, 110, 120],
    )


@component.add(
    name="Nihuil Entrada Agua",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def nihuil_entrada_agua():
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [80, 90, 70, 55, 45, 35, 30, 38, 55, 70, 88, 95],
    )


@component.add(
    name="Carrizal Salida Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "carrizal_demanda_riego": 1,
        "carrizal_caudal_regulado": 1,
        "carrizal_prioridad_energia": 1,
    },
)
def carrizal_salida_riego():
    return float(
        np.minimum(
            carrizal_demanda_riego(),
            float(
                np.maximum(
                    0, carrizal_caudal_regulado() * (1 - carrizal_prioridad_energia())
                )
            ),
        )
    )


@component.add(
    name="Carrizal Caudal Regulado",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "carrizal_disponible": 1,
        "carrizal_entrada_agua": 1,
        "carrizal_porcentaje_capacidad": 1,
    },
)
def carrizal_caudal_regulado():
    """
    Embalse en 65% (objetivo): libera exactamente el caudal entrante Embalse en 90% (muy lleno): libera hasta 50 hm³ extra para hacer espacio Embalse en 40% (bajo): libera hasta 50 hm³ menos para conservar agua
    """
    return float(
        np.minimum(
            carrizal_disponible(),
            float(
                np.maximum(
                    0,
                    carrizal_entrada_agua()
                    + (carrizal_porcentaje_capacidad() - 0.65) * 25,
                )
            ),
        )
    )


@component.add(
    name="Entrada Agua Potrerillos",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def entrada_agua_potrerillos():
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [300, 350, 280, 220, 170, 140, 120, 130, 180, 240, 320, 370],
    )


@component.add(
    name="Nihuil Salida Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "nihuil_demanda_riego": 1,
        "nihuil_caudal_regulado": 1,
        "nihuil_prioridad_energia": 1,
    },
)
def nihuil_salida_riego():
    return float(
        np.minimum(
            nihuil_demanda_riego(),
            float(
                np.maximum(
                    0, nihuil_caudal_regulado() * (1 - nihuil_prioridad_energia())
                )
            ),
        )
    )


@component.add(
    name="Agua Del Toro Salida Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_demanda_riego": 1,
        "agua_del_toro_caudal_regulado": 1,
        "agua_del_toro_prioridad_energia": 1,
    },
)
def agua_del_toro_salida_riego():
    return float(
        np.minimum(
            agua_del_toro_demanda_riego(),
            float(
                np.maximum(
                    0,
                    agua_del_toro_caudal_regulado()
                    * (1 - agua_del_toro_prioridad_energia()),
                )
            ),
        )
    )


@component.add(
    name="Carrizal Entrada Agua",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def carrizal_entrada_agua():
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [65, 75, 60, 48, 35, 28, 25, 30, 45, 60, 75, 80],
    )


@component.add(
    name="Carrizal Salida Energia",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_caudal_regulado": 1, "carrizal_salida_riego": 1},
)
def carrizal_salida_energia():
    """
    Agua turbinada en la central hidroeléctrica de Potrerillos (315 MW instalados). Es lo que queda disponible después de satisfacer riego, limitado por la fracción de prioridad energética.
    """
    return float(np.maximum(0, carrizal_caudal_regulado() - carrizal_salida_riego()))


@component.add(
    name="Nihuil Salida Energia",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_caudal_regulado": 1, "nihuil_salida_riego": 1},
)
def nihuil_salida_energia():
    """
    Agua turbinada en la central hidroeléctrica de Potrerillos (315 MW instalados). Es lo que queda disponible después de satisfacer riego, limitado por la fracción de prioridad energética.
    """
    return float(np.maximum(0, nihuil_caudal_regulado() - nihuil_salida_riego()))


@component.add(
    name="Agua Del Toro Cabeza Neta",
    units="m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_porcentaje_capacidad": 1},
)
def agua_del_toro_cabeza_neta():
    """
    Energía hidráulica real y efectiva de Agua del Toro disponible para generar electricidad. Mínimo 60 m, máximo 180 m.
    """
    return 60 + 120 * agua_del_toro_porcentaje_capacidad()


@component.add(
    name="Agua Del Toro Cap Max",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def agua_del_toro_cap_max():
    """
    Capacidad máxima del embalse Agua Del Toro.
    """
    return 380


@component.add(
    name="Agua Del Toro Consumo Urbano",
    units="hm3/mes",
    comp_type="Constant",
    comp_subtype="Normal",
)
def agua_del_toro_consumo_urbano():
    """
    Consumo urbano de General Alvear y zona del Diamante.
    """
    return 3


@component.add(
    name="Agua Del Toro Demanda Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def agua_del_toro_demanda_riego():
    """
    Demanda estacional de riego del oasis del Tunuyán (zona Este de Mendoza, viticultura y fruticultura).
    """
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [84, 92, 88, 59, 34, 29, 29, 42, 67, 84, 96, 88],
    )


@component.add(
    name="Agua Del Toro Disponible",
    units="hm3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_volumen_embalse": 1, "agua_del_toro_vol_min": 1},
)
def agua_del_toro_disponible():
    """
    Agua realmente disponible para erogar (total menos el volumen muerto). Garantiza que el embalse nunca quede completamente vacío.
    """
    return float(
        np.maximum(0, agua_del_toro_volumen_embalse() - agua_del_toro_vol_min())
    )


@component.add(
    name="Agua Del Toro Evaporacion",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_evap_mensual": 1},
)
def agua_del_toro_evaporacion():
    """
    Pérdida por evaporación superficial. Factor 0.6 por alta altitud (menor temperatura real que el promedio de Mendoza).
    """
    return tasa_evap_mensual() * 0.6


@component.add(
    name="Agua Del Toro Generacion GWh",
    units="GWh/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_salida_energia": 1, "agua_del_toro_cabeza_neta": 1},
)
def agua_del_toro_generacion_gwh():
    """
    Energía generada mensualmente. Fórmula hidráulica: Potencia [kW] = 9.81 × Q[m³/s] × H[m]. Convertida a GWh. Alta montaña = mayor altura de caída = más eficiencia energética.
    """
    return agua_del_toro_salida_energia() * 0.002314 * agua_del_toro_cabeza_neta()


@component.add(
    name="Agua Del Toro Porcentaje Capacidad",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_volumen_embalse": 1, "agua_del_toro_cap_max": 1},
)
def agua_del_toro_porcentaje_capacidad():
    """
    Porcentaje de llenado (0 a 1). Es la variable de entrada del algoritmo de decisión. Cuando es bajo, priorizar riego; cuando es alto, priorizar energía.
    """
    return agua_del_toro_volumen_embalse() / agua_del_toro_cap_max()


@component.add(
    name="Agua Del Toro Prioridad Energia",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_porcentaje_capacidad": 2},
)
def agua_del_toro_prioridad_energia():
    """
    Embalse > 80% → balance con algo de energía (0.50) Embalse entre 40% y 80% → balance moderado (0.35) Embalse < 40% → prioridad al riego (0.10) Valores similares al Nihuil: sirve a 81.400 ha de cultivos mixtos (35% viñas, 41% frutales).
    """
    return if_then_else(
        agua_del_toro_porcentaje_capacidad() > 0.8,
        lambda: 0.5,
        lambda: if_then_else(
            agua_del_toro_porcentaje_capacidad() < 0.4, lambda: 0.1, lambda: 0.35
        ),
    )


@component.add(
    name="Agua Del Toro Satisfaccion Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"agua_del_toro_salida_riego": 1, "agua_del_toro_demanda_riego": 1},
)
def agua_del_toro_satisfaccion_riego():
    """
    Fracción de la demanda de riego satisfecha. 1.0 = todos los agricultores reciben toda el agua que necesitan. Valores < 0.7 indican situación crítica para el sector agropecuario.
    """
    return agua_del_toro_salida_riego() / float(
        np.maximum(0.01, agua_del_toro_demanda_riego())
    )


@component.add(
    name="Agua Del Toro Vol Inicial",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def agua_del_toro_vol_inicial():
    """
    Volumen al inicio de la simulación
    """
    return 240


@component.add(
    name="Agua Del Toro Vol Min",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def agua_del_toro_vol_min():
    """
    Volumen mínimo operacional (muerto). No se puede erogar por debajo de este nivel.
    """
    return 40


@component.add(
    name="Agua Del Toro Volumen Embalse",
    units="hm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_agua_del_toro_volumen_embalse": 1},
    other_deps={
        "_integ_agua_del_toro_volumen_embalse": {
            "initial": {"agua_del_toro_vol_inicial": 1},
            "step": {
                "agua_del_toro_entrada_agua": 1,
                "agua_del_toro_consumo_urbano": 1,
                "agua_del_toro_evaporacion": 1,
                "agua_del_toro_salida_energia": 1,
                "agua_del_toro_salida_riego": 1,
            },
        }
    },
)
def agua_del_toro_volumen_embalse():
    """
    Volumen de agua almacenado en Agua Del Toro en cada instante de la simulación. Aumenta únicamente con Pot_Entrada (que viene del CSV de Python). Disminuye por las 4 salidas. Es el corazón del modelo para este embalse.
    """
    return _integ_agua_del_toro_volumen_embalse()


_integ_agua_del_toro_volumen_embalse = Integ(
    lambda: agua_del_toro_entrada_agua()
    - agua_del_toro_consumo_urbano()
    - agua_del_toro_evaporacion()
    - agua_del_toro_salida_energia()
    - agua_del_toro_salida_riego(),
    lambda: agua_del_toro_vol_inicial(),
    "_integ_agua_del_toro_volumen_embalse",
)


@component.add(
    name="Carrizal Cabeza Neta",
    units="m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_porcentaje_capacidad": 1},
)
def carrizal_cabeza_neta():
    """
    Energía hidráulica real y efectiva del Carrizal disponible para generar electricidad. Mínimo 30 m, máximo 100 m.
    """
    return 30 + 70 * carrizal_porcentaje_capacidad()


@component.add(
    name="Carrizal Cap Max", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def carrizal_cap_max():
    """
    Capacidad máxima del embalse Carrizal.
    """
    return 195


@component.add(
    name="Carrizal Consumo Urbano",
    units="hm3/mes",
    comp_type="Constant",
    comp_subtype="Normal",
)
def carrizal_consumo_urbano():
    """
    Consumo urbano de Tunuyán y alrededores.
    """
    return 2


@component.add(
    name="Carrizal Demanda Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def carrizal_demanda_riego():
    """
    Demanda estacional de riego del oasis del Tunuyán (zona Este de Mendoza, viticultura y fruticultura).
    """
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [50, 55, 52, 35, 20, 17, 17, 25, 40, 50, 58, 52],
    )


@component.add(
    name="Carrizal Disponible",
    units="hm3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_volumen_embalse": 1, "carrizal_vol_min": 1},
)
def carrizal_disponible():
    """
    Agua realmente disponible para erogar (total menos el volumen muerto). Garantiza que el embalse nunca quede completamente vacío.
    """
    return float(np.maximum(0, carrizal_volumen_embalse() - carrizal_vol_min()))


@component.add(
    name="Carrizal Evaporacion",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_evap_mensual": 1},
)
def carrizal_evaporacion():
    """
    Pérdida por evaporación superficial. Factor 0.8 por superficie menor del Carrizal.
    """
    return tasa_evap_mensual() * 0.8


@component.add(
    name="Carrizal Generacion GWh",
    units="GWh/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_salida_energia": 1, "carrizal_cabeza_neta": 1},
)
def carrizal_generacion_gwh():
    """
    Energía generada mensualmente. Fórmula hidráulica: Potencia [kW] = 9.81 × Q[m³/s] × H[m]. Convertida a GWh.
    """
    return carrizal_salida_energia() * 0.002314 * carrizal_cabeza_neta()


@component.add(
    name="Carrizal Porcentaje Capacidad",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_volumen_embalse": 1, "carrizal_cap_max": 1},
)
def carrizal_porcentaje_capacidad():
    """
    Porcentaje de llenado (0 a 1). Es la variable de entrada del algoritmo de decisión. Cuando es bajo, priorizar riego; cuando es alto, priorizar energía.
    """
    return carrizal_volumen_embalse() / carrizal_cap_max()


@component.add(
    name="Carrizal Prioridad Energia",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_porcentaje_capacidad": 2},
)
def carrizal_prioridad_energia():
    """
    Embalse > 80% → puede ceder algo a energía (0.30) Embalse entre 40% y 80% → preferencia por riego (0.20) Embalse < 40% → casi todo para riego (0.05) El Carrizal tiene los valores más bajos de prioridad energética porque abastece 4.302 km de canales de riego agrícola del oasis del Tunuyán.
    """
    return if_then_else(
        carrizal_porcentaje_capacidad() > 0.8,
        lambda: 0.3,
        lambda: if_then_else(
            carrizal_porcentaje_capacidad() < 0.4, lambda: 0.05, lambda: 0.2
        ),
    )


@component.add(
    name="Carrizal Satisfaccion Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"carrizal_salida_riego": 1, "carrizal_demanda_riego": 1},
)
def carrizal_satisfaccion_riego():
    """
    Fracción de la demanda de riego satisfecha. 1.0 = todos los agricultores reciben toda el agua que necesitan. Valores < 0.7 indican situación crítica para el sector agropecuario.
    """
    return carrizal_salida_riego() / float(np.maximum(0.01, carrizal_demanda_riego()))


@component.add(
    name="Carrizal Vol Inicial",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def carrizal_vol_inicial():
    """
    Volumen al inicio de la simulación
    """
    return 120


@component.add(
    name="Carrizal Vol Min", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def carrizal_vol_min():
    """
    Volumen mínimo operacional (muerto). No se puede erogar por debajo de este nivel.
    """
    return 20


@component.add(
    name="Carrizal Volumen Embalse",
    units="hm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_carrizal_volumen_embalse": 1},
    other_deps={
        "_integ_carrizal_volumen_embalse": {
            "initial": {"carrizal_vol_inicial": 1},
            "step": {
                "carrizal_entrada_agua": 1,
                "carrizal_consumo_urbano": 1,
                "carrizal_evaporacion": 1,
                "carrizal_salida_energia": 1,
                "carrizal_salida_riego": 1,
            },
        }
    },
)
def carrizal_volumen_embalse():
    """
    Volumen de agua almacenado en Carrizal en cada instante de la simulación. Aumenta únicamente con Pot_Entrada (que viene del CSV de Python). Disminuye por las 4 salidas. Es el corazón del modelo para este embalse.
    """
    return _integ_carrizal_volumen_embalse()


_integ_carrizal_volumen_embalse = Integ(
    lambda: carrizal_entrada_agua()
    - carrizal_consumo_urbano()
    - carrizal_evaporacion()
    - carrizal_salida_energia()
    - carrizal_salida_riego(),
    lambda: carrizal_vol_inicial(),
    "_integ_carrizal_volumen_embalse",
)


@component.add(
    name="Consumo Urbano Potrerillos",
    units="hm3/mes",
    comp_type="Constant",
    comp_subtype="Normal",
)
def consumo_urbano_potrerillos():
    """
    Agua potable para el Gran Mendoza (Capital, Godoy Cruz, Guaymallén, Las Heras, Maipú). Constante: 8 hm³/mes ≈ 96 hm³/año.
    """
    return 8


@component.add(
    name="Conviene Energia",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"decision_sistema": 1},
)
def conviene_energia():
    """
    dmnl (1=sí · 0=no) Vale 1 cuando la respuesta es "priorizar la energía". Siempre complementario a Conviene_Riego: uno vale 1 y el otro vale 0.
    """
    return if_then_else(decision_sistema() >= 0.5, lambda: 1, lambda: 0)


@component.add(
    name="Conviene Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"decision_sistema": 1},
)
def conviene_riego():
    """
    dmnl (1=sí · 0=no) Vale 1 cuando la respuesta a la pregunta de investigación es "priorizar el riego". Directamente legible en el gráfico de resultados.
    """
    return if_then_else(decision_sistema() < 0.5, lambda: 1, lambda: 0)


@component.add(
    name="Crisis Hidrica",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"total_porcentaje_de_llenado_completo": 1},
)
def crisis_hidrica():
    """
    dmnl (0=normal, 1=crisis) Se activa cuando el sistema cae por debajo del 30% de su capacidad total. Permite contar cuántos meses de crisis ocurren en los años simulados.
    """
    return if_then_else(
        total_porcentaje_de_llenado_completo() < 0.3, lambda: 1, lambda: 0
    )


@component.add(
    name="Decision Sistema",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"total_porcentaje_de_llenado_completo": 3},
)
def decision_sistema():
    """
    Responde directamente la pregunta de investigación según el estado del sistema: 0.00 → Sistema en crisis: TODO para riego, suspender energía 0.25 → Sistema en alerta: preferencia fuerte por riego 0.50 → Sistema normal: balance equitativo 0.80 → Sistema holgado: priorizar energía (genera ingresos)
    """
    return if_then_else(
        total_porcentaje_de_llenado_completo() < 0.3,
        lambda: 0,
        lambda: if_then_else(
            total_porcentaje_de_llenado_completo() < 0.5,
            lambda: 0.25,
            lambda: if_then_else(
                total_porcentaje_de_llenado_completo() < 0.7, lambda: 0.5, lambda: 0.8
            ),
        ),
    )


@component.add(name="Eficiencia Riego", comp_type="Constant", comp_subtype="Normal")
def eficiencia_riego():
    return 0.6


@component.add(
    name="Evaporacion Potrerillos",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_evap_mensual": 1},
)
def evaporacion_potrerillos():
    """
    Pérdida por evaporación superficial. El factor 1.4 refleja que Potrerillos tiene el espejo de agua más grande del sistema ( 28 km² a plena capacidad).
    """
    return tasa_evap_mensual() * 1.4


@component.add(
    name="Mes Actual",
    units="Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time": 1},
)
def mes_actual():
    """
    Devuelve el mes actual (0=Enero, 1=Feb, ..., 11=Dic). Es la clave para tablas estacionales.
    """
    return modulo(time(), 12)


@component.add(
    name="Nihuil Cabeza Neta",
    units="m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_porcentaje_capacidad": 1},
)
def nihuil_cabeza_neta():
    """
    Energía hidráulica real y efectiva del Nihuil disponible para generar electricidad. Mínimo 40 m, máximo 150 m.
    """
    return 40 + 110 * nihuil_porcentaje_capacidad()


@component.add(
    name="Nihuil Cap Max", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def nihuil_cap_max():
    """
    Capacidad máxima del embalse Nihuil.
    """
    return 320


@component.add(
    name="Nihuil Consumo Urbano",
    units="hm3/mes",
    comp_type="Constant",
    comp_subtype="Normal",
)
def nihuil_consumo_urbano():
    """
    Consumo urbano de San Rafael (zona Atuel).
    """
    return 2


@component.add(
    name="Nihuil Demanda Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def nihuil_demanda_riego():
    """
    Demanda estacional de riego del oasis del Atuel (San Rafael). Cultivos mixtos de viñedos y frutales en la zona sur de Mendoza.
    """
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [65, 71, 68, 45, 26, 22, 22, 32, 52, 65, 74, 68],
    )


@component.add(
    name="Nihuil Disponible",
    units="hm3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_volumen_embalse": 1, "nihuil_vol_min": 1},
)
def nihuil_disponible():
    """
    Agua realmente disponible para erogar (total menos el volumen muerto). Garantiza que el embalse nunca quede completamente vacío.
    """
    return float(np.maximum(0, nihuil_volumen_embalse() - nihuil_vol_min()))


@component.add(
    name="Nihuil Evaporacion",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_evap_mensual": 1},
)
def nihuil_evaporacion():
    """
    Pérdida por evaporación superficial. Factor 0.9 por superficie intermedia del Nihuil.
    """
    return tasa_evap_mensual() * 0.9


@component.add(
    name="Nihuil Generacion GWh",
    units="GWh/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_salida_energia": 1, "nihuil_cabeza_neta": 1},
)
def nihuil_generacion_gwh():
    """
    Energía generada mensualmente. Fórmula hidráulica: Potencia [kW] = 9.81 × Q[m³/s] × H[m]. Convertida a GWh.
    """
    return nihuil_salida_energia() * 0.002314 * nihuil_cabeza_neta()


@component.add(
    name="Nihuil Porcentaje Capacidad",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_volumen_embalse": 1, "nihuil_cap_max": 1},
)
def nihuil_porcentaje_capacidad():
    """
    Porcentaje de llenado (0 a 1). Es la variable de entrada del algoritmo de decisión. Cuando es bajo, priorizar riego; cuando es alto, priorizar energía.
    """
    return nihuil_volumen_embalse() / nihuil_cap_max()


@component.add(
    name="Nihuil Prioridad Energia",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_porcentaje_capacidad": 2},
)
def nihuil_prioridad_energia():
    """
    Embalse > 80% → balance moderado con algo de energía (0.50) Embalse entre 40% y 80% → ligera preferencia por riego (0.35) Embalse < 40% → prioridad al riego (0.10) El Nihuil tiene valores intermedios porque sirve a agricultores del Atuel pero también genera energía.
    """
    return if_then_else(
        nihuil_porcentaje_capacidad() > 0.8,
        lambda: 0.5,
        lambda: if_then_else(
            nihuil_porcentaje_capacidad() < 0.4, lambda: 0.1, lambda: 0.35
        ),
    )


@component.add(
    name="Nihuil Satisfaccion Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nihuil_salida_riego": 1, "nihuil_demanda_riego": 1},
)
def nihuil_satisfaccion_riego():
    """
    Fracción de la demanda de riego satisfecha. 1.0 = todos los agricultores reciben toda el agua que necesitan. Valores < 0.7 indican situación crítica para el sector agropecuario.
    """
    return nihuil_salida_riego() / float(np.maximum(0.01, nihuil_demanda_riego()))


@component.add(
    name="Nihuil Vol Inicial", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def nihuil_vol_inicial():
    """
    Volumen al inicio de la simulación
    """
    return 200


@component.add(
    name="Nihuil Vol Min", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def nihuil_vol_min():
    """
    Volumen mínimo operacional (muerto). No se puede erogar por debajo de este nivel.
    """
    return 100


@component.add(
    name="Nihuil Volumen Embalse",
    units="hm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_nihuil_volumen_embalse": 1},
    other_deps={
        "_integ_nihuil_volumen_embalse": {
            "initial": {"nihuil_vol_inicial": 1},
            "step": {
                "nihuil_entrada_agua": 1,
                "nihuil_consumo_urbano": 1,
                "nihuil_evaporacion": 1,
                "nihuil_salida_energia": 1,
                "nihuil_salida_riego": 1,
            },
        }
    },
)
def nihuil_volumen_embalse():
    """
    Volumen de agua almacenado en Nihuil en cada instante de la simulación. Aumenta únicamente con Pot_Entrada (que viene del CSV de Python). Disminuye por las 4 salidas. Es el corazón del modelo para este embalse.
    """
    return _integ_nihuil_volumen_embalse()


_integ_nihuil_volumen_embalse = Integ(
    lambda: nihuil_entrada_agua()
    - nihuil_consumo_urbano()
    - nihuil_evaporacion()
    - nihuil_salida_energia()
    - nihuil_salida_riego(),
    lambda: nihuil_vol_inicial(),
    "_integ_nihuil_volumen_embalse",
)


@component.add(
    name="Potrerillos Cabeza Neta",
    units="m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potrerillos_porcentaje_capacidad": 1},
)
def potrerillos_cabeza_neta():
    """
    Energía hidráulica real y efectiva de Potrerillos disponible para generar electricidad. Mínimo 40 m, máximo 150 m. Mínimo 150 m (embalse casi vacío), máximo 350 m (embalse lleno). Rango realista para una central de 315 MW.
    """
    return 150 + 200 * potrerillos_porcentaje_capacidad()


@component.add(
    name="Potrerillos Cap Max", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def potrerillos_cap_max():
    """
    Capacidad máxima del embalse Potrerillos.
    """
    return 1885


@component.add(
    name="Potrerillos Demanda Riego",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="with Lookup",
    depends_on={"mes_actual": 1},
)
def potrerillos_demanda_riego():
    """
    Demanda estacional de riego del oasis norte (Lavalle, Las Heras, Maipú, Luján de Cuyo, Godoy Cruz). Máxima en verano (cultivos en crecimiento), mínima en invierno. Esta tabla es DETERMINÍSTICA — la aleatoriedad de la oferta viene de Python, la demanda sigue un patrón conocido.
    """
    return np.interp(
        mes_actual(),
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [250, 275, 262, 175, 100, 87, 87, 125, 200, 250, 287, 262],
    )


@component.add(
    name="Potrerillos Disponible",
    units="hm3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"volumen_embalse_potrerillos": 1, "potrerillos_vol_min": 1},
)
def potrerillos_disponible():
    """
    Agua realmente disponible para erogar (total menos el volumen muerto). Garantiza que el embalse nunca quede completamente vacío.
    """
    return float(np.maximum(0, volumen_embalse_potrerillos() - potrerillos_vol_min()))


@component.add(
    name="Potrerillos Generacion GWh",
    units="GWh/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"salida_energia_potrerillos": 1, "potrerillos_cabeza_neta": 1},
)
def potrerillos_generacion_gwh():
    """
    Energía generada mensualmente. Fórmula hidráulica: Potencia [kW] = 9.81 × Q[m³/s] × H[m]. Convertida a GWh. A plena capacidad Potrerillos puede generar 220 GWh/mes.
    """
    return salida_energia_potrerillos() * 0.002314 * potrerillos_cabeza_neta()


@component.add(
    name="Potrerillos Porcentaje Capacidad",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"volumen_embalse_potrerillos": 1, "potrerillos_cap_max": 1},
)
def potrerillos_porcentaje_capacidad():
    """
    Porcentaje de llenado (0 a 1). Es la variable de entrada del algoritmo de decisión. Cuando es bajo, priorizar riego; cuando es alto, priorizar energía.
    """
    return volumen_embalse_potrerillos() / potrerillos_cap_max()


@component.add(
    name="Potrerillos Prioridad Energia",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potrerillos_porcentaje_capacidad": 2},
)
def potrerillos_prioridad_energia():
    """
    Embalse > 80% → priorizar energía fuertemente (0.80) Embalse entre 40% y 80% → balance (0.50) Embalse < 40% → priorizar riego urgentemente (0.15) Potrerillos tiene los valores más altos porque es la principal fuente hidroeléctrica de Mendoza.
    """
    return if_then_else(
        potrerillos_porcentaje_capacidad() > 0.8,
        lambda: 0.8,
        lambda: if_then_else(
            potrerillos_porcentaje_capacidad() < 0.4, lambda: 0.15, lambda: 0.5
        ),
    )


@component.add(
    name="Potrerillos Satisfaccion Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"salida_riego_potre": 1, "potrerillos_demanda_riego": 1},
)
def potrerillos_satisfaccion_riego():
    """
    Fracción de la demanda de riego satisfecha. 1.0 = todos los agricultores reciben toda el agua que necesitan. Valores < 0.7 indican situación crítica para el sector agropecuario.
    """
    return salida_riego_potre() / float(np.maximum(0.01, potrerillos_demanda_riego()))


@component.add(
    name="Potrerillos Vol Inicial",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def potrerillos_vol_inicial():
    """
    Volumen al inicio de la simulación
    """
    return 1200


@component.add(
    name="Potrerillos Vol Min", units="hm3", comp_type="Constant", comp_subtype="Normal"
)
def potrerillos_vol_min():
    """
    olumen mínimo operacional (muerto). No se puede erogar por debajo de este nivel.
    """
    return 100


@component.add(name="Precio MWh", comp_type="Constant", comp_subtype="Normal")
def precio_mwh():
    """
    Precio promedio de venta de energía eléctrica en el mercado mayorista argentino
    """
    return 80


@component.add(
    name="Tasa Evap Mensual",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"temperatura_actual": 1},
)
def tasa_evap_mensual():
    """
    Evaporación base del sistema. Mendoza tiene clima árido con alta evapotranspiración potencial. A 25°C: (25-5)*0.05 = 1 hm³/mes por embalse.
    """
    return float(np.maximum(0, (temperatura_actual() - 5) * 0.05))


@component.add(
    name="Temperatura Actual",
    units="°C",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time": 1},
)
def temperatura_actual():
    """
    Ciclo anual de temperatura. Pico en enero ( 28°C), mínimo en julio ( 12°C). Representa el clima de Mendoza.
    """
    return 20 + 8 * float(np.sin(2 * 3.14159 * time() / 12))


@component.add(
    name="Total Capacidad Maxima",
    units="hm3",
    comp_type="Constant",
    comp_subtype="Normal",
)
def total_capacidad_maxima():
    """
    1885 + 320 + 195 + 380 = 2.780 hm³. Capacidad total del sistema de los 4 embalses simulados.
    """
    return 2780


@component.add(
    name="Total Demanda Riego",
    units="hm3/m",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_demanda_riego": 1,
        "carrizal_demanda_riego": 1,
        "nihuil_demanda_riego": 1,
        "potrerillos_demanda_riego": 1,
    },
)
def total_demanda_riego():
    """
    Demanda agrícola total del sistema. En enero puede superar los 680 hm³/mes.
    """
    return (
        agua_del_toro_demanda_riego()
        + carrizal_demanda_riego()
        + nihuil_demanda_riego()
        + potrerillos_demanda_riego()
    )


@component.add(
    name="Total Energia GWh",
    units="GWh/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_generacion_gwh": 1,
        "carrizal_generacion_gwh": 1,
        "nihuil_generacion_gwh": 1,
        "potrerillos_generacion_gwh": 1,
    },
)
def total_energia_gwh():
    """
    Energía eléctrica total generada por los 4 embalses.
    """
    return (
        agua_del_toro_generacion_gwh()
        + carrizal_generacion_gwh()
        + nihuil_generacion_gwh()
        + potrerillos_generacion_gwh()
    )


@component.add(
    name="Total Ingresos Energia",
    units="USD/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"total_energia_gwh": 1, "precio_mwh": 1},
)
def total_ingresos_energia():
    """
    Ingresos mensuales por venta de energía eléctrica. La conversión ×1000 transforma GWh a MWh para aplicar el precio unitario.
    """
    return total_energia_gwh() * precio_mwh() * 1000


@component.add(
    name="Total Porcentaje de Llenado Completo",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"total_volumen": 1, "total_capacidad_maxima": 1},
)
def total_porcentaje_de_llenado_completo():
    """
    Porcentaje de llenado del sistema completo. Umbrales de interpretación: Mayor a 0.70 → Sistema holgado 0.50 a 0.70 → Normal 0.30 a 0.50 → Alerta hídrica Menor a 0.30 → Crisis hídrica
    """
    return total_volumen() / total_capacidad_maxima()


@component.add(
    name="Total Riego Entregado",
    units="hm3/mes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_salida_riego": 1,
        "carrizal_salida_riego": 1,
        "nihuil_salida_riego": 1,
        "salida_riego_potre": 1,
        "eficiencia_riego": 1,
    },
)
def total_riego_entregado():
    """
    Agua que REALMENTE llega a los cultivos en toda Mendoza, descontando el 40% de pérdidas en la red de canales.
    """
    return (
        agua_del_toro_salida_riego()
        + carrizal_salida_riego()
        + nihuil_salida_riego()
        + salida_riego_potre()
    ) * eficiencia_riego()


@component.add(
    name="Total Satisfaccion Riego",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"total_riego_entregado": 1, "total_demanda_riego": 1},
)
def total_satisfaccion_riego():
    """
    Fracción de la demanda agrícola total que fue satisfecha. Es el indicador de impacto social del modelo. Valor 1.0 = todos los agricultores tienen el agua que necesitan.
    """
    return total_riego_entregado() / float(np.maximum(0.01, total_demanda_riego()))


@component.add(
    name="Total Volumen",
    units="hm3",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "agua_del_toro_volumen_embalse": 1,
        "carrizal_volumen_embalse": 1,
        "nihuil_volumen_embalse": 1,
        "volumen_embalse_potrerillos": 1,
    },
)
def total_volumen():
    """
    Agua total almacenada en el sistema en cada instante. Principal indicador del estado hídrico general de Mendoza.
    """
    return (
        agua_del_toro_volumen_embalse()
        + carrizal_volumen_embalse()
        + nihuil_volumen_embalse()
        + volumen_embalse_potrerillos()
    )


@component.add(
    name="Volumen Embalse Potrerillos",
    units="hm3",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_volumen_embalse_potrerillos": 1},
    other_deps={
        "_integ_volumen_embalse_potrerillos": {
            "initial": {"potrerillos_vol_inicial": 1},
            "step": {
                "entrada_agua_potrerillos": 1,
                "consumo_urbano_potrerillos": 1,
                "evaporacion_potrerillos": 1,
                "salida_energia_potrerillos": 1,
                "salida_riego_potre": 1,
            },
        }
    },
)
def volumen_embalse_potrerillos():
    """
    Volumen de agua almacenado en Potrerillos en cada instante de la simulación. Aumenta únicamente con Pot_Entrada (que viene del CSV de Python). Disminuye por las 4 salidas. Es el corazón del modelo para este embalse.
    """
    return _integ_volumen_embalse_potrerillos()


_integ_volumen_embalse_potrerillos = Integ(
    lambda: entrada_agua_potrerillos()
    - consumo_urbano_potrerillos()
    - evaporacion_potrerillos()
    - salida_energia_potrerillos()
    - salida_riego_potre(),
    lambda: potrerillos_vol_inicial(),
    "_integ_volumen_embalse_potrerillos",
)
