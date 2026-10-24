# ExecPlan 0033: Home Credit Model Improvement Roadmap

## Estado del documento

- Estado: activo.
- Fecha inicial: 2026-10-25.
- Última actualización: 2026-10-25.
- Responsable: agente `coordinator`.
- Alcance: evolución controlada del benchmark académico Home Credit desde el
  baseline actual hasta un informe reproducible de modelos clásicos y deep
  learning.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ADR-0031, el plan 0032 y el
  roadmap solicitado por el usuario.

Este documento es un roadmap propuesto. No autoriza todavía añadir nuevas
dependencias, abrir el test, crear un champion ni presentar los resultados como
capacidad productiva.

## Propósito y resultado observable

La persona que revise el portfolio debe poder seguir una cadena de evidencia
completa:

```text
baseline fiable
  → hipótesis de features
  → ablación y contribución
  → benchmark de modelos
  → tuning reproducible
  → deep-learning benchmark opcional
  → robustez y explainability
  → informe público reproducible
```

Al finalizar el roadmap, la aplicación y la documentación deberán explicar en
lenguaje humano:

1. qué cambió entre una iteración y la siguiente;
2. qué seed, dataset, split y feature version se utilizaron;
3. si la mejora se mantuvo entre folds, seeds y validation;
4. por qué un candidato fue aceptado o rechazado;
5. qué significan AP, ROC-AUC, Brier, precision, recall y calibration;
6. qué conclusiones siguen siendo académicas y cuáles no están permitidas.

El test final permanece cerrado hasta que exista una autorización explícita y
un protocolo de evaluación congelado.

## Base verificada

Inspección realizada el 2026-10-25 con `pwd`, `git status --short`, `find`,
lectura de `README.md`, `AGENTS.md`, `PLANS.md`, el plan 0032 y los módulos de
datos, training y evaluación:

- El snapshot local Home Credit contiene 307,511 filas y 44 features de
  modelo.
- Las familias actuales son application, bureau, previous application e
  installments.
- El split es entity-disjoint 70/15/15 mediante hash estable de `SK_ID_CURR`.
- La validación tiene una prevalencia aproximada del 8.1%.
- Existen Logistic Regression y LightGBM con tres candidatos por familia.
- La búsqueda actual usa 3-fold stratified cross-validation y seed 42 en el
  código.
- El reporte actual no expone de forma completa el seed, la feature version ni
  el contrato de reproducibilidad como campos de la API.
- El endpoint académico y el frontend de scrollytelling ya muestran trials,
  validation, calibration, policy y comparación baseline → selected.
- El test final está cerrado y no debe utilizarse para selección, tuning,
  calibration, thresholding ni explainability.
- No se verificó todavía Optuna, MLflow, CatBoost, XGBoost, PyTorch, SHAP ni
  bootstrap como capacidades implementadas en el árbol actual.

## Alcance

### Wave 1 — Auditoría y limpieza del baseline

- Formalizar seed, dataset fingerprint, feature version, split contract,
  folds, library versions y parameters en los artefactos.
- Verificar leakage en agregaciones, preprocessing, resampling y evaluación.
- Reconciliar métricas de training, model lab, validation y policy.
- Crear una explicación humana del protocolo reproducible.

### Wave 2 — Feature Engineering v2

- Añadir ratios financieros y señales de missingness sólo con columnas
  disponibles y permitidas.
- Añadir agregados de comportamiento de bureau, previous applications e
  installments con ventanas relativas seguras.
- Ejecutar ablaciones feature-family y documentar hipótesis, disponibilidad,
  leakage checks y contribución.
- Versionar features sin sobrescribir `features-v0`.

### Wave 3 — Model Benchmark v2

- Mantener Logistic Regression y LightGBM como referencias.
- Añadir CatBoost y XGBoost sólo después de justificar dependencias, licencia,
  coste y compatibilidad local.
- Implementar búsqueda Optuna dentro de train-CV.
- Comparar class weighting y SMOTE-Tomek como challengers dentro de los folds.
- Mostrar parámetros, seeds, tiempos, folds, métricas y decisión de cada trial.

### Wave 4 — Deep Learning benchmark

- Implementar un MLP tabular en PyTorch como benchmark académico separado.
- Registrar curvas de aprendizaje, early stopping, seed y número de parámetros.
- Comparar contra el mejor modelo clásico usando exactamente los mismos splits
  y métricas.
- Considerar FT-Transformer sólo como propuesta posterior si el MLP aporta
  evidencia suficiente; no convertirlo en dependencia por defecto.

### Wave 5 — Explainability y robustez

- Añadir calibración, reliability diagrams, bootstrap y evaluación por
  segmentos permitidos.
- Añadir SHAP o permutation importance sólo con una metodología documentada y
  sin convertir asociación en causalidad.
- Medir estabilidad entre seeds y folds.
- Documentar errores, casos extremos y límites del benchmark.

### Wave 6 — Portfolio y entrega

- Crear model card y reportes de experimentos.
- Integrar la historia de iteraciones en la API y el frontend.
- Actualizar README con comandos reproducibles reales.
- Congelar una evaluación final sin abrir el test durante selección.
- Ejecutar revisión read-only y milestone finisher antes de cualquier commit.

## Fuera de alcance

- Uso de datos privados, PII o decisiones crediticias reales.
- Apertura del test para probar hipótesis durante el desarrollo.
- Promoción automática de un champion.
- Claims de fairness, causalidad, estabilidad temporal o utilidad productiva.
- Prefect, Docker Compose completo, cloud, feature store y operación productiva.
- Sustituir las 19 features UCI congeladas; UCI sigue siendo una referencia
  separada y no se mezclará con Home Credit.
- FT-Transformer como requisito de éxito de este roadmap.

## Decisiones

### Aceptadas y aplicables

- LightGBM es la familia primaria actual.
- Optuna es la tecnología aceptada para HPO.
- MLflow es la tecnología aceptada para tracking futuro.
- SMOTE-Tomek sólo se usa cuando la comparación experimental lo justifique y
  siempre dentro del training fold.
- El test final queda fuera de selección, HPO, early stopping, calibration,
  thresholds y explainability.
- Los atributos audit-only no son inputs de ningún modelo.

### Pendientes

- Aceptación de CatBoost y XGBoost como nuevas dependencias.
- Aceptación de PyTorch como dependencia del benchmark deep learning.
- Número definitivo de Optuna trials y presupuesto de cómputo.
- Gating cuantitativo para aceptar una mejora.
- Definición de segmentos de evaluación autorizados.
- Método y parámetros concretos de bootstrap, SHAP y calibración.
- Milestone de introducción de MLflow.

### Propuestas

- Usar AP como métrica primaria por el desbalance de clases.
- Usar ROC-AUC, Brier, log loss y precision/recall@capacity como métricas
  secundarias.
- Ejecutar al menos cinco seeds en un experimento de estabilidad antes de
  afirmar que una mejora es robusta.
- Mostrar cada experimento como `hypothesis → change → evidence → decision`.

## Seguridad y restricciones

- Todos los datos deben ser públicos anonimizados o sintéticos.
- Los artefactos no deben incluir IDs individuales, PII ni secretos.
- Cada feature debe documentar fuente, disponibilidad, transformación y test de
  leakage.
- Resampling y preprocessing deben ajustarse dentro de cada training fold.
- Las métricas de validation se usan para comprobación, no para repetir tuning
  indefinidamente.
- El test sólo podrá abrirse mediante un paso explícito y documentado después
  de congelar el protocolo.

## Plan de ejecución

Las waves y tasks ejecutables están en
`docs/workflows/0033-home-credit-model-improvement.yaml`. Cada task tiene un
owner, dependencias, allowlist y estado independiente.

1. Completar Wave 1 y obtener revisión read-only del contrato reproducible.
2. Implementar una feature family por iteración, empezando por ratios y
   terminando cada una con ablación.
3. Ejecutar benchmark clásico antes de considerar deep learning.
4. Añadir el MLP sólo si la comparación clásica está estable y documentada.
5. Completar robustez y explainability antes de actualizar la historia pública.
6. Cerrar con validación completa, revisión, model card y finisher.

## Validación y criterios de aceptación

Cada wave debe ejecutar los checks aplicables y conservar el test cerrado.

```bash
.venv/bin/python scripts/validate_workflow.py \
  docs/workflows/0033-home-credit-model-improvement.yaml
.venv/bin/python -m scripts.workflow_status \
  docs/workflows/0033-home-credit-model-improvement.yaml --json
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

Wave-specific evidence must include:

- reproducibility metadata and seed consistency;
- leakage and schema tests for each new feature family;
- ablation report with baseline and challenger metrics;
- model comparison with folds, parameters and runtime;
- deep-learning curves and parameter count if implemented;
- calibration, bootstrap, explainability and segment reports if implemented;
- human-readable iteration history in the API/frontend;
- explicit `test_status: unopened` until the final evaluation gate.

## Registro de progreso

- [x] Roadmap translated into six waves and bounded tasks.
- [x] Current baseline and missing reproducibility metadata audited.
- [ ] Wave 1 baseline contract implementation (in progress).
- [ ] Wave 2 Feature Engineering v2.
- [ ] Wave 3 Model Benchmark v2.
- [ ] Wave 4 Deep Learning benchmark.
- [ ] Wave 5 Explainability and robustness.
- [ ] Wave 6 Portfolio and final delivery.

## Hallazgos inesperados

- Seed 42 is already used by split, CV and model constructors, but the current
  generated reports do not expose it consistently.
- The current model lab contains only three candidates per model family, so its
  improvement evidence is useful but not a broad hyperparameter study.
- The current frontend can display iteration evidence, but it needs a richer
  reproducibility and human-explanation contract for future feature versions.
- CatBoost, XGBoost, PyTorch, Optuna, MLflow and SHAP must not be described as
  implemented until their files, dependencies, runs and tests are verified.

## Registro de decisiones del plan

- 2026-10-25 — The roadmap is proposed rather than active because new
  dependencies, quantitative gates and deep-learning scope remain pending.
- 2026-10-25 — The test remains closed across all six waves.
- 2026-10-25 — Feature versions and iteration records must preserve the
  baseline instead of overwriting it.

## Resultados y retrospectiva

No implementation has been performed under this proposed plan. The baseline
and the Home Credit academic frontend remain available as the starting point.
The main risk is adding complexity without a stable improvement; every wave
therefore requires an ablation, a validation comparison and a human-readable
decision record.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0033-home-credit-model-improvement-roadmap.md
- docs/workflows/0033-home-credit-model-improvement.yaml
- docs/decisions/
- docs/model-cards/
- src/cop/data/
- src/cop/evaluation/
- src/cop/training/
- src/cop/api.py
- src/cop/serving/
- scripts/
- tests/
- app/web/
- README.md

Generated artifacts forbidden:

- data/**
- runs/**
- models/**
- mlruns/**
- .venv/**

Expected commit message:

- feat(home-credit): improve reproducible model development
