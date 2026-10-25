# ExecPlan 0024: visualización explícita de cross-validation

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: hacer visible la estabilidad por fold y el candidato seleccionado.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0023.

## Propósito y resultado observable

Model Development declara cuál es el mejor candidato bajo Average Precision de
train-CV y muestra un gráfico con el AP de cada fold para los trials
seleccionados de Logistic Regression y LightGBM.

## Base verificada

El panel ya mostraba candidatos agregados, pero el asset podía quedar cacheado
con una versión anterior y no había un gráfico específico de estabilidad por
fold.

## Alcance

- Añadir conclusión académica por métrica primaria.
- Añadir gráfico de AP por fold con líneas de media.
- Versionar el asset frontend para invalidar cache.
- Actualizar prueba de asset.

## Fuera de alcance

- Cambiar la métrica de selección.
- Ejecutar test o promover modelos.
- Simular progreso en vivo de trials.

## Decisiones

- LightGBM o Logistic Regression se declara mejor sólo bajo la métrica elegida
  para esta comparación; no se presenta como campeón productivo.
- La estabilidad se muestra con folds de train y no con validation/test.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Conclusión por Average Precision.
- [x] Gráfico de estabilidad CV.
- [x] Invalidación de cache frontend y tests.

## Resultados y retrospectiva

El panel ahora permite distinguir el mejor candidato por criterio y observar si
la señal se mantiene entre folds. La API y el serving no cambian.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0024-cross-validation-visualization.md
- app/web/index.html
- app/web/app.js
- app/web/styles.css
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(web): visualize cross-validation stability
