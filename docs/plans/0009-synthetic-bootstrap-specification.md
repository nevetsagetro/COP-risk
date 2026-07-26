# ExecPlan 0009: decisión y especificación del bootstrap sintético

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-26.
- Última actualización: 2026-07-26.
- Responsable: agente `coordinator`.
- Alcance: Milestone 5 solicitado, documentación del bootstrap sintético.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato, protocolo, checklist,
  ADR 0005 y ExecPlan 0008.

## Propósito y resultado observable

Especificar y registrar la aceptación humana de un bootstrap sintético
determinista como fuente principal inicial, con contrato, diccionario,
escenarios de drift y límites, sin generar datos ni implementar código.

## Base verificada

Inspección del 2026-07-26:

- `pwd` es `/home/nvsagt/projects/cop-credit-risk`;
- `HEAD` inicial es `91bee9398884b87645a57ed185a585e00bc678e7`;
- `git status --short` inicial no produjo salida;
- existen contrato, protocolo, checklist, ADR 0001-0005 y planes 0001-0008;
- 0008 está completado y ningún dataset real fue aprobado o quedó elegible para
  cuarentena;
- no existen generador, dataset sintético, split, modelo o monitoring.

El roadmap 0001 usa históricamente “Milestone 5” para entrenamiento. Este
ExecPlan conserva el nombre solicitado sin renumerar ni autorizar ese trabajo.

## Alcance

- `docs/decisions/0006-synthetic-data-bootstrap.md`;
- `docs/synthetic-data-specification.md`;
- `docs/synthetic-data-dictionary.md`;
- `docs/synthetic-drift-scenarios.md`;
- este ExecPlan;
- `README.md`;
- `AGENTS.md`;
- `CHANGELOG.md`;
- `docs/plans/0001-bootstrap.md`.

Un único agente, `coordinator`, escribe documentación. Dos agentes `data_ml` y
uno `monitoring` aportan análisis read-only; `reviewer` realiza revisión final
read-only.

## Fuera de alcance

Generador, YAML ejecutable, CSV/Parquet material, datos, entrenamiento,
preprocessing, SMOTE-Tomek, LightGBM, Optuna, MLflow, Prefect, FastAPI, Docker,
Evidently, cuarentena, dependencias y commit.

## Decisiones

### Aceptadas aplicables

Solo datos sintéticos o públicos anonimizados; atributos protegidos nunca son
inputs; split antes de fit; test intacto; drift no promueve; reproducibilidad y
evidencia versionada.

### Aceptadas

ADR 0006: datos sintéticos deterministas como fuente principal inicial;
generador, configuración, semillas y snapshots versionados; salida Parquet;
manifest con hashes físicos/lógicos; `snapshot_as_of`; target derivado de
schedule/ledger; unknown preservado; split temporal y por `borrower_id`; test
intacto; atributos protegidos separados; mismos gates para datos reales; sin
claims reales.

### Pendientes

Definición final del target, umbral DPD, horizonte, población, estimand, tamaño,
borrowers, solicitudes, prevalencia, ventanas, distribuciones, correlaciones,
escenarios exactos de drift, thresholds, gates y mecanismo material de sellado.

### Propuestas no aceptadas

Solicitud como unidad, `application_id`, target 90+ DPD en 12 meses y familias
concretas de features, distribuciones, interacciones y escenarios.

## Seguridad y restricciones

No PII, claims reales ni fairness washing. Atributos protegidos separados.
Target derivado de eventos posteriores. Truth de escenarios fuera de inputs y
monitoring. Datos reales futuros conservan todos los gates. El ADR está
`Accepted`; aceptación documental no equivale a implementación.

## Plan de ejecución

1. Inspeccionar árbol, normativa, contrato, protocolo y último plan.
2. Recibir análisis read-only de contrato y mecanismo de features.
3. Recibir análisis read-only de escenarios de monitoring.
4. Redactar los cinco documentos iniciales con un único writer.
5. Validar invariantes, alcance, baseline y diff completo.
6. Solicitar revisión final read-only y corregir critical/high.
7. Registrar resultados reales y completar el plan.
8. Tras aprobación humana, reconciliar ADR, especificación, normativa,
   changelog y roadmap sin implementar capacidades.

## Validación y criterios de aceptación

```bash
test -s docs/decisions/0006-synthetic-data-bootstrap.md
test -s docs/synthetic-data-specification.md
test -s docs/synthetic-data-dictionary.md
test -s docs/synthetic-drift-scenarios.md
test -s docs/plans/0009-synthetic-bootstrap-specification.md
rg -n "Status: Accepted" docs/decisions/0006-synthetic-data-bootstrap.md
test "$(rg -l '^- Status: Accepted$' docs/decisions/*.md | wc -l)" -eq 6
test "$(rg -l '^- Status: Proposed$' docs/decisions/*.md | wc -l)" -eq 0
rg -n "available_at" docs/synthetic-data-{specification,dictionary}.md
rg -n "immature|inmadura|unknown" docs/synthetic-data-{specification,dictionary}.md
rg -n "covariate|prior probability|concept drift|delayed labels|recuperación|retraining" docs/synthetic-drift-scenarios.md
test -z "$(git diff --name-only | grep -Ev '^(README.md|AGENTS.md|CHANGELOG.md|docs/plans/0001-bootstrap.md)$')"
test -z "$(git ls-files --others --exclude-standard | grep -Ev '^(docs/decisions/0006-synthetic-data-bootstrap.md|docs/synthetic-data-specification.md|docs/synthetic-data-dictionary.md|docs/synthetic-drift-scenarios.md|docs/plans/0009-synthetic-bootstrap-specification.md)$')"
.venv/bin/python -c "import pathlib, tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.toml')]"
PYTHONPATH=src .venv/bin/python -c "import cop"
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests
.venv/bin/python -m pytest
git diff --check
git status --short
git diff --no-index /dev/null docs/decisions/0006-synthetic-data-bootstrap.md
git diff --no-index /dev/null docs/synthetic-data-specification.md
git diff --no-index /dev/null docs/synthetic-data-dictionary.md
git diff --no-index /dev/null docs/synthetic-drift-scenarios.md
git diff --no-index /dev/null docs/plans/0009-synthetic-bootstrap-specification.md
```

La revisión comprobará además que cada input tenga regla `available_at`, que
no exista camino desde outcome, que unknown no sea negativo, que el split
separe entidad, que el test esté fuera de usos adaptativos y que no haya claims
reales.

## Registro de progreso

- [x] 2026-07-26: inspección obligatoria sobre árbol limpio.
- [x] 2026-07-26: análisis read-only de contrato, features y monitoring.
- [x] 2026-07-26: borrador de los cinco documentos por un único writer.
- [x] 2026-07-26: baseline, allowlist y diff completo.
- [x] 2026-07-26: reviewer final y correcciones; sin critical/high/medium.
- [x] 2026-07-26: aprobación humana del ADR 0006 registrada y documentación
  normativa reconciliada.

## Hallazgos inesperados

- “Milestone 5” ya nombra un milestone histórico distinto en el roadmap; no se
  modifica porque queda fuera de alcance.
- Generar directamente el target ocultaría errores del schedule/ledger.
- Byte hashes de Parquet dependen del writer; se propone además hash lógico.
- La primera revisión detectó que faltaba `snapshot_as_of`; sin cutoff la
  madurez podía depender del reloj de ejecución.

## Registro de decisiones del plan

- 2026-07-26: conservar `Status: Proposed` y separar fuente propuesta de
  parámetros metodológicos no aceptados.
- 2026-07-26: reservar verdad de escenarios solo para evaluación sintética.
- 2026-07-26: usar al coordinator como único writer.
- 2026-07-26: incorporar `snapshot_as_of` a configuración, identidad y manifest.
- 2026-07-26: no asumir redistribución sin licencia aceptada.
- 2026-07-26: se acepta el alcance estratégico del ADR 0006 sin aceptar sus
  parámetros metodológicos pendientes.

## Resultados y retrospectiva

Se crearon la especificación, el diccionario y los escenarios configurables.
La aprobación humana cambió ADR 0006 a `Accepted` y se reconciliaron README,
AGENTS, CHANGELOG y roadmap. Target, horizonte y parámetros cuantitativos
siguen pendientes; ningún dato quedó generado.

Validación final:

- seis ADR `Accepted` y cero `Proposed`;
- cambios limitados a documentación permitida, sin código, tests,
  dependencias, datos o infraestructura;
- 7 TOML parseados y `cop` importó;
- Ruff format/lint y mypy pasaron;
- pytest superó `1` test;
- invariantes documentales y `git diff --check` pasaron;
- el diff completo fue leído;
- reviewers read-only de especificación y cierre reconciliaron sus hallazgos y
  confirmaron cero critical/high/medium abiertos.

No se generaron datos, implementaron capacidades, añadieron dependencias o
hicieron commits. Permanecen abiertos target, umbral DPD, horizonte, población,
estimand, tamaños, prevalencia, ventanas, distribuciones, correlaciones,
licencia, escenarios exactos de drift, thresholds y gates.
