from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ConfigEmbalse:
    nombre: str
    capacidad_max_hm3: float
    altura_minima_m: float
    altura_maxima_m: float


@dataclass(frozen=True)
class ConfigDique:
    """Un embalse del modelo Vensim y su porción de la oferta hídrica.

    `variable_entrada` es el nombre EXACTO de la variable del .mdl que
    recibe la serie de entrada de agua. `proporcion_entrada` reparte el
    volumen total generado entre los diques (deben sumar 1).
    """

    nombre: str
    slug: str
    variable_entrada: str
    proporcion_entrada: float


# Proporciones calibradas contra los lookups originales del .mdl
# (promedios mensuales: Potrerillos ~235, Agua del Toro ~76, Nihuil ~62,
# Carrizal ~52 hm3/mes).
DIQUES_MENDOZA: tuple[ConfigDique, ...] = (
    ConfigDique("Potrerillos", "potrerillos", "Entrada Agua Potrerillos", 0.55),
    ConfigDique("Agua del Toro", "agua_del_toro", "Agua Del Toro Entrada Agua", 0.18),
    ConfigDique("El Nihuil", "nihuil", "Nihuil Entrada Agua", 0.15),
    ConfigDique("El Carrizal", "carrizal", "Carrizal Entrada Agua", 0.12),
)


@dataclass(frozen=True)
class ConfigPipeline:
    """Configuración del pipeline batch (diseño por artefactos)."""

    seed: int = 42
    n_anios: int = 500
    horizonte_meses: int = 120  # FINAL TIME del .mdl
    asignacion: str = "uniforme"
    area_cuenca_total_m2: float = 5_600_000_000
    raiz_artefactos: Path = field(default_factory=lambda: Path("artefactos"))
    ruta_mdl: Path = field(
        default_factory=lambda: Path(
            "modeloDinamico/ProyectoGlobalSimulacion(PrimerModeloTerminado).mdl"
        )
    )
    diques: tuple[ConfigDique, ...] = DIQUES_MENDOZA
    pesos_score: tuple[float, float, float] = (0.5, 0.3, 0.2)


@dataclass(frozen=True)
class ConfigSimulacion:
    seed: int = 42
    n_años: int = 500
    estrategias: tuple[str, ...] = (
        "prioridad_energia",
        "prioridad_riego",
        "balance",
    )
    embalse: ConfigEmbalse = field(
        default_factory=lambda: ConfigEmbalse(
            nombre="Potrerillos",
            capacidad_max_hm3=1885,
            altura_minima_m=970,
            altura_maxima_m=1210,
        )
    )
    dir_resultados: Path = field(default_factory=lambda: Path("resultados"))
