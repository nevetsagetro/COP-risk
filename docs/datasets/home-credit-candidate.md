# Home Credit candidate gate

## Current status

The candidate is **accepted for a static academic benchmark only**. The
official archive is present locally under `data/raw/home-credit/` and passes
the structural inventory, but the application tables do not expose an
application timestamp. A temporal split is therefore out of scope.

## What is implemented

Run the offline inspector with:

```bash
python3 scripts/evaluate_home_credit_candidate.py
```

The inspector checks a human-supplied local acquisition and reports missing
files, basic application schema, target presence, and entity ID presence. It
never downloads data, modifies the acquisition, or accepts the dataset.

Current local result: `schema_inspected_pending_methodology`; all required
files are present, `TARGET` is only in train, and `SK_ID_CURR` is present in
train and test. The static snapshot uses entity-disjoint hashed splits and
records the non-temporal limitation.

## Required local acquisition inventory

The gate expects the application tables and historical tables used by the
candidate workflow, plus the column description file. The exact inventory is
encoded in `scripts/evaluate_home_credit_candidate.py` and must be revisited
against the applicable source rules before acceptance.

## Pending evidence

- provenance, version, hashes, license, and competition rules;
- target and prediction horizon;
- decision-time snapshot and feature availability windows;
- entity joins and cardinality checks;
- post-outcome and audit-only column quarantine;
- defensible temporal split;
- confirmation that no PII or unapproved customer data is present.

See [ADR-0031](../decisions/ADR-0031-home-credit-dataset.md) for the proposed
decision and rejection conditions.
