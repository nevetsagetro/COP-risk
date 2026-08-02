# Aceptación del snapshot sintético v1

## Estado

- Resultado: **Accepted for local synthetic demonstration training**.
- Fecha: 2026-08-01.
- Aprobación humana: registrada en ADR 0007.
- Naturaleza: datos sintéticos generados por el proyecto; no dataset real ni externo.

## Identidad materializada

- Configuración: `configs/data/synthetic-v1-approved.yaml`.
- Snapshot ID: `synthetic-v1-20260131T000000Z-40487371cea952131b53ea218a8e630047240d08bf36d966b262c47cffd8f5a5`.
- Hash lógico del snapshot: `7e7f3c95e519964e3d8c9e452c6027e5ac1f2de0eb72ebeab990adf00797126d`.
- Hash del código generador: `0968655b0aadb8cbaff5c41ffb5ffd031a605ec3e87c9c20010e3a62451e9a00`.
- Hash lógico de splits: `351e74f41791944819851124b18445b8ab78c1756a94c10e830ff5dd310d76b3`.
- Filas: 100000 applications, 100000 audit-only y 1156068 eventos de ledger.
- Borrowers: 75000.
- Labels: 98050 maduras, 1950 censuradas y 0 inmaduras.
- Prevalencia realizada entre labels maduras: 0.09991841. Es evidencia del
  simulador, no gate ni claim real.

Los Parquet y manifests materiales viven bajo `data/` y están ignorados por
Git. Esta página registra identidad y evidencia sin versionar filas.

## Repetición y limitaciones

Hay 11250 borrowers repetidos. La distribución realizada de solicitudes por
borrower es: 63750 con una, 3323 con dos, 4075 con tres, 2432 con cuatro, 996
con cinco, 321 con seis, 83 con siete, 16 con ocho y 4 con nueve. Entre
borrowers repetidos la media es 3.22222222 y el máximo 9.

La repetición prueba el control por entidad, pero no constituye una historia
longitudinal rica. El ledger binario usa estados DPD simulados y no representa
pagos, mora o dinámica crediticia reales.

## Splits y purga

| Partición | Filas | Borrowers | Hash lógico |
|---|---:|---:|---|
| train | 35086 | 32666 | `dde79f19d3a2b20eb014fcf43037ff5e80df55409610d94c7f5499bad0969ca6` |
| validation | 12954 | 12442 | `4688d90cadfc8fba8f545c0897ed351bd0fd03abfb789948dbc41ffb9c99fb60` |
| calibration | 6520 | 6375 | `e911ab4cf88014c751eb9592502db5e5357026d20c24f4c5b1def0514407bde6` |
| threshold | 7137 | 6925 | `3598dfef1ada9719c7c13570baec75ff1cff43776c2ccd4d021fd1d2509a4b54` |
| test | 16348 | 15219 | `c0cc117ae7700cef498c4317beac0e2514d3d4fccf7ea791c29fb8c11e2ffdc9` |

La asignación a la ventana más reciente purgó 20424 filas de 9449 borrowers:
20005 labels maduras y 419 censuradas. Después de la purga se excluyeron otras
1531 censuradas. La reconciliación es
`78045 supervisadas + 20424 purgadas + 1531 censuradas = 100000`.

Las intersecciones de `borrower_id`, `application_id` y fingerprint lógico son
cero. Calibration, threshold y test conservan identidades y propósitos
separados. El test no participa en gates ni adaptación.

## Gobernanza

- provenance: project-generated synthetic data;
- source_data: none;
- external_data_dependencies: none;
- training_use: approved_for_local_demo;
- real_credit_use: prohibited;
- redistribution: pendiente de licencia explícita del proyecto;
- publication_claims: restricted_to_synthetic_engineering_demo.

No se permiten claims sobre desempeño, representatividad, calibración,
fairness, utilidad crediticia o cumplimiento regulatorio reales.

## Reproducción y verificación

```bash
python3 scripts/generate_synthetic_snapshot.py \
  --config configs/data/synthetic-v1-approved.yaml
python3 scripts/create_synthetic_splits.py \
  --snapshot data/raw/synthetic/<snapshot_id>
python3 scripts/generate_synthetic_snapshot.py \
  --verify data/raw/synthetic/<snapshot_id>
python3 scripts/create_synthetic_splits.py \
  --snapshot data/raw/synthetic/<snapshot_id> \
  --verify data/processed/synthetic-v1/<snapshot_id>
```
