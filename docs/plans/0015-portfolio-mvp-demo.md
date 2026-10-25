# ExecPlan 0015: demo MVP local para portfolio

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: una CLI de demostración sobre el baseline académico UCI existente.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y el alcance confirmado por el usuario.

## Propósito y resultado observable

Una persona puede ejecutar una orden local para entrenar o reutilizar el run de
development, ver métricas de validation y comprobar que el test sigue cerrado.

## Base verificada

El baseline UCI de `docs/plans/0014-uci-baseline-models.md` ya entrena Logistic
Regression y LightGBM sobre datos locales, guarda artefactos bajo `runs/` y
mantiene el test separado. La CLI existente devuelve únicamente la ruta del
run.

## Alcance

- CLI `scripts/run_mvp_demo.py`.
- Test de integración de la salida de demo.
- Documentación de uso en README y CHANGELOG.

## Fuera de alcance

API, serving, cloud, MLflow, Prefect, monitoring, tuning, resampling,
promoción, rollback y cualquier uso crediticio real.

## Decisiones

### Aceptadas

La demo usa solo train/validation y no abre el test. Reutiliza el baseline
congelado y sus artefactos verificables.

### Pendientes

No hay decisiones arquitectónicas pendientes introducidas por este cambio.

### Propuestas

No aplica.

## Seguridad y restricciones

No se incluyen datos ni artefactos en Git. El resumen conserva el aviso de uso
académico y muestra el test como `unopened`.

## Plan de ejecución

1. Añadir la CLI de demo sobre `train_development`.
2. Añadir una prueba de salida estable.
3. Actualizar documentación y changelog.
4. Ejecutar validaciones completas y preparar staging mediante allowlist.

## Validación y criterios de aceptación

```bash
.venv/bin/python scripts/run_mvp_demo.py
.venv/bin/python scripts/run_mvp_demo.py --json
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
git diff --check
```

## Registro de progreso

- [x] 2026-10-24: CLI, test, README y CHANGELOG implementados.
- [x] 2026-10-24: README y CHANGELOG actualizados.
- [x] 2026-10-24: demo human-readable y JSON ejecutadas con el snapshot UCI
  local; Ruff, mypy, pytest (103 tests) y `git diff --check` correctos.
- [ ] Allowlist revisada y staging preparado; queda pendiente por coexistir
  con el staging previo del milestone 0014, sin commit autorizado.

## Hallazgos inesperados

Ninguno.

## Registro de decisiones del plan

- 2026-10-24: la demo no finaliza el test automáticamente para preservar el
  contrato consumible del baseline.

## Resultados y retrospectiva

La demo se ejecutó correctamente y reutilizó el run
`uci-baseline-c52cb3e02f0bec92fa6675a21a55af04e73cdd40027762a1c373d98599a299fb`.
Mostró validation ROC-AUC 0.783911 para LightGBM y 0.774804 para Logistic
Regression, manteniendo el test como `unopened`. La salida JSON también fue
verificada. El plan queda completado; el staging conjunto permanece pendiente
de una decisión explícita sobre el commit de los milestones 0014 y 0015.

## Version-control allowlist

Tracked files or directories allowed:

- CHANGELOG.md
- README.md
- docs/plans/0015-portfolio-mvp-demo.md
- scripts/run_mvp_demo.py
- tests/integration/test_mvp_demo.py

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(demo): add runnable local academic MVP
