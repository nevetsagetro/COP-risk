# ExecPlan 0035: Home Credit EDA and Data Audit Tab

## Status

- Status: active.
- Scope: an independent Home Credit EDA tab for curious users and academic
  inspection.
- This plan does not authorize implementation, model retraining, or changes to
  the existing Home Credit scrollytelling.
- Source of truth: `AGENTS.md`, `PLANS.md`, and the Home Credit academic plans.

Implementation checkpoint: the EDA report, read-only endpoint, and independent
frontend tab are implemented and remain `complete_pending_review` in the
workflow. Independent review and milestone closure are still pending.

## Objective

Add a read-only, cached EDA experience that lets a user inspect the Home Credit
dataset before reading the model-development story. The tab must be optional:
the existing scrollytelling remains the primary narrative and must render with
the same content, metrics, and behavior when the EDA tab is not opened.

## Product contract

The EDA tab answers:

1. What is the target prevalence in the available snapshot and validation
   split?
2. Which variables have missing values or unusual ranges?
3. How do selected numeric variables differ by observed target class?
4. Which numeric variables are strongly correlated or redundant?
5. Which columns are excluded from model inputs and why?

The first version should expose a focused audit rather than a 62-variable
dashboard:

- target prevalence summary;
- missingness overview for model-input features;
- selected numeric distributions by target class;
- a readable correlation matrix for a documented subset of numeric features;
- audit-only and excluded-column summary;
- dataset fingerprint, feature version, split seed, and test status.

The correlation view must state its method, population, and limitations. It is
descriptive association, not feature importance, causality, fairness evidence,
or leakage proof.

## Non-negotiable boundaries

- All EDA artifacts are generated locally before presentation and stored under
  the existing ignored `runs/` artifact convention.
- Opening the tab never loads raw rows into the browser, retrains a model, or
  recalculates statistics live.
- The final test remains unopened and cannot contribute to feature selection or
  EDA-driven model choices.
- Home Credit remains separate from UCI in API contracts, DOM scope, labels,
  charts, and styles.
- Missing evidence is shown as unavailable; no placeholder values or invented
  charts are permitted.
- Existing scrollytelling sections, charts, metrics, and explanatory text are
  preserved.

## Waves and exit criteria

### Wave 1 — EDA evidence contract

Define the statistical scope, approved variables, population, and artifact
schema before implementation.

Exit criteria:

- Every EDA output has a source, split/population, method, and limitation.
- The correlation subset and selection rule are documented.
- Test status and audit-only boundaries are explicit.

### Wave 2 — Offline EDA materialization

Generate deterministic JSON/CSV evidence from the local Home Credit snapshot.

Exit criteria:

- The job is deterministic, idempotent, and seed-aware.
- No raw rows or protected/audit-only inputs are emitted to frontend artifacts.
- Missingness, prevalence, distributions, and correlations have schema tests.

### Wave 3 — Read-only API contract

Expose the cached report without changing existing Home Credit or UCI endpoints.

Exit criteria:

- A versioned read-only endpoint serves the EDA report.
- Existing response contracts remain compatible.
- API tests prove the test remains unopened and arbitrary filesystem paths are
  not accepted from clients.

### Wave 4 — Independent EDA tab

Add a tab or sub-navigation entry that is visually and technically separate
from the Home Credit scrollytelling.

Exit criteria:

- The tab loads cached evidence only when selected or during the existing
  static page load contract.
- It contains readable charts with exact-value tooltips and text summaries.
- It has loading, unavailable, and empty-data states.
- Responsive, keyboard, reduced-motion, and English-language behavior work.
- UCI visuals and the Home Credit story are not affected.

### Wave 5 — Review and milestone closure

Run regression review and prepare closure through the repository workflow.

Exit criteria:

- Existing frontend/API tests and fixed validations pass.
- A read-only reviewer confirms no scientific or dataset-boundary regression.
- The milestone finisher validates only the allowlist.

## Out of scope

- Feature selection, hyperparameter tuning, or model retraining from EDA.
- SHAP, causal inference, fairness claims, or automated feature promotion.
- A full pairwise matrix for every feature without a documented readability
  justification.
- Raw-row exploration, customer-level records, or PII.
- Changes to UCI charts, UCI API semantics, or the existing Home Credit
  scrollytelling narrative.

## Validation commands

```bash
python3 scripts/validate_workflow.py
python3 -m scripts.workflow_status
python3 -m pytest
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
git diff --check
```
