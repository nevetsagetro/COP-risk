# ADR-0032: Home Credit model improvement roadmap and milestone boundary

- Status: Accepted
- Date: 2026-10-25
- Scope: Home Credit academic benchmark only

## Context

The current Home Credit vertical has a reproducible Logistic Regression and
LightGBM baseline, but its seed, feature version, model improvement history,
and human-readable experiment contract are not yet complete. The portfolio
needs to demonstrate the complete development path through a controlled deep
learning benchmark without turning the project into a production credit
decision system. The first milestone is intentionally limited to classical
model development and its human-readable presentation; deep learning is a
later sprint.

## Decision

1. Preserve the current baseline as immutable `features-v0` evidence.
2. Add feature engineering as versioned snapshots and compare each version by
   train cross-validation, validation, calibration, and review-capacity policy.
3. Keep Average Precision as the primary ranking metric because the target is
   imbalanced; keep ROC-AUC, Brier, log loss, and precision/recall at capacity
   as secondary evidence.
4. Persist seed, dataset fingerprint, split, feature version, parameters and
   model family in every report. Seed 42 is the initial reproducibility seed.
5. Benchmark CatBoost and XGBoost as classical challengers only when their
   optional dependencies are explicitly installed and tested.
6. Defer the PyTorch MLP to a future sprint. When authorized, it will be an
   academic challenger, not an automatic promotion or production model.
7. Keep the final test closed throughout feature work, hyperparameter search,
   early stopping, calibration, threshold selection, and explainability.
8. Show engineering details in backend artifacts and explain their meaning in
   human language in the scrollytelling frontend.

## Consequences

- Generated v2 snapshots and model reports remain local and are not committed.
- New candidates must be comparable with the frozen baseline.
- The first milestone closes after classical tuning and UX/UI integration;
  deep learning success will be defined in a later sprint by evidence on the
  same split and metrics, not by using a neural network by itself.
- Optional dependencies increase installation and validation cost; their
  versions must be recorded before the benchmark is considered reproducible.

## Rejected alternatives

- Replacing the baseline without a comparison record.
- Opening the final test to select features or models.
- Presenting feature importance as causal explanation.
- Claiming that a neural model is better because it is more complex.
