# ExecPlan 0004: contrato de datos y protocolo de evaluación

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-25.
- Última actualización: 2026-07-25.
- Responsable: agente `coordinator`.
- Alcance: documentación metodológica del Milestone 2.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y ADR 0001-0005.

## Propósito y resultado observable

Definir un metacontrato verificable para evaluar futuros datasets antes de
seleccionarlos o materializarlos, junto con un protocolo que preserve un test
intacto y una checklist de rechazo. El resultado no contiene datos, código ML,
validadores, métricas calculadas ni tecnología implementada.

## Base verificada

Inspección del 2026-07-25:

- `HEAD` es `7a79283be5f59800be4af0bc3d8963a78857cf74` en `main`;
- `git status --short` no produjo salida;
- existen exactamente cinco ADR y los cinco tienen `Status: Accepted`;
- existen los ExecPlans 0001, 0002 y 0003;
- `pyproject.toml` mantiene cero dependencias runtime y tres herramientas de
  desarrollo;
- el código verificado se limita al paquete mínimo `src/cop/__init__.py` y un
  smoke test;
- no se encontraron datasets, notebooks, pipelines, modelos, servicios ni
  infraestructura funcional.

## Alcance

- `docs/data-contract.md`;
- `docs/evaluation-protocol.md`;
- `docs/dataset-acceptance-checklist.md`;
- este ExecPlan;
- reconciliación del Milestone 2 en `docs/plans/0001-bootstrap.md`.

## Fuera de alcance

Seleccionar, buscar, descargar, generar o transformar datos; definir valores
concretos de target, horizonte, features, métricas, gates o thresholds;
implementar validadores, splits, preprocessing, entrenamiento, tracking,
serving, orquestación, monitoring, infraestructura o dependencias.

## Decisiones

### Aceptadas aplicables

Rigen las decisiones de `AGENTS.md` y los cinco ADR Accepted. En particular,
el test debe permanecer intacto, los atributos protegidos nunca son inputs,
drift no promociona modelos y la aceptación tecnológica no demuestra
implementación.

### Decisiones operativas del plan

- El contrato tiene dos capas: reglas generales ahora y un futuro
  perfil/manifest por candidato.
- `No evidenciado` falla un requisito obligatorio.
- El split temporal es la estimación principal y la separación por entidad es
  el default conservador; cualquier excepción exige protocolo predeclarado.
- No se crea ADR: estas reglas concretan controles normativos sin aceptar
  dataset, target, métricas o arquitectura nueva.

### Pendientes

Fuente/licencia, entidad y población concretas, target, horizonte, features,
estimand, tamaños de split, métricas finales, gates, thresholds, método de
censura, snapshot storage y autoridad de aceptación.

## Seguridad y restricciones

Solo se permiten futuros datos sintéticos o públicos anonimizados. PII,
procedencia incierta y licencia incompatible son rechazos. Los atributos
protegidos quedan separados para auditoría y nunca como inputs. Ningún
documento puede afirmar fairness, producción o existencia de datos.

## Plan de ejecución

1. Inspeccionar Git, reglas, documentación, todos los ADR/planes y agentes.
2. Recibir cuatro análisis independientes read-only sobre contrato, leakage,
   monitoring y revisión crítica.
3. Consolidar contrato, protocolo, checklist y este plan.
4. Reconciliar el roadmap sin convertir propuestas en decisiones.
5. Verificar estructura, coherencia, alcance y baseline; revisar diff.
6. Solicitar revisión final read-only y corregir solo hallazgos del milestone.
7. Registrar resultados reales y cerrar el plan.

## Validación y criterios de aceptación

```bash
test -s docs/data-contract.md
test -s docs/evaluation-protocol.md
test -s docs/dataset-acceptance-checklist.md
test -s docs/plans/0004-data-evaluation-contract.md
test "$(rg -l '^- Status: Accepted$' docs/decisions | wc -l)" -eq 5
git diff -- pyproject.toml src tests docs/decisions .codex docker-compose.yml
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

Los archivos nuevos sin seguimiento se revisan además con
`git diff --no-index --check /dev/null <archivo>`. El test final debe estar
prohibido explícitamente para feature selection, HPO, early stopping,
calibración, threshold y comparación iterativa. No puede cambiar código,
dependencias, ADR, agentes o infraestructura.

## Registro de progreso

- [x] 2026-07-25: inspección y lectura obligatorias completadas sobre árbol
  limpio.
- [x] 2026-07-25: cuatro análisis read-only recibidos y consolidados.
- [x] 2026-07-25: contrato, protocolo, checklist y ExecPlan redactados.
- [x] 2026-07-25: roadmap reconciliado; estructura, baseline, whitespace,
  alcance y diff completo validados.
- [x] 2026-07-25: revisión final read-only completada; seis hallazgos
  corregidos y reverificados sin hallazgos abiertos.

## Hallazgos inesperados

- El roadmap asignaba Milestone 2 a configuración tipada y reservaba contrato y
  evaluación para milestones posteriores. Debe reconciliarse con la
  autorización actual.
- La fuente del dataset bloquea instanciar el contrato, pero no definir ahora
  su forma general.
- La recomendación histórica de un dataset sintético no es una decisión y no
  se incorpora como selección.
- La primera redacción exigía evidencia material antes de descargar, aunque
  hashes, PII y duplicados solo pueden verificarse inspeccionando el artefacto.
  La revisión final motivó dos gates: pre-adquisición documental e inspección
  controlada previa a selección.

## Registro de decisiones del plan

- 2026-07-25: se adopta un metacontrato con evidencia y rechazo por requisito,
  sin inventar valores concretos.
- 2026-07-25: se conserva separación estricta del test y segregación de
  atributos protegidos como reglas no negociables.
- 2026-07-25: no se crea ADR adicional porque no se acepta una decisión
  arquitectónica duradera nueva.
- 2026-07-25: la adquisición futura en cuarentena se separa de la selección y
  uso; no se descarga nada en este milestone.

## Resultados y retrospectiva

Resultados observados el 2026-07-25:

- se crearon el metacontrato, protocolo, checklist y este ExecPlan, y se
  reconcilió el roadmap;
- cuatro análisis iniciales read-only cubrieron definición del problema,
  leakage/evaluación, requisitos futuros de monitoring y revisión crítica;
- exactamente cinco ADR permanecen Accepted y cero Proposed;
- no cambiaron código, tests, dependencias, ADR, agentes ni infraestructura;
- siete TOML parsearon, `cop` importó, Ruff format/lint y mypy pasaron, y pytest
  aprobó `1` test;
- `git diff --check` y los checks equivalentes de los cuatro archivos nuevos
  no mostraron errores;
- el reviewer final detectó una contradicción high en el orden de adquisición,
  tres ambigüedades medium y dos mejoras low. Se introdujeron los dos gates, se
  precisaron estados, atributos, joins, calibración y roadmap;
- la reverificación read-only confirmó que los seis hallazgos quedaron
  corregidos y no dejó hallazgos abiertos.

No se buscó, descargó, generó, seleccionó ni transformó ningún dataset. No se
implementó código ML ni se creó un ADR. Permanecen abiertos todos los valores
específicos enumerados en la sección de decisiones.
