# ExecPlan 0034: Home Credit Deep Learning Benchmark

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-25.
- Última actualización: 2026-10-25.
- Responsable: agente `coordinator`.
- Alcance: benchmark MLP tabular offline sobre Home Credit `features-v2`.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ADR-0032, ADR-0033 y ADR-0034.

## Propósito y resultado observable

The portfolio will show a controlled neural challenger after the classical
benchmark. The frontend will explain the architecture, early stopping,
parameter count, learning curve, validation result and limitations. It will not
create a champion or a lending decision.

## Base verificada

The classical milestone is tagged `v0.3.0-home-credit-classical`. Its v2
snapshot, classical report, feature ablation and read-only API are available.
The final test is unopened.

## Alcance

- Offline PyTorch MLP training and cached validation evidence.
- Read-only API exposure and neural scrollytelling.
- Tests, technical documentation, review, commit and separate tag.

## Fuera de alcance

- Opening the final test, FT-Transformer, GPU infrastructure, online training,
  MLflow, deployment, champion promotion, fairness claims, or real decisions.
- Calling training, preprocessing or CV from FastAPI or the browser.

## Decisiones

### Aceptadas

- PyTorch is an optional `deep-learning` dependency.
- Train-only preprocessing and train-only early stopping are required.
- Validation is evaluated once after the checkpoint is frozen.
- Average Precision is primary; ROC-AUC, Brier, log loss, precision, recall and
  F1 remain secondary evidence.

### Pendientes

- Whether a future neural architecture deserves additional tuning.
- Any promotion gate; this phase does not promote a model.

## Seguridad y restricciones

- Public anonymized data only; no PII or audit-only inputs.
- `test_status` remains `unopened`.
- Generated state, predictions and reports remain under ignored `runs/`.
- Missing artifacts produce an explicit unavailable state.

## Plan de ejecución

1. Implement and unit-test the offline MLP trainer.
2. Run it locally against the v2 snapshot and classical report.
3. Expose the materialized evidence in the API and story.
4. Refine the frontend's technical hierarchy without changing calculations.
5. Run full validation and commit each coherent phase separately.

## Validación y criterios de aceptación

```bash
.venv/bin/python scripts/run_home_credit_deep_learning.py
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/python scripts/validate_workflow.py docs/workflows/0034-home-credit-deep-learning.yaml
git diff --check
```

The cached report must include seed, feature version, architecture, parameter
count, split boundaries, learning curve, validation metrics, classical
comparison and `test_status: unopened`.

## Registro de progreso

- [x] Classical milestone preserved at its existing tag.
- [x] MLP trainer and CLI implemented.
- [x] Cached run, API/story integration and visual refinement.
- [x] Full validation, review, commit and tag.

## Hallazgos inesperados

- The first interrupted MLP attempt produced no artifacts; the benchmark is
  being rerun through the explicit offline CLI.

## Registro de decisiones del plan

- 2026-10-25 — Deep learning is an intermediate phase after the classical tag;
  changes remain independently revertible.
- 2026-10-25 — The application reads cached artifacts and never trains live.

## Resultados y retrospectiva

The offline run materialized `runs/home-credit-static-v2/deep-learning/` with
seed 42, architecture `(128, 64)`, 18,305 parameters, 11 completed epochs,
and validation Average Precision `0.2419`. The classical comparison remains
stronger on this split (XGBoost `0.2593`, CatBoost/LightGBM `0.2558`), so the
MLP is retained as a documented challenger rather than a replacement.
The API reads the cached report with `test_status: unopened`; the browser never
trains. The frontend adds the neural chapter and targeted visual refinement
without changing metrics or the UCI reference scope.

Validation completed: focused unit/service/API tests passed, full repository
tests passed, Ruff formatting/linting passed, mypy passed, workflow validation
passed, JavaScript syntax was reviewed through the browser-serving integration
path (Node.js is not installed in this environment), and `git diff --check`
passed.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0034-home-credit-deep-learning-benchmark.md
- docs/decisions/ADR-0034-home-credit-mlp.md
- docs/workflows/0034-home-credit-deep-learning.yaml
- src/cop/training/deep_learning.py
- src/cop/serving/home_credit.py
- scripts/run_home_credit_deep_learning.py
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

- feat(home-credit): add offline deep learning benchmark
