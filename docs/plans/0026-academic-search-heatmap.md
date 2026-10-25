# ExecPlan 0026: heatmap del proceso de cross-validation

## Estado del documento

- Estado: supersedido por `docs/plans/0027-academic-trial-ranking.md`.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: sustituir la visualización plana de estabilidad por una vista del
  rendimiento de todos los trials en cada fold.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0025.

## Propósito y resultado observable

Model Development muestra un heatmap donde cada fila es una combinación de
parámetros, cada columna un fold de train y cada celda Average Precision. KNN
queda visible como una familia comparable dentro del mismo protocolo.

## Base verificada

El gráfico de estabilidad mostraba sólo los trials seleccionados y tres puntos
por modelo, con diferencias visualmente pequeñas. El laboratorio ya conservaba
las métricas por fold de todos los candidatos.

## Alcance

- Reemplazar el gráfico plano por heatmap de todos los trials.
- Mantener ranking, selección y métricas sin cambios.
- Actualizar texto y prueba de presencia de la nueva explicación.

## Fuera de alcance

- Cambiar candidatos, selección o métricas.
- Abrir test o modificar serving.

## Decisiones

- Average Precision sigue siendo la métrica visual y primaria de selección.
- Las filas se comparan dentro de la misma partición de train-CV.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Heatmap de trials y folds.
- [x] KNN visible en la comparación.
- [x] Tests y validaciones.

## Resultados y retrospectiva

La nueva visualización explica mejor el proceso de búsqueda: permite seguir
cada combinación, comparar familias y observar si la elección mantiene señal
en los folds, sin presentar una estabilidad plana como conclusión principal.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0026-academic-search-heatmap.md
- app/web/index.html
- app/web/app.js
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(web): show cross-validation search heatmap
