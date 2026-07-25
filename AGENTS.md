# AGENTS.md

## Project identity

COP is a portfolio and demonstration project for credit-risk scoring,
drift monitoring, and controlled model retraining.

It is not approved for real credit decisions.

## Mandatory repository inspection

Before proposing or implementing changes:

1. Run `pwd`.
2. Run `git status --short`.
3. Inspect the repository with `find` or equivalent.
4. Read `README.md`, `AGENTS.md`, relevant files under `docs/`,
   and the active execution plan.
5. Distinguish clearly between:
   - product vision;
   - verified repository state;
   - accepted technical decisions;
   - pending decisions;
   - proposals.

Never claim that a file, service, dataset, model, experiment, dashboard,
deployment, or integration exists unless verified in the working tree.

## Accepted technical decisions

- Python is the implementation language.
- Class balancing uses SMOTE-Tomek where justified.
- The primary model family is LightGBM.
- Hyperparameter optimization uses Optuna.
- Experiment tracking uses MLflow.
- Serving uses FastAPI and Docker.
- Drift monitoring uses Evidently.
- Operational visualization uses Grafana.

## Pending decisions

Do not silently decide:

- dataset source;
- Airflow versus Prefect;
- cloud provider;
- metadata and feature storage;
- drift thresholds;
- model promotion and rollback strategy.

Record accepted decisions as ADRs under `docs/decisions/`.

## Safety and compliance

- Never use real customer data or PII.
- Only use synthetic or public anonymized data.
- Never commit credentials, tokens, secrets, or real connection strings.
- Keep secrets in environment variables.
- Do not describe this project as suitable for real lending decisions.
- Do not optimize or evaluate using protected attributes as decision inputs.
- Document fairness and limitations, but do not make unsupported fairness claims.

## ML correctness rules

- Split data before fitting resampling or preprocessing steps.
- Fit SMOTE-Tomek only on training folds.
- Prevent target leakage and temporal leakage.
- Keep a reproducible untouched test set.
- Record seeds, dataset version, features, parameters, metrics, and artifacts.
- Compare challengers against an existing champion before promotion.
- Drift detection may trigger training, but must not by itself promote a model.

## Engineering rules

- Prefer small, reviewable changes.
- Add or update tests with every behavioral change.
- Run formatting, linting, type checking, and relevant tests before completion.
- Avoid adding dependencies without explaining why.
- Keep domain logic separate from orchestration and HTTP code.
- Update README and CHANGELOG only with capabilities that actually exist.

## Completion report

At the end of every task, report:

- files changed;
- commands executed;
- tests and their results;
- decisions introduced;
- remaining risks or unresolved questions.

## Execution plans

For multi-component features, architecture changes, or work expected to span
multiple sessions, create and maintain an ExecPlan under `docs/plans/`
following `PLANS.md`.