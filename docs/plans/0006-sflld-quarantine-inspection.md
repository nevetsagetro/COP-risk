# ExecPlan 0006: registro e inspección controlada de SFLLD Sample 2019

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-07-26.
- Última actualización: 2026-07-26.
- Responsable: agente `coordinator`.
- Alcance: Milestone 4A, registro e inspección limitada en cuarentena.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, contrato, protocolo, checklist y
  ADR 0001-0005.

## Propósito y resultado observable

Registrar por hash el ZIP local, verificar su integridad, extraer únicamente
dos TXT esperados a una cuarentena ignorada por Git e inspeccionar estructura y
riesgos contractuales sin aceptar el dataset ni crear artefactos de ML. El
resultado observable son dos informes, una configuración declarativa y una
conclusión única: **Reject**.

## Base verificada

Inspección del 2026-07-26:

- `HEAD` inicial fue `ac3eb78c713829cfbe62799a8a1bb22ec2c68212`;
- `git status --short` inicial no produjo salida;
- contrato, protocolo, checklist y ExecPlans 0001-0005 estaban versionados;
- `data/raw/sample_2019.zip` existía y Git lo ignoraba mediante `data/**`;
- el repositorio seguía sin pipeline, splits, modelos o servicios ML.

La existencia del ZIP es estado local verificado; no demuestra fuente
aprobada, licencia aceptada ni aptitud para entrenamiento.

## Alcance

- `docs/datasets/sflld-sample-2019-acquisition.md`;
- `docs/datasets/sflld-sample-2019-inspection.md`;
- `configs/datasets/sflld-sample-2019.yaml`;
- este ExecPlan;
- reconciliación de progreso en `docs/plans/0001-bootstrap.md`;
- datos locales solo bajo `data/raw/sflld/2019/quarantine/`.

## Fuera de alcance

Processed, aceptación para entrenamiento, splits, features finales, notebooks,
EDA completa, entrenamiento, SMOTE-Tomek, LightGBM, Optuna, MLflow, Prefect,
FastAPI, Docker, Evidently, ADR de selección o commit.

## Decisiones

### Aceptadas aplicables

Solo se permiten datos sintéticos o públicos anonimizados; PII y procedencia
incierta son rechazos; el split precede todo fit; el test queda intacto;
atributos protegidos nunca son inputs; drift no promociona.

### Pendientes

Release y términos exactos, responsable/aprobador, retención, privacidad,
entidad, evento, población, target, horizonte, censura, roles de features,
split, métricas y monitoring operativo.

### Propuesta del plan

Conservar el artefacto solo en cuarentena mientras se resuelven los pendientes.
No se crea ADR porque no se acepta dataset ni decisión arquitectónica.

## Seguridad y restricciones

El ZIP y su extracción permanecen ignorados. Se publican únicamente hashes,
tamaños, nombres de fichero, esquema y agregados. No se versionan filas, IDs o
valores originales. El servicing se trata como post-decision para originación
y ningún campo se aprueba como input.

## Plan de ejecución

1. Inspeccionar Git, reglas, contrato, protocolo, checklist y roadmap.
2. Ejecutar ignore, hash, metadata, tipo, integridad y listado del ZIP.
3. Confirmar allowlist y seguridad de miembros; extraer solo a cuarentena.
4. Inspeccionar estructura mínima y agregados de integridad.
5. Recibir análisis read-only de `data_ml`, `monitoring` y `reviewer`.
6. Redactar únicamente los cinco archivos permitidos.
7. Ejecutar baseline completo, controles de Git/datos y revisar el diff.
8. Solicitar revisión final read-only, corregir hallazgos y cerrar.

## Validación y criterios de aceptación

```bash
git check-ignore -v data/raw/sample_2019.zip
sha256sum data/raw/sample_2019.zip
stat data/raw/sample_2019.zip
file data/raw/sample_2019.zip
unzip -t data/raw/sample_2019.zip
unzip -l data/raw/sample_2019.zip
git check-ignore -v data/raw/sflld/2019/quarantine/*.txt
git ls-files data/raw
test -z "$(git status --short --untracked-files=all | sed -E 's/^.. //' | grep -Ev '^(docs/datasets/sflld-sample-2019-(acquisition|inspection).md|configs/datasets/sflld-sample-2019.yaml|docs/plans/0006-sflld-quarantine-inspection.md|docs/plans/0001-bootstrap.md)$')"
PYTHONPATH=src .venv/bin/python -c "import cop"
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests
.venv/bin/python -m pytest
git diff --check
git status --short
git diff
```

El resultado exige ZIP íntegro, datos ignorados, hash/tamaño registrados,
ningún dato individual versionado, consistencia contractual, baseline completo
y revisión final read-only.

## Registro de progreso

- [x] 2026-07-26: inspección obligatoria iniciada sobre árbol limpio.
- [x] 2026-07-26: ZIP identificado, hasheado, listado y validado.
- [x] 2026-07-26: dos TXT seguros extraídos únicamente a cuarentena ignorada.
- [x] 2026-07-26: inspección agregada limitada y análisis especializados
  read-only completados.
- [x] 2026-07-26: documentación y baseline completados.
- [x] 2026-07-26: revisión final read-only completada; dos hallazgos high y
  dos medium corregidos y reverificados.

## Hallazgos inesperados

- `unzip` no estaba instalado. El intento global falló por permisos; se
  descargó el paquete Ubuntu a `/tmp` y se ejecutó el binario real con `PATH`
  temporal, sin añadir una dependencia al proyecto.
- La checklist usa `Pending`, `Rejected` y `Eligible for human review`; el
  encargo exige otros tres rótulos. `Rejected`, exigido cuando existe un
  rechazo duro `Not evidenced`, se expresa aquí como `Reject` sin cambiar la
  checklist normativa.
- Los dos ficheros tienen 32 columnas, pero la existencia del loan ID no
  resuelve identidad de prestatario ni disponibilidad as-of.

## Registro de decisiones del plan

- 2026-07-26: un allowlist exacto de dos TXT regulares, sin cifrado, links o
  rutas inseguras, fue condición de extracción.
- 2026-07-26: se limita la inspección a estructura y agregados; no se publica
  contenido fuente.
- 2026-07-26: servicing se considera post-decision para originación hasta que
  un contrato humano futuro defina target y roles.
- 2026-07-26: no se acepta el snapshot ni se crea ADR.

## Resultados y retrospectiva

El ZIP pasó `unzip -t`, contiene exactamente los dos TXT esperados y quedó
registrado junto con hashes y tamaños de su contenido. Los datos extraídos
siguen ignorados por Git y ninguna fila, ID o valor fuente aparece en archivos
versionables. La inspección agregó estructura, blanks, claves, duplicados,
joins y rangos sin crear splits ni transformaciones.

Validación previa a la revisión final:

- `cop` importó correctamente;
- Ruff format y lint pasaron;
- mypy no encontró issues en dos archivos fuente;
- pytest superó `1` test;
- `git diff --check` no produjo errores;
- el intento de parsear YAML con PyYAML quedó bloqueado porque esa dependencia
  no está instalada; no se añadió una dependencia solo para validar config;
- el allowlist de cambios y el whitespace de archivos nuevos se comprueban
  nuevamente después de la revisión final.

La revisión final confirmó la integridad técnica y detectó que el estado
provisional no aplicaba literalmente la regla terminal de la checklist. Se
añadió la matriz requisito por requisito, se corrigió el allowlist para incluir
untracked y se adoptó **Reject** porque hay rechazos duros `Not evidenced`.
Es un rechazo con la evidencia actual, reabrible si una revisión posterior
aporta y acepta la evidencia ausente; no deriva de un fallo técnico del ZIP.
El dataset no queda aceptado para entrenamiento ni como reference dataset.
