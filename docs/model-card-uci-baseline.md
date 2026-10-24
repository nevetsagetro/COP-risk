# Model card: baseline académico UCI

## Estado y uso autorizado

Logistic Regression y LightGBM son baselines académicos reproducibles sobre
UCI Default of Credit Card Clients. Su único uso autorizado es demostración
académica local. No son modelos champion, no están aprobados para producción y
no deben intervenir en decisiones crediticias reales.

## Datos y particiones

El snapshot académico v2 y sus splits estratificados estables 70/15/15 se
identifican por hashes en `configs/training/uci-baseline.yaml`. El desarrollo
ajusta exclusivamente con train (21000 filas) y registra métricas sobre
validation (4500). Test (4500) permanece cerrado hasta una invocación explícita
con `--finalize-test`.

No existe validación temporal: UCI no proporciona timestamps row-level ni
identidad longitudinal defendible. La prevalencia se informa por split sin
interpretarla como una prevalencia operacional.

## Features y leakage

Se usan exactamente 19 inputs: `LIMIT_BAL`, `PAY_0`, `PAY_2`–`PAY_6`,
`BILL_AMT1`–`BILL_AMT6` y `PAY_AMT1`–`PAY_AMT6`. `ID`, el target y las cuatro
columnas `audit_only` (`SEX`, `EDUCATION`, `MARRIAGE`, `AGE`) están excluidos.
No hay imputación: cualquier missing detiene el proceso.

`PAY_0` y `PAY_2`–`PAY_6` se procesan como categóricas. En Logistic Regression,
one-hot y escalado numérico se ajustan dentro del pipeline solo con train. En
LightGBM, one-hot se ajusta solo con train y las numéricas pasan sin escalado.
No se aplica resampling, pesos de clase, tuning ni early stopping.

## Configuración congelada

- Logistic Regression: `C=1.0`, L2 mediante `l1_ratio=0.0`, solver
  `liblinear`, intercept, `max_iter=1000`, `class_weight=null`, semilla 42.
- LightGBM: 200 árboles, `learning_rate=0.05`, 31 hojas,
  `min_child_samples=20`, profundidad sin límite, sampling de filas y columnas
  1.0, regularización 0, modo determinista, un hilo, `class_weight=null`,
  semilla 42.
- Threshold descriptivo fijo: 0.5.

La configuración, los modelos, manifests y resultados de validation se
congelan en un directorio atómico bajo `runs/uci-baseline/`, ignorado por Git.
La ejecución de LightGBM requiere que el sistema proporcione el runtime OpenMP
GNU (`libgomp.so.1` en Linux), además de las dependencias Python declaradas.

Los hashes del manifest local detectan corrupción accidental o cambios
aislados antes de abrir test. No constituyen firma criptográfica externa: un
actor con escritura sobre todo el run podría reemplazar coordinadamente modelo
y manifest. Este baseline local no afirma resistencia frente a ese adversario.

## Métricas

Para cada modelo se registran ROC-AUC, average precision, log loss, Brier
score, precision, recall, F1 y matriz de confusión a threshold 0.5. Estas
métricas son descriptivas; no se declara métrica primaria, ganador, champion,
threshold óptimo ni calibración real.

La ejecución reproducible local congelada
`uci-baseline-c52cb3e02f0bec92fa6675a21a55af04e73cdd40027762a1c373d98599a299fb`
registró prevalencias 0.221190 en train, 0.221111 en validation y 0.221333 en
test. Los resultados descriptivos fueron:

| Split | Modelo | ROC-AUC | Average precision | Log loss | Brier | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| validation | Logistic Regression | 0.774804 | 0.546653 | 0.435027 | 0.135353 | 0.676749 | 0.359799 | 0.469816 |
| validation | LightGBM | 0.783911 | 0.555368 | 0.428262 | 0.134185 | 0.667286 | 0.360804 | 0.468363 |
| test | Logistic Regression | 0.773572 | 0.555595 | 0.431840 | 0.134965 | 0.684418 | 0.348394 | 0.461743 |
| test | LightGBM | 0.786889 | 0.568776 | 0.423817 | 0.132480 | 0.698113 | 0.371486 | 0.484928 |

Las matrices de confusión `[[TN, FP], [FN, TP]]` fueron respectivamente
`[[3334, 171], [637, 358]]`, `[[3326, 179], [636, 359]]`,
`[[3344, 160], [649, 347]]` y `[[3344, 160], [626, 370]]` en el orden de la
tabla. Los artefactos materiales y predicciones permanecen bajo `runs/**` y no
se versionan.

## Protocolo de test final

Antes de finalizar se verifican hashes de configuración, manifests, snapshot,
los tres splits y modelos. Después se crea `finalize-test.claim` de forma
exclusiva y solo entonces se abre test. La claim consume el test aunque el
proceso falle: no existe reintento ni sobrescritura. Resultados y predicciones
finales se crean también con exclusión y permanecen como artefactos locales no
versionados.

```bash
python3 scripts/train_uci_baseline.py
python3 scripts/train_uci_baseline.py --finalize-test
```

## Limitaciones

El dataset es estático, histórico y académico. No aporta evidencia de
representatividad actual, estabilidad temporal, fairness, cumplimiento,
calidad operacional, utilidad crediticia real ni readiness productiva. Las
variables sensibles se preservan fuera de las matrices, por lo que este
milestone tampoco realiza una evaluación de fairness.
