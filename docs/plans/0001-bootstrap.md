# ExecPlan 0001: bootstrap de una vertical local de demostración

## Estado del documento

- Estado: roadmap general; no es el ExecPlan activo de implementación.
- Fecha: 2026-07-25.
- Última actualización: 2026-07-25.
- Alcance: preparar, mediante cambios pequeños, una primera vertical local y
  reproducible de COP.
- Ejecución: cada milestone requiere un ExecPlan pequeño propio. El Milestone 0
  se ejecuta en `docs/plans/0002-baseline-documental.md`.
- Fuera de alcance de este roadmap: autorizar por sí mismo implementación o
  resolver decisiones pendientes.
- Fuente normativa: `AGENTS.md`.
- Plantilla: `PLANS.md`. El documento nació con formato provisional cuando la
  plantilla estaba vacía y se reconcilió al completar el Milestone 0.

## Propósito

El resultado perseguido es una demo local que permita recorrer, con datos
permitidos y sin uso crediticio real, el ciclo de preparación de datos,
entrenamiento reproducible, evaluación, registro del experimento, serving,
observabilidad de drift y retraining controlado. La promoción de modelos debe
permanecer separada del disparo de retraining y requerir una comparación
explícita entre challenger y champion.

Este ExecPlan no afirma que esa vertical exista. Define el orden en que podría
construirse después de que las decisiones pendientes necesarias sean revisadas
y registradas como ADR.

## Base verificada del repositorio

Inspección realizada el 2026-07-25:

- La ruta de trabajo es `/home/nvsagt/projects/cop-credit-risk`.
- La rama es `main`, no tiene commits y `git status --short` presenta todos los
  archivos visibles como no rastreados.
- `AGENTS.md` contiene la identidad del proyecto, decisiones técnicas,
  restricciones de seguridad, reglas de corrección ML y reglas de ingeniería.
- `README.md`, `PLANS.md`, `CHANGELOG.md`, `pyproject.toml`,
  `docker-compose.yml`, `.env.example`, `.gitignore` y
  `src/cop/__init__.py` existen, pero están vacíos.
- Existen directorios vacíos para `configs`, `data`, `docs/decisions`,
  `docs/plans`, `infra`, `models`, `notebooks`, `scripts`, módulos bajo
  `src/cop` y suites bajo `tests`.
- No se verificaron datasets, modelos, experimentos, dependencias declaradas,
  servicios, imágenes Docker, dashboards, tests, integraciones ni despliegues.
- No había otro ExecPlan activo bajo `docs/plans/` antes de crear este archivo.

## Visión del producto

Según `AGENTS.md`, COP es un proyecto de portfolio y demostración para scoring
de riesgo de crédito, monitorización de drift y retraining controlado. No está
aprobado para decisiones crediticias reales.

La visión describe el destino del producto; no prueba que sus capacidades
estén implementadas.

## Decisiones técnicas aceptadas

Estas decisiones proceden de `AGENTS.md` y no son propuestas de este plan:

- Python como lenguaje de implementación.
- SMOTE-Tomek para balanceo cuando esté justificado.
- LightGBM como familia principal de modelos.
- Optuna para optimización de hiperparámetros.
- MLflow para seguimiento de experimentos.
- FastAPI y Docker para serving.
- Evidently para monitorización de drift.
- Grafana para visualización operacional.

## Decisiones pendientes

`AGENTS.md` exige no decidir silenciosamente:

- fuente del dataset;
- Airflow frente a Prefect;
- proveedor cloud;
- almacenamiento de metadatos y features;
- umbrales de drift;
- estrategia de promoción y rollback de modelos.

Toda decisión que se acepte deberá registrarse en un ADR bajo
`docs/decisions/`. Las recomendaciones de este documento no cambian aún su
estado pendiente.

## Límites de seguridad, cumplimiento y corrección

- No usar datos reales de clientes ni PII; solo datos sintéticos o públicos
  anonimizados.
- No versionar credenciales, tokens, secretos ni conexiones reales; usar
  variables de entorno.
- No presentar COP como apto para decisiones crediticias reales.
- No usar atributos protegidos como entradas de decisión ni hacer afirmaciones
  de fairness sin evidencia.
- Separar los datos antes de ajustar preprocesamiento o resampling.
- Ajustar SMOTE-Tomek únicamente dentro de folds de entrenamiento.
- Evitar leakage de target y temporal, y conservar un test reproducible e
  intacto.
- Registrar semillas, versión de dataset, features, parámetros, métricas y
  artefactos.
- Comparar challenger con champion antes de promover.
- Permitir que drift dispare entrenamiento, pero nunca promoción automática por
  sí solo.

## Contradicciones, riesgos y bloqueos

### Contradicciones o tensiones

1. En la inspección inicial, `AGENTS.md` obligaba a seguir `PLANS.md`, pero
   `PLANS.md` estaba vacío. El Milestone 0 resolvió esa tensión con una
   plantilla normativa; este roadmap conserva constancia de su origen
   provisional.
2. Existe una estructura de carpetas amplia, pero casi todos los archivos están
   vacíos y no hay commits. La estructura puede sugerir capacidades que no
   existen y todavía no proporciona una base reproducible.
3. MLflow, Docker, FastAPI, Evidently y Grafana están aceptados, pero no existen
   dependencias, configuración ni servicios verificados. La aceptación de una
   tecnología no equivale a implementación.
4. Se exige comparar challengers con un champion, pero aún no hay política
   aceptada para crear el champion inicial, promover o hacer rollback.

### Decisiones que bloquean la primera vertical

- La fuente y licencia del dataset bloquean el contrato de datos, el esquema,
  los tests de leakage y la definición del target.
- Prefect frente a Airflow bloquea solo la capa de orquestación; no debe bloquear
  el dominio si los casos de uso se mantienen independientes del orquestador.
- El almacenamiento local de MLflow, metadatos y artefactos debe definirse para
  que los experimentos sean reproducibles. La elección cloud no bloquea una
  demo estrictamente local.
- La política de champion inicial, promoción y rollback bloquea cualquier
  retraining de extremo a extremo.
- Los umbrales de drift bloquean alertas o triggers automáticos. No bloquean la
  generación de informes descriptivos sin acciones automáticas.
- Falta decidir cómo versionar materialmente el dataset y cómo identificar cada
  snapshot; esto forma parte de la decisión de fuente/almacenamiento.

### Riesgos principales

- Leakage por resampling o preprocessing antes del split.
- Evaluación optimista por tocar repetidamente el test intacto.
- Dependencia accidental de atributos protegidos o proxies no documentados.
- Dataset público con licencia, procedencia, representatividad o anonimización
  insuficientes.
- Confundir drift estadístico con degradación de desempeño cuando no hay
  labels recientes.
- Promoción automática provocada por drift o por una única métrica.
- Estado local no reproducible debido a artefactos sin versión, imágenes sin
  pinning o datos manuales.
- Ampliar demasiado la primera vertical incorporando scheduler, dashboards y
  tuning antes de validar el camino mínimo.

## Arquitectura mínima propuesta para una demo local

Esta arquitectura es una propuesta, no estado existente:

1. **Adaptador de datos**: carga un snapshot permitido, valida esquema,
   procedencia, licencia, ausencia de PII conocida y contrato del target.
2. **Dominio de preparación**: realiza un split determinista en
   train/validation/test antes de ajustar transformaciones; conserva el test
   intacto.
3. **Dominio de entrenamiento**: construye un pipeline donde preprocessing y
   SMOTE-Tomek, si se justifica, se ajustan solo en folds de entrenamiento;
   entrena LightGBM y registra evidencia reproducible.
4. **Dominio de evaluación**: compara métricas y limitaciones del challenger
   contra un champion conforme a una política versionada.
5. **Tracking local**: usa MLflow con un backend local explícito y artefactos en
   un volumen/directorio ignorado por Git.
6. **Serving local**: FastAPI carga únicamente la referencia de modelo
   promovida y expone scoring de demostración y health check mediante Docker.
7. **Monitorización local**: Evidently compara datos de referencia y actuales;
   publica métricas técnicas consumibles por Grafana, sin promover modelos.
8. **Orquestación fina**: el orquestador que acepte un ADR futuro invoca casos
   de uso del dominio sin contener lógica de negocio.
9. **Control de retraining**: una señal de drift puede abrir o ejecutar un
   entrenamiento challenger; la promoción requiere un gate independiente,
   evidencia y rollback disponible.

Dependencias conceptuales:

`snapshot permitido -> validación -> split -> entrenamiento -> evaluación -> MLflow`

`modelo promovido -> FastAPI`

`referencia + datos actuales -> Evidently -> métricas -> Grafana`

`señal de drift -> retraining challenger -> evaluación -> gate de promoción`

## Recomendaciones sujetas a decisión

### Prefect frente a Airflow

**Criterios para decidir:** comparar operación local, scheduling, observabilidad,
coste de mantenimiento, portabilidad y encaje con el objetivo del portfolio.
La lógica de dominio debe seguir siendo invocable sin el orquestador elegido.
Este roadmap no recomienda ni selecciona Airflow o Prefect.

**Estado:** pendiente hasta aprobar un ADR.

### Dataset público frente a sintético

**Recomendación:** comenzar con un dataset sintético determinista y versionado
para el bootstrap y los tests de integración; evaluar en un milestone posterior
un dataset público anonimizado con licencia, datasheet y revisión de atributos.
Esto permite validar primero la ingeniería sin convertir procedencia o descarga
externa en un bloqueo.

Un dataset sintético no sustenta afirmaciones de desempeño, calibración,
fairness o utilidad en crédito real. Si el objetivo prioritario es demostrar
evaluación modelística creíble, deberá aceptarse después un dataset público
adecuado mediante ADR.

**Estado:** la fuente sigue pendiente hasta aprobar un ADR.

### Almacenamiento de MLflow

**Recomendación:** para una sola máquina, backend SQLite local y artefactos en
filesystem local dentro de rutas persistentes ignoradas por Git. Separar desde
el inicio las URI de backend y artefactos mediante configuración/variables de
entorno. No usar el filesystem backend de MLflow como solución implícita de
metadatos.

La migración a base de datos y object storage gestionados queda fuera del
bootstrap y depende de proveedor cloud y requisitos multiusuario.

**Estado:** propuesta de almacenamiento local; requiere ADR porque afecta al
almacenamiento de metadatos.

### Retraining, promoción y rollback iniciales

**Recomendación:**

- Retraining solo manual o bajo un comando explícito durante el bootstrap.
- En una fase posterior, drift puede generar una solicitud o ejecución de
  challenger, nunca una promoción.
- Crear el champion inicial mediante un bootstrap revisado y documentado.
- Exigir que el challenger supere gates predefinidos en validation, no degrade
  métricas críticas frente al champion y pase checks de datos y seguridad.
- Mantener el test intacto como evaluación excepcional de release, no como
  objetivo de tuning.
- Promoción manual mediante una referencia/alias versionado y con evidencia
  registrada.
- Rollback manual a la versión champion anterior, cuya referencia y artefactos
  deben conservarse.
- Posponer umbrales numéricos hasta contar con baseline y documentarlos por
  separado; no inventarlos en el bootstrap.

**Estado:** pendiente hasta aprobar ADR; especialmente los gates cuantitativos,
la autoridad de aprobación y el mecanismo exacto de alias/rollback.

## Estrategia de ejecución

Los milestones siguientes son secuenciales. Ninguno que dependa de una decisión
pendiente debe comenzar antes de aprobar el ADR correspondiente. Cada cambio
debe ser pequeño, revisable y acompañado de tests cuando altere comportamiento.

### Milestone 0: establecer documentación y baseline del repositorio

**Objetivo**

Convertir el scaffold vacío en una base documental, segura y reproducible, con
packaging y smoke test mínimos, sin implementar capacidades de dominio.

**Archivos previstos**

- `README.md`
- `PLANS.md`
- `CHANGELOG.md`
- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `src/cop/__init__.py`
- `tests/test_import.py`
- `.codex/config.toml`
- `.codex/agents/*.toml`
- `docs/plans/0001-bootstrap.md`
- `docs/plans/0002-baseline-documental.md`

**Comandos de validación**

```bash
git status --short
find . -path './.git' -prune -o -type f -print | sort
test -s README.md
test -s PLANS.md
test -s docs/plans/0001-bootstrap.md
python3 -c "import pathlib, tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.toml')]"
PYTHONPATH=src python3 -c "import cop"
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
git diff --check
```

**Criterio de aceptación**

La documentación distingue visión, estado real, decisiones y propuestas; no
afirma capacidades inexistentes; el formato de ExecPlan queda definido; los
artefactos locales y secretos previstos están ignorados; todos los TOML son
válidos; el paquete se importa; y lint, tipos y smoke test pasan.

**Riesgos**

Documentar una intención como si fuera capacidad existente o ignorar rutas
demasiado amplias y ocultar archivos fuente.

### Milestone 1: resolver decisiones mínimas mediante ADR

**Objetivo**

Aceptar o rechazar explícitamente las propuestas necesarias para comenzar,
incluyendo sus consecuencias y alternativas.

**Archivos previstos**

- `docs/decisions/0001-orchestrator.md`
- `docs/decisions/0002-bootstrap-dataset.md`
- `docs/decisions/0003-local-mlflow-storage.md`
- `docs/decisions/0004-model-lifecycle.md`
- `docs/decisions/0005-data-versioning-and-local-storage.md`

**Comandos de validación**

```bash
find docs/decisions -maxdepth 1 -type f -print | sort
rg -n "^(#|Status:|Context:|Decision:|Consequences:)" docs/decisions
rg -n "pending|proposed|accepted|rejected" docs/decisions
git diff --check
```

**Criterio de aceptación**

Cada ADR tiene estado explícito, contexto, decisión, alternativas y
consecuencias. Están resueltos fuente inicial, orquestador, almacenamiento
local, identificación/versionado de datos y ciclo inicial de modelo. Los
umbrales numéricos pueden seguir pendientes si no se automatizan triggers.

**Riesgos**

Aceptar decisiones sin evidencia suficiente, mezclar dataset de bootstrap con
dataset de evaluación o fijar gates arbitrarios antes de disponer de baseline.

### Milestone 2: añadir configuración tipada y ampliar controles de calidad

**Objetivo**

Extender el paquete mínimo con configuración tipada y sus tests, sin entrenar
modelos. El packaging y las herramientas de calidad básicos ya pertenecen al
Milestone 0.

**Archivos previstos**

- `src/cop/config.py`
- `tests/unit/test_config.py`
- `.env.example`
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

El entorno se instala de forma reproducible; configuración y secretos están
separados; lint, formato, tipos y tests pasan; no se añaden dependencias sin
justificación documentada.

**Riesgos**

Sobrecargar dependencias antes de necesitarlas, asumir versiones incompatibles
o filtrar secretos mediante defaults.

### Milestone 3: implementar contrato y snapshot de datos permitido

**Objetivo**

Materializar únicamente la fuente aceptada en ADR, con generación o ingestión
reproducible, validación de esquema y versionado, sin entrenamiento.

**Archivos previstos**

- `configs/data.yaml`
- `src/cop/data/contracts.py`
- `src/cop/data/load.py`
- `scripts/prepare_data.py`
- `tests/unit/data/`
- `tests/integration/test_prepare_data.py`
- documentación de procedencia/licencia o especificación del generador
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 scripts/prepare_data.py --help
python3 -m pytest tests/unit/data tests/integration/test_prepare_data.py
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

El snapshot se reproduce y posee identificador de versión; esquema y target
están documentados; no contiene PII real; atributos protegidos no son features
de decisión; errores de contrato fallan de forma explícita.

**Riesgos**

Licencia no compatible, descarga no reproducible, PII inadvertida, proxies no
identificados o target mal definido.

### Milestone 4: establecer split y baseline de evaluación

**Objetivo**

Crear el split determinista e intacto y una evaluación ingenua de referencia
antes de introducir LightGBM, resampling u optimización.

**Archivos previstos**

- `configs/evaluation.yaml`
- `src/cop/data/split.py`
- `src/cop/evaluation/metrics.py`
- `src/cop/evaluation/baseline.py`
- `tests/unit/data/test_split.py`
- `tests/unit/evaluation/`
- artefacto de manifest del split en una ruta local ignorada
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit/data/test_split.py tests/unit/evaluation
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

El split es reproducible, no solapado y anterior a cualquier fit; el test queda
marcado como intacto; las métricas y su dirección están documentadas; existe un
baseline no promocionable.

**Riesgos**

Leakage temporal o de entidad, selección oportunista de métricas y uso
prematuro del test.

### Milestone 5: entrenar un challenger reproducible y registrarlo

**Objetivo**

Entrenar LightGBM con pipeline correcto y registrar ejecución, configuración,
datos, métricas y artefactos en MLflow local. Optuna y SMOTE-Tomek se añaden
solo si una comparación documentada los justifica.

**Archivos previstos**

- `configs/training.yaml`
- `src/cop/features/`
- `src/cop/training/pipeline.py`
- `src/cop/training/train.py`
- `src/cop/evaluation/compare.py`
- `scripts/train.py`
- `tests/unit/features/`
- `tests/unit/training/`
- `tests/integration/test_training.py`
- configuración local de MLflow acorde al ADR
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 scripts/train.py --help
python3 -m pytest tests/unit/features tests/unit/training tests/integration/test_training.py
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

Dos ejecuciones con la misma semilla y snapshot producen resultados dentro de
tolerancias documentadas; preprocessing y resampling se ajustan solo en folds
de entrenamiento; MLflow registra todos los elementos exigidos; no hay
promoción automática.

**Riesgos**

Leakage dentro de cross-validation, reproducibilidad incompleta de LightGBM,
optimización excesiva o uso injustificado de SMOTE-Tomek.

### Milestone 6: introducir champion y gate manual

**Objetivo**

Aplicar el ADR de ciclo de modelo para crear un champion inicial auditable,
comparar challengers y hacer promoción/rollback manual.

**Archivos previstos**

- `configs/promotion.yaml`
- `src/cop/evaluation/gates.py`
- `src/cop/training/registry.py`
- `scripts/promote_model.py`
- `scripts/rollback_model.py`
- `tests/unit/evaluation/test_gates.py`
- `tests/integration/test_model_lifecycle.py`
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit/evaluation/test_gates.py tests/integration/test_model_lifecycle.py
python3 scripts/promote_model.py --help
python3 scripts/rollback_model.py --help
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

La promoción exige evidencia y acción explícita; un challenger fallido no
reemplaza al champion; rollback recupera la referencia anterior; cada
transición queda registrada.

**Riesgos**

Gates mal calibrados, mutación no atómica de referencias, artefactos eliminados
o ambigüedad sobre quién aprueba.

### Milestone 7: servir el champion local

**Objetivo**

Exponer health check y scoring de demostración desde FastAPI en Docker,
manteniendo el dominio separado de HTTP.

**Archivos previstos**

- `src/cop/serving/app.py`
- `src/cop/serving/schemas.py`
- `infra/docker/api.Dockerfile`
- `docker-compose.yml`
- `tests/unit/serving/`
- `tests/integration/test_api.py`
- `.env.example`
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit/serving tests/integration/test_api.py
docker compose config
docker compose build api
docker compose up -d api
curl --fail http://localhost:8000/health
docker compose down
python3 -m ruff check .
python3 -m mypy src tests
```

**Criterio de aceptación**

La API carga solo una referencia promovida, valida entradas, no acepta ni
registra PII real, expone versión del modelo y funciona localmente desde una
imagen reproducible.

**Riesgos**

Contrato HTTP divergente del pipeline, logs con datos sensibles, modelo ausente
o dependencias/imágenes sin pinning.

### Milestone 8: añadir informe de drift sin automatización

**Objetivo**

Comparar referencia y snapshot actual con Evidently y exponer métricas
descriptivas para Grafana, sin triggers ni promoción.

**Archivos previstos**

- `configs/monitoring.yaml`
- `src/cop/monitoring/report.py`
- `src/cop/monitoring/metrics.py`
- `scripts/run_drift_report.py`
- `infra/grafana/`
- `infra/prometheus/`
- `tests/unit/monitoring/`
- `tests/integration/test_monitoring.py`
- `docker-compose.yml`
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit/monitoring tests/integration/test_monitoring.py
python3 scripts/run_drift_report.py --help
docker compose config
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

El informe identifica snapshots y configuración, distingue drift de datos de
desempeño, Grafana visualiza métricas verificables y ninguna señal inicia
acciones automáticas.

**Riesgos**

Umbrales sin baseline, falsa interpretación causal, cardinalidad excesiva de
métricas o dashboards no provisionables.

### Milestone 9: orquestar retraining controlado

**Objetivo**

Tras aceptar umbrales y política completa, coordinar con el orquestador elegido
la detección, creación de challenger y evaluación; mantener la promoción como
gate separado.

**Archivos previstos**

- ADR de umbrales de drift
- `configs/orchestration.yaml`
- `src/cop/orchestration/flows.py`
- `scripts/run_retraining_flow.py`
- `tests/unit/orchestration/`
- `tests/integration/test_retraining_flow.py`
- `README.md`
- `CHANGELOG.md`

**Comandos de validación**

```bash
python3 -m pytest tests/unit/orchestration tests/integration/test_retraining_flow.py
python3 scripts/run_retraining_flow.py --help
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src tests
git diff --check
```

**Criterio de aceptación**

El flujo es idempotente y auditable; el drift puede producir un challenger,
pero no cambia el champion; fallos conservan el modelo servido; reintentos no
duplican promociones ni corrompen el tracking.

**Riesgos**

Automatización prematura, reintentos no idempotentes, carreras entre runs,
thresholds inestables o acoplamiento del dominio al orquestador.

## Validación global de la vertical futura

Cuando todos los milestones aplicables estén implementados:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
docker compose config
git diff --check
git status --short
```

La aceptación global requerirá además una ejecución local documentada desde un
snapshot permitido hasta un challenger registrado, una promoción manual
auditable, serving del champion, un informe de drift y una demostración de que
drift no promueve por sí mismo.

## Registro de progreso

- [x] 2026-07-25: inspección inicial y creación de este ExecPlan.
- [x] 2026-07-25: implementación del Milestone 0 mediante
  `docs/plans/0002-baseline-documental.md`; su validación y cierre se registran
  en ese plan específico.
- [ ] Milestone 1.
- [ ] Milestone 2.
- [ ] Milestone 3.
- [ ] Milestone 4.
- [ ] Milestone 5.
- [ ] Milestone 6.
- [ ] Milestone 7.
- [ ] Milestone 8.
- [ ] Milestone 9.

## Registro de decisiones del plan

- 2026-07-25: se adopta un formato provisional porque `PLANS.md` está vacío.
- 2026-07-25: dataset sintético de bootstrap, SQLite más filesystem local para
  MLflow y promoción manual se registran solo como recomendaciones. No
  constituyen ADR ni decisión aceptada.
- 2026-07-25: cloud queda fuera de la primera demo local y continúa pendiente.
- 2026-07-25: el Milestone 0 establece `PLANS.md` como plantilla normativa,
  adopta `python3` como comando canónico y traslada su ejecución detallada al
  ExecPlan 0002.
- 2026-07-25: Airflow frente a Prefect continúa neutral y pendiente de ADR; el
  roadmap conserva únicamente criterios para una decisión futura.

## Hallazgos inesperados

- El repositorio contiene muchos directorios con nombres de componentes, pero
  están vacíos. No deben tomarse como prueba de implementación.
- No existe historia de Git desde la cual inferir decisiones o capacidades.

## Resultados y retrospectiva

El Milestone 0 materializó documentación, packaging mínimo, protecciones
locales, configuración de agentes y un smoke test sin añadir funcionalidad de
dominio. Los resultados y bloqueos de validación se mantienen en
`docs/plans/0002-baseline-documental.md`.

Los Milestones 1 a 9 continúan sin ejecutar. Las propuestas que contienen no
son capacidades existentes ni decisiones aceptadas.
