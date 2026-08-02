# Diccionario propuesto de datos sintéticos

## Convenciones

Este diccionario es una propuesta, no un esquema implementado. Toda columna
declara un rol y una regla de disponibilidad. `input` requiere
`available_at <= decision_timestamp`; `partition_only`, `target_only`,
`audit_only` y `prohibited` nunca entran en la matriz de features.

Cada input materializado tendrá metadata de `event_time`, `recorded_at` y
`available_at`, aunque la representación física final siga pendiente.

## Identidad y partición

| Campo | Tipo conceptual | Rol | Disponibilidad y regla |
|---|---|---|---|
| `borrower_id` | string pseudónimo | `partition_only` | Al crear la entidad; nunca input |
| `application_id` | string único | `partition_only` | Al crear la solicitud; nunca input |
| `decision_timestamp` | timestamp UTC | `partition_only` | Instante de decisión; nunca input absoluto |
| `snapshot_id` | string | `partition_only` | Al materializar; nunca input |
| `snapshot_as_of` | timestamp UTC | `partition_only` | Cutoff congelado, parte de `snapshot_id`; nunca input |
| `split_name` | enum | `partition_only` | Después del freeze; nunca input |
| `generator_version` | string | `prohibited` | Metadata de generación |
| `scenario_id` | string | `prohibited` | Solo evaluación sintética |

## Inputs candidatos

| Campo | Tipo/distribución candidata | Regla de `available_at` | Lineage y límites |
|---|---|---|---|
| `requested_amount` | decimal positivo; lognormal/gamma | `application_validated_at` | Solicitud validada |
| `requested_term_months` | entero categórico | `application_validated_at` | Catálogo versionado |
| `product_type` | categoría | `application_validated_at` | Catálogo versionado |
| `application_channel` | categoría | `application_validated_at` | Fuente de solicitud |
| `monthly_income` | decimal; lognormal truncada | `income_verification_completed_at` | No usar revisiones posteriores |
| `income_volatility` | decimal no negativo | `cashflow_aggregate_available_at` | Solo eventos anteriores y disponibles |
| `employment_tenure_months` | entero no negativo | `income_verification_completed_at` | Ceros estructurales explícitos |
| `monthly_housing_cost` | decimal no negativo | `income_verification_completed_at` | Missing distinto de cero |
| `existing_monthly_debt` | decimal no negativo | `bureau_report_available_at` | Obligaciones conocidas as-of |
| `open_credit_lines` | entero no negativo | `bureau_report_available_at` | Historia previa |
| `revolving_balance` | decimal no negativo | `bureau_report_available_at` | Historia previa |
| `credit_limit` | decimal no negativo | `bureau_report_available_at` | Regla explícita para cero |
| `utilization_ratio` | decimal acotado/configurable | máximo de saldo y límite | División y clipping versionados |
| `recent_inquiries_count` | entero no negativo | `bureau_report_available_at` | Lookback semiabierto as-of |
| `recent_delinquencies_count` | entero no negativo | `bureau_report_available_at` | Solo eventos previos registrados |
| `max_prior_dpd` | ordinal no negativo | `bureau_report_available_at` | Nunca DPD del préstamo actual |
| `oldest_credit_age_months` | entero no negativo | `bureau_report_available_at` | Historia disponible |
| `prior_matured_loan_count` | entero no negativo | fin del agregado | Solo préstamos previos maduros |
| `prior_observed_adverse_count` | entero no negativo | fin del agregado | `label_observed_at <= decision_timestamp` |
| `macro_stress_index` | decimal | publicación más reciente | Nunca valor futuro o revisado |
| `debt_to_income` | decimal | máximo de dependencias | Fórmula versionada |
| `estimated_installment_to_income` | decimal | máximo de dependencias | Usa términos solicitados, no aprobados |
| indicadores de missing | boolean | igual que su fuente | No pueden depender del outcome |
| estacionalidad permitida | categoría/cíclica | `decision_timestamp` | Sin fecha absoluta ni cohort ID |

Distribuciones, lookbacks, límites y fórmulas son parámetros pendientes. La
regla de disponibilidad no lo es: ninguna fila puede usar información futura.

## Outcome, madurez y auditoría

| Campo | Rol | Regla |
|---|---|---|
| `contractual_due_at` | `target_only` | Evento posterior del schedule |
| `payment_event_at` | `target_only` | Evento posterior del ledger |
| `days_past_due` | `target_only` | Derivado causalmente de schedule/pagos |
| `first_90dpd_at` | `target_only` | Primer cruce del evento propuesto |
| `outcome_timestamp` | `target_only` | Instante del evento, nunca input |
| `horizon_end` | `target_only` | Decisión más horizonte configurado |
| `label_90dpd_12m` | `target_only` | `1`, `0` o `unknown`; definición pendiente |
| `label_observed_at` | `target_only` | Llegada del hecho o confirmación fuente; no implica madurez |
| `label_ready_at` | `target_only` | Primer instante con horizonte, lag, cobertura y label disponibles; siempre `>= horizon_end` |
| `followup_end` | `target_only` | Fin verificable de cobertura |
| `label_status` | `target_only` | `mature`, `immature` o `censored` |
| `censoring_reason` | `target_only` | Motivo versionado |
| atributos protegidos sintéticos | `audit_only` | Parquet separado; nunca inputs |
| factores latentes y shocks | `prohibited` | Solo mecanismo/evaluación |

Los atributos de auditoría no se usarán para generar el target ni para HPO,
calibración o threshold. Si se estudia deliberadamente un proxy o disparidad,
será un escenario diagnóstico separado y no apto para selección del modelo.
Ningún resultado permitirá afirmar fairness.

## Variables expresamente prohibidas como inputs

- Todos los campos de outcome, pagos, DPD, collections, charge-off, recovery,
  settlement, forbearance, madurez y censura.
- Importe aprobado, precio final, decisión de underwriting y acciones tomadas
  después de `decision_timestamp`.
- Datos macroeconómicos futuros o revisiones publicadas después de la decisión.
- IDs, timestamps absolutos de partición, snapshot, cutoff o ingesta.
- Target, proxies directos, factores latentes, shocks y verdad de escenario.
- Atributos protegidos o transformaciones derivadas de ellos.
- Agregados globales o ajustados con validation, calibración o test.

## Tests contractuales futuros

1. Toda feature tiene fuente y `available_at` no nulo.
2. Toda dependencia de una derivada cumple la misma regla as-of.
3. El DAG no contiene caminos de roles no-input hacia `input`.
4. Ninguna label `immature` o `censored` tiene valor cero.
5. El target se reproduce desde los eventos sin usar la columna materializada.
6. Atributos `audit_only` no aparecen en `features.parquet`.
7. Toda label cumple `label_observed_at <= label_ready_at`; solo
   `label_ready_at <= snapshot_as_of` habilita uso supervisado. La madurez no
   consulta el reloj de ejecución.
8. Existe inventario y revisión registrada de proxies potenciales por
   correlación o causa común. La verdad `audit_only` solo se usa en esa
   auditoría y nunca en fit, HPO, calibración o threshold.
