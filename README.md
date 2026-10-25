# COP · Credit Risk Model Labs

COP is a local-first portfolio project for demonstrating a reproducible credit-risk machine-learning workflow: data contracts, controlled splits, feature engineering, model comparison, threshold policies, model serving, and human-readable analysis.

> **Scope:** COP is an academic and portfolio demonstration. It is not approved for real credit decisions. Use only public anonymized or synthetic data. Do not use its outputs to approve, deny, or modify credit.

## Current status

The repository currently contains two separate academic data verticals:

| Vertical | Purpose | Current interface |
| --- | --- | --- |
| **Home Credit** | Model-development evidence: feature construction, trials, validation, policy analysis, and the cached MLP challenger | FastAPI + static Plotly frontend |
| **UCI Default of Credit Card Clients** | Reproducible baseline with Logistic Regression and LightGBM, threshold analysis, and anonymized what-if cases | FastAPI + static Plotly frontend; Streamlit fallback |

The frontend keeps both projects separate. It reads local cached artifacts and does not train models, tune parameters, or open the final test while the application is running.

Implemented and verified in the repository:

- Python package and local API under `src/cop`;
- public anonymized UCI baseline with train/validation development and a closed final test;
- Home Credit cached academic artifacts for feature engineering, ablation, cross-validation, tuning, classical challengers, policy analysis, and the MLP milestone;
- FastAPI endpoints and an English-first static HTML/Plotly frontend with an optional `EN / ES` toggle;
- reproducible CLI jobs, tests, linting, and type checking;
- synthetic data generation and split utilities kept isolated from the UCI pipeline.

Not production-ready or approved by this repository:

- no production champion, promotion, rollback, or lending authorization;
- no live retraining from the browser;
- no MLflow persistence, Prefect orchestration, Evidently monitoring, Grafana dashboard, or cloud deployment as an operational system;
- no fairness or real-world performance claim.

## Quick start

Requirements: Python 3.12, Git, and the development dependencies declared in `pyproject.toml`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev,api]'
python3 -m uvicorn cop.api:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

The API is read-only with respect to model development: it serves local reports and model artifacts. Opening the application never retrains a model or runs tuning.

Useful endpoints:

```text
/health
/api/overview
/api/metrics
/api/roc
/api/probabilities
/api/calibration
/api/examples
/api/threshold-sweep?model=lightgbm
/api/model-lab
/api/home-credit
/api/home-credit/academic
/api/predict
```

## Product structure

The frontend presents the two datasets as independent labs.

### Home Credit Decision Lab

This is the model-development story. It explains:

1. what the source `TARGET` represents;
2. which train, validation, and test evidence is open;
3. how application data becomes aggregated features;
4. how Logistic Regression, LightGBM, CatBoost, XGBoost, and the MLP challenger are compared;
5. how cross-validation and validation are interpreted;
6. how review capacity changes precision, recall, and lift;
7. why the result remains an academic static benchmark.

Home Credit results are materialized offline under `runs/`. The browser only presents those cached JSON/CSV artifacts.

### UCI Reference Baseline

This is the original academic baseline. It uses the 19 frozen UCI variables and compares Logistic Regression with LightGBM. The final test remains closed unless explicitly finalized through the documented CLI.

The UCI simulator supports public anonymized validation cases using the convention `UCI-VAL-####`. A user can change one, several, or all variables without being forced to edit unrelated fields.

## Reproducible model development

### UCI baseline

```bash
python3 scripts/train_uci_baseline.py
python3 scripts/run_mvp_demo.py
```

The development flow fits on train, evaluates selected candidates on validation, and keeps the final test outside selection. To explicitly finalize the test, use the separate command below only when that action is intended:

```bash
python3 scripts/train_uci_baseline.py --finalize-test
```

The finalization is explicit and cannot be reopened or overwritten. UCI results are descriptive academic benchmark results; they do not select a production champion.

### Home Credit model-improvement milestone

Home Credit experiments are executed offline and cached:

- feature engineering and feature-family ablation;
- reproducible train cross-validation;
- classical model trials;
- Optuna-based parameter search where the cached experiment supports it;
- validation comparison;
- review-capacity policy analysis;
- cached MLP challenger evidence as a separate intermediate milestone.

Reproduction requires the recorded dataset fingerprint, feature version, split seed, experiment seed, and model parameters. The final test remains closed during development.

### Academic model lab

```bash
python3 scripts/run_academic_model_lab.py
```

The lab compares Logistic Regression, LightGBM, and KNN candidates using cross-validation over train. KNN is included as an academic benchmark with scaled numeric variables; its presence does not imply that it is the selected model. Candidates are compared by the declared metric and then checked on validation.

## Data and methodological contract

- Only public anonymized or synthetic data is allowed.
- Splits are reproducible and must prevent target leakage and temporal leakage.
- Resampling and preprocessing are fit inside training folds only.
- The final test remains outside feature selection, hyperparameter search, calibration, early stopping, and threshold selection.
- Protected or audit-only attributes are physically separated and never used as model inputs.
- Metrics are reported with their split and role: train-CV supports selection; validation checks the selected candidate; test is reserved for explicit final evaluation.
- Synthetic results do not support claims about real credit performance, calibration, fairness, or usefulness.

## Optional Streamlit fallback

```bash
python3 -m pip install -e '.[demo]'
python3 -m streamlit run app/streamlit_app.py
```

Streamlit is retained as a fallback presentation for the UCI baseline. The FastAPI/static frontend is the primary experience because it keeps the Home Credit and UCI labs separated and presents cached model evidence without live computation.

## Validation

Run the focused checks before submitting a change:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
git diff --check
```

The integration tests verify the API contract, static frontend, dataset separation, cached academic evidence, and regression-sensitive chart structure.

## Synthetic demonstration vertical

The synthetic generator is isolated from the UCI and Home Credit model paths. It is useful for demonstrating data contracts and reproducible splits, not for making claims about real credit.

```bash
python3 scripts/generate_synthetic_snapshot.py \
  --config configs/data/synthetic-v1-approved.yaml

python3 scripts/generate_synthetic_snapshot.py \
  --verify data/raw/synthetic/<snapshot_id>

python3 scripts/create_synthetic_splits.py \
  --snapshot data/raw/synthetic/<snapshot_id>
```

Generated data remains outside Git. The accepted methodology is documented in `docs/synthetic-data-specification.md` and the corresponding dataset decision files.

## Documentation map

- `AGENTS.md` — repository rules and accepted technical decisions;
- `docs/plans/` — execution plans and milestone scope;
- `docs/decisions/` — accepted architectural decisions;
- `docs/datasets/uci-default-credit-card.md` — UCI provenance and limitations;
- `docs/datasets/home-credit-candidate.md` — Home Credit dataset contract;
- `docs/model-card-uci-baseline.md` — UCI academic model card;
- `docs/evaluation-protocol.md` — split and evaluation rules;
- `docs/workflows/` — wave and task definitions for planned work.

## Roadmap

The first portfolio milestone is the classical Home Credit model-development story plus the cached frontend presentation. Deep learning is deliberately a separate follow-up sprint even though the current UI can present the cached MLP challenger evidence.

Future work remains explicitly planned rather than implied as production capability:

1. complete the classical benchmark and documentation gates;
2. deepen explainability, calibration, error and segment analysis;
3. run the dedicated deep-learning benchmark;
4. add controlled monitoring and artifact tracking;
5. define human approval, promotion, rollback, and operational deployment contracts.

Prefect, MLflow, Evidently, Grafana, Docker Compose topology, cloud deployment, feature storage, promotion authority, and backup procedures remain subject to their accepted ADRs and later implementation milestones.

## Milestone closure

Each technical milestone has an ExecPlan with a version-control allowlist. The finisher validates only that allowlist and never authorizes commits, pushes, resets, deletion, or rebases automatically.

```bash
python3 scripts/finish_milestone.py \
  --plan docs/plans/<plan>.md --check

python3 scripts/finish_milestone.py \
  --plan docs/plans/<plan>.md --stage
```
