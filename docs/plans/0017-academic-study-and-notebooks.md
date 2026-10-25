# ExecPlan 0017: estudio académico, notebooks y frontend analítico

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: demostrar dominio académico sobre los baselines UCI y presentar la
  evidencia en notebooks y Streamlit.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y alcance confirmado por el usuario.

## Propósito y resultado observable

El proyecto produce un estudio reproducible con cross-validation sobre train,
comparación en validation, calibración, threshold sweep y predicciones OOF. La
app y los notebooks convierten esa evidencia en una presentación analítica con
gráficas y motion graphics explicativos.

## Base verificada

Existe un baseline UCI con Logistic Regression y LightGBM, una app Streamlit y
artefactos locales de entrenamiento. No existían cross-validation académica ni
notebooks.

## Alcance

- `src/cop/evaluation/academic.py`.
- `scripts/run_academic_study.py`.
- `app/streamlit_app.py` y extra Plotly.
- `notebooks/`.
- tests, README y CHANGELOG.

## Fuera de alcance

Optuna, redes neuronales, nuevo dataset, serving productivo, API, MLflow,
monitoring operacional, promoción, rollback y claims de producción.

## Decisiones

### Aceptadas

OOF se genera solo desde train; validation se usa para la comparación final; el
test permanece cerrado. La calibración se aplica a LightGBM como experimento
descriptivo. Plotly se usa para gráficos y motion graphics, sin toolbar ni
scroll zoom en la app.

### Pendientes

La elección de champion, los gates cuantitativos y el threshold productivo no
se deciden en este milestone.

### Propuestas

No aplica.

## Seguridad y restricciones

No se versionan datos, modelos ni runs. Los notebooks no deben abrir el test ni
usar atributos `audit_only` como inputs.

## Plan de ejecución

1. Implementar el estudio y separar OOF de validation.
2. Añadir notebooks narrativos y frontend académico con Plotly.
3. Ejecutar estudio real sobre el snapshot local.
4. Validar app, notebooks como JSON y suite completa.

## Validación y criterios de aceptación

```bash
.venv/bin/python scripts/run_academic_study.py --folds 5
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
.venv/bin/python -c "import json, pathlib; [json.loads(p.read_text()) for p in pathlib.Path('notebooks').glob('*.ipynb')]"
git diff --check
```

La app debe renderizar las dos vistas mediante Streamlit AppTest sin
excepciones y el estudio debe dejar `test_status=unopened`.

## Registro de progreso

- [x] 2026-10-24: estudio CV/calibración/threshold implementado.
- [x] 2026-10-24: OOF y validation separados y estudio real ejecutado.
- [x] 2026-10-24: dos notebooks narrativos generados.
- [x] 2026-10-24: frontend actualizado con Plotly y motion graphics.
- [x] 2026-10-24: validación final, ejecución de notebooks y staging preparados.

## Hallazgos inesperados

La primera ejecución intentó mezclar OOF de train con validation; se corrigió
separando ambos artefactos para evitar una comparación inválida.

## Registro de decisiones del plan

- 2026-10-24: el motion graphic se limita al threshold lab para representar un
  trade-off metodológico real, no una animación decorativa.

## Resultados y retrospectiva

El estudio real produjo LightGBM CV ROC-AUC `0.7724 ± 0.0065`; la versión
calibrada obtuvo validation Brier `0.13374` frente a `0.13418` del LightGBM
sin calibrar. Estos resultados son descriptivos y no seleccionan champion.

La validación final quedó verificada con 104 tests, Ruff, mypy, parseo JSON de
los notebooks y Streamlit AppTest para las dos vistas y la predicción. Ambos
notebooks también se ejecutaron con `nbconvert`; el artefacto de test mantiene
`test_status=unopened`.

## Version-control allowlist

Tracked files or directories allowed:

- CHANGELOG.md
- README.md
- app/streamlit_app.py
- docs/plans/0017-academic-study-and-notebooks.md
- notebooks/
- pyproject.toml
- scripts/run_academic_study.py
- src/cop/evaluation/academic.py
- tests/integration/test_academic_study.py

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(research): add reproducible academic study and notebooks
