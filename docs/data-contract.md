# Contrato metodológico de datos

## Estado y alcance

Este documento define las condiciones que cualquier dataset candidato deberá
demostrar antes de ser seleccionado, transformado o usado. Es un metacontrato:
no selecciona una fuente, no define un target concreto y no afirma que existan
datos.

Un candidato futuro deberá aportar un perfil y un manifest versionados que
instancien todas las definiciones pendientes. Una columna con un nombre
plausible no constituye evidencia de su semántica, temporalidad o procedencia.

## Convención de verificabilidad

Cada requisito tiene cuatro partes:

- **definición operacional**: significado que no depende del nombre de una
  columna;
- **declaración del candidato**: valor concreto que deberá proponerse;
- **evidencia**: artefacto o comprobación reproducible exigida;
- **rechazo**: condición que impide aceptar el candidato.

`No evidenciado` equivale a incumplimiento en los requisitos obligatorios. Los
valores concretos de población, target, horizonte y gates requieren aprobación
humana posterior.

La evaluación futura tendrá dos gates:

1. **Pre-adquisición documental**: antes de autorizar una descarga se verifican
   identidad de la fuente, procedencia, licencia, descripción del esquema,
   mecanismo de acceso y declaraciones disponibles sobre PII/anonimización.
2. **Inspección controlada**: solo una fuente que supere el primer gate puede
   recuperarse en una cuarentena local ignorada por Git. Allí se verifican
   contenido, hashes, esquema, IDs, timestamps, duplicados, labels, PII y
   viabilidad del split. La adquisición no equivale a selección y no autoriza
   transformación ni entrenamiento.

Este milestone solo define ambos gates; no ejecuta adquisición alguna.

## Unidad, población e instante de decisión

| Término | Definición operacional | Declaración y evidencia futuras | Rechazo |
|---|---|---|---|
| Unidad de observación | Un evento de decisión elegible para una entidad en un instante definido. Una fila fuente no se presume equivalente a una observación. | Clave natural, reglas de normalización y reconciliación entre filas fuente y eventos. | Una fila mezcla eventos o no puede vincularse sin ambigüedad a uno. |
| Unidad de predicción | Una predicción para una entidad elegible en un evento de decisión, con una oportunidad definida de observar el resultado. | Entidad, evento, cadencia y cardinalidad esperada. | No puede determinarse qué representa una predicción. |
| Población elegible | Predicado determinista de inclusión y exclusión evaluable solo con hechos disponibles en el instante de decisión. | Universo, reglas versionadas, denominador y conteos por exclusión. | La elegibilidad depende del outcome, target o información posterior. |
| Instante de decisión | Momento en que se emitiría la predicción y queda cerrado el conjunto de información permitido. | Fuente, zona horaria, calendario y regla de desempate. | Se usa extracción, ingestión u outcome como sustituto sin evidencia. |

La semántica general es una predicción por pareja entidad-evento. La entidad,
el evento y la población concretos permanecen pendientes.

## Target, horizonte, madurez y censura

El target futuro deberá expresarse como una función predeclarada y auditable:
`y = 1` si y solo si un evento positivo definido mediante fuente y códigos
trazables ocurre dentro de la ventana acordada desde el instante de decisión.
Deberá declarar también el evento negativo, eventos competidores, correcciones
tardías, extremos inclusivos o exclusivos y tratamiento de valores ausentes.

- **Horizonte**: intervalo entre el instante de decisión y el cierre de la
  ventana de resultado, con unidad, calendario, zona y extremos explícitos.
- **Timestamp de resultado**: instante del evento que determina el outcome,
  separado de cuándo se registró o ingirió.
- **Madurez**: una observación es apta para análisis supervisado solo cuando el
  cutoff del snapshot supera el horizonte completo más el retraso de
  observación declarado y existe cobertura verificable hasta ese cierre. La
  misma regla se aplica a toda la cohorte.
- **Censura**: falta de observación completa del horizonte por corte
  administrativo, pérdida de seguimiento, evento competidor u otra cobertura
  insuficiente. Se registra su motivo y `followup_end`.

Una etiqueta inmadura, ausente o censurada nunca se convierte en negativa. Si
el evento target, la ventana, la madurez o la censura no pueden reconstruirse,
el candidato se rechaza.

## Identificadores y tiempo

El perfil futuro deberá mapear, como mínimo, estos conceptos:

| Campo conceptual | Requisito verificable | Uso permitido |
|---|---|---|
| `entity_id` | Pseudónimo estable que permite detectar observaciones repetidas; no contiene PII y su estabilidad se prueba. | Particionado, joins y auditoría; nunca input. |
| `observation_id` | Identificador único y reproducible del evento de decisión. | Integridad y trazabilidad; nunca input. |
| `decision_timestamp` | Timestamp con zona que representa el instante de decisión. | Split temporal y disponibilidad. |
| `outcome_timestamp` | Instante del evento target, si ocurre. | Construcción y auditoría de label; nunca input. |
| `label_observed_at` | Momento en que la etiqueta pasó a estar disponible. | Madurez y simulación as-of. |
| `followup_end` | Último instante con cobertura verificable. | Detección de censura. |
| `snapshot_as_of` | Cutoff temporal del contenido materializado. | Reproducción y madurez. |
| `ingested_at` | Momento técnico de ingestión. | Lineage; no prueba disponibilidad para decidir. |

Los timestamps se normalizarán a ISO-8601 con zona. El orden físico de las
filas no prueba orden temporal. Una pseudonimización sigue siendo información
enlazable y exige minimización y control de acceso.

## Inventario y disponibilidad de features

Cada feature y cada dependencia de su transformación deberá declarar:

- nombre, significado, tipo, unidad, categorías y semántica de missing;
- fuente y lineage;
- `event_time`, `recorded_at` y `available_at`, o una regla de disponibilidad
  equivalente y verificable;
- ventana de lookback y extremos;
- transformación y versión;
- rol: `input`, `audit_only`, `partition_only`, `target_only` o `prohibited`.

Para cada observación e input debe cumplirse
`available_at <= decision_timestamp`. `ingested_at` no sustituye
`available_at`. Una transformación agregada debe demostrar que todas sus
dependencias respetan el corte as-of.

Son siempre inputs prohibidos:

- target, derivados, proxies directos y componentes de su definición;
- outcome, cobranza, recuperación, cierre o acciones conocidos después de la
  decisión;
- identificadores, claves de partición y metadata de snapshot;
- atributos protegidos o sensibles;
- datos con disponibilidad desconocida o posterior a la decisión;
- agregados o transformaciones ajustados usando validation, test o la
  población completa.

Un proxy sospechoso exige revisión explícita; excluir nombres sensibles no
demuestra ausencia de sesgo.

## Duplicados y observaciones repetidas

Un duplicado representa el mismo evento de decisión más de una vez. Se
detectará con la clave natural y fingerprints, y se resolverá antes del split
mediante una regla determinista basada en procedencia, nunca en el target.
Conflictos irresolubles en campos críticos implican rechazo.

Una observación repetida es un evento distinto para la misma entidad. Debe
tener otro `observation_id`, un trigger o cadencia justificable y ventanas de
features reconstruidas as-of. Se cuantificará por entidad. Si no puede
distinguirse repetición de duplicación o no existe un `entity_id` útil para
controlar contaminación, el candidato se rechaza.

## Procedencia, licencia, anonimización y privacidad

Solo se permiten datos sintéticos o públicos anonimizados. El candidato deberá
aportar fuente original, publicador, versión, condiciones de uso y
redistribución, cadena de transformaciones y evaluación documentada de PII.

PII, procedencia incierta o licencia incompatible son rechazos duros. La
ausencia de PII no se presume por un escaneo de nombres. También se revisan
valores libres, identificadores, rutas y metadata.

Los atributos protegidos, si su conservación es lícita y necesaria, quedan en
una vista separada `audit_only`, con acceso documentado. Nunca entran en la
matriz de inputs, feature engineering, HPO, calibración o selección de
threshold. Si no pueden separarse, se rechaza el candidato. Si no existen datos
adecuados para auditoría, se documenta la limitación y no se afirma fairness.

## Snapshot y manifest obligatorios

Antes de aceptar un candidato deberá poder materializarse un snapshot
inmutable. Su manifest incluirá:

- `snapshot_id`, versión del contrato y versión de esquema;
- procedencia y versión de origen, licencia y evidencia asociada;
- cutoff, intervalo de decisiones, zona horaria y fecha de creación;
- hashes criptográficos del contenido y de cada fichero;
- filas, entidades, rangos temporales y conteos de reconciliación;
- diccionario de columnas y roles;
- población y exclusiones;
- duplicados, repeticiones, labels maduras, inmaduras y censuradas;
- transformaciones, snapshots padre y versión de código/configuración;
- comando o procedimiento futuro de materialización;
- responsable, resultado y evidencia de aceptación.

No se elige aquí herramienta o almacenamiento de versionado. Si el snapshot no
puede reproducirse o verificarse por hash, se rechaza.

## Requisitos para monitoring futuro

Sin implementar monitoring, el contrato reserva metadata para:

- **reference dataset**: snapshot congelado, no derivado del test final, con
  población, contrato, esquema, periodo y lineage explícitos;
- **current dataset**: cohorte temporal delimitada, con el mismo contrato
  semántico, conteos de elegibles/excluidos y versiones de features y modelo;
- **prediction drift**: `prediction_id`, `observation_id`,
  `prediction_timestamp`, score o clase, `model_version` y batch;
- **performance degradation**: unión auditable de predicciones inmutables con
  labels maduras, `outcome_timestamp`, `label_observed_at` y censura.

Reference y current deben ser comparables en unidad, población, semántica,
unidades, missing y disponibilidad. Cambios incompatibles bloquean la
comparación agregada o exigen segmentación; no se etiquetan como drift. No se
fijan métricas, ventanas ni umbrales.

## Vinculación con el protocolo de evaluación

Un candidato solo es compatible con este contrato si permite ejecutar
`docs/evaluation-protocol.md`: split temporal principal, separación por entidad
por defecto cuando existan observaciones repetidas, train/validation/test
separados y test final intacto. Feature selection, preprocessing, resampling,
HPO y early stopping se limitan a folds de entrenamiento; calibración y
threshold usan datos pre-test designados. El test no participa en ninguna de
esas tareas ni en comparación iterativa. La estrategia concreta de ventanas,
purga y estimand se declarará antes de materializar el split.

## Criterio de aceptación

Una fuente solo podrá adquirirse para inspección si supera el gate documental.
Un dataset solo podrá proponerse para selección o uso cuando cada campo
obligatorio tenga un valor concreto, evidencia reproducible y responsable; la
inspección controlada y la checklist estén completas sin fallos; y el protocolo
de evaluación pueda reservar particiones válidas. La aceptación del contrato
general no autoriza una descarga ni acepta ningún dataset.

## Decisiones humanas abiertas

- fuente, licencia y responsable de aprobación;
- entidad, evento, población y cadencia concretos;
- target, horizonte, retraso de observación y eventos competidores;
- política específica para repetidos y tratamiento futuro de censura;
- features, transformaciones y atributos disponibles para auditoría;
- mecanismo material de snapshots, retención y acceso;
- fuente y renovación del reference dataset;
- tamaños mínimos, métricas finales, gates y umbrales.
