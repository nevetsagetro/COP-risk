# ExecPlan 0025: benchmark KNN en el laboratorio académico

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: evaluar KNN como benchmark adicional sin alterar baseline ni serving.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0024.

## Propósito y resultado observable

El laboratorio compara Logistic Regression, LightGBM y KNN bajo el mismo
protocolo de train-CV, mostrando parámetros, métricas y threshold. KNN sirve
para demostrar una alternativa basada en distancia y poder justificar su
inclusión o descarte con evidencia.

## Base verificada

LightGBM es la mejor familia del laboratorio actual por AP de CV; KNN no se
había evaluado en el experimento.

## Alcance

- Añadir KNN con preprocessing numérico escalado.
- Probar `n_neighbors`, `weights` y `p` en una grilla pequeña.
- Incluir KNN en la respuesta y visualización del laboratorio.
- Documentar y verificar resultados.

## Fuera de alcance

- Cambiar los dos modelos baseline.
- Promover KNN o alterar serving.
- Abrir el test final.

## Decisiones

- KNN es benchmark académico, no challenger de producción.
- La métrica principal continúa siendo Average Precision de train-CV.
- La elección entre familias sigue siendo descriptiva y requiere una decisión
  humana posterior.

## Seguridad y restricciones

- El escalado y el fit ocurren dentro de cada pipeline y fold.
- No se usan validation/test para seleccionar parámetros.
- El estado del test permanece `unopened`.

## Validación y criterios de aceptación

```bash
.venv/bin/python scripts/run_academic_model_lab.py --folds 3
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] KNN integrado al laboratorio.
- [x] Resultado comparado con Logistic Regression y LightGBM.
- [x] Frontend y API actualizados.

## Hallazgos inesperados

KNN obtiene AP CV `0.510642`, por debajo de LightGBM `0.551469` y Logistic
Regression `0.533323`; es útil como contraste metodológico, pero no es el mejor
modelo bajo la métrica primaria.

## Resultados y retrospectiva

KNN queda visible como benchmark y no modifica el serving. En validation con
threshold aprendido obtuvo F1 `0.502711`, frente a `0.549975` de LightGBM y
`0.548266` de Logistic Regression.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0025-knn-academic-benchmark.md
- README.md
- src/cop/evaluation/model_lab.py
- app/web/index.html
- app/web/app.js
- app/web/styles.css
- tests/integration/test_api.py
- tests/integration/test_model_lab_integration.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(ml): add knn academic benchmark
