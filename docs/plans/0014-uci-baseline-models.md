# ExecPlan 0014: baseline académico UCI y cierre automatizado

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-08-02.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: Milestone 9, baseline académico y cierre seguro de milestones.
- Fuente normativa: aprobación humana, `AGENTS.md`, ADR 0008, ADR 0009 y
  `PLANS.md`.

## Propósito y resultado observable

Entrenar Logistic Regression y LightGBM reproducibles con parámetros fijos
sobre UCI, separando development de una única finalización del test, y añadir
un finisher que valide y stagee solo una allowlist sin commit automático.

## Base verificada

- `HEAD`: `5f549ec510c1c3928888966fa4b5d3467eb069a3`;
- working tree inicial limpio y HEAD importable desde worktree limpio;
- vertical UCI sin imports hacia `cop.data.synthetic`;
- snapshot v2 académico y splits 21000/4500/4500 vigentes;
- sin modelos, MLflow, Optuna, imbalanced-learn o dependencias ML instaladas.

## Alcance

Agente y script finisher, reglas de allowlist, configuración/pipelines/métricas
del baseline, CLI en dos fases, artefactos locales ignorados, tests y model card.

## Fuera de alcance

Resampling, tuning, early stopping, MLflow, Prefect, serving, Evidently,
selección de winner/champion, métrica primaria, threshold optimizado y claims
temporales, productivos, de fairness o crédito real.

## Decisiones

### Aceptadas

Se usan exactamente 19 features; PAY_0 y PAY_2–PAY_6 son categóricas;
`missing_policy=fail`; threshold descriptivo 0.5; ambos modelos y parámetros se
congelan antes del test. ADR 0008 limita el uso a baseline académico.

### Pendientes

No se decide ganador, champion, métrica primaria, gate o promoción.

### Propuestas

No aplica.

## Seguridad y restricciones

Development no abre test ni audit_only. Finalización crea una claim exclusiva
después de verificar hashes y antes de abrir test; no permite reintento ni
sobrescritura. Artefactos de runs permanecen ignorados. El finisher bloquea
datos, secretos y artefactos aunque aparezcan en la allowlist.

## Plan de ejecución

1. Implementar agente y finisher con tests Git temporales.
2. Actualizar convención de planes y reglas de cierre.
3. Añadir dependencias permitidas y baseline train-only.
4. Ejecutar development, congelar artefactos y finalizar test una vez.
5. Validar, revisar, ejecutar finisher check/stage y mostrar staged diff.

## Validación y criterios de aceptación

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/pytest
git diff --check
git ls-files data models artifacts predictions runs reports/local
python3 scripts/finish_milestone.py --plan docs/plans/0014-uci-baseline-models.md --check
python3 scripts/finish_milestone.py --plan docs/plans/0014-uci-baseline-models.md --stage
```

## Registro de progreso

- [x] 2026-08-02: inspección limpia y tres revisiones read-only de diseño.
- [x] 2026-08-02: agente, finisher y tests Git temporales.
- [x] 2026-08-02: allowlist obligatoria añadida al plan y convención.
- [x] 2026-08-02: baseline y tests ML.
- [x] 2026-08-02: development y única finalización real del test.
- [x] 2026-08-02: reviewer final sin hallazgos critical/high.
- [x] 2026-08-02: finisher `--check` completo sin errores.
- [x] 2026-08-02: finisher `--stage` preparado tras el check final; diff
  staged revisado sin commit.
- [x] 2026-10-24: validación final reproducida en `.venv`: Ruff format/check,
  mypy, 102 tests, `git diff --check`, control de datos versionados y
  `finisher --check`, todo correcto.

## Hallazgos inesperados

Los verificadores UCI completos abren el test; no se reutilizan durante
development. El loader de desarrollo verificará metadata y leerá solo
train/validation con filtros explícitos.

La primera revisión final detectó que el manifest de splits exponía conteos de
test en development y dos bypasses del finisher. Se separó metadata congelada
de train/validation, se preservó semántica archivo/directorio y se ampliaron
bloqueos de secretos y formatos de modelos. El staging usa ahora un índice
temporal de preflight.

Una ejecución operativa posterior mostró que invocar el finisher con el Python
del sistema intenta resolver Ruff, mypy y pytest en ese intérprete. El finisher
construye ahora los comandos dinámicamente desde `sys.executable`, comprueba que
las tres herramientas estén instaladas allí y produce un error explícito antes
de tocar el índice si falta alguna. Para este repositorio debe invocarse con
`.venv/bin/python`.

## Registro de decisiones del plan

- 2026-08-02: finalización del test es consumible aun si falla después de crear
  la claim, evitando reapertura adaptativa.
- 2026-08-02: el finisher ejecuta validaciones fijas; nunca comandos extraídos
  del Markdown.

## Resultados y retrospectiva

El run local `uci-baseline-c52cb3e02f0bec92fa6675a21a55af04e73cdd40027762a1c373d98599a299fb`
registró validation y consumió test una vez; una segunda finalización fue
bloqueada. En test, Logistic Regression obtuvo ROC-AUC 0.773572 y average
precision 0.555595; LightGBM obtuvo 0.786889 y 0.568776. Son resultados
descriptivos sin selección. Antes de las correcciones de review pasaron Ruff,
mypy, 90 tests y `git diff --check`; la validación final se repetirá antes del
finisher. LightGBM necesitó `libgomp.so.1`, extraído localmente en la venv por
falta de privilegios de instalación del sistema. Tras las correcciones del
reviewer, la suite alcanzó 98 tests y no quedaron hallazgos critical/high. El
primer cierre detectó un fixture de credencial ficticia; se eliminó el patrón
literal del propio test y el `--check` completo posterior pasó Ruff format,
Ruff check, mypy, 98 tests, `git diff --check` y el control de datos versionados.
La validación final del 2026-10-24 pasó 102 tests y el `finisher --check`; no
quedan tareas dentro del alcance del plan.

## Version-control allowlist

Tracked files or directories allowed:

- .codex/agents/milestone-finisher.toml
- .gitignore
- AGENTS.md
- CHANGELOG.md
- PLANS.md
- README.md
- configs/training/
- docs/model-card-uci-baseline.md
- docs/plans/0014-uci-baseline-models.md
- pyproject.toml
- scripts/__init__.py
- scripts/finish_milestone.py
- scripts/train_uci_baseline.py
- src/cop/evaluation/
- src/cop/features/
- src/cop/training/
- tests/integration/
- tests/unit/

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(model): add reproducible UCI academic baselines and milestone finisher
