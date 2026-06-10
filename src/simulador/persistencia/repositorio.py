"""Repositorio de artefactos: rutas, lectura y escritura de cada corrida.

Cada corrida vive en `artefactos/{seed}_{timestamp}/` con su manifest
y los artefactos numerados por fase. El manifest evoluciona: cada fase
agrega sus propios campos (asignación, hash del modelo, etc.).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from simulador.persistencia import esquemas
from simulador.util import convertir_a_json

ARCHIVO_MANIFEST = "manifest.json"
ARCHIVO_SERIES = "01_series_climaticas.csv"
ARCHIVO_VALIDACION = "02_validacion.json"
PLANTILLA_ESCENARIO = "03_escenario_{slug}.csv"
ARCHIVO_RESULTADOS = "04_resultados_pysd.csv"
ARCHIVO_KPIS = "05_kpis.csv"
ARCHIVO_RANKING_GLOBAL = "ranking_global.csv"


class CorridaNoEncontradaError(FileNotFoundError):
    """No existe la corrida o el artefacto pedido."""


@dataclass(frozen=True)
class ManifestCorrida:
    """Metadatos de reproducibilidad de una corrida."""

    id_corrida: str
    seed: int
    n_anios: int
    creado: str
    asignacion: str | None = None
    horizonte_meses: int | None = None
    proporciones_diques: dict[str, float] = field(default_factory=dict)
    ruta_mdl: str | None = None
    hash_mdl: str | None = None
    version_pysd: str | None = None

    @staticmethod
    def nuevo(seed: int, n_anios: int) -> "ManifestCorrida":
        ahora = datetime.now()
        return ManifestCorrida(
            id_corrida=f"{seed}_{ahora:%Y%m%d_%H%M%S}",
            seed=seed,
            n_anios=n_anios,
            creado=ahora.isoformat(timespec="seconds"),
        )


class RepositorioArtefactos:
    """Acceso tipado a los artefactos de las corridas en disco."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz

    # ------------------------------------------------------------ rutas
    def dir_corrida(self, id_corrida: str) -> Path:
        directorio = self.raiz / id_corrida
        if not directorio.is_dir():
            raise CorridaNoEncontradaError(
                f"No existe la corrida '{id_corrida}' en {self.raiz}/"
            )
        return directorio

    def listar_corridas(self) -> list[str]:
        """IDs de corridas existentes, ordenadas cronológicamente."""
        if not self.raiz.is_dir():
            return []
        return sorted(
            d.name
            for d in self.raiz.iterdir()
            if d.is_dir() and (d / ARCHIVO_MANIFEST).is_file()
        )

    def resolver_id(self, id_corrida: str) -> str:
        """Permite usar 'ultima' como alias de la corrida más reciente."""
        if id_corrida != "ultima":
            return id_corrida
        corridas = self.listar_corridas()
        if not corridas:
            raise CorridaNoEncontradaError(
                f"No hay corridas en {self.raiz}/ (¿corriste 'generar'?)"
            )
        return corridas[-1]

    # --------------------------------------------------------- manifest
    def crear_corrida(self, manifest: ManifestCorrida) -> Path:
        directorio = self.raiz / manifest.id_corrida
        directorio.mkdir(parents=True, exist_ok=False)
        self._escribir_json(directorio / ARCHIVO_MANIFEST, asdict(manifest))
        return directorio

    def leer_manifest(self, id_corrida: str) -> ManifestCorrida:
        ruta = self.dir_corrida(id_corrida) / ARCHIVO_MANIFEST
        contenido = json.loads(ruta.read_text())
        return ManifestCorrida(**contenido)

    def actualizar_manifest(self, id_corrida: str, **campos: object) -> None:
        ruta = self.dir_corrida(id_corrida) / ARCHIVO_MANIFEST
        contenido = json.loads(ruta.read_text())
        contenido.update(campos)
        self._escribir_json(ruta, contenido)

    # -------------------------------------------------------- artefactos
    def escribir_series(self, id_corrida: str, series: pd.DataFrame) -> Path:
        esquemas.validar_esquema(series, esquemas.ESQUEMA_SERIES, "series")
        return self._escribir_csv(id_corrida, ARCHIVO_SERIES, series)

    def leer_series(self, id_corrida: str) -> pd.DataFrame:
        series = self._leer_csv(id_corrida, ARCHIVO_SERIES)
        esquemas.validar_esquema(series, esquemas.ESQUEMA_SERIES, "series")
        return series

    def escribir_validacion(self, id_corrida: str, reporte: dict) -> Path:
        ruta = self.dir_corrida(id_corrida) / ARCHIVO_VALIDACION
        self._escribir_json(ruta, reporte)
        return ruta

    def escribir_escenario(
        self, id_corrida: str, slug: str, escenario: pd.DataFrame
    ) -> Path:
        esquemas.validar_esquema(
            escenario, esquemas.ESQUEMA_ESCENARIO, f"escenario_{slug}"
        )
        nombre = PLANTILLA_ESCENARIO.format(slug=slug)
        return self._escribir_csv(id_corrida, nombre, escenario)

    def leer_escenario(self, id_corrida: str, slug: str) -> pd.DataFrame:
        nombre = PLANTILLA_ESCENARIO.format(slug=slug)
        escenario = self._leer_csv(id_corrida, nombre)
        esquemas.validar_esquema(
            escenario, esquemas.ESQUEMA_ESCENARIO, f"escenario_{slug}"
        )
        return escenario

    def escribir_resultados(
        self, id_corrida: str, resultados: pd.DataFrame
    ) -> Path:
        esquemas.validar_esquema(
            resultados, esquemas.ESQUEMA_RESULTADOS, "resultados"
        )
        return self._escribir_csv(id_corrida, ARCHIVO_RESULTADOS, resultados)

    def leer_resultados(self, id_corrida: str) -> pd.DataFrame:
        resultados = self._leer_csv(id_corrida, ARCHIVO_RESULTADOS)
        esquemas.validar_esquema(
            resultados, esquemas.ESQUEMA_RESULTADOS, "resultados"
        )
        return resultados

    def escribir_kpis(self, id_corrida: str, kpis: pd.DataFrame) -> Path:
        return self._escribir_csv(id_corrida, ARCHIVO_KPIS, kpis)

    def leer_kpis(self, id_corrida: str) -> pd.DataFrame:
        return self._leer_csv(id_corrida, ARCHIVO_KPIS)

    def escribir_ranking_global(self, ranking: pd.DataFrame) -> Path:
        self.raiz.mkdir(parents=True, exist_ok=True)
        ruta = self.raiz / ARCHIVO_RANKING_GLOBAL
        ranking.to_csv(ruta, index=False)
        return ruta

    # ---------------------------------------------------------- privados
    def _escribir_csv(
        self, id_corrida: str, nombre: str, contenido: pd.DataFrame
    ) -> Path:
        ruta = self.dir_corrida(id_corrida) / nombre
        contenido.to_csv(ruta, index=False)
        return ruta

    def _leer_csv(self, id_corrida: str, nombre: str) -> pd.DataFrame:
        ruta = self.dir_corrida(id_corrida) / nombre
        if not ruta.is_file():
            raise CorridaNoEncontradaError(
                f"Falta el artefacto '{nombre}' en la corrida '{id_corrida}'"
                " (¿ejecutaste la fase anterior?)"
            )
        return pd.read_csv(ruta)

    @staticmethod
    def _escribir_json(ruta: Path, contenido: dict) -> None:
        ruta.write_text(
            json.dumps(convertir_a_json(contenido), indent=2, ensure_ascii=False)
        )
