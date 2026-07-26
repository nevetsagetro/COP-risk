# ExecPlan 0008: tercera y última búsqueda dirigida de datasets reales

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-26.
- Última actualización: 2026-07-26.
- Responsable: agente `coordinator`.
- Alcance: Milestone 4C, última investigación documental real.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato, protocolo, checklist y
  ExecPlans 0006-0007.

## Propósito y resultado observable

Evaluar como máximo tres candidatos reales con IDs, tiempo y outcome, y decidir
si alguno merece cuarentena. Se evaluaron PKDD’99 Czech, Kiva y LendingClub.
Ninguno supera el gate; se detiene la búsqueda y se recomienda bootstrap
sintético principal con posible variante híbrida futura.

## Base verificada

Inspección del 2026-07-26:

- `HEAD` inicial es `a8e4b2cf39a8e6a74e65e4caa6379012a4d4fd7f`;
- `git status --short` inicial no produjo salida;
- contrato, protocolo, checklist y ExecPlans 0001-0007 están versionados;
- SFLLD sigue `Reject` y Home Credit Model Stability `Needs clarification`;
- no existe dataset aprobado, código de datos, split, modelo o monitoring;
- datos locales ignorados de SFLLD no se leyeron o modificaron.

## Alcance

- `docs/dataset-candidates.md`;
- `docs/dataset-selection-rationale.md`;
- este ExecPlan.

## Fuera de alcance

Descargas, cuentas, aceptación de términos, cuarentena, ingesta, código, datos
sintéticos, features, splits, notebooks, modelos, MLflow, Prefect, Docker,
Evidently, dependencias, ADR o commit.

## Decisiones

### Aceptadas aplicables

Solo datos sintéticos o públicos anonimizados; PII/procedencia incierta son
rechazos; atributos protegidos nunca inputs; split antes de fit; test intacto;
drift no promociona. La fuente y target siguen pendientes.

### Pendientes

Aceptación de enfoque sintético/híbrido, contrato concreto, target, entidad,
población, features, métricas, gates y mecanismo de snapshot.

### Propuesta

Finalizar búsqueda real y proponer sintético determinista como bootstrap
principal. Una capa real futura queda condicionada a aceptación completa.

## Seguridad y restricciones

Solo fuentes primarias. No mirrors/Kaggle como autoridad, endpoints de
descarga, términos aceptados o credenciales. Términos desconocidos bloquean.
No se convierte accesibilidad histórica en licencia.

## Plan de ejecución

1. Inspeccionar Git, normativa y resultados anteriores.
2. Evaluar un candidato académico relacional.
3. Evaluar Kiva con API/snapshots y terms oficiales.
4. Evaluar LendingClub solo desde fuente oficial.
5. Aplicar regla de parada tras tres candidatos.
6. Documentar clasificación y recomendación sintética/híbrida.
7. Ejecutar baseline, allowlist y diff review.
8. Solicitar reviewer final read-only y corregir hallazgos.

## Validación y criterios de aceptación

```bash
test -s docs/dataset-candidates.md
test -s docs/dataset-selection-rationale.md
test -s docs/plans/0008-final-real-dataset-search.md
rg -n "PKDD|Kiva|LendingClub" docs/dataset-candidates.md
rg -n "Eligible for quarantine inspection|Needs clarification|Reject" \
  docs/dataset-candidates.md docs/dataset-selection-rationale.md
rg -n "sintétic|híbrid" docs/dataset-selection-rationale.md
test -z "$(git diff --name-only | grep -Ev '^(docs/dataset-candidates.md|docs/dataset-selection-rationale.md)$')"
test -z "$(git ls-files --others --exclude-standard | grep -Ev '^docs/plans/0008-final-real-dataset-search.md$')"
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

Cierra al evaluar tres candidatos, decidir parar, recomendar siguiente enfoque,
mantener cero datos/código nuevos y reviewer sin critical/high.

## Registro de progreso

- [x] 2026-07-26: inspección obligatoria sobre árbol limpio.
- [x] 2026-07-26: tres candidatos y no más investigados.
- [x] 2026-07-26: gates, parada y recomendación documentados.
- [x] 2026-07-26: baseline y alcance validados.
- [x] 2026-07-26: reviewer final sin critical/high; dos medium y un low
  corregidos y reverificados.

## Hallazgos inesperados

- PKDD’99 tiene el esquema buscado, pero no licencia explícita verificable.
- Kiva define default de forma flexible y prohíbe publicar delinquency/default.
- LendingClub ya no ofrece el artefacto histórico abierto/licenciado buscado.

## Registro de decisiones del plan

- 2026-07-26: se detiene la búsqueda al tercer candidato.
- 2026-07-26: no se usa mirror para cubrir fuentes oficiales ausentes.
- 2026-07-26: se recomienda sintético principal; no se acepta ni implementa.
- 2026-07-26: resultados anteriores permanecen intactos.

## Resultados y retrospectiva

Se evaluaron exactamente tres candidatos y ninguno superó el gate. PKDD’99
queda `Needs clarification`; Kiva y LendingClub quedan `Reject`. La búsqueda
real se detiene y se propone bootstrap sintético determinista principal, con
una capa real futura solo tras aceptación completa.

Validación final:

- 7 TOML parseados; `cop` importó;
- Ruff format/lint y mypy pasaron;
- pytest superó `1` test;
- allowlist limitado a tres documentos;
- `git diff --check` y whitespace del archivo nuevo correctos;
- reviewer read-only sin critical/high; se corrigieron la madurez de PKDD, el
  alcance exacto de Terms Kiva y la cabecera de ronda.

No se descargó dato, aceptó término, creó cuenta, implementó código o creó ADR.
Resultados anteriores permanecen intactos y no existe dataset aprobado.
