# ExecPlan 0012: evaluador de datasets y baseline académico UCI

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-08-02.
- Última actualización: 2026-08-02.
- Responsable: agente `coordinator`.
- Alcance: Milestone 8, evaluación por capacidad y snapshot académico UCI.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato de datos, protocolo de
  evaluación y aprobación humana del Milestone 8.

## Propósito y resultado observable

Implementar un contrato machine-readable que decida usos de un dataset de
forma independiente y aplicarlo a UCI Default of Credit Card Clients. El
resultado debe aceptar un snapshot y splits estratificados únicamente para
baseline académico, manteniendo explícitos los fallos temporales,
longitudinales y productivos.

## Base verificada

Inspección del 2026-08-02:

- `HEAD`: `ad302dc9c5011edd38d6352f116570a81349a94f`;
- working tree no limpio con el trabajo sin commit de Milestones 6 y 7;
- existe `synthetic-v1` aprobado, pero no evaluador genérico, ingestor UCI,
  snapshot UCI ni splits académicos;
- UCI publica 30000 instancias, 23 features, clasificación, DOI
  `10.24432/C55S3H`, licencia CC BY 4.0 y un XLS de 5.3 MB;
- no existe dataset real aprobado para temporalidad o monitoring.

## Alcance

- contrato YAML de candidato y capacidades;
- adquisición solo desde URL oficial UCI;
- verificación de archivo, licencia declarada, esquema y target;
- evaluador determinista con estados independientes;
- snapshot Parquet y splits estratificados académicos reproducibles;
- manifests, documentación, tests y CLI.

## Fuera de alcance

LightGBM, SMOTE-Tomek, Optuna, MLflow, Prefect, FastAPI, Evidently,
preprocessing productivo, entrenamiento, métricas, gates de rendimiento,
validación temporal, drift longitudinal y claims reales o productivos.

## Decisiones

### Aceptadas

UCI puede evaluarse para baseline académico, clasificación binaria,
experimentos futuros de imbalance, LightGBM, Optuna y serving local. No queda
autorizado aún ningún componente ML. No se autoriza temporalidad, monitoring
longitudinal, producción, fairness ni decisiones crediticias reales.

### Operativas

Las capacidades se evalúan por separado; un `fail` metodológico permanece
visible pero solo bloquea los usos que dependan de ese gate. Snapshot y splits
académicos requieren `pass` exacto en provenance, license, target_definition,
schema y academic_modeling.

## Seguridad y restricciones

La descarga procede exclusivamente de UCI, queda bajo `data/**` ignorado y no
incluye credenciales. El dataset se trata como público y enlazable; las
variables demográficas no autorizan claims de fairness ni inputs futuros sin
otra decisión explícita.

## Plan de ejecución

1. Definir configuración y contrato de capacidades estricto.
2. Implementar descarga, extracción segura, hashes y manifest.
3. Inspeccionar XLS, normalizar snapshot y verificar esquema/target.
4. Implementar evaluación determinista y decisión de uso académico.
5. Crear splits estratificados solo tras gates documentales/técnicos.
6. Añadir tests, documentación, materialización y revisión final.

## Validación y criterios de aceptación

```bash
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
git diff --check
git check-ignore data/raw/uci-default-credit-card
```

Dos evaluaciones y dos materializaciones equivalentes deben reproducir hashes.
Los manifests deben conservar todos los `fail` y los splits deben ser
estratificados, disjuntos y deterministas.

## Registro de progreso

- [x] 2026-08-02: inspección obligatoria y verificación documental oficial.
- [x] 2026-08-02: contrato y evaluador determinista.
- [x] 2026-08-02: adquisición, snapshot separado y splits reproducibles.
- [x] 2026-08-02: tests y documentación.
- [x] 2026-08-02: tercera revisión final sin hallazgos critical o high abiertos.

## Hallazgos inesperados

- La revisión inicial detectó promoción tautológica de gates documentales y
  bypass de evaluación desde las APIs. Se corrigió exigiendo estado declarado
  `pass`, evidencia recomputada y enlaces de hashes entre contrato,
  adquisición, evaluación, snapshot y splits.
- La revisión inicial detectó variables sensibles dentro de la tabla modelable.
  Se separaron físicamente en `audit_only.parquet`.
- La segunda revisión detectó campos de autorización del manifest de splits no
  reconstruidos. La verificación ahora recompone el manifest completo, valida
  el nombre del sidecar y del directorio, y la publicación usa rename atómico.

## Registro de decisiones del plan

- 2026-08-02: los estados de capacidad no se agregan en una puntuación global.
- 2026-08-02: los fallos temporal/longitudinal/productivo no bloquean el uso
  académico autorizado si provenance, licencia y esquema pasan.

## Resultados y retrospectiva

Se adquirió el ZIP oficial (SHA-256 `56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602`)
y se aceptó un snapshot de 30000 filas solo para baseline académico. El
snapshot v2 separa cuatro columnas `audit_only`; sus splits 70/15/15 tienen
21000/4500/4500 filas, intersección cero de ID y hash lógico conjunto
`d1e3ff1bbf3063a146e2d57f4a59c533cf89fa58f57f02cae45dd14e1202fade`.
La evaluación conserva `fail` para timestamps, temporal_split,
longitudinal_monitoring y production_claims. Dos ejecuciones consecutivas
reutilizaron y verificaron las mismas identidades y hashes.
