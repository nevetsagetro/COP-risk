# ExecPlan 0020: challenger académico con features temporales

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: comparar un challenger LightGBM con features derivadas de historial
  contra el baseline UCI congelado.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y la solicitud explícita de mejora
  del modelo.

## Propósito y resultado observable

El repositorio tendrá un experimento reproducible que transforma únicamente
las 19 variables UCI aprobadas, selecciona parámetros usando CV sobre train y
compara el challenger contra el baseline en validation y, solo mediante un
comando explícito, en el test final. El challenger no se promoverá ni
sustituirá el serving existente.

## Base verificada

El baseline actual entrena Logistic Regression y LightGBM con una configuración
fija, ajusta solo con train y evalúa validation. El contrato de features exige
exactamente las 19 variables UCI y el test se abre únicamente mediante una
invocación explícita de finalización.

## Alcance

- Añadir transformación determinista de historial UCI.
- Añadir comparación baseline/challenger con CV sobre train.
- Añadir CLI local que emita JSON reproducible sin escribir artefactos de modelo.
- Añadir tests de leakage, determinismo, contrato de columnas y evaluación.
- Documentar la interpretación de resultados.

## Fuera de alcance

- Cambiar las 19 features del baseline o el endpoint de serving.
- Abrir el test final durante tests, serving o arranque automático.
- Promover automáticamente un challenger.
- Añadir MLflow, Prefect, Docker u Optuna como dependencia obligatoria.

## Seguridad y restricciones

- No se leen datos de test ni atributos `audit_only`.
- Las features derivadas usan exclusivamente columnas del historial disponible.
- La selección de parámetros ocurre solo en folds de train.
- Un resultado superior en validation no se presenta como evidencia de utilidad
  real ni autoriza promoción.

## Plan de ejecución

1. Implementar transformación determinista y challenger aislado.
2. Implementar selección pequeña y explícita de parámetros con CV estratificada.
3. Añadir tests unitarios e integración del experimento.
4. Ejecutar el experimento local y registrar su salida como evidencia temporal.
5. Ejecutar suite completa y mantener el serving en el baseline actual.
6. Dejar un comando separado para consumir el test únicamente con
   `--finalize-test`.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/python scripts/run_academic_challenger.py
git diff --check
```

La aceptación requiere que la transformación sea determinista, que no añada
columnas protegidas, que el experimento no abra test, que CV produzca métricas
completas y que la suite existente permanezca verde.

## Registro de progreso

- [x] Implementación del challenger.
- [x] Tests de regresión y leakage.
- [x] Ejecución reproducible del experimento.
- [x] Documentación de resultados observados.
- [x] Comparador explícito de challenger contra test final ejecutado mediante
  el flag irreversible y el claim existente.

## Hallazgos inesperados

La primera ejecución seleccionó `learning_rate=0.03`, `n_estimators=300` y
`num_leaves=31` usando tres folds sobre train. El challenger obtuvo en
validation ROC-AUC 0.7907 frente a 0.7839 del baseline (+0.0068), Average
Precision 0.5651 frente a 0.5554 (+0.0097), Brier 0.1330 frente a 0.1342
(−0.0012) y log loss 0.4234 frente a 0.4283 (−0.0049). El resultado es una
señal académica en validation, no una promoción ni una afirmación de utilidad
real. El test final ya tenía un claim y resultados previos; esta ejecución
reutilizó ese claim y no abrió un nuevo ciclo de evaluación.

## Registro de decisiones del plan

- 2026-10-24: se usa una búsqueda pequeña y explícita con sklearn para no
  introducir Optuna antes de que exista una decisión de dependencia y lock.

## Resultados y retrospectiva

El challenger permanece fuera del serving y no se promovió. En el test final
existente, el challenger mejoró ROC-AUC de 0.7869 a 0.7881, Average Precision
de 0.5688 a 0.5727, Brier de 0.1325 a 0.1318 y log loss de 0.4238 a 0.4219.
Sin embargo, con threshold 0.5 redujo Precision de 0.6981 a 0.6935, Recall de
0.3715 a 0.3635 y F1 de 0.4849 a 0.4769. La evidencia no justifica promoción
automática; el siguiente trabajo debería seleccionar y calibrar el threshold
con un objetivo explícito antes de comparar de nuevo.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0020-academic-challenger-model.md
- src/cop/features/academic_challenger.py
- src/cop/evaluation/challenger.py
- src/cop/training/challenger.py
- scripts/run_academic_challenger.py
- scripts/finalize_academic_challenger.py
- tests/unit/test_academic_challenger.py
- tests/integration/test_academic_challenger_integration.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(ml): add leakage-safe academic challenger experiment
