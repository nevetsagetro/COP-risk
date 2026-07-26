# Especificación propuesta del bootstrap sintético

## Estado y alcance

Esta es una especificación de diseño, no un dataset material ni implementado.
Instancia como propuesta los parámetros del metacontrato. El ADR 0006 está
`Accepted` para el alcance estratégico; target, umbral DPD, horizonte,
población, estimand, features, tamaños, prevalencia, ventanas, distribuciones,
correlaciones, escenarios exactos de drift y gates cuantitativos requieren
aceptación posterior.

El objetivo es permitir una implementación futura determinista, auditable y
causalmente ordenada sin hacer claims sobre crédito real.

## Contrato inicial propuesto

| Concepto | Propuesta | Estado |
|---|---|---|
| Unidad de predicción | Una solicitud sintética elegible que origina una exposición | Pendiente |
| Entidad | `borrower_id`, pseudónimo sintético estable | Pendiente |
| Observación | `application_id`, único e inmutable | Pendiente |
| Instante de decisión | `decision_timestamp` en UTC | Pendiente |
| Cutoff del snapshot | `snapshot_as_of` UTC, parte de `snapshot_id` | Regla obligatoria |
| Target | Llegar por primera vez a 90+ DPD dentro del horizonte | Pendiente |
| Horizonte | 12 meses calendario desde la decisión, inicio exclusivo y fin inclusivo | Pendiente |
| Disponibilidad del label | Como mínimo `decision_timestamp + 12 meses`, más lag configurado | Pendiente |
| Label inmadura/censurada | `unknown` | Regla obligatoria |
| Repeticiones | Varias solicitudes por `borrower_id` | Pendiente |
| Atributos protegidos | Vista física separada `audit_only` | Regla obligatoria |
| Formato | Parquet, configuración YAML y manifest con hashes físicos/lógicos | Parquet y hashes aceptados; estructura concreta pendiente |

La población principal propuesta incluye únicamente solicitudes sintéticas
originadas. Si se simulan rechazos, su resultado factual no existe: no pueden
etiquetarse como negativos. Una verdad contrafactual, si se necesitase para
evaluar el simulador, quedaría separada y nunca sería una label observada.

## Orden generativo causal

1. Crear entidad y factores latentes versionados no exportables.
2. Crear solicitud, tiempo de decisión e historia anterior.
3. Materializar fuentes y features estrictamente as-of.
4. Congelar la fila de decisión.
5. Generar exposición, calendario contractual y pagos posteriores.
6. Derivar DPD, outcome, madurez, censura y disponibilidad del label.
7. Asignar particiones con reglas congeladas y sellar el test.
8. Escribir Parquet y manifest canónicos.

No se generará primero `y` para condicionar después los inputs. El generador
deberá permitir recomputar el target independientemente desde schedule y
ledger.

## Target, outcome y disponibilidad

Definición propuesta:

```text
horizon_end = decision_timestamp + 12 meses calendario
y = 1  si first_90dpd_at > decision_timestamp
           y first_90dpd_at <= horizon_end
y = 0  si no ocurrió 90+ DPD y existe seguimiento completo hasta horizon_end
y = unknown si la observación es inmadura, está censurada o carece de cobertura
```

90+ DPD significa al menos 90 días naturales vencidos conforme al calendario
contractual y pagos aplicados. Es un evento `ever`: una cura posterior no
revierte un positivo. Prepago o pago total solo podrá cerrar como negativo si
la regla aprobada demuestra que elimina la posibilidad del evento. Charge-off,
eventos competidores y correcciones tardías necesitan reglas explícitas; no se
mapearán silenciosamente.

Para el bootstrap se propone la regla conservadora de no declarar madura una
observación hasta demostrar cobertura del horizonte completo y el máximo lag
de reporting, incluso cuando exista un positivo temprano. Solo cuentan hechos
con `available_at <= snapshot_as_of`; nunca se consulta el reloj de ejecución.
Se registrarán:

- `outcome_timestamp`;
- `horizon_end`;
- `label_observed_at`;
- `label_ready_at`, primer instante en que se cumplen para positivos y
  negativos horizonte, lag, cobertura y disponibilidad real del label;
- `followup_end`;
- `label_status = mature | immature | censored`;
- `censoring_reason`.

Inmaduras, ausentes y censuradas nunca se convierten en negativas. El
tratamiento modelístico de censura sigue pendiente; inicialmente podrán
excluirse del fit y deberán reconciliarse en el manifest.

`label_observed_at` registra cuándo llegó el hecho o confirmación fuente.
`label_ready_at` es el máximo operacional entre `horizon_end`, esa
disponibilidad, el lag exigido y la confirmación de cobertura. Por tanto,
`label_observed_at <= label_ready_at` y `label_ready_at >= horizon_end`. La
disponibilidad nominal propuesta a 12 meses no autoriza usar una label cuyo
registro o cobertura llegue después.

## Relaciones y mecanismo generativo

Factores latentes candidatos, no exportables, incluyen capacidad financiera,
estabilidad de ingresos, profundidad del historial, liquidez y estado
macroeconómico temporal. Podrán relacionarse mediante una cópula o distribución
multivariante cuya matriz sea versionada, simétrica y semidefinida positiva.

Las marginales candidatas incluyen lognormal/gamma para importes positivos,
binomial negativa para conteos sobredispersos, mezclas con masa en cero,
categorías sobre catálogos cerrados y procesos temporales para macroeconomía.
Ninguna familia o parámetro está aceptado todavía.

El riesgo podrá combinar:

- saturación de importe respecto a ingreso;
- efecto convexo o por tramos de debt-to-income;
- saturación de antigüedad laboral y crediticia;
- recencia de consultas y atrasos previos;
- utilización no lineal;
- `income_volatility × estimated_installment_to_income`;
- `recent_delinquencies_count × recent_inquiries_count`;
- `thin_file × requested_amount`;
- `requested_term_months × macro_stress_at_decision`;
- shocks posteriores independientes e invisibles al modelo.

El intercepto/hazard controla la tasa simulada. Está prohibido forzarla
eliminando o duplicando filas después de observar `y`. La prevalencia será un
parámetro explícito de simulación, no una estimación realista.

## Missingness y observaciones repetidas

Missingness podrá depender de fuente, canal y disponibilidad anterior a la
decisión, nunca del outcome posterior. `zero`, `unknown`, `not_applicable` y
`not_observed` conservarán semánticas distintas.

Cada solicitud repetida recibe un nuevo `application_id`. La historia previa
solo alimenta una solicitud si sus eventos y labels estaban disponibles en ese
`decision_timestamp`. Una repetición no es un duplicado; la deduplicación usa
clave natural y fingerprint sin consultar el target.

## Prevención de leakage

Cada valor conserva `event_time`, `recorded_at` y `available_at`. Todo input
debe probar:

```text
available_at <= decision_timestamp
```

Un agregado con lookback solo puede usar eventos en
`[decision_timestamp - lookback, decision_timestamp)` que además ya estuvieran
registrados. El `available_at` de una derivada es el máximo de todas sus
dependencias.

Se prohíben como inputs:

- target y componentes de su definición;
- schedule, pagos, DPD, saldo o estado posteriores de la exposición actual;
- collections, charge-off, recovery, settlement y forbearance;
- outcome, madurez, censura y timestamps de label;
- importe aprobado, precio final o resultado de underwriting posteriores al
  instante propuesto;
- macroeconomía futura, backfills y labels anteriores aún no observadas;
- IDs, partición, snapshot, cutoff y metadata del generador;
- factores latentes, shocks y verdad de escenarios;
- atributos protegidos y derivados;
- agregados ajustados con validation, calibración o test.

El futuro DAG de lineage deberá impedir cualquier camino desde roles
`target_only`, `audit_only` o `prohibited` hacia `input`.

## Split y evaluación

La propuesta principal estima nuevas entidades:

```text
train < validation < calibration/threshold < final_test
```

Primero se fijan ventanas temporales. Después se reserva cada `borrower_id`
para su partición más reciente y se purgan sus observaciones de particiones
anteriores mediante una regla independiente del label. Gaps y límites exactos
son parámetros pendientes.

Las intersecciones de `application_id`, fingerprint y `borrower_id` entre
particiones deben ser cero. Un estimand futuro sobre prestatarios conocidos
requerirá un protocolo walk-forward aprobado; no será una relajación para
mejorar métricas.

El test queda fuera de feature selection, preprocessing, resampling, HPO,
early stopping, calibración, threshold, monitoring reference y comparación
iterativa. Cualquier cambio motivado por su resultado lo convierte en
diagnóstico y exige una cohorte final futura.

## Configuración, salidas y manifest

El YAML futuro deberá declarar sin defaults silenciosos:

- versiones de dataset, esquema y generador;
- `snapshot_as_of` UTC, incorporado a la identidad del snapshot;
- semilla maestra, algoritmo y namespaces de semillas derivadas;
- población, recurrencia de entidades, calendario y cohortes;
- factores, correlaciones, distribuciones y missingness;
- DAG, roles y reglas `available_at`;
- repayment, target, madurez, censura y eventos competidores;
- atributos `audit_only`;
- split, gaps y sellado del test;
- escenarios de drift y serialización.

Salidas propuestas:

- `observations.parquet`;
- `features.parquet`;
- `audit_only.parquet`;
- outcomes y labels de desarrollo;
- labels del test en ubicación sellada;
- `split_assignments.parquet`;
- manifest canónico y sidecar de hashes.

El manifest registra configuración resuelta y SHA-256, `snapshot_as_of`,
versión/commit y licencia del generador y snapshots, seeds, versiones de
librerías, esquema, roles, lineage, orden canónico, opciones de Parquet, hash
por archivo y hash lógico del contenido. También reconcilia filas, entidades,
duplicados, purgas, labels por estado, tasa realizada, rangos y estadísticas de
control.

## Parámetros no aceptados

No se aceptan automáticamente:

- número de entidades u observaciones y frecuencia de repetición;
- rango temporal, cadencia, lookbacks, ventanas, gaps y purgas;
- target, horizonte, lag, eventos competidores y censura;
- tasa positiva, intercepto, hazard o class imbalance;
- distribuciones, categorías, missingness, correlaciones y coeficientes;
- mezcla de atributos de auditoría;
- onset, duración, magnitud y reglas exactas de drift;
- métricas primarias, thresholds, tolerancias o gates cuantitativos.

## Validaciones de una implementación futura

- IDs únicos, estables y joins íntegros.
- Timestamps con zona y orden causal válido.
- `available_at <= decision_timestamp` para cada input y dependencia.
- Target recomputable desde schedule/ledger.
- Toda label cumple `label_observed_at <= label_ready_at`; solo
  `label_ready_at <= snapshot_as_of` habilita uso supervisado.
- Cero negativos entre labels inmaduras o censuradas.
- Reconciliación de elegibles, excluidos y estados del label.
- Cero solapamiento de IDs, fingerprints y entidades.
- Test físicamente protegido y fuera de usos adaptativos.
- Misma configuración y semillas producen hashes lógicos idénticos.
- Misma configuración, semilla y cutoff producen hashes lógicos idénticos.
- Avanzar el cutoff produce otro snapshot y solo transiciones de madurez
  permitidas; cambiar versión/configuración también cambia su identidad.
- Inventario y revisión registrada de proxies sensibles por correlación o causa
  común, usando `audit_only` únicamente en auditoría. Los gates cuantitativos
  permanecen pendientes.
- Ningún snapshot se publica sin licencia y condiciones de redistribución
  aceptadas.
