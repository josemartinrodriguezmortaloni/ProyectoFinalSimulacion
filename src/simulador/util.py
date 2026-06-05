import json
from pathlib import Path

import numpy as np
import pandas as pd


def convertir_a_json(obj):
    """Convierte escalares de NumPy a tipos nativos de Python para json.dump."""
    if isinstance(obj, dict):
        return {k: convertir_a_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convertir_a_json(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def guardar_resultados(
    df: pd.DataFrame,
    reporte: dict,
    dir_resultados: Path,
) -> None:
    dir_resultados.mkdir(parents=True, exist_ok=True)

    df.to_csv(dir_resultados / "resultados_simulacion.csv", index=False)

    with open(dir_resultados / "validacion_estadistica.json", "w") as f:
        json.dump(convertir_a_json(reporte), f, indent=2)
