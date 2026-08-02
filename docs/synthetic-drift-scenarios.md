# Escenarios propuestos de drift sintético

## Estado y separación de capas

Este catálogo es configurable y medible, pero no está implementado. Magnitudes,
ventanas, thresholds y respuestas automáticas permanecen pendientes.

| Capa | Puede conocer | No puede hacer |
|---|---|---|
| Generador | Configuración y verdad completa del escenario | Presentarla como evidencia real |
| Evaluación sintética | Verdad, snapshots, predicciones y labels maduras | Exponer oracle al modelo |
| Monitoring | Reference/current comparables y datos disponibles as-of | Consultar `scenario_id`, factores latentes u onset real |
| Lifecycle | Informe y evidencia auditada | Promover o hacer rollback automáticamente |

`scenario_id`, mecanismo, onset real, propensiones, factores latentes y shocks
son `prohibited` para inputs y monitoring. Solo sirven para puntuar la
evaluación del escenario.

## Parámetros comunes

Cada escenario declarará versión, semilla, calendario, cohortes, segmento,
onset, duración, ramp-up/ramp-down, recurrencia, dimensión, dirección y
magnitud. También declarará mecanismo base y perturbado, reglas de labels,
particiones, versiones congeladas de modelo/calibrador/threshold y definiciones
de métricas.

No habrá defaults silenciosos para ventanas, magnitudes, tasa, thresholds,
cohortes consecutivas o suficiencia muestral.

## Catálogo mínimo

### Control estacionario

Mantiene `P(X)`, `P(Y|X)`, elegibilidad, disponibilidad y retraso. Mide
variación muestral y falsos positivos de la política candidata.

### Covariate drift

Cambia `P(X)` de inputs válidos manteniendo fijo `P(Y|X)`. Admite una feature,
un conjunto correlacionado o segmento; cambio abrupto, gradual, pulso o
recurrente. La prevalencia puede variar como consecuencia del cambio de
población y no se fuerza artificialmente.

### Prior probability drift

Cambia `P(Y)` manteniendo `P(X|Y)` fijo por construcción y verificándolo contra
la verdad sintética. La prevalencia solo se observa con labels maduras; score o
tasa predicha son proxies y no prueban label shift.

### Concept drift

Mantiene `P(X)` y cambia `P(Y|X)`: intercepto, coeficientes, interacciones o
inversión localizada. Incluirá una variante aproximadamente estable en
prevalencia para separarlo de prior drift. La versión del mecanismo nunca está
disponible para monitoring.

### Delayed labels

Mantiene `P(X,Y)` y `outcome_timestamp`, pero cambia la distribución de
`label_observed_at` y, por ello, el primer instante de madurez
`label_ready_at`. Retraso, pérdida de cobertura y censura son perturbaciones
separadas. Unknown nunca se convierte en negativo.

### Degradación

Es una consecuencia medida sobre un champion congelado, no una bandera
generada. Se induce mediante drift relevante y solo se confirma con
predicciones inmutables y labels maduras comparables.

### Recuperación

Se distinguen:

- retorno distributivo de inputs o scores;
- recuperación supervisada de métricas maduras;
- retorno natural del mecanismo al régimen base;
- adaptación de un challenger sobre cohortes comparables.

El retorno de una señal descriptiva no prueba recuperación de performance. Un
challenger mejor no queda promovido automáticamente.

### Ventanas de retraining

Cada caso separará:

- current observable, aunque aún no tenga labels;
- subconjunto supervisado maduro as-of;
- ventana de train deslizante o expansiva;
- gap/purga compatibles con horizonte y lag;
- validation/comparison posterior y disjunta;
- calibración/threshold pre-test;
- test final intacto.

Se medirá cuánto dato post-cambio maduro entra realmente en training. Falta de
madurez se registra como limitación, no se corrige recodificando labels.

Primero se evaluarán perturbaciones aisladas. Combinaciones como covariate
drift más delayed labels serán escenarios posteriores explícitos.

## Mediciones propuestas

| Señal | Medición candidata | Condición |
|---|---|---|
| Calidad | Tasa de violación de esquema, IDs, timestamps y roles | Cada cohorte |
| Numérica | Wasserstein normalizada con escala reference | Reference/current comparables |
| Categórica | Jensen-Shannon incluyendo missing | Reference/current comparables |
| Missingness | Diferencia de proporciones por feature | Semántica estable |
| Predicción | Distancia de scores | Mismo `model_version` y calibrador |
| Tasa predicha | Diferencia con threshold congelado | Solo diagnóstico |
| Prevalencia | Media de `y` con conteos e incertidumbre | Labels maduras y cobertura |
| Madurez | Maduras elegibles / elegibles; censura separada | Por cohorte/cutoff |
| Registro positivo | `label_observed_at - outcome_timestamp` solo en positivos observados | No describe negativos |
| Disponibilidad del label | `label_ready_at - horizon_end`, siempre no negativa, en toda la cohorte elegible | Denominadores y censura explícitos |
| Performance | Brier, log loss, ROC-AUC y PR-AUC con prevalencia | Cohorte madura común |
| Threshold | Sensibilidad, especificidad, precisión, FPR y FNR | Threshold congelado |
| Concepto | Riesgo por bins/estratos predeclarados | Diagnóstico, no causalidad |
| Detección | Latencia, falsos positivos y falsos negativos | Solo con oracle sintético |
| Retraining | Mezcla pre/post-onset, madura y censurada | Solo evaluación sintética |

Ninguna métrica tiene aún threshold aceptado. Sin política aprobada, la
respuesta máxima es informe offline y triage humano.

## Invariantes

- Configuración, snapshots y predicciones son inmutables y tienen hashes.
- Inputs cumplen `available_at <= decision_timestamp`.
- Target, atributos protegidos, IDs, oracle y factores latentes no son inputs.
- Reference/current comparten contrato; cambios incompatibles bloquean o
  segmentan la comparación.
- Prediction drift conserva modelo, calibrador y threshold.
- Métricas supervisadas usan únicamente labels maduras.
- Toda label cumple `label_observed_at <= label_ready_at`; solo
  `label_ready_at <= snapshot_as_of` habilita métricas supervisadas.
- Particiones no solapan IDs, fingerprints ni entidades cuando corresponde.
- El test no es reference, train, fuente de thresholds o comparación iterativa.
- Challenger/champion usan la misma cohorte y contrato.
- Drift descriptivo, degradación y causalidad no se confunden.
- Monitoring puede solicitar revisión; nunca promociona ni hace rollback.
- El diseño es batch/offline y no se presenta como real-time.

## Riesgos y límites

Variación muestral, múltiples comparaciones, estacionalidad, referencias
deficientes, cambios de esquema, censura diferencial y mezcla de segmentos
pueden crear falsos positivos. Concept drift marginalmente invisible,
degradación localizada, labels tardías y dependencias multivariantes pueden
crear falsos negativos.

Escenarios demasiado limpios sobreestiman detectabilidad. Sus resultados no
sustentan performance, calibración, fairness ni utilidad sobre datos reales.
Antes de aceptar thresholds se separarán una suite de desarrollo y otra
sellada de evaluación de la política para no ajustarla al mismo oracle.
Las pruebas incluirán cohortes completamente negativas, positivas tempranas y
mixtas: aumentar solo el lag debe aumentar la medición sin cambiar `P(X,Y)` ni
recodificar unknown.
