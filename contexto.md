# Contexto del Proyecto

## Estado Actual
- Bug en `simulador_hidrico.py` corregido.
- Tipos de numpy (`numpy.bool_` y `numpy.float64`) causaban `TypeError` al hacer `json.dump`.
- Se castearon valores estadísticos (`chi2_stat`, `p_valor`, `correlacion`) a tipos estándar de Python (`float`, `bool`).
- Se ejecutó `git stash` y `git pull` para resolver conflicto de merge en `resultados/validacion_estadistica.json`.
- Simulación corriendo para verificar fix.

## Decisiones Técnicas
- Casteo explícito en lugar de custom JSON encoder para simplicidad (SRP cumplido).
- Git stash para limpiar archivos generados antes del pull.

## Pendientes
- Verificar ejecución exitosa de simulación.
- Actualizar `walkthrough.md` con evidencia.
