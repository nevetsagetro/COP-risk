# ExecPlan 0023: trazabilidad visual de la búsqueda de parámetros

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: hacer visible el proceso de búsqueda y selección del laboratorio
  académico ya integrado.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0022.

## Propósito y resultado observable

La sección Model Development muestra el flujo de experimentación, cada trial,
sus parámetros, ranking, Average Precision de CV, desviación entre folds y el
threshold seleccionado. Un gráfico compara visualmente los trials y resalta
el candidato seleccionado.

## Base verificada

El laboratorio ya devolvía candidatos y métricas agregadas, pero la tabla sólo
mostraba una etiqueta genérica de candidato y no exponía ranking, variación ni
la combinación de parámetros.

## Alcance

- Añadir ranking, identificador de trial y desviaciones de métricas al informe.
- Añadir flujo, tabla detallada y gráfico comparativo al frontend.
- Añadir assertions de trazabilidad al test de integración.

## Fuera de alcance

- Cambiar el algoritmo de selección.
- Introducir optimización online o promoción automática.
- Abrir el test o modificar serving.

## Decisiones

### Aceptadas

- La búsqueda continúa siendo una grilla pequeña, determinista y auditable.
- El ranking se basa en AP de CV, luego ROC-AUC y finalmente menor log loss.
- La variación mostrada es la desviación estándar entre folds de train.

### Pendientes

- Añadir ejecución realmente incremental por trial requeriría una API de jobs o
  streaming y queda fuera de este milestone.

## Seguridad y restricciones

- Los folds y el threshold se calculan sólo con train.
- Validation sólo se evalúa después de seleccionar.
- El test conserva estado `unopened`.

## Plan de ejecución

1. Enriquecer el payload del laboratorio con ranking y dispersión.
2. Renderizar tabla, gráfico y flujo en el frontend.
3. Ejecutar tests y validaciones globales.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Payload trazable.
- [x] UI detallada.
- [x] Tests y validaciones.

## Hallazgos inesperados

La ejecución actual es síncrona: la UI puede mostrar el estado de carga, pero
el gráfico de trials aparece cuando finaliza la búsqueda. Esto es deliberado
para evitar introducir un sistema de jobs para un demo local.

## Registro de decisiones del plan

- 2026-10-24: se eligió mostrar el resultado completo y reproducible, no
  simular progreso de trials que todavía no ha terminado.

## Resultados y retrospectiva

La búsqueda ahora deja evidencia de cada combinación y permite explicar por
qué una configuración fue seleccionada sin usar validation o test para elegir.
Se ejecutaron `.venv/bin/pytest -q` con `117 passed`, Ruff format/check,
Mypy sin incidencias y `git diff --check` correctamente. El navegador no pudo
ejecutar `node --check` porque Node.js no está instalado en el entorno.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0023-model-search-trace.md
- src/cop/evaluation/model_lab.py
- app/web/index.html
- app/web/app.js
- app/web/styles.css
- tests/integration/test_model_lab_integration.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(web): expose academic model search trace
