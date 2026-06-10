# Resumen de Cambios: Integración PySD + Pipeline por Artefactos

## Cambios Implementados

### Dependencias
- Agregado `pysd >= 3.14.3` a `pyproject.toml` con `uv add pysd` (convive sin conflictos con pandas 3.0.3 y numpy 2.x).
- Agregado `pytest` como dependencia de desarrollo (`uv add --dev pytest`).

### Arquitectura nueva (pipeline batch)
- **`src/simulador/core/`** — núcleo funcional puro (sin I/O):
  - `generacion.py`: distribuciones climáticas (Gamma para precipitación, Normal para fusión/afluentes, demanda estacional, temperatura senoidal) con `np.random.default_rng` inyectado.
  - `estadistica.py`: tests de hipótesis como dataclasses congeladas. **Fix importante**: la χ² ahora es bondad de ajuste contra la Gamma ajustada por momentos con bins equiprobables (la versión anterior comparaba contra frecuencia uniforme, lo que rechazaría datos Gamma válidos).
  - `conversion.py`: física de cuenca (mm + m³/s → hm³/mes) y pesos estacionales mendocinos (deshielo pica dic–feb).
  - `kpis.py`: indicadores agregados + score multiobjetivo (`0.5·riego + 0.3·energía − 0.2·crisis`).
- **`src/simulador/persistencia/`** — esquemas de los CSV (contratos entre fases) y `RepositorioArtefactos` con `ManifestCorrida` (seed, hash del `.mdl`, versión de PySD).
- **`src/simulador/fases/`** — las 5 fases del pipeline; `simular.py` es el **único módulo que importa pysd** e inyecta las series por dique con `model.run(params={...})`, pisando los `WITH LOOKUP` sin tocar el `.mdl`.
- **`src/simulador/cli.py`** — subcomandos `generar / validar / convertir / simular / analizar / pipeline / eventos`, con alias `--corrida ultima`.
- **`src/simulador/config.py`** — agregados `ConfigDique`, `DIQUES_MENDOZA` (los 4 embalses con sus variables Vensim y proporciones 0.55/0.18/0.15/0.12) y `ConfigPipeline`. Lo existente no se tocó.
- **`tests/test_core.py`** — 16 tests unitarios del núcleo (conversión contra el ejemplo de clase, reproducibilidad por seed, gate acepta/rechaza, KPIs, esquemas).
- **`README.md`** — documentación completa: arquitectura, uso, artefactos, integración PySD, troubleshooting.

### Entry points y limpieza
- `src/simulador/__main__.py` y `src/__main__.py` ahora delegan en el mismo CLI (`python src pipeline ...` ≡ `uv run simular pipeline ...`). El flujo viejo quedó como subcomando `eventos`.
- `resultados/` (output regenerable del modo legacy) borrada y destrackeada con `git rm --cached`; `.gitignore` actualizado con `artefactos/` y `.pytest_cache/`.

## Verificación
- **Smoke test PySD**: el `.mdl` traduce completo (90 variables, ninguna faltante) y la inyección funciona — con entrada=0 el volumen de Potrerillos cae mes a mes.
- **Tests**: `uv run pytest tests/ -q` → 16 passed.
- **E2E**: `uv run simular pipeline --seed 42` corre las 5 fases en ~2 s; gate aceptado (χ² p=0.19, KS p=0.89); 4 escenarios generados; 121 meses simulados; KPIs calculados.
- **Ranking global**: `uv run simular analizar --todas` compara corridas `uniforme` (score 0.440) vs `estacional` (score 0.409) y escribe `artefactos/ranking_global.csv`.
- **Trazabilidad**: cada corrida guarda manifest con seed, asignación, proporciones, hash del `.mdl` y versión de PySD.

> [!TIP]
> PySD permite reemplazar cualquier variable del modelo Vensim pasando una `pandas.Series` indexada por tiempo en el argumento `params` de `model.run()`: interpola linealmente entre puntos y no hace falta editar el `.mdl`. La traducción `.mdl → .py` conviene cachearla (PySD la escribe junto al modelo) porque `pysd.load()` es mucho más rápido que `read_vensim()`.

> [!NOTE]
> Hallazgo para la próxima sesión: la satisfacción de riego media da ~0.29 porque la oferta generada (~144 hm³/mes para Potrerillos) queda por debajo de los lookups originales del `.mdl` (~235 hm³/mes). Hay que calibrar proporciones de reparto, área de cuenca o media de afluentes.
