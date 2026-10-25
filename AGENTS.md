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
- Prefect is the future orchestrator, but it must not be introduced until a
  manual Python pipeline is tested, reproducible, and idempotent.
- The project is local-first. Docker Compose is introduced incrementally only
  for concrete services; cloud deployment remains out of scope.
- Initial MLflow persistence uses SQLite for metadata and a local filesystem
  for artifacts. This does not define or replace a feature store.
- `uv.lock` is the dependency lock strategy; installing uv and generating the
  lock belong to a later technical milestone.
- Drift may request or start challenger training, but promotion and rollback
  require explicit human action, comparison with the champion, and an
  auditable record.
- ADR 0006 initially selected deterministic synthetic data for bootstrap; ADR
  0009 supersedes that priority and makes UCI the principal vertical. Synthetic
  code remains isolated and must not be a dependency of the UCI pipeline.
- Synthetic targets are derived from a generated schedule/ledger. Immature,
  absent, and censored labels remain unknown.
- Splits respect time and `borrower_id`; the final test remains outside
  selection, HPO, early stopping, calibration, and thresholds.
- Protected attributes are physically separated as `audit_only` and never
  inputs. Future real datasets must pass the same methodological, legal, and
  quarantine gates.
- Synthetic results do not support claims about real credit performance,
  calibration, fairness, or usefulness.

Accepted decisions do not prove implementation. A later ADR with
`Status: Accepted` takes precedence over historical pending-decision lists in
general project documentation.

## Pending operational details

Do not silently decide or implement:

- Prefect operational details and configuration;
- the exact milestone or readiness gate for introducing orchestration;
- migration criteria and procedure from SQLite to PostgreSQL;
- migration criteria and procedure to object storage;
- feature store and feature storage;
- the complete Docker Compose topology;
- the exact model alias mechanism;
- approver identity, authentication, and authorization;
- the concrete promotion and rollback implementation;
- backup, retention, restore, and migration procedures;
- cloud provider;
- synthetic generator/snapshot license and publication terms;
- final target definition and exact DPD threshold;
- horizon, population, estimand, snapshot size, borrower/application counts,
  prevalence, temporal windows, distributions, and correlations;
- production model features; the 19 UCI academic-baseline features are frozen;
- final model metrics and quantitative gates;
- exact drift scenarios, metrics, windows, and thresholds.

Record accepted decisions as ADRs under `docs/decisions/`.

## Not implemented yet

The accepted roadmap technologies and policies remain unimplemented until
verified in the working tree. In particular, the repository does not yet
implement Prefect, MLflow persistence, SQLite state, a local artifact store,
`uv.lock`, functional Docker Compose services, production training, monitoring,
challenger/champion transitions, promotion, rollback, or cloud infrastructure.

The repository does implement one local academic UCI training baseline with
fixed Logistic Regression and LightGBM configurations. It is not a production
pipeline, tracked MLflow experiment, champion, or authorization for serving.

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

## Milestone closure

Every technical milestone ends with a read-only reviewer and then the
`milestone_finisher`. The finisher reads the active ExecPlan allowlist, runs
fixed validations, and may prepare staging only through
`scripts/finish_milestone.py`. Automated closure never uses `git add .`.

A commit always requires explicit human authorization in the current turn and
an explicit message matching the ExecPlan. The finisher never pushes, deletes,
cleans, resets, amends, rebases, restores, or force-updates repository state.
