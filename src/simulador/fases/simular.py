"""Fase 4: simulación del modelo Vensim con PySD.

Único módulo del proyecto que importa `pysd` (Adapter implícito): si
mañana cambia el motor, solo se toca este archivo. La traducción del
.mdl se cachea como .py junto al modelo para acelerar corridas.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pysd

from simulador.config import ConfigPipeline
from simulador.persistencia.repositorio import RepositorioArtefactos

VARIABLE_TEMPERATURA = "Temperatura Actual"

COLUMNAS_RESULTADOS: tuple[str, ...] = (
    "Total Volumen",
    "Total Porcentaje de Llenado Completo",
    "Total Energia GWh",
    "Total Ingresos Energia",
    "Total Demanda Riego",
    "Total Riego Entregado",
    "Total Satisfaccion Riego",
    "Volumen Embalse Potrerillos",
    "Carrizal Volumen Embalse",
    "Nihuil Volumen Embalse",
    "Agua Del Toro Volumen Embalse",
    "Potrerillos Satisfaccion Riego",
    "Carrizal Satisfaccion Riego",
    "Nihuil Satisfaccion Riego",
    "Agua Del Toro Satisfaccion Riego",
    "Potrerillos Generacion GWh",
    "Carrizal Generacion GWh",
    "Nihuil Generacion GWh",
    "Agua Del Toro Generacion GWh",
    "Conviene Riego",
    "Conviene Energia",
)


def _cargar_modelo(ruta_mdl: Path):
    """Traduce el .mdl (o carga el .py cacheado si está actualizado)."""
    traducido = ruta_mdl.with_suffix(".py")
    if traducido.is_file() and traducido.stat().st_mtime >= ruta_mdl.stat().st_mtime:
        return pysd.load(str(traducido))
    return pysd.read_vensim(str(ruta_mdl))


def _hash_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def _armar_params(
    repo: RepositorioArtefactos, id_corrida: str, config: ConfigPipeline
) -> dict[str, pd.Series]:
    """Series de entrada por dique + temperatura, indexadas por mes."""
    params: dict[str, pd.Series] = {}
    temperatura: pd.Series | None = None

    for dique in config.diques:
        escenario = repo.leer_escenario(id_corrida, dique.slug)
        indice = escenario["mes"].to_numpy()
        params[dique.variable_entrada] = pd.Series(
            escenario["entrada_agua_hm3"].to_numpy(), index=indice
        )
        if temperatura is None:
            temperatura = pd.Series(
                escenario["temperatura_c"].to_numpy(), index=indice
            )

    if temperatura is not None:
        params[VARIABLE_TEMPERATURA] = temperatura
    return params


def ejecutar(
    repo: RepositorioArtefactos, id_corrida: str, config: ConfigPipeline
) -> Path:
    """Inyecta los escenarios en el .mdl, corre y persiste resultados."""
    manifest = repo.leer_manifest(id_corrida)
    horizonte = manifest.horizonte_meses or config.horizonte_meses

    modelo = _cargar_modelo(config.ruta_mdl)
    params = _armar_params(repo, id_corrida, config)

    disponibles = set(modelo.doc["Real Name"].dropna())
    desconocidas = [v for v in params if v not in disponibles]
    if desconocidas:
        raise KeyError(
            f"Variables no encontradas en el modelo: {desconocidas}. "
            "Revisá ConfigDique.variable_entrada contra el .mdl."
        )

    columnas = [c for c in COLUMNAS_RESULTADOS if c in disponibles]
    resultados = modelo.run(
        params=params,
        final_time=horizonte,
        return_columns=columnas,
    )
    resultados.index.name = "mes"
    resultados = resultados.reset_index()

    ruta = repo.escribir_resultados(id_corrida, resultados)
    repo.actualizar_manifest(
        id_corrida,
        ruta_mdl=str(config.ruta_mdl),
        hash_mdl=_hash_archivo(config.ruta_mdl),
        version_pysd=pysd.__version__,
    )

    print(f"✓ Simulación PySD completada ({len(resultados)} meses)")
    print(f"  Artefacto: {ruta}")
    return ruta
