# ExecPlan 0011: snapshot sintético v1 y splits reproducibles

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-08-01.
- Última actualización: 2026-08-01.
- Responsable: agente `coordinator`.
- Alcance: Milestone 7, aprobación y materialización de `synthetic-v1`.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ADR 0006, ADR 0007, contrato y protocolo de evaluación.

## Propósito y resultado observable

Congelar y materializar el snapshot sintético v1 aprobado y cinco particiones
reproducibles, sin solapamiento de entidades ni uso adaptativo del test.

## Base verificada

El 2026-08-01, `HEAD` era `ad302dc9c5011edd38d6352f116570a81349a94f`
y el árbol ya contenía cambios sin commit del generador del Milestone 6. Hay
seis ADR Accepted previos, snapshots pequeños `synthetic-v1-test` ignorados,
pero ningún snapshot aprobado, implementación de split o manifest de splits.
Ruff, mypy y los 36 tests existentes pasaban.

## Alcance

ADR 0007, configuración congelada, corrección causal del generador, snapshot
v1, splitting y purga por borrower, manifests, tests y documentación de
aceptación. Los datos materiales permanecen ignorados.

## Fuera de alcance

Preprocessing, features productivas, SMOTE-Tomek, LightGBM, Optuna, MLflow,
Prefect, API, Docker, Evidently, modelos, métricas o gates de rendimiento.

## Decisiones

ADR 0007 contiene los parámetros humanos aceptados. El test nunca participa en
gates. La prevalencia solo se reporta. El ledger y la recurrencia tienen las
limitaciones documentadas en el ADR.

## Seguridad y restricciones

Solo datos sintéticos generados por el proyecto, sin fuentes externas ni PII.
Uso de entrenamiento limitado a demo local; redistribución pendiente.

## Plan de ejecución

1. Congelar configuración y eliminar ajuste global del generador.
2. Implementar cinco particiones, purga, fingerprints y manifests.
3. Añadir pruebas de causalidad temporal, separación y reproducibilidad.
4. Generar y verificar snapshot y splits ignorados.
5. Actualizar documentación y ejecutar validaciones completas.
6. Obtener revisión final read-only sin hallazgos critical/high.

## Validación y criterios de aceptación

```bash
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy src tests scripts
.venv/bin/python -m pytest
git diff --check
git check-ignore data/processed/synthetic-v1
```

También se verificarán dos generaciones lógicas equivalentes, dos splits
equivalentes, hashes, madurez, orden temporal, purga e intersecciones cero.

## Registro de progreso

- [x] 2026-08-01: inspección y tres análisis read-only.
- [x] 2026-08-01: aprobación humana explícita y ADR 0007.
- [x] 2026-08-01: corrección del generador y configuración congelada.
- [x] 2026-08-01: splits, manifests y tests.
- [x] 2026-08-01: materialización y reproducción completa en una segunda raíz.
- [x] 2026-08-01: revisión final y delta sin hallazgos critical/high.

## Hallazgos inesperados

El generador ajustaba momentos e intercepto sobre todo el snapshot y el gate de
prevalencia consultaba todas las labels maduras. Ambos comportamientos deben
eliminarse antes de aprobar el artefacto.

## Registro de decisiones del plan

- 2026-08-01: las cinco ventanas conservan identidad física y lógica separada.
- 2026-08-01: la aprobación se limita a entrenamiento sintético local.

## Resultados y retrospectiva

El snapshot aprobado contiene 100000 solicitudes, 75000 borrowers, 98050
labels maduras, 1950 censuradas y ninguna inmadura. Su hash lógico es
`7e7f3c95e519964e3d8c9e452c6027e5ac1f2de0eb72ebeab990adf00797126d`.
La prevalencia sintética realizada es 0.09991841 y no se usa como gate.

La purga elimina 20424 filas de 9449 borrowers. Las cinco particiones contienen
78045 filas supervisadas, tienen intersecciones cero y hash lógico conjunto
`351e74f41791944819851124b18445b8ab78c1756a94c10e830ff5dd310d76b3`.
Una segunda generación completa bajo `/tmp` reprodujo ambos hashes.

La revisión final no dejó hallazgos critical/high. Sus dos observaciones medium
se resolvieron con un fingerprint de contenido predecisión independiente de IDs
y un hash del código generador incorporado a identidad y procedencia. Las
observaciones low también se cubrieron con tests de identidad ante cambio de
código y coherencia entre `test_months` y la ventana congelada.

Validación final: Ruff format/check pasan; mypy strict pasa; pytest ejecuta 45
tests, todos pasan; las CLI verifican snapshot y splits; `git diff --check`
pasa; los datos permanecen ignorados y no se hizo commit.
