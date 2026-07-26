# ExecPlan 0007: segunda búsqueda de datasets candidatos

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-26.
- Última actualización: 2026-07-26.
- Responsable: agente `coordinator`.
- Alcance: Milestone 4B, investigación documental limitada.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato, protocolo, checklist,
  ExecPlan 0006 y ADR 0001-0005.

## Propósito y resultado observable

Evaluar tres alternativas reales tras el rechazo de SFLLD, con fuentes
primarias y énfasis en publicación, target, tiempo, leakage y monitoring.
Credit Risk Model Stability queda `Needs clarification`; Home Credit Default
Risk y Polish Companies Bankruptcy quedan `Reject`. Ninguno supera el gate.

## Base verificada

Inspección del 2026-07-26:

- `HEAD` inicial es `dd71e2ac9ed876a4736b464fad636527a5e90a4b`;
- `git status --short` inicial no produjo salida;
- contrato, protocolo, checklist y ExecPlans 0001-0006 están versionados;
- ExecPlan 0006 y su informe concluyen `Reject` para SFLLD;
- no existe dataset aprobado, split, pipeline, modelo o servicio ML;
- el ZIP SFLLD local ignorado no se leyó o modificó en esta tarea.

## Alcance

- `docs/dataset-candidates.md`;
- `docs/dataset-selection-rationale.md`;
- este ExecPlan.

## Fuera de alcance

Descargas, aceptación de reglas, cuentas, cuarentenas, ingesta, snapshots,
datos sintéticos, features, splits, notebooks, entrenamiento, MLflow, Prefect,
Docker, Evidently, servicios, dependencias, ADR o commit.

## Decisiones

### Aceptadas aplicables

Solo datos sintéticos o públicos anonimizados; PII/procedencia incierta son
rechazos; atributos protegidos nunca inputs; split antes de fit; test intacto;
drift no promociona. Los ADR tecnológicos no prueban implementación.

### Pendientes

Fuente, target, horizonte, entidad, población, features, términos, aprobador,
retención, split, métricas y monitoring operativo.

### Propuesta

Solicitar solo aclaración documental sobre Credit Risk Model Stability. No
autorizar cuarentena hasta verificar permisos y target. No crear ADR.

## Seguridad y restricciones

Solo se consultan páginas/reglas/documentación oficiales y papers originales.
Blogs, notebooks y mirrors no sostienen hechos. Un unknown de términos
permanece bloqueante. No se accede a descargas ni se manejan credenciales.

## Plan de ejecución

1. Inspeccionar Git y normativa, incluida la decisión SFLLD.
2. Consultar fuentes primarias de los dos candidatos Home Credit.
3. Evaluar un tercero con target/licencia documentados.
4. Comparar publicación y requisitos metodológicos.
5. Clasificar sin confundir aclaración, cuarentena y aceptación.
6. Actualizar dos documentos y este ExecPlan.
7. Ejecutar baseline, allowlist y revisar el diff.
8. Solicitar revisión final read-only y corregir hallazgos.

## Validación y criterios de aceptación

```bash
test -s docs/dataset-candidates.md
test -s docs/dataset-selection-rationale.md
test -s docs/plans/0007-second-dataset-search.md
rg -n "FACT|INFERENCE|UNKNOWN|RISK" docs/dataset-candidates.md
rg -n "Needs clarification|Eligible for quarantine inspection|Reject" \
  docs/dataset-candidates.md docs/dataset-selection-rationale.md
rg -n "SFLLD.*Reject|Reject.*SFLLD" \
  docs/dataset-candidates.md docs/dataset-selection-rationale.md
test -z "$(git diff --name-only | grep -Ev '^(docs/dataset-candidates.md|docs/dataset-selection-rationale.md)$')"
test -z "$(git ls-files --others --exclude-standard | grep -Ev '^docs/plans/0007-second-dataset-search.md$')"
.venv/bin/python -c "import pathlib, tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path('.').rglob('*.toml')]"
PYTHONPATH=src .venv/bin/python -c "import cop"
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests
.venv/bin/python -m pytest
git diff --check
git status --short
git diff
```

Termina con comparaciones verificables, ningún candidato que supere el gate,
cero datos/código/dependencias nuevos y reviewer sin critical/high abiertos.

## Registro de progreso

- [x] 2026-07-26: inspección obligatoria sobre árbol limpio.
- [x] 2026-07-26: tres candidatos investigados con fuentes primarias.
- [x] 2026-07-26: comparación, clasificaciones y rationale redactados.
- [x] 2026-07-26: baseline y alcance validados.
- [x] 2026-07-26: reviewer final sin critical/high; dos medium y un low
  corregidos y reverificados.

## Hallazgos inesperados

- Kaggle no expuso el texto completo de reglas específicas sin interacción;
  no se sustituyó con reglas genéricas o evidencia secundaria.
- Credit Risk Model Stability aporta fecha/semana, pero target incompleto.
- Polish tiene licencia/horizontes claros, pero no tiempo/identidad por fila.

## Registro de decisiones del plan

- 2026-07-26: términos no visibles son unknown bloqueante.
- 2026-07-26: facilidad/popularidad no sustituyen el contrato.
- 2026-07-26: SFLLD conserva `Reject`, sin aceptación parcial.

## Resultados y retrospectiva

Tres candidatos fueron comparados con fuentes primarias. Ninguno supera el
gate: Model Stability queda en triage `Needs clarification`, no como resultado
de fase A; Default Risk y Polish quedan `Reject`. SFLLD conserva `Reject`.

Validación final:

- 7 TOML parseados; `cop` importó;
- Ruff format/lint y mypy pasaron;
- pytest superó `1` test;
- allowlist limitado a los tres documentos;
- `git diff --check` y whitespace del archivo nuevo correctos;
- reviewer read-only sin critical/high abiertos; se corrigieron procedencia
  Polish, alcance de CC BY y distinción entre triage y checklist.

No se descargó dataset, aceptó regla, creó cuenta, implementó código o creó
ADR. Sigue sin existir dataset aprobado para entrenamiento.
