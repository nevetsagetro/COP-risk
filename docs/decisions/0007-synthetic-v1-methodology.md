# ADR 0007: metodología del snapshot sintético v1

- Status: Accepted
- Date: 2026-08-01
- Accepted: 2026-08-01
- Decision owners: aprobación humana registrada en la sesión del Milestone 7

## Context

ADR 0006 aceptó el bootstrap sintético, pero mantuvo pendientes población,
estimand, target, horizonte, tamaño, prevalencia y ventanas. El generador del
Milestone 6 existe y es reproducible, aunque su configuración todavía era de
desarrollo y no existían snapshot ni splits aprobados para entrenamiento.

## Decision

`synthetic-v1` representa 100000 solicitudes sintéticas elegibles que originan
una exposición para 75000 `borrower_id`. En esta versión decisión y originación
coinciden. El 15% de borrowers (11250) tiene más de una solicitud; esta
repetición prueba separación por entidad, pero no representa una historia
longitudinal rica.

Las decisiones pertenecen a `[2022-01-01T00:00:00Z,
2025-01-01T00:00:00Z)` y el snapshot tiene
`snapshot_as_of = 2026-01-31T00:00:00Z`.

El target vale uno si el primer evento con al menos 90 DPD ocurre en
`(decision_timestamp, decision_timestamp + 12 meses calendario]`. Vale cero
solo con horizonte y cobertura completos y label disponible tras 30 días de
lag. Labels inmaduras, censuradas o ausentes son nulas y quedan fuera de la
población supervisada. La censura administrativa sintética objetivo es
aproximadamente 2% y se reconcilia por separado.

La prevalencia objetivo aproximada del 10% es un parámetro del simulador, no un
gate de aceptación ni un claim sobre datos reales. El mecanismo de riesgo usa
parámetros fijos y versionados; no estima normalizaciones ni interceptos sobre
el snapshot. Ningún gate consulta labels, prevalencia o métricas del test.

El estimand es el desempeño retrospectivo sintético sobre solicitudes
temporalmente posteriores de borrowers ausentes de las demás particiones. Las
ventanas UTC son semiabiertas:

| Partición | Ventana |
|---|---|
| `train` | `[2022-01-01, 2023-07-01)` |
| `validation` | `[2023-07-01, 2024-01-01)` |
| `calibration` | `[2024-01-01, 2024-04-01)` |
| `threshold` | `[2024-04-01, 2024-07-01)` |
| `test` | `[2024-07-01, 2025-01-01)` |

Cada borrower se asigna a la ventana de su solicitud más reciente. Solo se
conservan allí sus observaciones maduras; sus observaciones de ventanas
anteriores se purgan. Las cinco identidades permanecen separadas y las
intersecciones de borrower, application y fingerprint lógico son cero.

El ledger binario es una simplificación de ingeniería con estados DPD
simulados; no modela una dinámica crediticia realista.

## Governance

- `provenance`: `project-generated synthetic data`;
- `source_data`: `none`;
- `external_data_dependencies`: `none`;
- `training_use`: `approved_for_local_demo`;
- `real_credit_use`: `prohibited`;
- `redistribution`: pendiente de una licencia explícita del proyecto;
- `publication_claims`: `restricted_to_synthetic_engineering_demo`.

La aprobación permite desarrollo y experimentos sintéticos locales. No
sustenta desempeño, representatividad, calibración, fairness, utilidad
crediticia ni cumplimiento regulatorio reales.

## Consequences

El test queda fuera de selección, HPO, early stopping, calibración, threshold,
reference de monitoring y gates de aceptación. Cualquier consulta adaptativa
invalida su condición de test final. La purga por borrower reduce la muestra y
sus conteos deben quedar visibles en el manifest.

