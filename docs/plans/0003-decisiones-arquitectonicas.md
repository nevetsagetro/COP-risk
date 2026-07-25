# ExecPlan 0003: decisiones arquitectónicas iniciales

## Estado del documento

- Estado: completado y decisiones aprobadas.
- Fecha inicial: 2026-07-25.
- Última actualización: 2026-07-25.
- Responsable: agente `coordinator`.
- Alcance: investigar y preparar cinco ADR Proposed para el Milestone 1 y
  registrar su aprobación humana posterior sin implementarlos.
- Fuente normativa: `AGENTS.md` y `PLANS.md`.

## Propósito y resultado observable

Documentar comparaciones revisables para orquestación, entorno local,
persistencia MLflow, lock de dependencias y lifecycle de modelos. El resultado
inicial fueron propuestas; el 2026-07-25 recibieron aprobación humana y
quedaron aceptadas documentalmente sin implementar componentes.

## Base verificada

Inspección realizada el 2026-07-25:

- `HEAD` es `04106f4723933d5daff759b147d5477d35e64464`
  (`chore: establish documented and reproducible project baseline`) en `main`.
- `git status --short` no produjo salida antes de comenzar.
- Existen el roadmap `0001` y el ExecPlan completado `0002`.
- No existía `docs/decisions/` con archivos.
- `pyproject.toml` declara Python 3.12, cero dependencias runtime y tres
  herramientas de desarrollo; no existe lock transitivo.
- No hay dataset, modelos, MLflow, orquestador, servicios, cloud ni Compose
  funcional.
- Los agentes heredan modelo del runtime; `reviewer.toml` declara read-only.

## Alcance

- Este ExecPlan.
- Reconciliación documental del Milestone 1 en el roadmap.
- Cinco ADR bajo `docs/decisions/`, inicialmente Proposed y posteriormente
  Accepted por aprobación humana.
- Actualización documental de README y CHANGELOG al registrar la aprobación.

## Fuera de alcance

- Implementar cualquiera de las decisiones aceptadas.
- Modificar código, dependencias, lock, variables o infraestructura.
- Elegir dataset, target, features, métricas, thresholds, proveedor cloud,
  feature store o topología completa de Compose.

## Decisiones

### Aceptadas aplicables

Se mantienen únicamente las decisiones de `AGENTS.md`: Python, SMOTE-Tomek
cuando se justifique, LightGBM, Optuna, MLflow, FastAPI y Docker, Evidently y
Grafana. Su aceptación no implica implementación.

### Pendientes

Continúan pendientes dataset, target, features, métricas, thresholds, proveedor
cloud, feature store y configuración completa de Compose.

### Decisiones aceptadas el 2026-07-25

- Prefect futuro, posponiendo toda implementación hasta tener un pipeline
  Python manual, reproducible, probado e idempotente.
- Ejecución local-first con Compose incremental y cloud aplazado.
- SQLite y filesystem local para metadata y artefactos iniciales de MLflow.
- `uv.lock` como estrategia futura de lock.
- Drift puede crear o entrenar challengers; promoción y rollback permanecen
  humanos, separados y auditados.

Los cinco ADR conservan separadas decisión e implementación.

## Seguridad y restricciones

- No se añaden secretos, datos, endpoints ni conexiones.
- Cualquier UI futura deberá limitarse a loopback por defecto.
- El ADR MLflow no decide feature storage.
- Ninguna decisión permite promoción automática por drift.
- Las fuentes son documentación primaria; sus versiones deberán reconfirmarse
  al implementar.

## Plan de ejecución

1. Inspeccionar commit, working tree, documentación, planes, ADRs y agentes.
2. Delegar cuatro análisis independientes read-only.
3. Consolidar cinco comparaciones con requisitos, opciones, costes, riesgos,
   consecuencias, reversibilidad y preguntas abiertas.
4. Crear los ADR con estado Proposed y reconciliar el roadmap.
5. Ejecutar checks estructurales y baseline; revisar diff completo.
6. Solicitar una revisión final read-only.
7. Corregir solo hallazgos documentales y cerrar este plan.
8. Tras aprobación humana, actualizar los cinco estados a Accepted y
   reconciliar README, CHANGELOG y roadmap sin implementar decisiones.

## Validación y criterios de aceptación

```bash
test "$(find docs/decisions -maxdepth 1 -type f | wc -l)" -eq 5
test "$(rg -l "^- Status: Accepted$" docs/decisions | wc -l)" -eq 5
! rg -n "^- Status: Proposed$" docs/decisions
git diff -- pyproject.toml src tests docker-compose.yml .env.example
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
git diff --check
git status --short
git diff
```

Además, cada ADR debe contener Context, Requirements, Options, Decision,
Consequences, Reversibility y Open questions. El diff de código,
dependencias e infraestructura debe permanecer vacío.

Mientras los archivos nuevos sigan sin seguimiento, se comprueba también cada
uno con `git diff --no-index --check /dev/null <archivo>`.

## Registro de progreso

- [x] 2026-07-25: inspección obligatoria completada con working tree limpio.
- [x] 2026-07-25: cuatro análisis read-only recibidos.
- [x] 2026-07-25: cinco ADR Proposed y este ExecPlan redactados.
- [x] 2026-07-25: roadmap reconciliado; estructura, baseline y diff completo
  validados.
- [x] 2026-07-25: revisión final read-only de la fase Proposed incorporada.
- [x] 2026-07-25: hallazgo de whitespace corregido, resultados registrados y
  plan cerrado sin commit.
- [x] 2026-07-25: aprobación humana incorporada a los cinco ADR, README,
  CHANGELOG y roadmap, sin implementar las decisiones.
- [x] 2026-07-25: revisión final read-only de la aceptación incorporada; sus
  hallazgos documentales se corrigieron o registraron como riesgo.

## Hallazgos inesperados

- El Milestone 1 del roadmap mezclaba dataset y versionado de datos con las
  decisiones arquitectónicas; ambos quedaron fuera. La primera autorización
  exigió propuestas y una autorización humana posterior aceptó las cinco.
- Docker no está disponible en el entorno inspeccionado; no es necesario para
  esta tarea documental.
- El sandbox efectivo de reviewer puede no aplicar el modo read-only declarado;
  la revisión debe respetarlo operacionalmente y registrar cualquier
  discrepancia.
- `AGENTS.md` continúa enumerando como pendientes Airflow/Prefect, metadata y
  feature storage, y promoción/rollback. Los ADR 0001, 0003 y 0005 son
  decisiones posteriores que resuelven parte de esas entradas, pero actualizar
  la fuente normativa quedó fuera de los archivos autorizados en este cierre.
  Hasta reconciliarla, futuros agentes deben leer los ADR Accepted junto con
  `AGENTS.md`.

## Registro de decisiones del plan

- 2026-07-25: se crean cinco ADR separados para evitar que backend MLflow
  resuelva implícitamente feature storage.
- 2026-07-25: todas las recomendaciones se mantienen Proposed y sin
  implementación hasta aprobación humana.
- 2026-07-25: dataset, data versioning, target, features y thresholds quedan
  fuera del plan.
- 2026-07-25: aprobación humana registrada; los cinco ADR pasan a Accepted y
  su implementación permanece aplazada a milestones posteriores.

## Resultados y retrospectiva

Resultados observados el 2026-07-25:

- se crearon inicialmente cinco ADR Proposed y, tras aprobación humana, los
  cinco pasaron a `Status: Accepted`;
- cada ADR contiene las secciones y comparaciones exigidas;
- `pyproject.toml`, código, tests, entorno, agentes e infraestructura no
  cambiaron;
- siete TOML parsearon correctamente y la importación de `cop` terminó bien;
- Ruff format y lint, mypy estricto y el smoke test pasaron; pytest aprobó
  `1` test;
- `git diff --check` pasó y los seis archivos nuevos pasaron además
  `git diff --no-index --check`;
- el reviewer final de la fase Proposed no dejó hallazgos abiertos;
- su único hallazgo, una línea vacía adicional al final de cada archivo nuevo,
  se corrigió y originó la comprobación explícita para archivos sin seguimiento;
- el reviewer final de aceptación confirmó estados y checks; su hallazgo bajo
  sobre referencias históricas se corrigió, y la contradicción normativa con
  `AGENTS.md` quedó registrada como riesgo porque ese archivo estaba fuera del
  alcance autorizado;
- el estado Git final contiene solo README, CHANGELOG y roadmap modificados,
  los cinco ADR y este plan, todos documentales.

Las cinco propuestas fueron aceptadas documentalmente por aprobación humana,
pero ninguna fue implementada. Dataset, target, features, métricas, thresholds,
proveedor cloud, feature store y topología de Compose continúan abiertos. No
se creó commit.
