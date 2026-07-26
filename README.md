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

El repositorio contiene únicamente un baseline de ingeniería:

- documentación del proyecto y reglas para mantener ExecPlans;
- un paquete Python mínimo bajo `src/cop`;
- configuración de packaging y herramientas de desarrollo en
  `pyproject.toml`;
- una plantilla segura de variables de entorno;
- exclusiones de Git para secretos y artefactos locales;
- perfiles de agentes de desarrollo;
- un smoke test que comprueba que `cop` puede importarse;
- una decisión aceptada y especificación documental, todavía sin
  implementación, para el bootstrap sintético.

No hay dataset aceptado, versionado o utilizable para entrenamiento, ni EDA,
pipeline de features, modelo, entrenamiento, experimento, API, imagen Docker
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

Los ADR aceptados añaden estas decisiones documentales, todavía sin
implementación:

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

## Decisiones todavía pendientes

Continúan sin decidir:

- la definición final del target, umbral DPD y horizonte;
- población, estimand, tamaño, borrowers, solicitudes y prevalencia;
- ventanas, distribuciones, correlaciones y escenarios exactos de drift;
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

## Planificación

El roadmap general está en `docs/plans/0001-bootstrap.md`. Cada milestone
ejecutable debe mantenerse como un ExecPlan pequeño conforme a `PLANS.md`.
