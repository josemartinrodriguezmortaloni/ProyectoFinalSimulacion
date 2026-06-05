# Resumen de Cambios: Fix Bug de JSON Serializable

## Cambios Implementados
- Modificado `simulador_hidrico.py` (Unidad 5) para castear tipos de `numpy` a tipos estándar de Python.
- Los valores de tipo `numpy.bool_` generados por comparaciones como `p_valor > 0.05` y `abs(correlacion) < ic` ahora se parsean explícitamente usando la función `bool()`.
- Los valores como estadísticos también se envuelven en `float()` para garantizar serialización.
- Se configuró la terminal a utf-8 para manejar caracteres especiales como '✓' durante la impresión en pantalla del script con `uv`.
- Se resolvieron los conflictos de Git y se actualizó la rama local.

## Verificación
- El script de simulación completó exitosamente las tres fases de operación (Validación de Aleatoriedad, Simulación de 500 años y Análisis de Resultados).
- Generación exitosa de los artefactos del programa (`resultados_simulacion.csv` y `validacion_estadistica.json`).

> [!TIP]
> Al exportar métricas estadísticas al formato estándar de JSON usando `json.dump`, es buena práctica castear las variables primitivas de bibliotecas como `numpy` y `pandas` a tipos predeterminados de Python para asegurar la compatibilidad sin necesidad de un `JSONEncoder` personalizado.
