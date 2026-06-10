# Contexto del Proyecto

## Estado Actual
El proyecto integra el modelo de dinámica de sistemas de Vensim (`modeloDinamico/*.mdl`, 4 embalses: Potrerillos, El Carrizal, El Nihuil y Agua del Toro) con los números pseudoaleatorios generados en Python, usando **PySD 3.14.3** como motor de simulación.

Se implementó una **arquitectura de pipeline batch por artefactos** (Pipes & Filters + functional core/imperative shell), elegida entre dos diseños propuestos:

```
generar → validar (gate) → convertir → simular (PySD) → analizar
```

- Cada fase es un subcomando del CLI (`uv run simular <fase>`) que lee/escribe artefactos en `artefactos/{seed}_{timestamp}/` (CSV + JSON + manifest de reproducibilidad).
- Las fases no se importan entre sí: solo comparten los esquemas de `persistencia/esquemas.py`.
- La fase `validar` es un quality gate: si los tests estadísticos rechazan (χ², KS, autocorrelación), el pipeline corta con exit 1 y no se simula.
- Los números generados se inyectan al `.mdl` vía `model.run(params={...})` de PySD, **sin modificar el archivo Vensim** (pisa los `WITH LOOKUP` de las entradas de agua de los 4 diques + `Temperatura Actual`).
- El simulador discreto original (Unidad 4) sigue intacto como `uv run simular eventos`.

Verificado e2e: pipeline completo corre en ~2 s, 16 tests unitarios en verde, ranking global comparando políticas `uniforme` vs `estacional` funcionando.

## Estructura nueva
```
src/simulador/
├── core/           # funciones puras: generacion, estadistica, conversion, kpis
├── persistencia/   # esquemas (contratos CSV) + repositorio de artefactos
├── fases/          # generar, validar, convertir, simular (única que importa pysd), analizar
├── cli.py          # argparse con subcomandos (+ alias --corrida ultima)
└── config.py       # + ConfigDique, DIQUES_MENDOZA, ConfigPipeline
```

## Decisiones Técnicas
- **Pipeline batch sobre OOP en capas**: cada unidad de la materia mapea 1:1 con una fase y deja evidencia inspeccionable para el informe; Monte Carlo paralelizable con `xargs -P` (corridas = directorios aislados).
- **PySD aislado en `fases/simular.py`**: cambiar de motor toca un solo archivo; la traducción `.mdl → .py` se cachea por mtime junto al modelo.
- **Fix estadístico**: la χ² original comparaba contra frecuencia uniforme (rechazaría datos Gamma legítimos); ahora es bondad de ajuste contra la Gamma ajustada con bins equiprobables y gl = k−1−2.
- **Reparto entre diques** por proporciones calibradas contra los lookups del `.mdl`: Potrerillos 0.55, Agua del Toro 0.18, Nihuil 0.15, Carrizal 0.12 (configurable en `DIQUES_MENDOZA`).
- **`numpy.random.default_rng(seed)`** en el core nuevo (en lugar de `np.random.seed` global): reproducibilidad sin estado global.
- Limpieza de repo: `resultados/` (output legacy regenerable) borrada y destrackeada; `.gitignore` ahora cubre `artefactos/` y `.pytest_cache/`.

## Pendientes
- Calibrar la oferta hídrica: la satisfacción de riego media da ~0.29 (Potrerillos recibe ~144 hm³/mes vs ~235 de los lookups originales). Ajustar proporciones, área de cuenca o media de afluentes.
- Definir la asignación definitiva de Lluvia/Nieve/Afluentes por dique (hoy: `uniforme` y `estacional` como estrategias registradas).
- Corrida Monte Carlo masiva (100+ seeds) y análisis de distribuciones de KPIs.
- Commit de todos los cambios (quedaron staged las deleciones de `resultados/`; el resto sin commitear).
