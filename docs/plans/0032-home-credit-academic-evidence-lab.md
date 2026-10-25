# ExecPlan 0032: Home Credit Academic Evidence Lab

## Estado del documento

- Estado: activo.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: versión 2 de la experiencia Home Credit para demostrar desarrollo,
  evaluación y selección académica de modelos.
- Fuente normativa: `AGENTS.md`, `PLANS.md`,
  `docs/plans/0031-home-credit-decision-lab.md` y la solicitud explícita de
  hacer visible la capacidad académica del flujo.

Este plan propone trabajo nuevo. No autoriza todavía su implementación ni
convierte resultados académicos en una decisión de producción.

## Propósito y resultado observable

La versión actual muestra principalmente una tabla de resultados y tarjetas de
política. La versión 2 debe permitir que una persona siga la evidencia desde
los datos hasta la política seleccionada:

```text
dataset y target
  → contrato y splits
  → agregaciones y features
  → búsqueda de candidatos
  → estabilidad de cross-validation
  → validación y calibración
  → política bajo capacidad limitada
```

Al abrir `Home Credit Decision Lab`, el usuario debe poder responder:

1. ¿Qué contiene el dataset y qué target se está modelando?
2. ¿Qué información se convirtió en features y qué quedó fuera?
3. ¿Cómo se probaron los candidatos y con qué métrica se eligió el modelo?
4. ¿Qué diferencia existe entre train-CV y validation?
5. ¿Cómo cambia la política cuando cambia la capacidad de revisión?
6. ¿Qué afirmaciones no permite hacer este benchmark estático?

El test final debe seguir cerrado y cada resultado debe conservar el estado
`academic_static_benchmark_only`.

## Base verificada

Inspección ejecutada en el repositorio el 2026-10-24:

- `src/cop/serving/home_credit.py` expone un resumen read-only con snapshot,
  modelos, trial seleccionado, métricas de validation y política.
- `/api/home-credit` existe y consume artefactos locales cacheados; no entrena
  ni abre el test.
- `runs/home-credit-static/model-lab-results.json` contiene candidatos,
  parámetros, métricas por fold, medias, desviaciones y validation de Logistic
  Regression y LightGBM.
- `runs/home-credit-static/policy-results.json` contiene capacidades 1%, 5%,
  10% y 20%, precision, recall, lift, casos revisados y defaults encontrados.
- `data/processed/home-credit-static/manifest.json` contiene el tamaño del
  snapshot, features y estrategia de split entity-disjoint.
- `app/web/index.html` muestra actualmente una tabla de modelos y tarjetas de
  política para Home Credit, pero no gráficos académicos específicos de esta
  vertical.
- `app/web/app.js` tiene visualizaciones Plotly y una narrativa académica más
  completa para UCI, pero Home Credit sólo usa `renderHomeCredit` con HTML de
  resumen.
- La validación histórica registrada en el plan 0031 indica `131 passed`,
  Ruff, mypy y `git diff --check` correctos antes de este plan.

No se afirma que exista todavía una curva de calibración Home Credit, una
explicación de feature importance, un endpoint de caso Home Credit o un chart
de búsqueda Home Credit en la aplicación. Los artefactos de modelo sí
contienen evidencia de trials y políticas que puede exponerse.

## Alcance

### Backend y contrato analítico

- Extender `HomeCreditService` con una respuesta académica estable, o crear un
  endpoint read-only específico `/api/home-credit/academic`, sin romper la
  respuesta existente de `/api/home-credit`.
- Exponer, con nombres explícitos y estado de evidencia:
  - procedencia, target, uso autorizado y limitaciones;
  - filas, prevalencia, train/validation/test y split strategy;
  - grupos de features derivados del manifest y su explicación;
  - candidatos, parámetros, ranking, CV mean, CV std y validation;
  - capacidades 1%, 5%, 10% y 20%;
  - estado `test_status: unopened`.
- Añadir calibración de validation para Home Credit sólo si se puede calcular
  desde predicciones locales existentes sin reentrenar ni abrir test.
- Mantener separadas las funciones de lectura de artefactos, métricas y HTTP.

### Frontend Home Credit V2

Construir una secuencia de secciones dentro de la pestaña Home Credit:

1. **Academic question**
   - target en lenguaje claro;
   - qué significa una probabilidad;
   - advertencia de benchmark estático.
2. **Dataset and evidence boundary**
   - gráfico de composición train/validation/test;
   - prevalencia validation frente a población revisada;
   - explicación de por qué el test permanece cerrado.
3. **Feature construction**
   - diagrama o timeline de application, bureau, previous application e
     installments/payments hacia agregados;
   - tabla o tarjetas con familias de features y exclusiones audit-only;
   - nota explícita de que agregación no implica causalidad.
4. **Model development**
   - gráfico de trials con CV Average Precision y barras de variación;
   - Logistic Regression y LightGBM distinguibles por color y forma;
   - trial seleccionado destacado;
   - tooltip con parámetros y fold variation.
5. **Validation interpretation**
   - comparación separada de AP, ROC-AUC, Brier y Log Loss;
   - explicación de qué responde cada métrica;
   - calibración si la evidencia está disponible;
   - diferencia visual entre train-CV y validation.
6. **Capacity policy**
   - gráfico compartido o small multiples para precision, recall y lift según
     1%, 5%, 10% y 20%;
   - marcador del punto 10% usado en el resumen actual;
   - explicación “más cobertura implica revisar más casos y cambia la
     precisión”.
7. **Academic conclusion**
   - conclusión determinista basada en la métrica primaria declarada;
   - limitaciones y claims prohibidos;
   - enlace a los artefactos y estado del test.

Los charts pueden compartir componentes Plotly genéricos, pero cada vertical
debe tener un adaptador de datos y un título/contexto propio. Reutilizar la
implementación visual no debe mezclar datasets, métricas ni significados.

### UX y accesibilidad

- Mantener Home Credit como pestaña principal y UCI como referencia separada.
- Incorporar navegación interna de la evidencia sin convertirla en un wizard
  obligatorio.
- Usar divulgación progresiva para parámetros y notas metodológicas.
- Mantener tooltips, texto alternativo equivalente y estados de carga/error.
- Evitar barras o anotaciones solapadas; leyendas debajo cuando reduzcan el
  área útil del chart.
- Mantener el toggle de idioma existente y añadir traducciones para todos los
  textos nuevos.

### Tests y documentación

- Tests unitarios para el contrato académico y la transformación de artefactos.
- Tests de API para endpoint, estado `unopened`, trial seleccionado y ausencia
  de apertura del test.
- Tests estáticos del frontend para secciones, chart containers y textos
  académicos esenciales.
- Actualizar README o CHANGELOG únicamente después de implementar y verificar
  la capacidad real.

## Fuera de alcance

- Abrir, seleccionar, calibrar o tunear usando el test final.
- Reclamar estabilidad temporal: el archivo Home Credit clásico no contiene
  timestamp de aplicación defendible.
- Añadir Optuna, MLflow, Prefect, Docker Compose o infraestructura cloud como
  parte de esta mejora visual/analítica.
- Crear explicaciones causales o de fairness no soportadas por los artefactos.
- Introducir SHAP o feature importance hasta definir una metodología y tests
  que no confundan asociación con causalidad.
- Crear un endpoint productivo o una decisión crediticia real.
- Sustituir la vertical UCI ni mezclar sus charts o resultados en Home Credit.

## Decisiones

### Aceptadas

- Home Credit permanece como benchmark académico estático.
- LightGBM y Logistic Regression son los modelos actuales verificables.
- Average Precision es la métrica primaria de selección registrada en el
  experimento actual.
- El test permanece cerrado y la política se evalúa en validation.
- La API seguirá read-only y consumirá artefactos cacheados.

### Pendientes

- Si la calibración Home Credit se incorpora en esta versión o se deja como
  milestone posterior si faltan predicciones/artifactos reproducibles.
- La taxonomía exacta de las 44 features en familias explicables para la UI.
- Si el gráfico de composición debe mostrar sólo filas o también prevalencia.
- El nivel de detalle deseado para el diagrama de joins/agregaciones.

### Propuestas

- Añadir primero el endpoint académico compuesto y generar todos los charts a
  partir de él para evitar que el frontend lea artefactos directamente.
- Usar un gráfico de puntos con barras de error para trials y small multiples
  para métricas con escalas diferentes.
- Usar líneas de precision/recall/lift para capacidad, con un marcador
  vertical o anotación en 10%.
- Implementar calibración sólo después de demostrar que sus bins proceden de
  validation y no de test.

## Seguridad y restricciones

- No incluir filas individuales, IDs o PII en la interfaz.
- Mantener audit-only fuera de inputs y fuera de explicaciones que sugieran
  uso decisional.
- No generar datos ficticios para completar charts faltantes; mostrar estado
  de ausencia de evidencia.
- Conservar las limitaciones: static benchmark, no temporal stability, no
  production approval, no real-credit claim.
- El endpoint debe validar rutas de artefactos mediante la configuración
  existente y no aceptar paths arbitrarios del cliente.

## Plan de ejecución

### Wave 1 — contrato y evidencia backend

1. Auditar el manifest, baseline, model-lab y policy JSON completos.
2. Definir el schema de `HomeCreditAcademicEvidence` en el servicio read-only.
3. Implementar el endpoint o extensión backward-compatible.
4. Añadir tests de contrato, test cerrado y valores de selección.

### Wave 2 — data story

1. Añadir dataset/split/prevalence evidence.
2. Añadir feature-family metadata derivada de fuentes verificables.
3. Añadir copy educativo y estados de ausencia de evidencia.
4. Verificar que ningún texto sugiera temporalidad o causalidad.

### Wave 3 — model development charts

1. Crear adaptadores de datos para trial search, validation comparison y
   calibration.
2. Implementar el chart de trials con error bars y selección resaltada.
3. Implementar métricas en small multiples con escalas explícitas.
4. Añadir tooltips y notas interpretativas cerca de cada gráfico.

### Wave 4 — policy and conclusion

1. Implementar chart de capacidad para ambos modelos.
2. Conectar 10% con el resumen existente sin duplicar cálculos.
3. Añadir conclusión académica determinista y limitaciones.
4. Añadir navegación interna, responsive y traducciones.

### Wave 5 — integración y cierre

1. Ejecutar la app real y revisar Home Credit en desktop y viewport reducido.
2. Verificar que UCI continúa aislado y funcional.
3. Ejecutar validaciones completas.
4. Hacer revisión read-only de alcance y allowlist.
5. Mantener este plan en `activo` hasta que todas las validaciones sean
   observables y cerrar sólo con autorización explícita.

## Motion-graphic scrollytelling direction

The Home Credit experience should behave like an explanatory evidence story,
not a dashboard where all charts compete at once. The scroll sequence is:

```text
01 Context → 02 Data → 03 Features → 04 Model iterations
→ 05 Validation → 06 Policy → 07 Academic conclusion
```

Each chapter has a stable layout:

- **Narrative column:** one question, one short explanation, and one visible
  conclusion.
- **Evidence stage:** the chart or animated diagram for that question.
- **Checkpoint:** a compact “what we learned” statement that remains visible
  after the transition.

Motion rules:

- Use restrained opacity, position, and scale transitions; no decorative
  animation that changes the meaning of a metric.
- Animate only when a section enters the viewport, with reduced-motion support
  that presents the final state immediately.
- Keep the active chapter in the navigation and provide keyboard-accessible
  previous/next controls.
- Preserve chart hover, legend, exact values, and textual interpretation while
  the animation is running.
- Never animate a metric from one value to another without labeling the source
  and destination state.

### Iteration story

The model-development chapter must show the project improving through
observable iterations:

1. Baseline: Logistic Regression and first LightGBM candidate.
2. Controlled trials: parameter change, CV mean, fold variation and rank.
3. Selected candidate: why the declared primary metric chose it.
4. Validation check: what held outside train-CV.
5. Policy check: what changes under review capacity.

Future model improvements should add a new iteration record rather than
replace the old one. Each record should include model version/trial id,
parameters, fit split, selection metric, validation metrics, artifact status,
and a short reason for acceptance or rejection. This makes successful and
unsuccessful iterations visible without claiming that the latest model is
automatically better.

## Wave and task execution contract

The workflow manifest for this plan is
`docs/workflows/0032-home-credit-academic-evidence-lab.yaml`. Tasks are
bounded by path allowlists and may only start after their dependencies are
verified complete. The coordinator assigns tasks to separate agents where
their scopes do not overlap; the reviewer is read-only and the milestone
finisher never commits.

### Wave 1 — Story architecture and evidence contract

- **HC32-001 — Audit Home Credit evidence sources** (`data_ml`): map every
  available field in the manifest, baseline, model-lab, and policy reports to
  one chapter; document missing evidence. Depends on none.
- **HC32-002 — Design the scroll narrative** (`coordinator`): define chapter
  questions, transitions, checkpoints, reduced-motion behavior, and responsive
  fallback. Depends on HC32-001.
- **HC32-003 — Review claims and boundaries** (`reviewer`): verify that the
  proposed narrative does not imply temporal stability, causality, fairness,
  production approval, or test usage. Depends on HC32-001 and HC32-002.

Wave exit: the story map and evidence matrix are approved for implementation.

### Wave 2 — Academic evidence API

- **HC32-004 — Build the Home Credit academic evidence contract** (`mlops`):
  expose dataset, feature families, split, trials, validation, policy and
  evidence-status data without breaking `/api/home-credit`. Depends on HC32-003.
- **HC32-005 — Add iteration and chart-data tests** (`data_ml`): verify that
  trial parameters, CV variation, validation metrics, capacities and selected
  state are preserved exactly. Depends on HC32-004.
- **HC32-006 — API and artifact review** (`reviewer`): read-only check that
  endpoints use cached artifacts, keep test closed, and reject unsupported
  missing evidence instead of inventing values. Depends on HC32-004 and
  HC32-005.

Wave exit: the frontend can consume one versioned academic evidence response.

### Wave 3 — Scroll shell and motion system

- **HC32-007 — Implement chapter navigation and scroll state** (`coordinator`):
  add semantic chapters, active-section navigation, checkpoint states, keyboard
  controls, and reduced-motion fallback. Depends on HC32-006.
- **HC32-008 — Implement data and feature chapters** (`coordinator`): show
  dataset composition, split boundary, target context, source tables,
  aggregations, and exclusions with explanatory transitions. Depends on HC32-007.
- **HC32-009 — Implement model-iteration chapter** (`coordinator`): animate
  trial ranking and selected candidate while keeping parameter and fold details
  available in a table/tooltip. Depends on HC32-007.

Wave exit: a user can scroll from dataset to selected model and understand the
meaning of each transition without opening a notebook.

### Wave 4 — Validation, policy, and iteration comparison

- **HC32-010 — Implement validation and calibration evidence** (`data_ml`):
  expose and visualize validation metrics; add calibration only when
  validation predictions are verifiably available. Depends on HC32-006.
- **HC32-011 — Implement capacity policy motion** (`coordinator`): animate
  1%, 5%, 10% and 20% review capacity and show precision/recall/lift changes
  for both models. Depends on HC32-010.
- **HC32-012 — Add future iteration comparison state** (`mlops`): define the
  UI/API shape for appending a challenger iteration and showing metric deltas
  without changing promotion or rollback policy. Depends on HC32-006.
- **HC32-013 — Review the complete evidence story** (`reviewer`): verify
  train-CV, validation, policy and test states are not conflated and that
  animation does not hide required values. Depends on HC32-008, HC32-009,
  HC32-011 and HC32-012.

Wave exit: the full story demonstrates current model development and leaves a
tested seam for later model improvement work.

### Wave 5 — Accessibility, regression, and closure

- **HC32-014 — Responsive, language, and accessibility pass** (`coordinator`):
  validate English-first copy, Spanish toggle coverage, keyboard navigation,
  chart text equivalents, responsive layout, and reduced motion. Depends on
  HC32-013.
- **HC32-015 — Run milestone validation** (`milestone_finisher`): run the
  fixed test/lint/type/diff checks from the allowlist and prepare closure only
  when the reviewer has no critical findings. Depends on HC32-014.

Wave exit: all acceptance criteria are evidenced; commit remains blocked until
explicit human authorization.

## Validación y criterios de aceptación

Backend:

```bash
.venv/bin/python -m pytest -q tests/unit/test_home_credit_service.py tests/integration/test_api.py
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
git diff --check
```

Producto:

- `/api/home-credit` mantiene compatibilidad y el nuevo contrato se devuelve
  sin abrir test.
- La pestaña Home Credit contiene al menos un gráfico de datos/splits, uno de
  trials, uno de métricas o calibración y uno de capacidad.
- Cada gráfico tiene título, unidades, leyenda, tooltip y explicación textual.
- El trial seleccionado y la razón de selección son visibles.
- Train-CV, validation y test no se mezclan visualmente.
- La aplicación no muestra espacios vacíos silenciosos: carga, error y falta
  de evidencia tienen estado visible.
- UCI conserva sus gráficos y flujo de casos.
- El frontend sigue siendo English-first y el toggle traduce los textos nuevos.

## Registro de progreso

- [x] Inspección del estado Home Credit actual.
- [x] Identificación de la carencia: summary cards/table without academic
  charts or evidence chain.
- [x] Motion-graphic scrollytelling direction and wave/task workflow drafted.
- [x] Implementar y probar el contrato académico backend.
- [x] Implementar data/split evidence.
- [x] Implementar feature construction evidence.
- [x] Implementar model-development charts.
- [x] Mostrar explícitamente el resultado de la iteración: baseline AP,
  candidato seleccionado y cambio observado bajo la métrica primaria.
- [x] Exponer esa comparación en el contrato `/api/home-credit/academic` para
  mantener la afirmación reproducible fuera del frontend.
- [x] Implementar trial table, prevalence summary, and audit-only boundary evidence.
- [x] Implementar validation/calibration evidence from cached validation predictions.
- [x] Implementar capacity-policy chart.
- [x] Añadir estados visibles de carga, éxito, error y evidencia ausente para
  evitar charts académicos vacíos sin explicación.
- [x] Implementar English-first copy, Spanish toggle, reduced-motion support,
  keyboard focus states, responsive rules and a no-IntersectionObserver
  visibility fallback.
- [ ] Completar revisión visual responsive and accessibility in a real browser
  viewport.
- [ ] Ejecutar validación completa y revisión read-only.

### Validación ejecutada el 2026-10-24

- `pytest -q tests/integration/test_api.py`: 5 passed.
- `ruff format --check .`: passed.
- `ruff check .`: passed.
- `mypy src tests scripts`: passed.
- `git diff --check`: passed.
- The live FastAPI demo responded on the approved local service port with
  `/health`, `/api/home-credit/academic`, and the Home Credit story shell.
- Browser-level visual inspection remains pending because no browser runtime
  is available in the current environment.

## Hallazgos inesperados

- El reporte Home Credit ya contiene suficiente evidencia para trials y
  capacidad, pero la API actual la reduce a una tabla y tarjetas de 10%.
- El archivo de policy contiene cuatro capacidades y ambos modelos; no es
  necesario recalcular esa política para dibujar la primera versión.
- La incorporación de calibración requiere verificar que existan predicciones
  de validation reutilizables antes de presentarla como evidencia.
- Los charts UCI no deben copiarse sin un adaptador: la semántica de sus
  endpoints y el target de Home Credit son diferentes.

## Registro de decisiones del plan

- 2026-10-24: se propone una versión académica Home Credit separada de UCI;
  la reutilización será de componentes visuales, no de datos ni significado.
- 2026-10-24: se prioriza hacer visible el proceso de selección y política
  antes de añadir nuevas familias de modelos.

## Resultados y retrospectiva

Implementado parcialmente el 2026-10-24:

- `HomeCreditService.academic_evidence()` y `/api/home-credit/academic` exponen
  dataset, split boundary, feature groups, model iterations, validation,
  policy, validation calibration bins, and future iteration contract.
- Home Credit now contains seven scroll chapters with active-section motion,
  reduced-motion CSS fallback, split chart, feature provenance cards, trial
  comparison, validation metric chart, capacity precision/recall chart, lift
  chart, and academic conclusion.
- Live evidence verified: four feature groups, six trial iterations, four
  policy capacities, and `test_status=unopened`.
- The iteration chapter now shows exact parameters, CV fold variation, rank,
  and selected validation AP in a table; the data chapter shows prevalence and
  audit-only exclusions.
- Full validation returns `131 passed`; Ruff format/check, mypy, and
  `git diff --check` pass.

Remaining: independent read-only review, responsive/accessibility review,
language coverage for dynamic chart copy, and milestone closure.

## Version-control allowlist

Tracked files or directories allowed:

- docs/plans/0032-home-credit-academic-evidence-lab.md
- docs/workflows/0032-home-credit-academic-evidence-lab.yaml
- src/cop/serving/home_credit.py
- src/cop/api.py
- app/web/app.js
- app/web/index.html
- app/web/styles.css
- app/web/language.js
- tests/unit/test_home_credit_service.py
- tests/integration/test_api.py

Generated artifacts forbidden:

- data/**
- runs/**
- models/**
- reports/**
- .venv/**

Expected commit message:

- feat(home-credit): expose academic evidence lab
