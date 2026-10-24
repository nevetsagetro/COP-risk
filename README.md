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

El repositorio contiene un baseline de ingeniería y dos verticales de datos
claramente separadas:

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
- dos baselines académicos UCI reproducibles (Logistic Regression y LightGBM)
  con development limitado a train/validation y cierre explícito e inmutable
  del test;
- un `milestone_finisher` que valida una allowlist del ExecPlan y prepara
  staging literal sin autorizar commits automáticamente.

UCI Default of Credit Card Clients es la vertical principal. El código UCI no
depende del paquete sintético. La generación sintética se conserva como una
vertical metodológica aislada y no define la ruta principal del proyecto.

Existen un snapshot sintético v1 aprobado exclusivamente para entrenamiento
local de demostración; sus filas permanecen fuera de Git y su identidad se
registra en `docs/datasets/synthetic-v1-acceptance.md`; y un snapshot UCI
aceptado únicamente para baseline académico, documentado en
`docs/datasets/uci-default-credit-card.md`. Existe un baseline académico local,
pero no hay EDA general, modelo promovido, experimento MLflow, API, imagen Docker
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

Esta lista expresa la visión completa. Splits reproducibles y un baseline
académico local ya existen; serving, monitoring, retraining, promoción y
registro MLflow todavía no están implementados.

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
canónico. LightGBM está implementado únicamente en el baseline académico UCI.
SMOTE-Tomek, Optuna, MLflow, serving y monitoring siguen sin añadirse o
implementarse.

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
- ADR 0006 estableció inicialmente los datos sintéticos como fuente principal;
  ADR 0009 sustituye esa prioridad y establece UCI como vertical principal. La
  implementación sintética existente se conserva aislada y no es dependencia
  del pipeline UCI.

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
- las features de producción; las 19 features del baseline UCI están congeladas;
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

## Baseline académico UCI

La fase de desarrollo ajusta ambos modelos únicamente con train y evalúa
validation. El test solo se abre mediante la segunda invocación explícita:

```bash
python3 scripts/train_uci_baseline.py
python3 scripts/train_uci_baseline.py --finalize-test
```

Los artefactos quedan bajo `runs/**`, fuera de Git. La finalización consume una
claim y no admite reapertura o sobrescritura. Los resultados son descriptivos
para un benchmark estático; no seleccionan winner/champion ni autorizan claims
temporales, de fairness, producción o crédito real. En Linux, LightGBM requiere
el runtime del sistema `libgomp.so.1`.

### Demo MVP para portfolio

Para ejecutar el flujo local y mostrar un resumen de métricas sin abrir el
test:

```bash
python3 scripts/run_mvp_demo.py
```

La demo reutiliza un run reproducible si ya existe, muestra ROC-AUC y average
precision de validation para ambos modelos y confirma que el test permanece
cerrado. Para automatizar la salida:

```bash
python3 scripts/run_mvp_demo.py --json
```

Este es un MVP académico local, no un sistema de decisión crediticia.

### Home Credit model-improvement milestone

The Home Credit academic story is backed by offline artifacts. Feature
engineering, ablation, cross-validation, Optuna tuning and classical challenger
training run through explicit CLI jobs and save JSON/CSV evidence under
`runs/`. FastAPI and the browser only read those cached artifacts; opening the
demo never retrains a model or runs tuning. Reproduce a report by rerunning the
corresponding script with its recorded dataset fingerprint, feature version,
split seed and experiment seed. The first milestone covers classical models
and UX/UI storytelling. Deep learning is a separate future sprint.

### Presentación Streamlit

La interfaz opcional combina una vista de resultados académicos con tablas y
gráficas y una vista de predicción ilustrativa con las 19 features UCI:

```bash
python3 -m pip install -e '.[demo]'
python3 -m streamlit run app/streamlit_app.py
```

La app reutiliza los artefactos locales del baseline, no abre el test y no
representa un servicio de decisión crediticia. La vista académica incluye un
recorrido narrativo del threshold lab: tres paradas explican cuándo se busca
más cobertura, cuándo se prioriza precision y cómo F1 resume el equilibrio.
El control manual y el botón de reproducción permiten presentar el cambio como
un motion graphic autoexplicativo.

### Laboratorio académico de modelos

Para demostrar comparación de modelos, ajuste de parámetros y selección de
umbral sin contaminar validation o test:

```bash
python3 scripts/run_academic_model_lab.py
```

El laboratorio prueba candidatos reproducibles de Logistic Regression, LightGBM
y KNN usando únicamente cross-validation sobre train. KNN se incluye como
benchmark académico con variables numéricas escaladas; no se asume que añadir
otra familia mejore el resultado. Selecciona por
Average Precision, aprende el umbral con predicciones out-of-fold de train y
evalúa el resultado seleccionado en validation tanto con `0.5` como con el
umbral aprendido. La salida JSON conserva candidatos, parámetros, métricas de
fold, métricas agregadas y la decisión de umbral. El comando no abre el test,
no cambia el serving y no promueve un modelo.

### API y frontend analítico

La evolución separada del demo expone una API FastAPI y un frontend estático
HTML/Plotly. Streamlit se conserva como fallback, mientras que la URL de
FastAPI sirve la experiencia principal:

```bash
python3 -m pip install -e '.[api]'
python3 -m uvicorn cop.api:app --reload --port 8000
```

Abre `http://localhost:8000`. La API ofrece `/health`, `/api/overview`,
`/api/metrics`, `/api/roc`, `/api/probabilities`,
`/api/examples`, `/api/threshold-sweep?model=lightgbm`, `/api/model-lab` y
`POST /api/predict`. El laboratorio se ejecuta bajo demanda desde el frontend
para no ralentizar la carga inicial de gráficos; su resultado queda cacheado
durante la vida del proceso.
La interfaz incluye un toggle `EN / ES`; inglés es el idioma inicial y la
preferencia se conserva localmente en el navegador.
`/api/examples` devuelve casos públicos anonimizados de validation para probar
un solo cambio manteniendo el resto del contexto. Sus identificadores siguen la
convención `UCI-VAL-####` (`dataset UCI`, bloque `validation`, número anónimo),
y cada caso incluye un resumen legible del historial y del resultado observado.
Todos los resultados son
académicos, el test permanece cerrado y no existe un endpoint
de aprobación o denegación.

### Estudio académico y notebooks

El estudio reproducible genera cross-validation sobre train, comparación en
validation, calibración LightGBM, sweep de thresholds y predicciones OOF:

```bash
python3 scripts/run_academic_study.py --folds 5
python3 -m pip install -e '.[research]'
jupyter lab
```

Los notebooks `notebooks/01_academic_study.ipynb` y
`notebooks/02_error_analysis.ipynb` presentan los resultados con Plotly y
motion graphics del trade-off precision/recall. La app traduce recall como
“casos encontrados”, precision como “alertas correctas” y F1 como “equilibrio”,
y anota directamente los puntos de mayor cobertura, mayor precisión y mejor F1.
El test permanece cerrado.

## Cierre seguro de milestones

Cada ExecPlan técnico declara `Version-control allowlist`. Tras la revisión:

```bash
python3 scripts/finish_milestone.py --plan docs/plans/<plan>.md --check
python3 scripts/finish_milestone.py --plan docs/plans/<plan>.md --stage
```

El commit exige autorización humana y `--message` explícito. El finisher nunca
usa `git add .`, ni hace push, borrado, reset, amend o rebase.

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
