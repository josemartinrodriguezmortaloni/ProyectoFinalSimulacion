from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ConfigEmbalse:
    nombre: str
    capacidad_max_hm3: float
    altura_minima_m: float
    altura_maxima_m: float


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
