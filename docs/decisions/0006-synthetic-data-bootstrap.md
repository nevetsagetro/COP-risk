# ADR 0006: bootstrap con datos sintéticos

- Status: Accepted
- Date: 2026-07-26
- Accepted: 2026-07-26
- Decision owners: aprobación humana registrada

## Context

Tres rondas documentales no produjeron un dataset real apto para entrenamiento.
SFLLD permanece `Reject`; Home Credit Model Stability y PKDD’99 permanecen
`Needs clarification`; ningún candidato está autorizado para cuarentena. COP
necesita una fuente de desarrollo que no rebaje los gates metodológicos,
legales o de publicación.

El repositorio no contiene un generador, dataset sintético, split, modelo ni
monitoring. Este ADR registra una decisión de desarrollo; su aceptación no
demuestra implementación.

## Decision

Se adopta un dataset sintético determinista como dataset principal inicial de
la primera vertical de COP.

La decisión queda sujeta a estas condiciones:

1. El generador, su configuración, sus semillas y sus snapshots serán
   versionados. Una semilla maestra y semillas derivadas con namespaces
   estables determinarán cada snapshot.
2. Cada snapshot tendrá configuración resuelta, versión del generador,
   `snapshot_as_of` UTC, esquema, conteos, lineage y hashes físicos y lógicos
   en un manifest. El cutoff formará parte de la identidad y la madurez nunca
   dependerá del reloj de ejecución.
3. El dataset material se escribirá en Parquet y no se generará hasta un
   milestone posterior con implementación y tests propios.
4. El target se derivará de eventos de repayment posteriores a la decisión;
   ningún input podrá depender del outcome, de variables post-decision o de
   verdad interna del generador.
5. Las etiquetas inmaduras, ausentes o censuradas serán `unknown`, nunca
   negativas.
6. Los atributos protegidos, si se generan para auditoría, estarán físicamente
   separados como `audit_only` y nunca serán inputs.
7. Los splits respetarán temporalidad y `borrower_id`. El test final quedará
   intacto y fuera de selección, HPO, early stopping, calibración y thresholds.
8. Un dataset real futuro deberá superar exactamente el contrato, protocolo,
   gates documentales, cuarentena, checklist y aceptación humana vigentes. El
   bootstrap sintético no concede aceptación parcial a candidatos rechazados o
   pendientes.

La definición final del target, umbral de DPD, horizonte, población, estimand,
tamaño, número de borrowers y solicitudes, prevalencia, ventanas,
distribuciones, correlaciones, escenarios exactos de drift, thresholds y gates
cuantitativos permanecen pendientes. El contenido concreto de
`docs/synthetic-data-specification.md` sigue siendo propuesta y este ADR no lo
acepta automáticamente.

## Claims permitidos y prohibidos

El bootstrap podrá demostrar comportamiento de ingeniería: reproducibilidad,
lineage, controles de leakage, splits, evaluación, monitoring de escenarios
inyectados y lifecycle controlado.

No sustenta claims sobre:

- rendimiento, calibración o utilidad en crédito real;
- prevalencia, comportamiento o representatividad de una población real;
- fairness, ausencia de discriminación o cumplimiento regulatorio;
- validez causal o capacidad para tomar decisiones financieras.

Los resultados se identificarán siempre como sintéticos. Un resultado
favorable solo describe el mecanismo simulado y la configuración versionada.

## Alternatives considered

### Detener el desarrollo hasta encontrar datos reales

Preserva una conexión directa con evidencia empírica, pero la búsqueda cerrada
no encontró una fuente que superase los gates. Mantendría bloqueados controles
de ingeniería que sí pueden validarse sintéticamente.

### Relajar licencia, temporalidad, target o leakage

Se rechaza. Convertiría una restricción metodológica o legal en deuda oculta y
haría incompatible el resultado con un portfolio público verificable.

### Adoptar inmediatamente un enfoque híbrido

No es viable hoy porque no existe capa real aprobada. Permanece como opción
futura si un dataset real supera los mismos gates sin reinterpretar decisiones
anteriores.

## Consequences

- COP podrá avanzar con una fuente controlada y potencialmente redistribuible
  una vez que generador, licencia y condiciones de publicación sean aceptados
  e implementados.
- Drift, labels tardías y recuperación podrán probarse contra una verdad de
  simulación conocida.
- El realismo será deliberadamente limitado y documentado; mayor complejidad
  sintética no equivale a mayor validez externa.
- La especificación, el generador y los snapshots necesitarán versionado
  independiente.
- Cambiar el mecanismo generativo puede invalidar comparaciones entre
  snapshots aunque el esquema permanezca estable.

## Reversibility

Alta. El adaptador de datos y el contrato deben permanecer independientes del
origen. Sustituir o complementar el bootstrap exigirá aceptar el nuevo dataset
y crear snapshots nuevos; no permitirá reutilizar métricas sintéticas como
evidencia real.

## Open questions

- Definición final del target, umbral exacto de DPD y horizonte.
- Población y estimand.
- Tamaño del snapshot, número de borrowers y solicitudes, y prevalencia.
- Ventanas temporales, distribuciones y correlaciones.
- Escenarios exactos de drift, thresholds y gates cuantitativos.
- Formato exacto del manifest y mecanismo material para sellar el test.
- Ownership, licencia y condiciones de redistribución del generador y de sus
  snapshots.
