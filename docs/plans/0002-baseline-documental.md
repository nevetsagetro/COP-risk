# ExecPlan 0002: baseline documental, seguro y reproducible

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-25.
- Última actualización: 2026-07-25.
- Responsable: agente `coordinator`, con un único agente escritor.
- Alcance: ejecutar únicamente el Milestone 0 del roadmap
  `docs/plans/0001-bootstrap.md`.
- Fuente normativa: `AGENTS.md` y `PLANS.md`.

## Propósito y resultado observable

Convertir el scaffold vacío en un repositorio mínimo que explique con honestidad
qué es COP, proteja secretos y artefactos locales, declare un entorno Python
reconstruible y pueda importar el paquete `cop`. El resultado no incluye
funcionalidad de riesgo de crédito.

Una persona que clone el futuro baseline podrá distinguir visión, estado real,
decisiones aceptadas y trabajo pendiente; instalar el extra de desarrollo;
ejecutar un smoke test; y revisar los perfiles de agentes sin identificadores
de modelo incompatibles ni una elección implícita de orquestador.

## Base verificada

Inspección realizada el 2026-07-25 antes de editar:

- `pwd` devolvió `/home/nvsagt/projects/cop-credit-risk`.
- `git status --short` mostró todos los archivos del proyecto sin seguimiento.
- La rama nominal es `main`, no tiene commits y su `HEAD` simbólico todavía no
  resuelve a ningún commit.
- `README.md`, `PLANS.md`, `CHANGELOG.md`, `.gitignore`, `.env.example`,
  `pyproject.toml` y `src/cop/__init__.py` existían vacíos.
- `docker-compose.yml` existe vacío; no prueba que Docker esté implementado.
- `docs/plans/0001-bootstrap.md` existía como roadmap general de diez
  milestones.
- `.codex/config.toml` y los cinco perfiles bajo `.codex/agents/` fijaban el
  identificador de modelo `gpt-5.6`; `reviewer` ya declaraba
  `sandbox_mode = "read-only"`.
- La descripción y el alcance de `mlops` mencionaban Prefect pese a que Airflow
  frente a Prefect continúa pendiente.
- Los directorios de datos, modelos, infraestructura y componentes existen
  vacíos; no contienen implementaciones ni placeholders.
- `/usr/bin/python3` corresponde a Python 3.12.3. El comando `python` no existe.
- Ruff, mypy y pytest no están instalados en el intérprete inspeccionado.

## Alcance

- `README.md`, `PLANS.md`, `CHANGELOG.md`;
- `.gitignore`, `.env.example`, `pyproject.toml`;
- marcador mínimo `src/cop/__init__.py`;
- smoke test bajo `tests/`;
- `.codex/config.toml` y perfiles existentes bajo `.codex/agents/`;
- reconciliación del roadmap `docs/plans/0001-bootstrap.md`;
- este ExecPlan.

## Fuera de alcance

- elegir, generar o descargar datos;
- EDA, features, splits, resampling, entrenamiento o evaluación ML;
- LightGBM, Optuna, MLflow o cualquier dependencia productiva;
- API, serving, Docker o Docker Compose funcional;
- Airflow, Prefect u otra implementación de orquestación;
- Evidently, Prometheus, Grafana, drift o retraining;
- cloud, bases de datos, promoción o rollback de modelos.

El archivo vacío `docker-compose.yml` y las carpetas nominales fuera del alcance
no se modifican.

## Decisiones

### Aceptadas y aplicables

- Python es el lenguaje del proyecto.
- COP es una demostración de portfolio no aprobada para decisiones crediticias
  reales.
- No se usarán PII, datos reales de clientes ni secretos versionados.
- `reviewer.toml` configura `sandbox_mode = "read-only"`. La eficacia de esa
  configuración depende de su integración con el runtime.

### Decisiones de este baseline

- Python 3.12 es la versión soportada inicialmente, alineada con el intérprete
  3.12.3 verificado.
- `python3` es el comando canónico del repositorio porque `python` no está
  disponible en el entorno inspeccionado.
- pytest, Ruff y mypy son las únicas dependencias de desarrollo del baseline y
  quedan fijadas a versiones exactas en el extra `dev`.
- Los perfiles de agentes heredan el modelo compatible del runtime; el
  repositorio no fija un identificador de modelo.

Estas son decisiones de tooling del baseline y no resuelven arquitectura ML,
infraestructura ni operación.

### Pendientes

Continúan pendientes sin cambios:

- fuente del dataset;
- Airflow frente a Prefect;
- proveedor cloud;
- almacenamiento de metadatos y features;
- umbrales de drift;
- promoción y rollback de modelos.

## Seguridad y restricciones

- `.env.example` contiene solo valores ficticios y no secretos.
- `.env`, claves, datos, modelos, artefactos y estado local de MLflow deben
  quedar ignorados.
- Las reglas de ignore preservan `.env.example`, archivos `README.md` y
  `.gitkeep` usados como placeholders.
- La documentación no atribuye capacidades a directorios o tecnologías
  meramente planificadas.
- No se instalarán dependencias sin autorización si el entorno no las contiene.

## Plan de ejecución

1. Inspeccionar el árbol, estado Git, instrucciones y todos los archivos
   afectados.
2. Escribir documentación honesta, convención de planes y changelog inicial.
3. Añadir protecciones de Git y plantilla ficticia de entorno.
4. Declarar packaging Python 3.12 y herramientas de desarrollo mínimas.
5. Añadir el marcador de paquete y smoke test de importación.
6. Eliminar identificadores de modelo fijados, neutralizar la elección de
   orquestador y conservar la configuración read-only de `reviewer.toml`.
7. Reconciliar el roadmap general con el alcance real de Milestone 0.
8. Parsear TOML, importar `cop`, ejecutar las herramientas de calidad, revisar
   estado y diff completo.
9. Solicitar revisión independiente que respete operacionalmente solo lectura
   y corregir únicamente hallazgos dentro de este milestone.

## Validación y criterios de aceptación

Comandos obligatorios:

```bash
python3 -c "import pathlib, tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.toml')]"
PYTHONPATH=src python3 -c "import cop"
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
git diff --check
git status --short
git diff
```

Como el repositorio no tiene commits, su `HEAD` simbólico no resuelve a un
commit y todos sus archivos son no rastreados; `git diff` puede estar vacío.
Mientras continúe esa condición, la revisión debe complementarse leyendo todos
los archivos cambiados y usando
`git diff --no-index --check /dev/null <archivo>` para detectar errores de
whitespace en contenido no rastreado.

El milestone satisface su implementación cuando:

- los seis archivos inicialmente vacíos exigidos tienen contenido;
- visión, estado real, decisiones y propuestas están separados;
- Python 3.12, packaging y el extra `dev` están declarados sin dependencias
  productivas;
- `cop` puede importarse y existe al menos un smoke test;
- todos los TOML parsean;
- Ruff, mypy y pytest pasan;
- secretos, datos y artefactos locales están protegidos sin ocultar
  documentación o placeholders;
- el reviewer no encuentra hallazgos críticos o altos dentro del alcance;
- roadmap y ExecPlan reflejan los resultados reales;
- no existe implementación fuera del alcance.

## Registro de progreso

- [x] 2026-07-25: inspección obligatoria y lectura completa de instrucciones,
  roadmap y configuración.
- [x] 2026-07-25: documentación, packaging, protección local y smoke test
  implementados.
- [x] 2026-07-25: perfiles de agentes reconciliados sin fijar modelo ni
  orquestador.
- [x] 2026-07-25: entorno `.venv` creado; tras un primer fallo de instalación
  por DNS en el sandbox, el extra `dev` se instaló en modo editable con
  autorización.
- [x] 2026-07-25: TOML, importación, Ruff, mypy, pytest, whitespace, estado Git
  y reglas de ignore validados correctamente.
- [x] 2026-07-25: revisión independiente completada operacionalmente en solo
  lectura; no reportó hallazgos críticos ni altos.
- [x] 2026-07-25: hallazgos corregidos o documentados, resultados cerrados y
  plan marcado como completado.

## Hallazgos inesperados

- El repositorio no tiene commits; por tanto, `git diff` no muestra por sí solo
  el contenido no rastreado.
- El entorno inicial contenía Python 3.12.3, pero no las tres herramientas de
  calidad declaradas. El primer intento de instalación falló por resolución
  DNS dentro del sandbox; la instalación autorizada posterior terminó
  correctamente.
- La estructura amplia de directorios vacíos puede sugerir componentes que no
  existen.
- Aunque `reviewer.toml` declara `sandbox_mode = "read-only"`, el runtime
  efectivo de la revisión reportó `workspace-write`. El reviewer respetó
  operacionalmente la instrucción de solo lectura, pero queda como riesgo
  restante verificar en una integración futura que el runtime aplique el
  sandbox configurado.
- Los pins exactos cubren las dependencias directas de desarrollo, pero no
  existe un lock de dependencias transitivas. Es un riesgo de reproducibilidad
  no bloqueante para este scaffold y deberá revisarse antes de ampliar el
  entorno.

## Registro de decisiones del plan

- 2026-07-25: se limita el soporte inicial a Python 3.12, única línea verificada
  en el entorno, y se adopta `python3` como comando canónico.
- 2026-07-25: se usan pins exactos para las tres herramientas de desarrollo;
  no se introduce ninguna dependencia runtime.
- 2026-07-25: los agentes heredan el modelo del runtime para evitar repetir un
  identificador que el entorno no acepta.
- 2026-07-25: la mención específica a Prefect se reemplaza por el orquestador
  que acepte un ADR futuro.

## Resultados y retrospectiva

Resultados observados el 2026-07-25:

- se creó `.venv`; el primer `pip install -e '.[dev]'` falló por DNS en el
  sandbox y la repetición con autorización instaló correctamente el paquete y
  su extra `dev`;
- los siete archivos TOML del repositorio parsearon con `tomllib`;
- la importación de `cop` terminó correctamente;
- `python3 -m ruff format --check .` validó 2 archivos;
- `python3 -m ruff check .` terminó sin hallazgos;
- `python3 -m mypy src tests` terminó sin errores en 2 archivos fuente;
- `python3 -m pytest` ejecutó y aprobó 1 test;
- `git diff --check` no informó errores, aunque el repositorio sin commits y con
  un `HEAD` simbólico que no resuelve a commit no expone archivos no rastreados
  mediante el diff convencional;
- `git status --short` mantiene todo el scaffold sin seguimiento, condición
  inicial que no se modifica mediante este milestone;
- `git check-ignore -v` confirmó exclusión de `.env`, datos, modelos,
  artefactos y MLflow, y las excepciones para `.env.example`, `README.md` y
  `.gitkeep`.
- la revisión independiente terminó sin hallazgos críticos ni altos; reportó
  un hallazgo medio de integración sobre el sandbox efectivo del reviewer y
  dos hallazgos bajos no bloqueantes sobre la descripción de `HEAD` y la
  ausencia de lock transitivo. La descripción fue corregida y los dos riesgos
  restantes quedaron documentados.

El Milestone 0 queda completado sin commit. La implementación se mantiene
deliberadamente como scaffold: no contiene lógica de dominio ni servicios.
