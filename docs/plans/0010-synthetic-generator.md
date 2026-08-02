# ExecPlan 0010: generador sintético mínimo

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-27.
- Última actualización: 2026-07-27.
- Responsable: agente `coordinator`.
- Alcance: Milestone 6, generador sintético determinista y validado.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ADR 0006, contrato, protocolo,
  checklist y especificación sintética.

## Propósito y resultado observable

Implementar una CLI que lea YAML, genere applications, ledger y audit-only en
Parquet, derive labels desde el ledger, valide contrato e integridad y escriba
un manifest reproducible con hashes. Dos ejecuciones equivalentes deben tener
el mismo hash lógico.

## Base verificada

Inspección del 2026-07-27:

- `HEAD` inicial: `ad302dc9c5011edd38d6352f116570a81349a94f`;
- el working tree no estaba limpio: permanecían sin seguimiento
  `docs/synthetic-data-dictionary.md` y
  `docs/synthetic-drift-scenarios.md`; se preservan;
- existen seis ADR `Accepted` y ADR 0006 está aceptado;
- existen especificación y diccionario sintéticos;
- `data/raw/synthetic/` no contiene archivos y está ignorado por `data/**`;
- `src/cop` solo contenía `__init__.py`: no había generador ni pipeline ML;
- el entorno no contenía pandas, pyarrow, PyYAML, pydantic o polars.

## Alcance

- `configs/data/synthetic-v1.yaml`;
- `src/cop/data/synthetic/`;
- `src/cop/data/schemas/`;
- `src/cop/data/validation/`;
- `scripts/generate_synthetic_snapshot.py`;
- tests unitarios e integración del generador;
- `pyproject.toml`;
- este ExecPlan;
- snapshot pequeño ignorado bajo `data/raw/synthetic/`.

## Fuera de alcance

Split definitivo, preprocessing, features productivas, SMOTE-Tomek, LightGBM,
Optuna, MLflow, Prefect, FastAPI, Docker, Evidently, Grafana, notebooks y
commit.

## Decisiones

### Aceptadas aplicables

ADR 0006 exige determinismo, Parquet, manifest con hashes, cutoff reproducible,
target derivado de ledger, unknown para inmaduras/censuradas, separación
`audit_only`, temporalidad y ausencia de claims reales.

### Pendientes generales

Los valores de este YAML son una configuración de desarrollo v1 autorizada por
el milestone, no gates finales ni claims sobre poblaciones reales.

### Decisiones operativas

Se usan NumPy para RNG vectorizado, pandas para construcción, joins y
validaciones tabulares, pyarrow como único writer/reader Parquet y PyYAML para
configuración. Pandas reduce la complejidad del ledger y del target respecto a
operar Arrow directamente; no se añade polars en paralelo. Los validadores son
Python explícito; pydantic/pandera no se justifican en esta primera vertical.
Los stubs de pandas/PyYAML son dependencias `dev` necesarias para mypy strict.

La configuración se carga con SafeLoader que rechaza claves duplicadas,
unknowns y timestamps no UTC. `snapshot_id` usa SHA-256 sobre JSON canónico de
la configuración resuelta, excluyendo el path de salida. El hash lógico
`cop-logical-v1` tipa valores y ordena filas por clave; los hashes físicos son
SHA-256 del Parquet cerrado. El manifest JSON canónico queda sellado por un
sidecar SHA-256.

La escritura usa staging hermano, lock exclusivo, verificación desde disco,
rename y rollback mediante backup para `--force`. Solo reemplaza un directorio
con manifest COP y la misma identidad; paths ajenos o symlinks se rechazan.

## Seguridad y restricciones

Solo datos sintéticos. Los atributos protegidos viven en un Parquet separado.
IDs, target, outcome, timestamps futuros y metadata no son inputs. La CLI no
sobrescribe salvo `--force`; una ejecución fallida no publica un snapshot
parcial.

## Plan de ejecución

1. Recibir revisiones read-only de data/ML, monitoring y MLOps.
2. Añadir dependencias mínimas e instalarlas con editable pip vigente.
3. Implementar configuración, esquema, generación, target y validadores.
4. Implementar manifest, hashes y CLI segura.
5. Añadir tests unitarios e integración con configuración pequeña.
6. Generar dos snapshots pequeños y comparar determinismo.
7. Ejecutar baseline, revisar diff y solicitar reviewer final read-only.

## Validación y criterios de aceptación

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -c "import yaml; yaml.safe_load(open('configs/data/synthetic-v1.yaml'))"
.venv/bin/python scripts/generate_synthetic_snapshot.py \
  --config tests/fixtures/synthetic-small.yaml \
  --output-root data/raw/synthetic/milestone6-validation-a
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
git check-ignore data/raw/synthetic
git diff --check
git status --short
```

La integración usa una configuración pequeña y dos raíces temporales para
comparar hashes lógicos sin depender del path. El snapshot v1 completo de
100000 filas no es requisito de test.

## Registro de progreso

- [x] 2026-07-27: inspección obligatoria y desviación de árbol registradas.
- [x] 2026-07-27: revisiones de diseño read-only.
- [x] 2026-07-27: dependencias e implementación.
- [x] 2026-07-27: tests y dos snapshots pequeños equivalentes.
- [x] 2026-07-27: baseline, diff y reviewer final.

## Hallazgos inesperados

- El árbol inicial no estaba limpio por dos documentos previos sin seguimiento.
- Con 75000 borrowers y 100000 applications, 15% de borrowers repetidos exige
  repartir 25000 solicitudes adicionales entre 11250 borrowers; no equivale a
  15% de applications duplicadas.
- La primera revisión final detectó verificación parcial del manifest y un
  reemplazo `--force` insuficientemente defensivo. El cierre recompone el
  manifest completo desde Parquet, rechaza corrupción, inventario adicional y
  symlinks, y prueba rollback ante un fallo de publicación.

## Registro de decisiones del plan

- 2026-07-27: un único writer (`coordinator`); especialistas y reviewer son
  read-only.
- 2026-07-27: pandas + pyarrow + PyYAML; validación contractual propia.
- 2026-07-27: NumPy queda como dependencia directa porque el generador usa su
  RNG; pandas se elige sobre polars para joins/groupby y validación.
- 2026-07-27: tasa positiva aproximada, nunca garantía ni claim real.

## Resultados y retrospectiva

La CLI genera y verifica applications, ledger y audit-only en Parquet. El
target se recompone desde fechas y DPD del ledger; las labels inmaduras y
censuradas son nulas. El manifest registra configuración, esquema, lineage,
namespaces RNG, toolchain, conteos, reconciliaciones y hashes físicos/lógicos,
y su verificador reconstruye toda la metadata desde los archivos.

Dos ejecuciones del fixture pequeño produjeron el mismo snapshot ID y hash
lógico:
`7e1b0c515a17d1a09a832c206596c0623cc357b5f423268428f01891b27c3efb`.
Los snapshots permanecen ignorados por `data/**`.

Validación final:

- Ruff format/check: pasa;
- mypy strict: 17 archivos, sin hallazgos;
- pytest: 36 tests pasan;
- YAML real: parseado;
- `git diff --check`: pasa;
- datos versionados bajo `data/raw/synthetic`: ninguno;
- pipeline ML: no implementado.

Los valores de `synthetic-v1.yaml` siguen siendo parámetros operativos de la
primera demostración, autorizados por Milestone 6. No se convierten en target,
horizonte, población, prevalencia o gates metodológicos finales y no sustentan
claims sobre crédito real.
