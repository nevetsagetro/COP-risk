# ExecPlan 0021: laboratorio académico de tuning reproducible

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: comparar y ajustar Logistic Regression y LightGBM sin alterar el
  baseline servido.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y la solicitud explícita de
  demostrar desarrollo y ajuste de modelos.

## Propósito y resultado observable

El repositorio tendrá un CLI que produzca un informe JSON reproducible con los
candidatos probados, sus métricas de cross-validation, los parámetros
seleccionados, el umbral elegido usando únicamente predicciones out-of-fold de
train y la evaluación final de validation. El test permanece cerrado.

## Base verificada

Existe un baseline UCI con Logistic Regression y LightGBM de parámetros fijos y
un challenger LightGBM con features derivadas. No existía un informe común de
tuning para varios modelos ni una selección de umbral separada de validation.

## Alcance

- Añadir un laboratorio reproducible de candidatos para Logistic Regression y
  LightGBM.
- Seleccionar candidatos y umbral sólo con folds de train.
- Evaluar los seleccionados en validation con el umbral aprendido y con 0.5.
- Añadir tests y un CLI de demostración.
- Documentar el comando y sus límites.

## Fuera de alcance

- Cambiar el modelo del serving.
- Abrir o reevaluar el test final.
- Promover automáticamente un modelo.
- Añadir MLflow, Prefect, Optuna o infraestructura de despliegue en este
  milestone.
- Presentar los resultados como rendimiento crediticio real.

## Decisiones

### Aceptadas

- La selección usa sólo train mediante StratifiedKFold reproducible.
- Average Precision es la métrica primaria del ranking académico; ROC-AUC,
  Brier y log loss se conservan para la comparación.
- El umbral se selecciona en out-of-fold train maximizando F1, con recall como
  desempate, y se evalúa después en validation.
- El baseline de serving permanece intacto.

### Pendientes

- La incorporación futura de Optuna y MLflow requiere su propio alcance,
  dependencia y validación.

### Propuestas

- Exponer posteriormente el informe en el frontend analítico como una tabla de
  experimentos, sin convertirlo en un mecanismo de promoción.

## Seguridad y restricciones

- Se usan únicamente las 19 features UCI aprobadas.
- No se lee el split test ni columnas audit-only.
- El umbral no se elige usando validation ni test.
- Los resultados son académicos y descriptivos.

## Plan de ejecución

1. Implementar búsqueda pequeña y determinista para ambos modelos.
2. Implementar selección de umbral con OOF train y evaluación validation.
3. Añadir CLI, tests y documentación.
4. Ejecutar formato, lint, tipos, suite completa y el experimento.

## Validación y criterios de aceptación

```bash
.venv/bin/python scripts/run_academic_model_lab.py
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/pytest
git diff --check
```

La aceptación requiere que ambos modelos tengan candidatos y métricas, que el
umbral elegido esté entre 0 y 1, que el resultado indique `test_status` como
`unopened` y que la suite existente siga verde.

## Registro de progreso

- [x] Implementación del laboratorio y selección OOF.
- [x] CLI y tests.
- [x] Documentación y ejecución reproducible.
- [x] Validaciones obligatorias.

## Hallazgos inesperados

La selección de umbral es una decisión distinta de la selección de modelo: un
modelo puede mejorar AP y aun así producir peor F1 en el umbral fijo 0.5.

## Registro de decisiones del plan

- 2026-10-24: se mantiene una búsqueda pequeña explícita para que el demo sea
  rápido, auditable y no añada una dependencia nueva antes de fijar el lock.

## Resultados y retrospectiva

El CLI se ejecutó con tres folds y mantuvo `test_status` como `unopened`. La
selección observada fue:

- LightGBM: `learning_rate=0.03`, `n_estimators=400`, `num_leaves=15`,
  Average Precision CV `0.551469` y umbral aprendido `0.31`.
- Logistic Regression: `C=0.1`, `class_weight=None`, Average Precision CV
  `0.533323` y umbral aprendido `0.23`.

En validation, LightGBM obtuvo F1 `0.4720` con `0.5` y `0.5500` con el umbral
aprendido; Logistic Regression obtuvo F1 `0.4707` y `0.5483`, respectivamente.
El resultado demuestra el efecto del threshold tuning, pero no autoriza
promoción ni claims de rendimiento real.

Validaciones ejecutadas:

- `.venv/bin/pytest -q tests/unit/test_model_lab.py tests/integration/test_model_lab_integration.py`: 2 passed.
- `.venv/bin/python scripts/run_academic_model_lab.py --folds 3`: completado.
- `.venv/bin/pytest -q`: 117 passed.
- `.venv/bin/ruff format --check .`: 73 files already formatted.
- `.venv/bin/ruff check .`: passed.
- `.venv/bin/mypy src tests scripts`: no issues in 70 source files.
- `git diff --check`: passed.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0021-academic-model-lab.md
- src/cop/evaluation/model_lab.py
- scripts/run_academic_model_lab.py
- tests/unit/test_model_lab.py
- tests/integration/test_model_lab_integration.py
- README.md

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(ml): add reproducible academic model lab
