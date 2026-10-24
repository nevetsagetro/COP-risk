# ExecPlan 0019: API FastAPI y frontend analítico HTML/Plotly

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: separar serving local y presentación analítica para sustituir la
  dependencia exclusiva de Streamlit.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ExecPlans 0017/0018 y solicitud
  explícita de implementación.

## Propósito y resultado observable

El proyecto ofrece un backend local FastAPI que sirve el baseline académico y
un frontend HTML/JavaScript/Plotly que consume ese contrato. La persona puede
abrir una única URL, leer la narrativa, explorar ROC y probabilidades, mover el
threshold, reproducir el trade-off y enviar una predicción académica sin que el
navegador cargue ni replique el modelo.

Streamlit se conserva como fallback durante esta transición; no se elimina ni
se presenta como backend de serving.

## Base verificada

Antes de este plan existía una app Streamlit que cargaba directamente los
artefactos y contenía la presentación y parte de la lógica de gráficos. No
existía API, contrato HTTP ni frontend estático. El baseline UCI y el estudio
académico solo utilizan train/validation; el test permanece cerrado.

## Alcance

- Añadir `cop.serving.academic.AcademicService` como adaptador reutilizable.
- Añadir `cop.api` con endpoints read-only y `POST /api/predict`.
- Servir el frontend estático bajo la misma aplicación FastAPI.
- Añadir frontend HTML/CSS/JavaScript con Plotly, controles de threshold,
  anotaciones y formulario de predicción.
- Añadir tests de contrato HTTP con ASGI transport.
- Documentar ejecución local y dependencias API.

## Fuera de alcance

- Eliminar Streamlit en este milestone.
- Docker, cloud, autenticación, autorización, rate limiting o HTTPS.
- MLflow, champion/challenger, promoción, rollback o monitoring.
- Abrir el test o cambiar modelo, features, thresholds productivos o dataset.

## Decisiones

### Aceptadas

- FastAPI es el adaptador de serving local; el dominio ML permanece en
  `src/cop` y no se implementa de nuevo en JavaScript.
- El frontend consume JSON de la API y usa Plotly para interacción.
- `GET /health` declara explícitamente `test_status=unopened`.
- La API carga solo artefactos de train/validation y devuelve probabilidades
  descriptivas, no decisiones crediticias.
- FastAPI se fija en `0.115.12` para mantener un contrato reproducible con el
  TestClient/ASGI stack disponible.

### Pendientes

- La estrategia de autenticación, autorización y despliegue queda fuera de
  este MVP y requiere decisión posterior antes de cualquier entorno real.
- La dependencia Plotly del frontend usa CDN en esta demo local; una futura
  distribución offline debe incorporar el asset JS al paquete web.

### Propuestas

- Mantener la API como frontera estable si en el futuro se cambia HTML por
  React u otra capa visual.

## Seguridad y restricciones

- No se exponen datos brutos, PII, atributos `audit_only` ni el test.
- El endpoint de predicción exige exactamente las 19 features aprobadas y
  rechaza campos faltantes o desconocidos.
- El resultado contiene una probabilidad estimada y una advertencia; no hay
  endpoint de aprobación/denegación.

## Plan de ejecución

1. Extraer el servicio académico y reutilizar los loaders existentes.
2. Implementar schemas y endpoints FastAPI.
3. Construir frontend estático con narrativa y charts interactivos.
4. Añadir tests de health, assets, métricas, gráficos, sweep y predicción.
5. Ejecutar validaciones Python y levantar Uvicorn para un smoke test HTTP.
6. Actualizar README/CHANGELOG y cerrar con staging literal.

## Validación y criterios de aceptación

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/overview
git diff --check
```

La aceptación requiere los cuatro tests de contrato API, la suite completa,
un frontend HTML servido por `/`, `test_status=unopened` y una predicción que
use ambos pipelines reales.

## Registro de progreso

- [x] 2026-10-24: servicio académico extraído.
- [x] 2026-10-24: endpoints FastAPI implementados.
- [x] 2026-10-24: frontend HTML/CSS/Plotly implementado.
- [x] 2026-10-24: tests de contrato API implementados.
- [x] 2026-10-24: contrato descriptivo de API y copy principal migrados a
  inglés; las rutas, claves JSON, modelos y features permanecen sin cambios.
- [x] 2026-10-24: toggle EN/ES aislado en `language.js`, con asset versionado y
  tests de regresión para evitar acoplarlo al renderizado de Plotly.
- [x] 2026-10-24: smoke test de Uvicorn y validación completa.
- [x] 2026-10-24: frontend revisado para evitar solapamiento visual; ambos
  modelos se muestran en paralelo con threshold sincronizado.
- [x] 2026-10-24: documentación y staging actualizados.

## Hallazgos inesperados

El stack de test no ejecuta correctamente handlers síncronos en el entorno
local disponible; los endpoints se definieron `async` y el servicio ML sigue
siendo síncrono internamente. El smoke test ASGI funciona y evita depender de
un threadpool de test defectuoso.

## Registro de decisiones del plan

- 2026-10-24: se conserva Streamlit como fallback para evitar una migración
  destructiva antes de verificar paridad.
- 2026-10-24: se usa ASGITransport en tests porque el TestClient síncrono se
  bloquea en este entorno incluso con una app FastAPI mínima.

## Resultados y retrospectiva

La API FastAPI sirve el frontend HTML, health y overview mediante Uvicorn. El
endpoint de predicción respondió con ambos pipelines reales para las 19 features
aprobadas. La validación ejecutó 110 tests, Ruff, mypy, `git diff --check` y
smoke tests HTTP contra `/health`, `/`, `/api/overview`, assets y
`/api/predict`. La revisión visual deja ROC superpuesta para comparar, separa
probabilidades y threshold para evitar ruido, sincroniza el slider de ambos
modelos y añade presets para probar la predicción sin rellenar 19 campos. El
explorador añade casos anonimizados reales del bloque validation, de modo que
se puede modificar solo una variable —por ejemplo, el pago de septiembre— sin
inventar las otras 18. El test final permaneció cerrado. La UI declara el evento objetivo —impago
registrado el próximo mes— y mueve las etiquetas de la ROC a una leyenda
inferior para evitar solapamientos.

## Version-control allowlist

Tracked files or directories allowed:

- CHANGELOG.md
- README.md
- app/web/
- docs/plans/0019-fastapi-analytical-frontend.md
- pyproject.toml
- src/cop/api.py
- src/cop/serving/
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(api): add FastAPI analytical frontend
