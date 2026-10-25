# ExecPlan 0016: presentación Streamlit del MVP académico

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: interfaz local opcional para presentar el baseline UCI.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y alcance confirmado por el usuario.

## Propósito y resultado observable

Una persona puede abrir una interfaz local con dos vistas: resultados
académicos con tablas y gráficas, y una predicción ilustrativa introduciendo
las 19 features UCI.

## Base verificada

El repositorio contiene un baseline UCI funcional, artefactos locales bajo
`runs/` y una CLI de demo. No contiene todavía una interfaz web.

## Alcance

- `app/streamlit_app.py`.
- Extra opcional `demo` en `pyproject.toml`.
- README, CHANGELOG y prueba manual documentada.

## Fuera de alcance

Serving productivo, API, autenticación, persistencia, reentrenamiento desde la
UI, apertura automática del test, promoción, rollback, cloud y Docker.

## Decisiones

### Aceptadas

La app carga los modelos del run congelado y puede ejecutar development si el
run aún no existe. La predicción es descriptiva y usa threshold 0.5 únicamente
como referencia visual.

### Pendientes

No se introduce ninguna decisión de producción.

### Propuestas

No aplica.

## Seguridad y restricciones

La app no recibe PII, no utiliza atributos `audit_only`, no modifica artefactos
y no abre el test. Debe mostrar el disclaimer en la interfaz.

## Plan de ejecución

1. Implementar las vistas Streamlit y carga de artefactos.
2. Añadir dependencia opcional y documentación.
3. Instalar la extra en el entorno local y validar importación/arranque.
4. Ejecutar las validaciones del repositorio.

## Validación y criterios de aceptación

```bash
.venv/bin/python -m pip install -e '.[demo]'
.venv/bin/python -m streamlit run app/streamlit_app.py --server.headless true
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
git diff --check
```

El arranque debe responder en localhost sin abrir el test ni requerir una
cuenta externa.

## Registro de progreso

- [x] 2026-10-24: app, vistas, dependencia opcional y documentación añadidas.
- [x] 2026-10-24: extra `demo` instalada y servidor Streamlit arrancado en
  localhost; `/_stcore/health` respondió `ok`.
- [x] 2026-10-24: Streamlit AppTest ejecutó las vistas de resultados y
  predicción sin excepciones; la predicción mostró dos métricas.
- [x] 2026-10-24: Ruff format/check, mypy, pytest (103 tests) y `git diff
  --check` correctos.
- [x] 2026-10-24: campos de predicción traducidos a etiquetas human-readable,
  estados de pago convertidos a selectores explicados y gráficos convertidos
  a Altair estático sin zoom interno.
- [ ] Staging revisado sin commit.

## Hallazgos inesperados

El primer arranque en sandbox necesitó permisos de socket local; con permisos
de ejecución local el servidor arrancó y respondió correctamente. La app no
requiere cuenta externa ni abrió el test.

## Registro de decisiones del plan

- 2026-10-24: se eligió Streamlit frente a una API porque el objetivo es una
  presentación local visual del MVP.

## Resultados y retrospectiva

La interfaz local quedó verificada en sus dos vistas. El run UCI existente se
reutiliza y la app mantiene el disclaimer académico y el test cerrado.
La segunda revisión de UX eliminó el zoom interno de los gráficos y añadió
explicaciones a las variables y codificaciones UCI del formulario.

## Version-control allowlist

Tracked files or directories allowed:

- CHANGELOG.md
- README.md
- app/streamlit_app.py
- docs/plans/0016-streamlit-portfolio-demo.md
- pyproject.toml

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(demo): add Streamlit academic portfolio interface
