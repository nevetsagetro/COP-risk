# ADR-0031: Home Credit dataset gate

## Status

Accepted for a static academic benchmark only. The local acquisition is not
accepted for a temporal Home Credit vertical.

## Context

The next COP vertical needs a public dataset with richer application and
historical tables so the project can demonstrate leakage-safe feature
engineering and decision-policy evaluation. Home Credit Default Risk is a
candidate whose local archive and competition rules must be reviewed before
modeling.

## Verified repository state

- The local acquisition is present under `data/raw/home-credit/` and contains
  all required source files from the official archive.
- `application_train.csv` has 122 columns including `TARGET`; the test file
  has 121 columns and does not contain `TARGET`.
- `SK_ID_CURR` is present in train and test and is the applicant/loan entity
  key described by the data dictionary.
- A static snapshot manifest, entity-disjoint split artifacts, and a train/CV
  baseline report now exist under ignored local `data/processed/` and `runs/`
  paths. No Home Credit API or production serving exists.
- The existing UCI vertical remains the only verified academic model flow.

## Gate conditions

The static benchmark cannot be used beyond its declared scope until all
applicable conditions below have evidence:

1. Source provenance, version, hash, license, and competition rules are
   recorded.
2. The target and prediction horizon are defined.
3. The decision-time snapshot and feature availability windows are defined.
4. Joins and entity cardinalities are verified.
5. Post-outcome and audit-only columns are quarantined.
6. A temporal split is not required for this accepted static scope; the
   entity-disjoint split is reproducible and the temporal limitation is shown.
7. The repository contains no PII or unapproved customer data.

## Current evidence and limitation

The classic competition archive does not expose an application timestamp in
the main application table. Historical tables contain relative offsets such as
`DAYS_CREDIT`, `DAYS_DECISION`, and `MONTHS_BALANCE`, but those are not a
dataset-level ordering of application decisions. `SK_ID_CURR` must not be
treated as time. Therefore a defensible temporal split cannot be claimed from
this acquisition alone.

## Decision

Accept the local Home Credit archive for a static academic benchmark with
entity-disjoint splits. The benchmark must use the supplied `TARGET` as the
outcome exactly as defined by the source dictionary, without restating it as a
new horizon. It must not claim temporal stability, production performance, or
real credit usefulness. The temporal vertical remains rejected until a source
with an application-time ordering is approved.

The inspector may validate a local acquisition supplied by a human, but it
must never download or accept the dataset automatically.

## Consequences

- Static Home Credit training may start after the snapshot contract is
  implemented and verified. Temporal training and serving remain out of scope.
- `HC-001` can produce a machine-readable gate report without reading absent
  files.
- `HC-002` is satisfied by this explicit static-benchmark decision; independent
  review remains required before milestone closure.

## Reconsideration

The reviewer may accept, reject, or request changes after the inspector has
processed a complete local acquisition.
