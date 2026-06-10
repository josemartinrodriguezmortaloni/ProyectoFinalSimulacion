"""Núcleo funcional puro del pipeline: sin I/O, sin estado, sin prints.

Todo lo que hay acá son funciones deterministas (dado un rng) que
transforman datos. El shell imperativo vive en `simulador.fases` y
`simulador.persistencia`.
"""
