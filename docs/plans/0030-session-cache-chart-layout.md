# ExecPlan 0030: cache de sesión y layout estable del model lab

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: evitar repetir la carga del informe en una sesión y corregir el
  primer cálculo de ancho del gráfico.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0029.

## Propósito y resultado observable

La primera carga solicita el informe y lo guarda en `sessionStorage`. Las
recargas de la misma pestaña/sesión renderizan el informe localmente sin pedir
otra vez el endpoint. El chart se hace visible antes de que Plotly mida su
contenedor y recibe un resize inicial.

## Base verificada

El backend ya tenía cache de proceso, pero el navegador solicitaba el endpoint
en cada carga. El contenedor de resultados permanecía oculto al crear el chart,
provocando un primer ancho reducido y un reajuste posterior.

## Alcance

- Añadir cache de sesión versionada.
- Renderizar tras quitar `hidden`.
- Forzar resize inicial compatible con responsive Plotly.
- Versionar asset y actualizar smoke test.

## Fuera de alcance

- Persistir resultados entre sesiones o usuarios.
- Cambiar el cálculo del laboratorio.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q tests/integration/test_api.py::test_health_and_static_frontend
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Cache `sessionStorage`.
- [x] Layout visible antes de medir.
- [x] Resize inicial y validaciones.

## Resultados y retrospectiva

El informe queda cacheado por sesión en navegador y el chart ya no depende de
un segundo resize para ocupar el ancho correcto.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0030-session-cache-chart-layout.md
- app/web/app.js
- app/web/index.html
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- fix(web): cache model lab per session and stabilize chart layout
