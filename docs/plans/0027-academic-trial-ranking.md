# ExecPlan 0027: ranking visual de trials académicos

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: reemplazar el heatmap de bajo contraste por un ranking de trials.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0026.

## Propósito y resultado observable

El gráfico muestra todos los trials en una escala ajustada a los valores
observados de Average Precision, con error bars de variación entre folds y el
trial seleccionado resaltado.

## Base verificada

El heatmap anterior usaba un rango de color `0–1`, mientras los AP observados
estaban concentrados aproximadamente entre `0.51–0.55`, por lo que no aportaba
contraste visual suficiente.

## Alcance

- Sustituir el heatmap por un dot plot/ranking con escala contextual.
- Mantener parámetros, ranking, métricas y selección sin cambios.
- Actualizar el texto y la prueba de presencia del gráfico.

## Fuera de alcance

- Cambiar modelos, candidatos o criterio de selección.
- Abrir el test o modificar serving.

## Decisiones

- Se usa una escala contextual para facilitar comparación, con valores exactos
  disponibles en hover y tabla.
- La escala no representa una mejora absoluta desde cero; representa diferencias
  entre los trials evaluados.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q tests/integration/test_api.py
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Heatmap retirado.
- [x] Ranking contextual implementado.
- [x] Tests y validaciones.

## Resultados y retrospectiva

El gráfico prioriza la decisión académica: qué trial rindió mejor, cuánto
varió entre folds y dónde queda KNN respecto a las otras familias.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0026-academic-search-heatmap.md
- docs/plans/0027-academic-trial-ranking.md
- app/web/index.html
- app/web/app.js
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(web): improve academic trial comparison
