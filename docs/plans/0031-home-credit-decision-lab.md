# ExecPlan 0031: Home Credit Decision Lab

## Estado del documento

- Estado: activo.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: nueva vertical académica orientada a decisiones operativas sobre
  datos tabulares con historial y varias tablas relacionadas.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, `docs/plans/0028-dataset-to-decision-story.md`
  y la solicitud explícita de evolucionar COP más allá del notebook.

## Propósito y resultado observable

La siguiente vertical mostrará cómo un ML Engineer convierte datos de crédito
relacionados en una política de revisión académica: qué información está
disponible en el momento de decisión, qué features se construyen, qué modelos
se comparan, qué threshold/top-k se elige y cómo se presenta una predicción
con contexto y limitaciones.

La app deberá permitir recorrer:

```text
dataset y procedencia
  → contrato y disponibilidad temporal
  → joins y feature engineering
  → baseline y tuning
  → calibración
  → decisión bajo capacidad limitada
  → demo de caso
```

## Base verificada

El repositorio tiene una vertical UCI académica local, reproducible y
funcional, con Logistic Regression, LightGBM, KNN, tuning, threshold y
frontend. Esa vertical sigue siendo baseline; no es evidencia de desempeño
real ni temporal.

Home Credit Default Risk es un candidato público con tablas de aplicación,
créditos previos, balances y pagos. Su incorporación todavía no está aceptada
en el árbol, sus reglas de competición deben revisarse y los archivos no están
presentes en el repositorio.

## Alcance propuesto

### Fase A — gate de datos

- Registrar fuente, licencia/reglas, versión y hashes.
- Verificar esquema, target, missingness, duplicados y cardinalidades.
- Documentar columnas disponibles antes de la decisión y columnas posteriores.
- Separar cualquier atributo audit-only.
- Rechazar el dataset si no permite una ventana temporal defendible.

### Fase B — vertical de features

- Crear un adaptador aislado de UCI.
- Mantener joins y agregaciones en módulos de features, no en HTTP.
- Construir agregados históricos sólo con datos previos al snapshot.
- Generar un manifest de features, filas, hashes y ventanas.

### Fase C — experimentación

- Logistic Regression como baseline.
- LightGBM como modelo principal.
- KNN u otra familia sólo como benchmark justificable.
- Optuna para tuning reproducible.
- MLflow para parámetros, métricas, artefactos y versiones.
- Calibración y evaluación de Precision@k, Recall@k, AP, Brier y utilidad.

### Fase D — app analítica

- Timeline del dataset al modelo.
- Tabla de trials y parámetros.
- Curvas de calibración y ranking.
- Selector de capacidad (`top 1%`, `top 5%`, `top 10%`).
- Comparación de políticas, no sólo de modelos.
- Demo de caso con explicación de features y advertencias.
- Estado explícito: experimento, validation, test, candidate o promoted.

## Fuera de alcance

- Decisiones reales de concesión o denegación de crédito.
- Uso de PII o datos de clientes.
- Descargar datos automáticamente desde la API web.
- Promoción automática.
- Cambiar UCI o romper su contrato para acomodar Home Credit.
- Cloud, autenticación o despliegue productivo.

## Decisiones

### Aceptadas

- COP sigue siendo local-first y académico.
- El modelo se elige por una política de decisión definida, no por accuracy
  aislada.
- El test final permanece fuera de selección, calibración y threshold.
- La app cuenta el proceso completo y conserva la evidencia técnica.

### Pendientes

- Aceptación formal de Home Credit y sus reglas de uso.
- Target, horizonte, snapshot, ventana de observación y split temporal exactos.
- Capacidad operativa simulada y función de utilidad.
- Gates cuantitativos para elegir challenger/champion.
- Incorporación concreta de Optuna y MLflow.

### Propuestas

- Empezar con una tabla principal y dos tablas históricas, dejando la
  complejidad restante para una fase posterior.
- Elegir una política top-k para que el resultado sea interpretable:
  “con capacidad de revisar el 10%, ¿qué modelo concentra más eventos?”.

## Seguridad y restricciones

- No descargar ni introducir archivos del nuevo dataset hasta cerrar el gate de
  licencia y reglas.
- No usar columnas posteriores al momento de decisión.
- No usar atributos protegidos como inputs.
- No afirmar que una métrica académica implica utilidad crediticia real.

## Plan de ejecución

1. Crear ADR de aceptación o rechazo de Home Credit.
2. Implementar inspector de adquisición y contrato de vertical.
3. Materializar un snapshot local sólo después del gate.
4. Implementar split temporal y manifest reproducible.
5. Implementar features agregadas con tests de leakage.
6. Añadir experimento Optuna/MLflow controlado.
7. Extender la app con políticas top-k, calibración y error analysis.
8. Comparar challenger contra el baseline y documentar la decisión.

The multi-agent execution contract is defined in
`docs/workflows/0031-home-credit-decision-lab.yaml`. The coordinator must use
that manifest to assign bounded Tasks to the named agents, verify dependencies,
and keep each implementation inside its allowlist.

## Validación y criterios de aceptación

```bash
python3 scripts/evaluate_home_credit_candidate.py
python3 -m pytest -q
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests scripts
git diff --check
```

No se aceptará la vertical si falta procedencia, si el split temporal no es
defendible o si una feature usa información posterior al snapshot.

## Registro de progreso

- [x] App UCI dataset-to-decision implementada y etiquetada en `v0.2.0`.
- [x] Nuevo proyecto separado de la vertical UCI.
- [x] Gate tooling implemented; the local archive passes structural checks and static-benchmark scope is accepted.
- [x] Read-only workflow status command implemented; no task is ready while HC-001 awaits review.
- [x] Reusable validation capacity-policy metrics and API/frontend demonstration implemented on the existing UCI baseline.
- [x] Validation calibration curve and API/frontend explanation implemented on the existing UCI baseline.
- [x] Static entity-disjoint feature pipeline.
- [x] Home Credit static baseline and train-CV model-search report.
- [x] Validation capacity-policy report at 1%, 5%, 10%, and 20% review budgets.
- [x] Read-only Home Credit analytical API and English-first frontend panel.
- [x] Home Credit promoted to the primary frontend narrative; UCI is labeled as a reference baseline.
- [ ] Home Credit top-k policy API and analytical app integration.

## Hallazgos inesperados

El tamaño del archivo no es el criterio principal de calidad. Una vertical más
grande sólo aporta valor si contiene señal disponible antes de la decisión y
permite validar estabilidad temporalmente.

## Registro de decisiones del plan

- 2026-10-24: Home Credit queda como candidato de investigación, no como
  dataset aceptado. La app actual se cierra primero con UCI para conservar una
  demo reproducible mientras se ejecutan los gates.

## Resultados y retrospectiva

Validación ejecutada el 2026-10-24:

- `python3 -m scripts.workflow_status` devuelve `ready_tasks=0`, porque
  `HC-001` está en `complete_pending_review` y no se permite tratarlo como
  una dependencia completada.
- `python3 -m pytest -q` devuelve `125 passed`.
- The capacity-policy and calibration APIs/frontend compare validation evidence
  without opening the test; focused policy, calibration, and API tests pass.
- Ruff format, Ruff check, mypy y `git diff --check` pasan.
- The Home Credit inspector now returns `schema_inspected_pending_methodology`:
  all required files are present, train/test target separation is valid, and
  the data dictionary is available.
- The classic archive has no application timestamp, so `SK_ID_CURR` cannot be
  used as a temporal proxy. No Home Credit model or feature pipeline has been
  used for temporal claims.
- The materialized snapshot contains 307,511 entities and 44 model features;
  train/validation/test are 215,024/46,281/46,206 rows with disjoint IDs.
- The static model lab selected LightGBM trial 03 by train-CV Average Precision
  (`0.242777` mean); validation AP is `0.253194` and validation ROC-AUC is
  `0.762637`. The final test remains unopened.
- The analytical endpoint exposes the same report and the frontend shows the
  selected trials, validation metrics, and bounded-capacity policy results.
- Full validation now returns `131 passed`; Ruff format/check, mypy, and
  `git diff --check` pass.

Este plan no autoriza todavía claims temporales del nuevo dataset. La siguiente
acción válida es una revisión independiente de HC-001 que rechace el uso
temporal o autorice explícitamente una vertical estática con sus limitaciones.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0031-home-credit-decision-lab.md
- docs/workflows/0031-home-credit-decision-lab.yaml
- docs/workflows/README.md
- scripts/__init__.py
- scripts/validate_workflow.py
- scripts/workflow_status.py
- tests/unit/test_validate_workflow.py
- tests/unit/test_workflow_status.py
- src/cop/evaluation/policy.py
- src/cop/evaluation/calibration.py
- src/cop/serving/academic.py
- src/cop/api.py
- docs/decisions/ADR-0031-home-credit-dataset.md
- scripts/evaluate_home_credit_candidate.py
- scripts/build_home_credit_snapshot.py
- scripts/train_home_credit_baseline.py
- scripts/run_home_credit_model_lab.py
- scripts/run_home_credit_policy.py
- src/cop/data/home_credit.py
- src/cop/features/home_credit.py
- src/cop/evaluation/home_credit.py
- src/cop/training/home_credit.py
- src/cop/serving/home_credit.py
- tests/unit/data/test_home_credit.py
- tests/unit/test_home_credit_training.py
- tests/unit/test_home_credit_model_lab.py
- tests/unit/test_home_credit_service.py
- app/web/
- tests/unit/test_policy.py
- tests/unit/test_calibration.py
- tests/integration/test_api.py
- tests/

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(home-credit): add decision lab vertical
