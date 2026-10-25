# ADR-0034: Home Credit offline tabular MLP challenger

- Status: Accepted
- Date: 2026-10-25
- Scope: Home Credit academic benchmark, intermediate deep-learning phase

## Context

The classical milestone is frozen at `v0.3.0-home-credit-classical`. The next
phase must demonstrate that a neural model is evaluated as an experiment, not
selected only because it is more complex. The application must remain fast and
must never train on request.

## Decision

1. Use a small PyTorch MLP with hidden layers `(128, 64)`, ReLU, dropout `0.2`,
   AdamW, learning rate `0.001`, weight decay `0.0001`, and batch size `4096`.
2. Fit preprocessing on Home Credit `features-v2` train only and carve a 10%
   stratified holdout from train for early stopping.
3. Use seed 42 and deterministic CPU execution. Persist architecture,
   hyperparameters, parameter count, epochs, best epoch, and learning curves.
4. Evaluate the frozen checkpoint once on validation and compare Average
   Precision with the cached classical benchmark.
5. Save state and reports under ignored `runs/`; FastAPI and the browser only
   read the report and never invoke training.
6. Keep the final test unopened. The MLP is a challenger and is not promoted
   automatically.

## Consequences

- The neural result is comparable under the same feature version, split, target,
  seed, and primary metric.
- CPU training is paid once by the offline CLI; the demo remains a lightweight
  reader of JSON/CSV artifacts.
- A future architecture may be added as another experiment without rewriting
  the classical milestone.

## Rejected alternatives

- Training in FastAPI or in a browser request.
- Opening the final test for early stopping or architecture selection.
- Adding FT-Transformer before the small MLP has been evaluated.
