# ExecPlan 0029: ejecución automática y cacheada del model lab

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: eliminar la acción obligatoria para cargar el resultado del
  laboratorio académico.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0028.

## Propósito y resultado observable

Al abrir la página, el model lab se solicita automáticamente en segundo plano.
El usuario ve el estado de cálculo y el resultado aparece cuando termina. El
backend cachea el informe por configuración durante el proceso; el botón sólo
aparece como reintento si la carga falla.

## Base verificada

La UI exigía pulsar “Run tuning experiment” aunque el laboratorio formaba parte
de la narrativa principal y la API ya tenía cache por configuración.

## Alcance

- Ejecutar la carga del lab desde `setupModelLab` sin bloquear los gráficos.
- Mostrar estado de progreso y cache.
- Mantener retry sólo en error.
- Versionar el asset frontend y actualizar el test.

## Fuera de alcance

- Crear jobs persistentes o ejecutar tuning en cada request.
- Cambiar el algoritmo de selección o el serving.

## Decisiones

- La carga del laboratorio es asíncrona desde el navegador.
- La cache backend evita repetir la búsqueda en el mismo proceso.
- El arranque de gráficos no espera a que termine el tuning.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q tests/integration/test_api.py::test_health_and_static_frontend
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

## Registro de progreso

- [x] Carga automática en background.
- [x] Estado cacheado y retry de error.
- [x] Validaciones.

## Resultados y retrospectiva

La página ya cuenta la fase de desarrollo sin exigir una acción manual. La
primera carga del proceso puede tardar, pero no bloquea los charts ni requiere
que la persona conozca el flujo interno para iniciar la historia.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0029-background-model-lab-cache.md
- app/web/index.html
- app/web/app.js
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- runs/**
- reports/local/**

Expected commit message:

- feat(web): load academic model lab automatically
