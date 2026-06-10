"""Fase 1: generación de series climáticas pseudoaleatorias."""
from __future__ import annotations

import numpy as np

from simulador.core.generacion import ParametrosClimaticos, generar_series_climaticas
from simulador.persistencia.repositorio import ManifestCorrida, RepositorioArtefactos


def ejecutar(
    repo: RepositorioArtefactos,
    seed: int,
    n_anios: int,
    params: ParametrosClimaticos | None = None,
) -> str:
    """Genera las series, crea la corrida y devuelve su ID."""
    rng = np.random.default_rng(seed)
    series = generar_series_climaticas(rng, n_anios, params)

    manifest = ManifestCorrida.nuevo(seed=seed, n_anios=n_anios)
    repo.crear_corrida(manifest)
    ruta = repo.escribir_series(manifest.id_corrida, series)

    print(f"✓ Corrida creada: {manifest.id_corrida}")
    print(f"  Series generadas: {n_anios} años ({len(series)} filas)")
    print(f"  Artefacto: {ruta}")
    return manifest.id_corrida
