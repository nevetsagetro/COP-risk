# ExecPlan 0022: integración del laboratorio de modelos en el frontend

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: exponer el informe de tuning académico como operación explícita de
  la API y sección del frontend analítico.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ExecPlan 0021.

## Propósito y resultado observable

La persona que presenta COP puede abrir “Model development” y ejecutar el
experimento desde un botón. La interfaz muestra el estado de carga, los
parámetros seleccionados, el threshold aprendido, las métricas de validation y
la tabla de candidatos. La carga inicial de gráficos no espera al tuning.

## Base verificada

El laboratorio reproducible existía en Python y el frontend ya consumía la
API analítica de baseline. No existía endpoint ni sección visual para el
laboratorio.

## Alcance

- Añadir `/api/model-lab` como operación de lectura académica y cacheada.
- Añadir sección frontend con ejecución bajo demanda y estados de feedback.
- Añadir pruebas de integración de endpoint y presencia de UI.
- Actualizar la documentación de uso.

## Fuera de alcance

- Cambiar modelos, fórmulas, threshold del serving o predicción.
- Ejecutar tuning automáticamente al cargar la aplicación.
- Promover o servir el modelo seleccionado.
- Abrir el test final.

## Decisiones

### Aceptadas

- El endpoint reutiliza `run_model_lab` y cachea por configuración.
- El frontend ejecuta el laboratorio sólo mediante acción explícita.
- Los errores se comunican en el panel sin sustituir la página completa.

### Pendientes

- Traducción completa del nuevo bloque al idioma español del toggle existente.

## Seguridad y restricciones

- La respuesta mantiene `test_status=unopened`.
- No se escriben modelos ni resultados en `runs` desde el endpoint.
- Se conserva el disclaimer de uso académico.

## Plan de ejecución

1. Añadir operación cacheada a la capa de servicio.
2. Añadir ruta API y pruebas.
3. Añadir sección y renderizado del frontend bajo demanda.
4. Ejecutar validaciones de Python y suite completa.

## Validación y criterios de aceptación

```bash
.venv/bin/pytest -q
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
git diff --check
```

La aceptación requiere que la carga inicial no llame `/api/model-lab`, que el
botón ejecute el informe, que el endpoint conserve el test cerrado y que no
haya regresiones en los endpoints existentes.

## Registro de progreso

- [x] Endpoint y cache.
- [x] Sección frontend y estados de carga/error.
- [x] Tests de integración.
- [x] Validaciones.

## Hallazgos inesperados

El tuning tarda sensiblemente más que los endpoints descriptivos. Ejecutarlo
bajo demanda evita repetir la regresión de rendimiento observada durante la
carga inicial de los gráficos.

## Registro de decisiones del plan

- 2026-10-24: se eligió ejecución bajo demanda en lugar de incluir el endpoint
  en el `Promise.all` inicial.

## Resultados y retrospectiva

El endpoint y la sección visual están implementados. La prueba de API pasó con
5 casos y el laboratorio se ejecutó una sola vez gracias a la cache durante la
prueba del endpoint.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0022-model-lab-frontend-integration.md
- README.md
- src/cop/api.py
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

- feat(web): integrate academic model lab
