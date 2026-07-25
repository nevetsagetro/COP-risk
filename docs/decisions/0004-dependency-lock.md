# ADR 0004: estrategia de lock de dependencias

- Status: Accepted
- Date: 2026-07-25
- Accepted: 2026-07-25
- Decision owners: aprobación humana registrada

## Context

`pyproject.toml` limita Python a 3.12 y fija las tres dependencias directas de
desarrollo, pero sus dependencias transitivas se resuelven de nuevo en cada
instalación. No existe lock ni herramienta de lock aceptada. Este milestone no
añade herramientas, dependencias ni archivos generados.

## Requirements

- Resolución transitiva versionada y comprobable.
- Fuente declarativa conservada en `pyproject.toml`.
- Instalación bloqueada o frozen en desarrollo y CI.
- Política explícita de actualización y revisión del diff.
- Compatibilidad con Python 3.12 y las plataformas que se aprueben.
- Índices y credenciales fuera del lock.

## Options

### Mantener pins directos

Ventajas: sin tooling adicional y flujo pip conocido.

Inconvenientes: las transitivas pueden variar o desaparecer.

Riesgos: builds diferentes con el mismo commit.

Coste operativo: muy bajo, con reproducibilidad insuficiente.

### pip-tools y requirements compilados

Ventajas: salida instalable con pip, hashes opcionales y flujo ampliamente
conocido.

Inconvenientes: archivos derivados por entorno y disciplina para recompilarlos.

Riesgos: divergencia entre `pyproject.toml` y requirements compilados.

Coste operativo: bajo a medio.

### `uv.lock`

Ventajas:

- Lock único integrado con proyectos y grupos de dependencias.
- Comandos explícitos de comprobación y sincronización bloqueada.
- Resolución rápida y buen encaje con `pyproject.toml`.

Inconvenientes:

- Introduce la herramienta uv y un formato específico.
- Debe fijarse el bootstrap de uv y validar plataformas soportadas.

Riesgos: regeneración silenciosa o asumir portabilidad no probada.

Coste operativo: bajo.

### `pylock.toml` mediante tooling compatible

Ventajas: formato estandarizado y potencialmente independiente del resolver.

Inconvenientes: el pip 24.0 inspeccionado no ofrece el flujo necesario y la
madurez/compatibilidad deben verificarse antes de adoptarlo.

Riesgos: decidir por un flujo que el baseline actual no puede ejecutar.

Coste operativo: incierto hoy.

## Decision

`uv.lock` será la estrategia de lock versionado, manteniendo `pyproject.toml`
como fuente. Un milestone técnico posterior instalará uv, generará el lock y
definirá cómo ejecutar `uv lock --check` y `uv sync --locked`, revisar su diff
y actualizarlo.

Esta tarea no instala uv ni genera `uv.lock`. Plataformas soportadas, índices
permitidos, grupos y política de upgrade se resolverán antes o durante ese
milestone técnico.

## Consequences

- La instalación reproducible dependerá también de uv.
- Las dependencias directas seguirán declaradas en `pyproject.toml`.
- CI y documentación deberán usar modo locked/frozen.
- Los cambios de dependencias producirán un diff transitivo revisable.

## Reversibility

Media. Cambiar a pip-tools o a otro formato no altera las dependencias
declaradas, pero cambia bootstrap, CI, documentación y archivo de lock.

## Open questions

- ¿Qué plataformas y arquitecturas deben quedar resueltas?
- ¿Cómo se instala y fija la versión de uv?
- ¿Qué índices están permitidos?
- ¿Cómo se separan grupos de desarrollo y producción?
- ¿Quién aprueba actualizaciones y con qué frecuencia?
- ¿Se exigirán hashes adicionales o controles de procedencia?

## Sources

- [uv project locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [pip-tools documentation](https://pip-tools.readthedocs.io/)
- [Python pylock.toml specification](https://packaging.python.org/en/latest/specifications/pylock-toml/)
