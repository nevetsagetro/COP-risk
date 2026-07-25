# Protocolo metodológico de evaluación

## Estado y propósito

Este protocolo define cómo deberá evaluarse un futuro dataset aceptado sin
leakage. No evalúa datos, no elige modelo, métricas finales, gates ni
thresholds y no afirma que exista un pipeline.

## Precondiciones

Antes de particionar deberá existir un perfil del contrato aprobado, snapshot
inmutable y manifest con hashes; IDs de observación y entidad; timestamps de
decisión, disponibilidad y outcome; target, horizonte, madurez y censura
operacionales; inventario de features; procedencia/licencia; y estrategia de
split predeclarada.

## Orden obligatorio

1. Congelar snapshot, manifest y reglas.
2. Resolver duplicados sin consultar el target.
3. Determinar población, madurez y censura.
4. Asignar particiones por tiempo y, cuando corresponda, por entidad.
5. Congelar IDs, límites y política de acceso del test.
6. Ajustar selección, preprocessing, resampling, HPO y parada solo dentro de
   desarrollo.
7. Comparar configuraciones en datos pre-test designados.
8. Ajustar calibración y threshold con datos pre-test y reglas predeclaradas.
9. Congelar features, modelo, parámetros, calibrador y threshold.
10. Evaluar una vez sobre el test final.

## Particiones y estimand

El split principal será temporal; un split aleatorio no es la estimación
principal de comportamiento futuro. El orden conceptual es:

`train < validation < calibration/threshold < final_test`

Por defecto, una entidad pertenece a una sola partición. Primero se fijan
ventanas temporales y después se reservan las entidades de ventanas posteriores
para evitar que su historia aparezca en desarrollo. Las matrices de
intersección de `observation_id`, fingerprint y, cuando rige separación por
entidad, `entity_id`, deben ser cero.

Esta regla estima nuevas entidades y puede reducir la muestra. Si el futuro
caso de uso requiere nuevas decisiones sobre entidades conocidas, deberá
predeclararse un backtest walk-forward específico que pruebe historia as-of,
excluya labels futuras y trate dependencia por entidad. La elección del
estimand permanece abierta hasta definir la unidad de predicción; no puede
relajarse la separación solo para mejorar métricas.

En cada fold solo se usan labels que habrían estado observadas en su cutoff.
Pueden requerirse gaps o purga según horizonte, retraso y ventanas de features;
sus valores concretos quedan pendientes.

## Controles de leakage

| Riesgo | Regla operacional | Evidencia futura | Fallo |
|---|---|---|---|
| Entidad | Una entidad no cruza particiones salvo protocolo walk-forward aprobado. | Intersecciones y conteos por entidad. | Split inválido. |
| Temporal | Todo input cumple `available_at <= decision_timestamp`. | Inventario, lineage y comprobación as-of. | Feature prohibida o candidato rechazado. |
| Target | Ningún input depende del outcome, ventana target o acciones posteriores. | Lista prohibida y revisión de lineage. | Feature o candidato rechazado. |
| Label | Cada label de entrenamiento estaba disponible en el cutoff simulado. | `label_observed_at <= training_cutoff`. | Fila purgada o fold inválido. |
| Duplicado | IDs y fingerprints no cruzan particiones. | Reporte de solapamiento y deduplicación. | Split inválido. |
| Transformación | Todo fit ocurre dentro del fold de train. | Pipeline y tests futuros. | Evaluación inválida. |
| Adaptación al test | Ningún resultado del test cambia la pila. | Manifest congelado y registro de aperturas. | Deja de ser test final. |

SMOTE-Tomek, si se justifica en el futuro, se ajustará únicamente dentro del
fold de entrenamiento. Validation, calibración y test conservan la
distribución observada.

## Uso permitido de los datos

| Actividad | Datos permitidos | Datos prohibidos |
|---|---|---|
| Selección de features | Folds internos de train | Validation externa, calibración, threshold y test |
| Preprocessing/resampling | Fit en cada fold de train | Fit global o sobre cualquier partición posterior |
| HPO | CV temporal y agrupada dentro de train | Validation externa y test |
| Early stopping | Subfold separado del fit dentro de cada trial | Fold que puntúa el trial, validation externa y test |
| Calibración | Subconjunto pre-test dedicado o predicciones out-of-fold congeladas | Predicciones in-sample y test |
| Selección de threshold | Subconjunto pre-test dedicado y objetivo predeclarado | Test |
| Comparación challenger/champion | Misma cohorte de validation y contrato | Test consultado iterativamente |
| Evaluación final | Test intacto una vez congelada toda la pila | Cualquier ajuste posterior |

El fold usado para puntuar un trial no controla a la vez su early stopping.
Para el refit se registra una regla derivada de los folds internos. Calibración
y threshold usarán subsets disjuntos o predicciones cross-fitted. Si la
viabilidad muestral impide ambas opciones, los datos compartidos se tratan
íntegramente como desarrollo: no producen una estimación imparcial y cualquier
claim queda reservado al único test final aplicado con la pila congelada.

El test final nunca participa en selección de features, HPO, early stopping,
calibración, selección de threshold ni comparación iterativa de modelos. Si su
resultado provoca un cambio, ese resultado pasa a ser diagnóstico y una nueva
afirmación independiente requiere una cohorte final futura, no otra consulta
del mismo test.

## Duplicados, repetidos e incertidumbre

La deduplicación ocurre antes del split y registra conteos, claves y conflictos.
Nunca se elige una copia por su label. Las observaciones repetidas conservan
dependencia estadística; métricas e intervalos futuros deberán respetar
clustering por entidad y tiempo para no tratar filas correlacionadas como
independientes.

## Semillas y reproducibilidad

- Registrar una semilla maestra y semillas derivadas con nombre para split,
  folds, modelo, resampling y HPO.
- Registrar algoritmo de derivación, orden de filas, snapshot, código,
  configuración y versiones de librerías.
- Usar hash estable y versionado para asignación por ID; no el hash de proceso
  de Python.
- No escoger la semilla que produce la mejor métrica.
- Una semilla fija prueba repetibilidad, no estabilidad; la sensibilidad futura
  no utilizará el test para escoger semillas.

## Métricas candidatas

Sin designar métrica primaria ni gates, podrán estudiarse:

- discriminación: ROC-AUC y PR-AUC, siempre con prevalencia;
- probabilísticas: log loss y Brier score;
- calibración: intercepto, pendiente, curva de fiabilidad y, si se usa, ECE
  con binning registrado;
- tras fijar threshold: sensibilidad, especificidad, precisión, FPR, FNR y
  matriz de confusión;
- estabilidad por cohortes temporales e intervalos que respeten entidad y
  tiempo.

Las fórmulas, dirección y población se predeclaran antes de calcularlas y solo
usan labels maduras. El resampling no cambia las distribuciones de evaluación.
No se fijan aquí métricas finales, gates cuantitativos ni threshold.

## Atributos protegidos y límites de auditoría

Los atributos protegidos nunca son inputs ni se incorporan mediante
transformaciones. Si existen de forma permitida, se conservan separados para
auditoría descriptiva con acceso controlado. No participan en HPO,
calibración ni threshold. Las métricas por subgrupo no demuestran fairness y su
ausencia impide evaluar disparidades, no autoriza una afirmación de equidad.
Los proxies potenciales requieren revisión específica.

## Requisitos para monitoring posterior

Las señales futuras se mantienen separadas:

| Señal | Definición operacional | Datos mínimos | Respuesta máxima en este contrato |
|---|---|---|---|
| Calidad/esquema | Incumplimiento del contrato o integridad. | Manifest, esquema, IDs, timestamps y conteos. | Bloquear informe y revisión humana. |
| Data drift | Diferencia descriptiva entre features válidas de cohortes comparables. | Reference/current, lineage y valores as-of. | Informe offline y triage. |
| Prediction drift | Diferencia descriptiva de scores/clases bajo versión identificada. | Predicción, modelo, cohortes y timestamps. | Informe offline y triage. |
| Degradación supervisada | Cambio de métricas sobre labels maduras comparables. | Predicciones inmutables, target, madurez, censura y cobertura. | Revisión o solicitud auditable de challenger. |

Cada señal futura deberá declarar cálculo, ventana, threshold, respuesta y
limitaciones. Esos valores continúan pendientes. Drift no demuestra
degradación o causalidad y, conforme al ADR 0005, nunca promociona ni hace
rollback; ambas acciones requieren intervención humana.

## Evidencia futura de ejecución

Cada evaluación deberá registrar snapshot y split IDs, límites temporales,
intersecciones, code/lock/config versions, semillas, inventario de features,
parámetros, folds, usos de particiones, métricas y apertura del test. Este
milestone solo define la obligación; no crea validadores ni artefactos.

## Decisiones abiertas

- estimand: entidades nuevas o nuevas decisiones sobre entidades conocidas;
- target, horizonte, lag, purga y límites temporales concretos;
- tamaños y proporciones de particiones;
- estrategia exacta de CV y calibración;
- métrica primaria, uncertainty method, gates y threshold;
- frecuencia permitida de evaluación final y renovación del test;
- tratamiento modelístico de censura, si fuese necesario;
- métricas, ventanas y umbrales de monitoring.
