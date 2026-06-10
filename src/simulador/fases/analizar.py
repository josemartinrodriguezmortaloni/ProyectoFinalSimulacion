"""Fase 5: análisis de resultados y ranking global de corridas."""
from __future__ import annotations

import pandas as pd

from simulador.core.kpis import KPIsSistema, PesosScore, calcular_kpis, puntuar_corridas
from simulador.persistencia.repositorio import RepositorioArtefactos


def _kpis_como_fila(
    kpis: KPIsSistema, id_corrida: str, seed: int, asignacion: str | None,
    horizonte_meses: int | None,
) -> pd.DataFrame:
    """Aplana los KPIs (incluida la satisfacción por dique) en una fila."""
    fila: dict[str, object] = {
        "id_corrida": id_corrida,
        "seed": seed,
        "asignacion": asignacion,
        "horizonte_meses": horizonte_meses,
    }
    plano = kpis.a_dict()
    por_dique = plano.pop("satisfaccion_por_dique")
    fila.update(plano)
    for dique, valor in por_dique.items():
        clave = f"satisfaccion_{dique.lower().replace(' ', '_')}"
        fila[clave] = valor
    return pd.DataFrame([fila])


def ejecutar(repo: RepositorioArtefactos, id_corrida: str) -> KPIsSistema:
    """Calcula KPIs de una corrida y los persiste como artefacto."""
    manifest = repo.leer_manifest(id_corrida)
    resultados = repo.leer_resultados(id_corrida)
    kpis = calcular_kpis(resultados)

    tabla = _kpis_como_fila(
        kpis, id_corrida, manifest.seed, manifest.asignacion,
        manifest.horizonte_meses,
    )
    repo.escribir_kpis(id_corrida, tabla)

    print(f"✓ KPIs de la corrida {id_corrida}:")
    print(f"  Satisfacción riego media: {kpis.satisfaccion_riego_media:.3f}")
    print(f"  Energía total: {kpis.energia_total_gwh:.1f} GWh")
    print(f"  Ingresos: {kpis.ingresos_totales_usd:,.0f} USD")
    print(f"  Llenado medio: {kpis.llenado_medio:.2%} (mín {kpis.llenado_minimo:.2%})")
    print(f"  Meses en crisis: {kpis.meses_crisis} | en alerta: {kpis.meses_alerta}")
    for dique, valor in kpis.satisfaccion_por_dique.items():
        print(f"    {dique}: satisfacción {valor:.3f}")
    return kpis


def ejecutar_global(
    repo: RepositorioArtefactos, pesos: PesosScore
) -> pd.DataFrame:
    """Agrega los KPIs de todas las corridas y arma el ranking por score."""
    filas = []
    for id_corrida in repo.listar_corridas():
        try:
            filas.append(repo.leer_kpis(id_corrida))
        except FileNotFoundError:
            print(f"  (saltando {id_corrida}: sin KPIs, fase analizar pendiente)")

    if not filas:
        raise FileNotFoundError(
            "Ninguna corrida tiene KPIs. Ejecutá el pipeline al menos una vez."
        )

    consolidado = pd.concat(filas, ignore_index=True)
    ranking = puntuar_corridas(consolidado, pesos)
    ruta = repo.escribir_ranking_global(ranking)

    columnas_resumen = [
        "id_corrida", "asignacion", "satisfaccion_riego_media",
        "energia_total_gwh", "meses_crisis", "score",
    ]
    print("✓ Ranking global de corridas (mejor política primero):")
    print(ranking[columnas_resumen].to_string(index=False))
    print(f"  Artefacto: {ruta}")
    return ranking
