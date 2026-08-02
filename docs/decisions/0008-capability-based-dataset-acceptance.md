# ADR 0008: aceptación de datasets por capacidad

- Status: Accepted
- Date: 2026-08-02
- Accepted: 2026-08-02
- Decision owners: aprobación humana registrada

## Context

El contrato original evaluaba aptitud para la vertical completa, incluida
temporalidad y monitoring. Ese criterio no distingue datasets académicos
estáticos útiles para clasificación reproducible sin evidencia longitudinal.

## Decision

Cada dataset se evalúa independientemente para: provenance, license,
target_definition, schema, entity_identity, timestamps, temporal_split,
group_split, academic_modeling, longitudinal_monitoring,
public_portfolio_use y production_claims.

Los estados son `pass`, `limited`, `needs_review`, `fail` y `not_applicable`.
No se agregan ni compensan. Un fallo permanece visible y bloquea las
capacidades que dependen de él, pero no una capacidad independiente cuyos
gates hayan pasado.

UCI Default of Credit Card Clients queda autorizado como candidato para
baseline académico, clasificación binaria y futuros experimentos locales de
imbalance, LightGBM, Optuna y serving. Esta decisión no implementa esas
tecnologías. No queda autorizado para validación temporal, drift longitudinal,
claims de producción, fairness, cumplimiento, representatividad ni decisiones
crediticias reales.

Los splits académicos solo pueden crearse cuando provenance, license, schema y
target_definition pasan. Son estratificados y reproducibles, no temporales.

## Consequences

Un snapshot puede aceptarse para un uso parcial explícito. Manifests y
documentación conservan todos los fallos. La aceptación académica nunca se
hereda como autorización temporal, productiva o de monitoring.
