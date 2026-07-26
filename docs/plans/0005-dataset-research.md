# ExecPlan 0005: investigación documental de datasets candidatos

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-26.
- Última actualización: 2026-07-26.
- Responsable: agente `coordinator`.
- Alcance: investigación y comparación documental del Milestone 3.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato, protocolo, checklist y
  ADR 0001-0005.

## Propósito y resultado observable

Comparar fuentes documentadas de riesgo de crédito contra el contrato vigente y
proponer un único candidato para posible inspección futura, sin adquirir,
aceptar o transformar datos. El resultado observable son fichas con fuentes,
unknowns, riesgos, checklist y una recomendación humana pendiente.

## Base verificada

Inspección realizada el 2026-07-26:

- `HEAD` es `eeb87621c0d921007f020c5d00eac10661a924b9` en `main`;
- `git status --short` no produjo salida;
- existen cinco ADR y todos tienen `Status: Accepted`;
- contrato, protocolo, checklist y ExecPlan 0004 están versionados;
- `src/cop` conserva únicamente el paquete mínimo;
- no se encontraron archivos bajo `data`, `models` o `notebooks`, ni
  snapshots, pipelines o código ML.

## Alcance

- `docs/dataset-candidates.md`;
- `docs/dataset-selection-rationale.md`;
- este ExecPlan;
- reconciliación documental del Milestone 3 en el roadmap 0001.

## Fuera de alcance

Descargar o inspeccionar datos, usar APIs, aceptar términos, crear cuarentena o
snapshots, generar hashes, notebooks, EDA, ingesta, validadores, datos
sintéticos, preprocessing, entrenamiento, dependencias, servicios,
orquestación, tracking, serving, Docker o monitoring implementado.

## Decisiones

### Aceptadas aplicables

Solo datos sintéticos o públicos anonimizados, sin PII; atributos protegidos
nunca como inputs; split antes de cualquier fit; test intacto; drift no
promociona. Los cinco ADR tecnológicos no demuestran implementación.

### Propuesta de este plan

Freddie Mac SFLLD Sample es el candidato mejor documentado para solicitar una
decisión humana previa. Su estado permanece `Needs controlled inspection`.
UCI Taiwan, South German y Fannie Mae quedan `Reject` bajo la evidencia actual.

### Pendientes

No se decide fuente, target, horizonte, unidad de predicción, features,
release, términos aceptados, cuarentena, responsable, retención, métricas o
thresholds. No se crea ADR.

## Seguridad y restricciones

- Solo se consultan páginas, términos, guías y papers.
- No se abren endpoints o archivos de descarga.
- Una licencia no explícita se marca `UNKNOWN` y bloquea adquisición.
- Masking o “anonymized” no demuestran riesgo nulo de reidentificación.
- Mirrors y Kaggle no sustituyen permiso o procedencia del propietario.
- Cada factual claim debe tener una fuente primaria cercana.

## Plan de ejecución

1. Inspeccionar Git y leer toda la documentación normativa y agentes.
2. Delegar cuatro análisis read-only de contrato, metodología, licencia y
   monitoring.
3. Verificar al menos tres candidatos con fuentes primarias.
4. Consolidar hechos, inferencias, unknowns, riesgos y fase A de checklist.
5. Redactar comparación, rationale, ExecPlan y reconciliar roadmap.
6. Ejecutar checks estructurales y baseline; revisar el diff completo.
7. Solicitar revisión final read-only y corregir solo hallazgos del milestone.
8. Registrar resultados y cerrar el plan.

## Validación y criterios de aceptación

```bash
test -s docs/dataset-candidates.md
test -s docs/dataset-selection-rationale.md
test -s docs/plans/0005-dataset-research.md
rg -n "FACT|INFERENCE|UNKNOWN|RISK" docs/dataset-candidates.md
! rg -n "Status: Accepted|Resultado: Accepted" \
  docs/dataset-candidates.md docs/dataset-selection-rationale.md
test -z "$(git diff --name-only -- pyproject.toml src tests docs/decisions .codex docker-compose.yml)"
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

Los tres archivos nuevos se revisarán además con
`git diff --no-index --check /dev/null <archivo>`.

## Registro de progreso

- [x] 2026-07-26: inspección y lectura completas sobre working tree limpio.
- [x] 2026-07-26: cuatro análisis independientes read-only recibidos.
- [x] 2026-07-26: fuentes primarias y cuatro candidatos consolidados.
- [x] 2026-07-26: comparación, rationale y ExecPlan redactados.
- [x] 2026-07-26: roadmap reconciliado; checks estructurales, baseline,
  whitespace y diff completo revisados.
- [x] 2026-07-26: revisión final read-only completada; seis hallazgos
  documentales corregidos y reverificados sin findings critical, high o
  medium pendientes.

## Hallazgos inesperados

- Freddie Mac tiene mejor encaje metodológico, pero sus términos específicos
  requieren una confirmación humana sobre resultados públicos no comerciales;
  por prudencia no se clasifica directamente como Eligible.
- UCI Taiwan tiene una discrepancia documental de 30.000 instancias en UCI
  frente a 25.000 en la sección de datos del paper.
- Licencia permisiva no compensa ausencia de tiempo, madurez o entity control.
- Fannie Mae es longitudinalmente atractivo, pero `internal use only` no
  demuestra compatibilidad con el portfolio público.

## Registro de decisiones del plan

- 2026-07-26: se usa el estado más conservador propuesto por el reviewer:
  Freddie Mac Sample queda `Needs controlled inspection`.
- 2026-07-26: se rechazan candidatos con hard failures ya visibles en
  documentación; no se usa la cuarentena para inventar timestamps ausentes.
- 2026-07-26: no se crea ADR porque no existe aprobación humana de dataset.

## Resultados y retrospectiva

Cuatro revisiones independientes (`data_ml` por contrato, `data_ml` por
metodología, `reviewer` por licencia/privacidad y `monitoring`) evaluaron cuatro
candidatos. Freddie Mac SFLLD Sample queda como única recomendación condicional
`Needs controlled inspection`; UCI Taiwan, UCI South German y Fannie Mae
quedan `Reject`. Ningún dataset se adquirió, seleccionó o aceptó y no se creó
ADR.

Validación final:

- 7 TOML parseados correctamente;
- import de `cop` correcto;
- Ruff format y lint correctos;
- mypy sin issues en 2 archivos fuente;
- pytest: 1 test superado;
- exactamente 5 ADR Accepted y 0 Proposed;
- `git diff --check` y whitespace de los tres archivos nuevos correctos;
- diff fuera de los cuatro documentos del milestone vacío;
- ausencia verificada de datasets, snapshots, notebooks y código ML nuevo.

La revisión final detectó inicialmente un gate ausente en el roadmap, estados
no normativos de checklist, campos implícitos y trazabilidad mejorable de tres
fuentes. Se corrigieron y la reverificación confirmó cero hallazgos critical,
high o medium pendientes.

El siguiente paso no es implementar el split. Requiere una decisión humana
sobre los términos y el gate documental de Freddie Mac; cualquier adquisición
en cuarentena y fase B pertenecerán a otra tarea expresamente autorizada.
