# ExecPlan 0028: narrativa completa dataset-to-decision

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: hacer que la página explique el recorrido completo del laboratorio
  desde el dataset hasta la decisión académica del modelo.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y los ExecPlans 0021–0027.

## Propósito y resultado observable

La página presenta seis etapas conectadas: dataset, contrato de datos, splits,
experimentación, threshold y decisión final. Los hechos centrales también se
exponen desde `/api/overview` para que la interfaz no dependa únicamente de
texto decorativo.

## Base verificada

El frontend explicaba predicción, métricas, curvas, threshold y tuning, pero
no presentaba en un único recorrido los 30.000 registros, las 19 features, el
target, las particiones protegidas y el cierre del test.

## Alcance

- Añadir metadatos verificables de journey al endpoint overview.
- Añadir sección visual dataset-to-decision.
- Actualizar la conclusión dinámica cuando finaliza el model lab.
- Añadir tests de contrato y presencia de UI.

## Fuera de alcance

- Cambiar los modelos, métricas o particiones.
- Abrir test o crear promoción automática.
- Añadir claims de fairness, producción o crédito real.

## Decisiones

### Aceptadas

- La métrica primaria del laboratorio sigue siendo Average Precision.
- El threshold se aprende en train out-of-fold y se revisa en validation.
- El test queda cerrado por defecto.

### Pendientes

- Ninguna dentro del alcance de este milestone.

## Seguridad y restricciones

- Sólo se muestran hechos del contrato UCI académico verificado.
- Los atributos audit-only se describen como excluidos, no como inputs.
- La decisión final se presenta como académica y no como aprobación crediticia.

## Plan de ejecución

1. Exponer el resumen verificable en overview.
2. Renderizar la secuencia narrativa en la página.
3. Conectar el paso final con el resultado del laboratorio.
4. Ejecutar pruebas y validaciones.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q tests/integration/test_api.py
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Metadatos de journey.
- [x] Narrativa visual.
- [x] Conclusión dinámica.
- [x] Traducción completa ES del nuevo bloque.

## Hallazgos inesperados

La página ya tenía explicaciones distribuidas, por lo que el cambio necesario
era de arquitectura narrativa y no de nuevos cálculos estadísticos.

## Registro de decisiones del plan

- 2026-10-24: se mantiene la narrativa en inglés por defecto y se añade su
  traducción al toggle ES para conservar la coherencia de la experiencia.

## Resultados y retrospectiva

La narrativa dataset-to-decision y su traducción ES están implementadas. Las
validaciones del alcance pasan y no se modifican modelos, splits ni serving.
Resultados: smoke test de frontend/API `1 passed`, Mypy sin incidencias, Ruff
format/check correctos y `git diff --check` correcto. La suite completa de
regresión anterior permanece en `117 passed`.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0028-dataset-to-decision-story.md
- src/cop/serving/academic.py
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

- feat(web): tell dataset to decision story
