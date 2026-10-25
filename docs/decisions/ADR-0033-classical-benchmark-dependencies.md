# ADR-0033: Classical benchmark dependency boundary

- Status: Accepted
- Date: 2026-10-25
- Scope: Home Credit first milestone, academic benchmark only

## Context

The first milestone must demonstrate model selection and tuning without
introducing a neural-network implementation prematurely. Logistic Regression
and LightGBM remain the references; stronger classical candidates provide a
useful comparison only when their dependencies are explicit and the final test
stays closed.

## Decision

1. Use Optuna with a seeded TPE sampler to tune LightGBM inside train
   cross-validation. The selected parameters are then fit on train and checked
   once on validation.
2. Include CatBoost and XGBoost as fixed classical challengers when the
   optional `model-lab` dependency group is installed.
3. Keep the benchmark report local under `runs/`, expose only its materialized
   evidence through the read-only API, and cache it for the frontend.
4. Keep PyTorch in a separate `deep-learning` optional dependency group. It is
   not part of the first milestone implementation or tag.
5. Do not promote a model automatically based on one validation score; the
   report is academic evidence and the final test remains unopened.

## Runtime contract

The FastAPI service and browser never train, tune, run cross-validation, build
features, or open the test. Offline CLI jobs create the report once; the app
only reads the cached JSON/CSV artifacts. A missing artifact is reported as an
explicit unavailable state rather than silently triggering computation.

## Consequences

- The portfolio demonstrates a visible `hypothesis → tuning → comparison →
  validation` workflow without conflating classical and neural experiments.
- Optional classical dependencies increase installation cost but do not alter
  the required baseline installation.
- A future deep-learning sprint can add its own contract and ADR without
  changing the first milestone evidence.
