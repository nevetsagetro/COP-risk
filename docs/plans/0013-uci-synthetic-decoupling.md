# ExecPlan 0013: desacoplar UCI de la vertical sintética

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-08-02.
- Última actualización: 2026-08-02.
- Responsable: agente `coordinator`.
- Alcance: corrección arquitectónica previa al baseline académico.
- Fuente normativa: `AGENTS.md`, `PLANS.md` y decisión humana de este milestone.

## Propósito y resultado observable

Hacer que adquisición, evaluación, snapshot y splits UCI funcionen desde un
checkout limpio sin importar ningún módulo bajo `cop.data.synthetic`.

## Base verificada

- `HEAD` inicial: `d7a5658f696c6cca470a6b0ad9d8b226aa4a4ce6`;
- working tree inicial limpio;
- cuatro imports UCI/test dependían de hashing sintético y el contrato UCI
  dependía además del loader YAML definido en la configuración sintética;
- no existían modelos ni dependencias ML dentro del alcance prohibido.

## Alcance

Utilidades neutrales de hashing/YAML, imports UCI y synthetic, tests de
arquitectura, documentación, validación local y worktree limpio.

## Fuera de alcance

Entrenamiento, features de modelo, LightGBM, scikit-learn, SMOTE-Tomek,
Optuna, MLflow y eliminación del código o datos sintéticos.

## Decisiones

### Aceptadas

ADR 0009 registra UCI como vertical principal y prohíbe dependencias UCI hacia
synthetic. ADR 0008 conserva el uso exclusivamente académico de UCI.

### Pendientes

La disposición futura de la vertical sintética queda fuera de este cambio.

### Propuestas

No aplica.

## Seguridad y restricciones

Los datos siguen ignorados por Git. No se borra ni publica ningún artefacto y
no se amplían los claims autorizados.

## Plan de ejecución

1. Inventariar imports hacia synthetic.
2. Extraer hashing y YAML estricto a módulos neutrales.
3. Actualizar consumidores y añadir una prueba arquitectónica.
4. Ejecutar pipeline UCI y validaciones completas.
5. Aplicar el cambio mínimo a un worktree limpio y repetir la validación UCI.
6. Solicitar revisión final read-only.

## Validación y criterios de aceptación

```bash
! rg -n "cop\.data\.synthetic" src/cop/data/evaluation src/cop/data/ingestion
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/pytest
git diff --check
git ls-files data
```

El worktree limpio debe importar los módulos UCI y completar sus tests sin el
directorio `src/cop/data/synthetic`.

## Registro de progreso

- [x] 2026-08-02: inspección e inventario de imports.
- [x] 2026-08-02: extracción de hashing y YAML neutral.
- [x] 2026-08-02: actualización de imports y prueba arquitectónica.
- [x] 2026-08-02: validación local y worktree limpio sin paquete synthetic.
- [x] 2026-08-02: revisión final sin hallazgos abiertos de ninguna severidad.

## Hallazgos inesperados

El acoplamiento no se limitaba a hashing: `DatasetContract` importaba también
`UniqueKeyLoader` desde la configuración sintética.

## Registro de decisiones del plan

- 2026-08-02: se conserva un wrapper de compatibilidad en
  `cop.data.synthetic.hashing`; la implementación canónica es neutral.
- 2026-08-02: no se mueve ni elimina ningún módulo específico de synthetic.

## Resultados y retrospectiva

La suite local completó Ruff, mypy y 67 tests. La CLI UCI verificó adquisición,
evaluación, snapshot v2 y splits sin cambiar sus identidades. En un worktree
temporal detached desde `d7a5658`, se aplicó solo esta corrección, se retiró
físicamente `src/cop/data/synthetic` y los imports más 21 tests UCI pasaron. El
worktree temporal fue eliminado después de la prueba. `git diff --check` pasó,
`git ls-files data` no devolvió datos y no se añadieron dependencias ML.

La primera revisión final confirmó además 22 tests UCI con un import hook que
bloquea `cop.data.synthetic`; solicitó únicamente reconciliar una frase legacy
del README y registrar estos resultados antes de cerrar.

Tras corregir también el rationale histórico y ampliar la prueba arquitectónica
a subdirectorios y entrypoints, el reviewer cerró sin hallazgos critical, high,
medium o low.
