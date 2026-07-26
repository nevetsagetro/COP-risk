# Inspección controlada de SFLLD Sample 2019

## Conclusión

**Reject**

El contenido es técnicamente legible, internamente consistente en los checks
limitados y puede reabrirse con nueva evidencia. Se rechaza con la evidencia
actual porque la checklist convierte cualquier rechazo duro `Not evidenced`
en `Rejected`. No es elegible:
faltan evidencia de release/cutoff y términos aplicables, una entidad estable
a nivel prestatario, instante de decisión y disponibilidad as-of inequívocos,
target/horizonte aprobados, reglas de madurez y censura, y demostración de un
split temporal intacto sin entity leakage.

Para este milestone, `Rejected` se expresa con el rótulo solicitado `Reject`.
No es un fallo técnico del ZIP ni una aceptación para entrenamiento.

## Método y minimización

Se inspeccionaron nombres y metadata del ZIP, 64 KiB y como máximo 100 filas
por fichero para detectar codificación y delimitador, y después se realizó una
pasada secuencial agregada para anchura, missingness en blanco, duplicados,
claves y rangos temporales. La pasada no conservó ni emitió filas o IDs; los
IDs se mantuvieron solo en memoria para reconciliación. No se realizó EDA,
distribuciones de valores, selección de features ni construcción de labels.

## Inventario y formato

| Fichero | Rol fuente | Filas | Columnas | Formato |
|---|---|---:|---:|---|
| `sample_orig_2019.txt` | originación por préstamo | 50,000 | 32 | ASCII/UTF-8 compatible, sin header, `|` |
| `sample_svcg_2019.txt` | performance préstamo-mes | 1,847,477 | 32 | ASCII/UTF-8 compatible, sin header, `|` |

Todas las filas tuvieron 32 campos. No se detectaron bytes NUL ni errores de
decodificación. La estructura coincide con el layout de 32 posiciones de la
guía oficial de enero de 2026; la guía, no el nombre de columna, sigue siendo
la fuente semántica.

## Esquema y roles provisionales

Originación contiene atributos de crédito y préstamo, fechas de primer pago y
vencimiento, geografía aproximada, loan sequence number y metadata del
producto/originador. El loan sequence number es una clave técnica
`partition_only`, nunca input. Geografía, credit score, DTI, occupancy y otros
posibles proxies requieren revisión específica; ningún campo queda aprobado
como feature.

Servicing contiene loan sequence number, periodo mensual, saldo, mora, edad y
plazo, eventos de defecto/modificación/zero balance, recuperaciones, costes y
pérdidas. Para un modelo de originación son datos post-decision y se reservan
como `target_only`, `audit_only` o `prohibited` según una futura definición;
no son inputs de originación.

## Identificadores, tiempo y joins

- El loan sequence number fue único en originación.
- La pareja loan sequence number y periodo mensual fue única en servicing.
- Los 50,000 préstamos de originación tuvieron servicing y viceversa.
- No hubo registros servicing huérfanos.
- No se observó borrower ID estable entre préstamos. El loan ID controla
  repetición préstamo-mes, pero no prueba separación por prestatario.
- Primer pago observado: febrero de 2019 a junio de 2021.
- Reporting mensual observado: enero de 2019 a septiembre de 2025.

Las fechas agregadas no identifican por sí solas `decision_timestamp`,
`available_at`, `label_observed_at`, `followup_end` o `snapshot_as_of`.
Reporting month combina ciclos de reporte y no prueba disponibilidad en tiempo
real. La guía también advierte correcciones y gaps; por ello no se ha
demostrado todavía una simulación as-of.

## Missingness y duplicados

No hubo filas duplicadas exactas ni claves naturales duplicadas. Los blanks
por posición se registran en
`configs/datasets/sflld-sample-2019.yaml`. Los patrones principales fueron:

- originación: 4,574 blanks en MSA; tres campos casi totalmente ausentes con
  48,333 o 49,970 blanks;
- servicing: muchos campos de eventos, recuperación, pérdida y modificación
  están vacíos en la mayoría de los préstamo-mes, como cabe esperar para
  eventos condicionales;
- algunos códigos documentados representan “not available” sin estar vacíos;
  por tanto, blank no equivale a missingness semántica total.

La inspección no transformó sentinels, imputó valores ni resolvió significado
de nulls. Tampoco comprobó duplicados semánticos a nivel prestatario, porque no
existe una clave demostrada para ello.

## Labels potenciales y leakage

Mora mensual, zero balance y sus códigos/fechas, defectos, modificaciones,
disposición, recuperaciones y actual loss podrían contribuir a un target
futuro. Son solo candidatos de outcome: no se elige target, evento positivo,
horizonte, extremos, eventos competidores ni política de prepago/censura.

Estos mismos campos son post-decision para originación y quedarían prohibidos
como inputs. Incluso los atributos de originación requieren demostrar
`available_at <= decision_timestamp`. La falta de borrower ID deja abierto
entity leakage entre varios préstamos del mismo prestatario.

## Preparación para monitoring futuro

El loan sequence number y periodo mensual permiten comprobar integridad y
construir cohortes de préstamo; fechas de primer pago/originación y atributos
de producto podrían describir cambios de población. Mora, saldo,
modificaciones, zero balance y pérdidas servirían solo para calidad/outcomes o
performance tardía, respetando madurez.

No existen en la fuente `prediction_id`, `prediction_timestamp`,
`model_version` o batch; serían metadata futura. Antes de comparar reference y
current deben congelarse release/cutoff, población, esquema, reglas de missing
y disponibilidad. Correcciones retroactivas, masking, cambios de población y
seller/servicer pueden aparentar drift y deben segmentarse como cambios de
contrato, no interpretarse automáticamente como drift.

## Checklist aplicada

Responsable de todas las filas: agente `coordinator`. `NE` significa
`Not evidenced`. La evidencia se refiere a este informe, el registro de
adquisición (`ACQ`) o la configuración (`CFG`). `Hard` identifica los rechazos
duros de la checklist.

| ID | Requisito resumido | Estado | Evidencia | Observación |
|---|---|---|---|---|
| A1 Hard | Fuente, versión y procedencia | NE | ACQ: Procedencia | Release/cadena no reconciliados |
| A2 Hard | Licencia para inspección | NE | ACQ: Estado | Términos humanos pendientes |
| A3 | Esquema preliminar | Pass | Inventario/esquema | Guía y 32 posiciones coinciden |
| A4 | Acceso sin secretos versionados | Pass | ACQ: Git | ZIP local; cero credenciales |
| A5 | Declaración PII permite inspección | NE | Privacidad pendiente | No sustituye revisión |
| A6 | Cuarentena y responsable | Pass | ACQ: Estado/Git | Ruta ignorada y responsable técnico |
| B1 Hard | Unidad observación/predicción | NE | Identificadores | Préstamo vs préstamo-mes pendiente |
| B2 Hard | `entity_id` estable | NE | Identificadores | Loan ID no es borrower ID |
| B3 Hard | `observation_id` reproducible | NE | CFG: open fields | Pareja préstamo-mes no aceptada |
| B4 Hard | Población as-of | NE | CFG: open fields | Predicado no definido |
| B5 Hard | Target alineado | NE | Labels | Solo candidatos |
| B6 | Horizonte/códigos/competidores/missing | NE | Labels/missingness | Sin definición aprobada |
| B7 | Timestamps y zonas | NE | Tiempo | Campos conceptuales incompletos |
| B8 Hard | Madurez y cobertura | NE | Labels | Censura/cutoff no operacionales |
| B9 Hard | Tiempo suficiente/test futuro | NE | Rango agregado | Rango existe; viabilidad no probada |
| B10 Hard | Inputs disponibles al decidir | NE | Tiempo | `available_at` ausente |
| B11 Hard | Sin post-decision inseparable | Pass | Leakage | Servicing físicamente separable |
| B12 | IDs/metadata/futuro excluidos | NE | Roles provisionales | No hay inventario aprobado |
| B13 | Lineage/unidades/missing por feature | NE | Missingness/CFG | Solo blanks por posición |
| B14 | Duplicados cuantificados | Pass | Missingness/CFG | Exactos y claves: cero |
| B15 Hard | Conflictos/repetidos distinguibles | NE | Identificadores | Sin entidad prestatario |
| B16 Hard | Test temporal intacto | NE | CFG: open fields | Split fuera de alcance |
| B17 Hard | Evitar entity leakage | NE | Identificadores | Borrower ID ausente |
| B18 | Intersecciones IDs/fingerprint cero | NE | Protocolo futuro | Sin particiones |
| B19 | Intersección entidad cero | NE | Protocolo futuro | Sin entidad/split |
| B20 | Labels disponibles por cutoff | NE | Tiempo | `label_observed_at` ausente |
| B21 | Fit preprocessing/resampling en train | NE | Fuera de alcance | Sin pipeline/split |
| B22 | HPO solo CV interna | NE | Fuera de alcance | Sin HPO |
| B23 | Early stopping separado | NE | Fuera de alcance | Sin entrenamiento |
| B24 | Calibración pre-test/OOF | NE | Fuera de alcance | Sin calibración |
| B25 | Threshold pre-test | NE | Fuera de alcance | Sin threshold |
| B26 Hard | Test excluido de adaptación | NE | Fuera de alcance | Test no materializado |
| B27 | Semillas/versiones registradas | NE | Fuera de alcance | Split/pipeline ausentes |
| B28 | Artefacto corresponde a fase A | NE | ACQ: Procedencia | Hash local sin release oficial |
| B29 Hard | Licencia para uso previsto | NE | ACQ: Estado | Decisión humana pendiente |
| B30 Hard | Público anonimizado, sin PII | NE | Privacidad pendiente | No probado por nombres |
| B31 | IDs enlazables controlados | NE | Identificadores | Acceso/retención pendientes |
| B32 Hard | Atributos protegidos segregables | NE | Roles provisionales | Revisión de proxies pendiente |
| B33 | Límites de auditoría | Pass | Leakage | No se afirma fairness |
| B34 Hard | Snapshot estable recuperable | NE | ACQ: Procedencia | Hash local, recuperación no probada |
| B35 Hard | Hashes verifican snapshot | Pass | ACQ/CFG | ZIP y ambos TXT hasheados |
| B36 | Manifest completo | NE | CFG: open fields | Config es perfil, no manifest aceptado |
| B37 | Reconciliación completa | NE | CFG | Joins sí; labels/censura no |
| B38 | Lineage transformaciones/padres | NE | Sin transformaciones | Origen/release aún pendiente |
| B39 Hard | Test intacto, no reference | NE | Fuera de alcance | No hay test/reference |
| B40 | Reference/current comparables | NE | Monitoring | Contrato/cutoff pendientes |
| B41 | Metadata de predicción | NE | CFG: monitoring | Campos futuros ausentes |
| B42 | Join de labels tardías | NE | Monitoring | Timing/censura ausentes |
| B43 Hard | Join observación-predicción-label | NE | Monitoring | Solo loan ID/periodo fuente |
| B44 | Integridad futura de predicciones | NE | Fuera de alcance | No existen predicciones |
| B45 | Segmentar cambios incompatibles | NE | Monitoring | Requiere versiones futuras |

Los `Pass` técnicos no compensan los rechazos duros `NE`. Resultado único con
la evidencia actual: **Reject**. Puede abrirse una inspección posterior si se
aportan evidencias, pero este snapshot no se aprueba para entrenamiento.
