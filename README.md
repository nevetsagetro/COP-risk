# COP — demostración de riesgo de crédito

COP es un proyecto de portfolio y demostración cuyo objetivo es explorar un
ciclo controlado de scoring de riesgo de crédito: preparación de datos,
entrenamiento reproducible, evaluación, serving, observabilidad de drift y
retraining con promoción separada.

> **Advertencia:** COP no está aprobado para tomar decisiones crediticias
> reales. No debe utilizar datos reales de clientes ni información personal
> identificable (PII), y sus resultados no deben emplearse para conceder,
> denegar o modificar crédito.

## Estado actual verificable

El repositorio contiene un baseline de ingeniería y una primera capacidad de
datos sintéticos:

- documentación del proyecto y reglas para mantener ExecPlans;
- un paquete Python mínimo bajo `src/cop`;
- configuración de packaging y herramientas de desarrollo en
  `pyproject.toml`;
- una plantilla segura de variables de entorno;
- exclusiones de Git para secretos y artefactos locales;
- perfiles de agentes de desarrollo;
- un smoke test que comprueba que `cop` puede importarse;
- una decisión aceptada y configuración metodológica congelada para el
  snapshot sintético v1 de demostración local;
- un generador sintético por CLI con configuración YAML, Parquet, manifest,
  hashes físicos/lógicos y validación contractual;
- cinco splits temporales reproducibles y disjuntos por `borrower_id`, con
  purga y manifest verificable.
- un evaluador machine-readable de datasets por capacidad y un snapshot de UCI
  Default of Credit Card Clients aceptado solo para baseline académico local,
  con splits estratificados reproducibles.

Existen un snapshot sintético v1 aprobado exclusivamente para entrenamiento
local de demostración; sus filas permanecen fuera de Git y su identidad se
registra en `docs/datasets/synthetic-v1-acceptance.md`; y un snapshot UCI
aceptado únicamente para baseline académico, documentado en
`docs/datasets/uci-default-credit-card.md`. No hay EDA, pipeline de
features, modelo, entrenamiento, experimento, API, imagen Docker
funcional, servicio, orquestador, informe de drift, dashboard, retraining, base
de datos o infraestructura cloud implementados. El ZIP local de SFLLD fue
rechazado y no contradice este estado. Los directorios vacíos con nombres de
componentes reservan estructura, pero no demuestran capacidades.

## Visión y capacidades planificadas

La visión futura contempla una demostración local que pueda:

1. usar únicamente datos sintéticos o públicos anonimizados y con procedencia
   documentada;
2. preparar splits reproducibles sin target leakage ni temporal leakage;
3. entrenar y evaluar challengers sin contaminar un test intacto;
4. registrar evidencia reproducible de experimentos;
5. servir solo un modelo promovido mediante un proceso auditable;
6. observar drift sin convertirlo en promoción automática;
7. permitir retraining controlado con comparación challenger/champion y
   rollback.

Esta lista expresa trabajo planificado. Ninguna de estas capacidades existe
todavía en el repositorio.

## Decisiones técnicas aceptadas

`AGENTS.md` es la fuente normativa de las decisiones de producto aceptadas:

- Python como lenguaje de implementación;
- SMOTE-Tomek para balanceo cuando esté justificado;
- LightGBM como familia principal de modelos;
- Optuna para optimización de hiperparámetros;
- MLflow para seguimiento de experimentos;
- FastAPI y Docker para serving;
- Evidently para monitorización de drift;
- Grafana para visualización operacional.

El baseline de desarrollo soporta Python 3.12 y usa `python3` como comando
canónico. Las tecnologías enumeradas arriba están aceptadas para trabajo
futuro, pero no se han añadido como dependencias ni se han implementado.

Los ADR aceptados añaden estas decisiones; su implementación debe comprobarse
por separado en el árbol:

- Prefect será el orquestador cuando exista un pipeline Python manual,
  reproducible, probado e idempotente;
- COP será local-first y Docker Compose se añadirá incrementalmente para
  servicios concretos; cloud sigue fuera de alcance;
- MLflow usará inicialmente SQLite para metadata y filesystem local para
  artefactos, sin decidir feature store;
- `uv.lock` será la estrategia de lock y se generará en un milestone posterior;
- drift puede solicitar o iniciar challengers, pero promoción y rollback serán
  humanos, comparativos y auditados;
- datos sintéticos deterministas serán la fuente principal inicial; generador,
  configuración, semillas y snapshots serán versionados, con Parquet, manifest,
  hashes físicos/lógicos y `snapshot_as_of`.

La primera versión del generador sintético y los splits v1 están implementados
y validados por CLI. ADR 0007 acepta sus parámetros exclusivamente para la
demostración sintética local. Esto no implementa el pipeline ML ni aporta
evidencia sobre crédito real.

## Decisiones todavía pendientes

Continúan sin decidir fuera del perfil sintético local de ADR 0007:

- parámetros metodológicos para cualquier dataset real futuro;
- distribuciones, correlaciones y escenarios exactos de drift posteriores;
- el proveedor cloud, que permanece fuera de alcance;
- el feature store y el almacenamiento de features;
- las features concretas;
- los umbrales de drift;
- las métricas finales, gates cuantitativos y autoridad/mecanismo de
  aprobación;
- la configuración completa de Docker Compose;
- los detalles operativos de Prefect, MLflow, backup, retención y migración.

Una decisión aceptada debe registrarse mediante un ADR bajo
`docs/decisions/`. La aceptación documental no demuestra implementación.

## Desarrollo mínimo

Requisitos:

- Python 3.12;
- Git;
- acceso a un índice de paquetes compatible con `pip` para instalar las
  herramientas de desarrollo fijadas en `pyproject.toml`.

Preparación:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

Validación:

```bash
python3 -c "import cop"
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
git diff --check
git status --short
```

La configuración de entorno de ejemplo se copia solo cuando una funcionalidad
la necesite:

```bash
cp .env.example .env
```

`.env` es local y está ignorado por Git. Los valores actuales de
`.env.example` son ficticios y ninguna funcionalidad del paquete los consume
todavía.

## Generador sintético mínimo

Tras instalar las dependencias, la configuración v1 se ejecuta con:

```bash
python3 scripts/generate_synthetic_snapshot.py \
  --config configs/data/synthetic-v1-approved.yaml
```

La salida queda bajo `data/raw/synthetic/`, ignorada por Git. La CLI rechaza
sobrescrituras; `--force` debe indicarse expresamente. Un snapshot existente se
verifica sin escribir con:

```bash
python3 scripts/generate_synthetic_snapshot.py \
  --verify data/raw/synthetic/<snapshot_id>
```

Los splits aprobados se crean después de verificar el snapshot:

```bash
python3 scripts/create_synthetic_splits.py \
  --snapshot data/raw/synthetic/<snapshot_id>
```

Esta capacidad genera datos y splits de demostración; no crea un pipeline ML
ni evidencia sobre crédito real.

## Evaluación académica UCI

La adquisición y evaluación reproducibles se ejecutan con:

```bash
python3 scripts/download_uci_credit_card.py
python3 scripts/evaluate_dataset_candidate.py \
  --acquisition data/raw/uci-default-credit-card/<acquisition_id>
```

La aceptación UCI es estática y académica. Sus fallos de temporalidad,
monitoring longitudinal y producción permanecen explícitos.

## Planificación

El roadmap general está en `docs/plans/0001-bootstrap.md`. Cada milestone
ejecutable debe mantenerse como un ExecPlan pequeño conforme a `PLANS.md`.
