# Checklist de aceptación de datasets candidatos

## Uso

Esta checklist tiene dos fases. La fase A se completa antes de autorizar una
adquisición. Solo una fuente que la supera puede recuperarse en cuarentena
local ignorada por Git para completar la fase B. Esa adquisición controlada no
equivale a selección y no autoriza transformación ni entrenamiento. Este
milestone no ejecuta ninguna de las fases.

Cada fila registra `Pass`, `Fail`, `Not evidenced` o `Not applicable`,
evidencia reproducible, responsable y observaciones. `Not applicable` exige
justificación aceptada.

No existe puntuación compensatoria:

- un fallo o falta de evidencia en un rechazo duro produce `Rejected`;
- `Fail` o `Not evidenced` en cualquier otro requisito aplicable mantiene
  `Pending` hasta corregirse;
- `Not applicable` solo es válido con justificación revisada;
- `Eligible for human review` exige `Pass` en todos los requisitos aplicables.

Completar esta plantilla no implica que exista ni se haya aceptado un dataset.

## Fase A: autorización documental pre-adquisición

- [ ] **Rechazo duro:** fuente, publicador, versión y cadena de procedencia
  están identificados mediante evidencia conservable.
- [ ] **Rechazo duro:** la licencia permite obtener e inspeccionar el artefacto
  y es compatible, en principio, con el uso previsto.
- [ ] El esquema y diccionario publicados permiten formular unidad, target,
  timestamps e inventario preliminares sin presentarlos como verificados.
- [ ] El mecanismo de acceso no exige credenciales reales versionadas ni
  incorporar datos de clientes.
- [ ] Las declaraciones disponibles de anonimización/PII permiten una
  inspección controlada; no sustituyen la revisión de contenido.
- [ ] Se define una cuarentena local ignorada por Git y un responsable para
  decidir eliminación o paso a revisión.

Si la fase A no queda íntegramente resuelta, no se autoriza adquisición. Los
apartados siguientes pertenecen a la fase B y requieren acceso controlado al
artefacto.

## Fase B: inspección controlada previa a selección

## Identidad, población y target

- [ ] **Rechazo duro:** la unidad de observación y la unidad de predicción
  tienen una definición inequívoca y verificable.
- [ ] **Rechazo duro:** existe `entity_id` pseudonimizado, estable y suficiente
  para detectar repeticiones y prevenir entity leakage cuando corresponda.
- [ ] **Rechazo duro:** `observation_id` identifica de forma única y
  reproducible cada evento de decisión.
- [ ] **Rechazo duro:** población, inclusiones y exclusiones se calculan solo
  con información disponible en el instante de decisión.
- [ ] **Rechazo duro:** el target se deriva de eventos fuente trazables y
  corresponde al instante de decisión; no es una etiqueta post-outcome
  desalineada.
- [ ] Horizonte, extremos, códigos, eventos competidores y regla de missing
  están declarados.
- [ ] `decision_timestamp`, `outcome_timestamp`, `label_observed_at`,
  `followup_end` y cutoff tienen semántica, fuente y zona documentadas.
- [ ] **Rechazo duro:** las etiquetas utilizadas están maduras y su cobertura
  completa se demuestra; inmaduras, ausentes y censuradas no son negativas.

## Temporalidad, features y leakage

- [ ] **Rechazo duro:** existen timestamps y rango suficientes para validar
  temporalidad y reservar un test futuro.
- [ ] **Rechazo duro:** cada input y dependencia demuestra
  `available_at <= decision_timestamp`.
- [ ] **Rechazo duro:** no quedan inputs post-decision, post-outcome, derivados
  del target o proxies directos; si son inseparables, el candidato se rechaza.
- [ ] Identificadores, metadata de partición/snapshot y timestamps futuros
  están excluidos de inputs.
- [ ] Lineage, lookback, unidades, categorías y missing de cada feature están
  documentados.
- [ ] Duplicados exactos y semánticos están cuantificados y su política no
  consulta el target.
- [ ] **Rechazo duro:** conflictos de duplicados se pueden resolver sin elegir
  por label y repetidos se distinguen de duplicados.

## Particiones y evaluación

- [ ] **Rechazo duro:** puede reservarse un test temporal intacto y
  reproducible.
- [ ] **Rechazo duro:** puede evitarse entity leakage o existe una justificación
  verificable para un protocolo walk-forward compatible con el caso de uso.
- [ ] Las intersecciones de `observation_id` y fingerprints entre train,
  validation, calibración/threshold y test serán cero.
- [ ] Cuando rige separación por entidad, la intersección de `entity_id` entre
  particiones será cero.
- [ ] Labels usadas en cada fold estarán disponibles en su cutoff simulado.
- [ ] Preprocessing, selección de features y resampling se ajustarán solo
  dentro de folds de entrenamiento.
- [ ] HPO se limitará a CV interna de train.
- [ ] Early stopping usará un subfold distinto del que puntúa el trial.
- [ ] Calibración usará datos pre-test dedicados o predicciones out-of-fold.
- [ ] Threshold se elegirá solo con datos pre-test y objetivo predeclarado.
- [ ] **Rechazo duro:** el test quedará excluido de feature selection, HPO,
  early stopping, calibración, threshold y comparación iterativa.
- [ ] Semilla maestra, derivación, asignación estable y versiones quedarán
  registradas sin elegir semillas por resultado.

## Procedencia, licencia y privacidad

- [ ] La versión y contenido inspeccionados corresponden a la evidencia de
  procedencia aprobada en fase A.
- [ ] **Rechazo duro:** la licencia permite el uso previsto y, cuando aplique,
  transformación y redistribución, no solo la inspección.
- [ ] **Rechazo duro:** el dataset es sintético o público anonimizado y no
  contiene PII conocida; la revisión cubre valores y metadata, no solo nombres.
- [ ] Identificadores pseudonimizados se tratan como enlazables, con
  minimización y acceso documentado.
- [ ] **Rechazo duro:** si existen atributos protegidos y su conservación es
  lícita, pueden segregarse como `audit_only`; si están ausentes, se evidencia
  su ausencia de inputs; si son inseparables de inputs, se rechaza.
- [ ] Las limitaciones de cobertura de atributos de auditoría se documentan sin
  claims de fairness.

## Snapshot, manifest y reproducibilidad

- [ ] **Rechazo duro:** el snapshot se puede reconstruir o recuperar de forma
  inmutable con un `snapshot_id` estable.
- [ ] **Rechazo duro:** hashes por archivo y contenido verifican el snapshot.
- [ ] El manifest identifica contrato, esquema, origen, cutoff, rango temporal,
  filas, entidades y roles de columnas.
- [ ] El manifest reconcilia elegibles, exclusiones, duplicados, repetidos y
  labels maduras, inmaduras y censuradas.
- [ ] Transformaciones, padres y versión de código/configuración tienen
  lineage reproducible.
- [ ] **Rechazo duro:** el snapshot permite conservar un test intacto y no usa
  ese test como reference dataset de monitoring.

## Preparación para monitoring futuro

- [ ] Reference y current futuros podrán compartir contrato semántico,
  población, unidades, missing y reglas as-of.
- [ ] `prediction_id`, `observation_id`, `prediction_timestamp`,
  `model_version` y batch permitirán asociar predicciones sin ambigüedad.
- [ ] Labels tardías podrán unirse de forma auditable sin reescribir
  desconocidos como negativos.
- [ ] **Rechazo duro:** las claves y timestamps del candidato permiten definir
  una unión futura no ambigua entre observación, predicción, versión de modelo
  y label.
- [ ] La futura validación de monitoring comprobará integridad referencial y
  registros huérfanos cuando existan predicciones; no se presume ejecutada
  durante la aceptación del dataset.
- [ ] Cambios incompatibles de contrato, pipeline, población o modelo podrán
  identificarse y segmentarse antes de interpretar drift.

## Rechazo y decisión

El informe final deberá enumerar cada fallo y evidencia ausente. Se rechaza
explícitamente el candidato si ocurre cualquiera de estos casos:

- target desalineado con el instante de decisión;
- features post-outcome o post-decision inseparables;
- entity leakage inevitable o no verificable;
- timestamps insuficientes para validar temporalidad;
- licencia incompatible;
- PII o procedencia incierta;
- imposibilidad de reservar test intacto;
- snapshot no reproducible;
- labels sin madurez demostrable;
- atributos sensibles inseparables del input.

Resultado: `Pending | Rejected | Eligible for human review`.

Responsable:

Fecha:

Perfil/manifest revisado:

Evidencia y justificación:

## Decisiones que esta checklist no resuelve

Fuente, target, horizonte, features, métrica primaria, gates, threshold, tamaño
de particiones, método de censura, mecanismo de snapshots y autoridad de
aceptación continúan pendientes de decisión humana.
