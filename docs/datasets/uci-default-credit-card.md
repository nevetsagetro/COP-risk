# UCI Default of Credit Card Clients

## Decisión

- Estado: aceptado exclusivamente para baseline académico local.
- Publicador: UCI Machine Learning Repository.
- DOI: `10.24432/C55S3H`.
- Licencia: CC BY 4.0.
- Fuente: descarga oficial UCI, sin mirrors.
- Fecha de adquisición: 2026-08-02.

UCI publica 30000 instancias, 23 features y una tarea de clasificación binaria
con respuesta default payment next month. Esta aceptación no constituye
evidencia temporal, longitudinal o productiva.

## Adquisición y snapshot

- Página: `https://archive.ics.uci.edu/dataset/350/default`.
- Descarga:
  `https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip`.
- ZIP: 5539494 bytes; SHA-256
  `56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602`.
- XLS original: `default of credit card clients.xls`, 5539328 bytes; SHA-256
  `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933`.
- Snapshot ID:
  `uci-default-credit-card-academic-b5e140d1bc9a620a12b1b2c3b86f79f5b71a140ac5063927f2d951d8800b6a9a`.
- Hash lógico de la fuente normalizada:
  `381973309c56d838bf37d3514e0aa3dce54a0a05242913e5acd64a96f2584d6e`.
- Hash lógico modelable:
  `4e8a12bfa1fd3e73281c9966126b0ec053ef1a3a4edcf1999c8340f816c318d0`.
- Hash lógico `audit_only`:
  `443806a7b6045cf679ca354ce7fc8f32a73c1f1c70b7aae203d1b15f25cde783`.

Los datos y manifests materiales permanecen bajo `data/**`, ignorados por Git.

## Inspección

- 30000 filas y 25 columnas contando ID y target;
- ID único, sin evidencia de identidad estable entre eventos;
- cero celdas ausentes;
- target `default_payment_next_month` con valores `{0, 1}`;
- sin timestamps de decisión, outcome o disponibilidad de label;
- las columnas mensuales no proporcionan un timestamp de decisión por fila ni
  cohortes longitudinales.

`SEX`, `EDUCATION`, `MARRIAGE` y `AGE` quedan físicamente separadas en
`audit_only.parquet`, enlazado uno-a-uno por `ID`; no aparecen en
`dataset.parquet`. No quedan autorizadas como inputs ni permiten claims de
fairness en este milestone.

## Decisión por capacidad

| Capacidad | Estado | Consecuencia |
|---|---|---|
| provenance | pass | Origen oficial, DOI y hashes registrados |
| license | pass | UCI declara CC BY 4.0 |
| target_definition | pass | Target binario publicado y verificado |
| schema | pass | Filas, columnas, missing y dominio verificados |
| entity_identity | limited | ID único, semántica longitudinal no evidenciada |
| timestamps | fail | No hay timestamps row-level adecuados |
| temporal_split | fail | No existe orden temporal defendible |
| group_split | limited | No puede comprobarse repetición de entidades |
| academic_modeling | pass | Clasificación estática y splits reproducibles |
| longitudinal_monitoring | fail | No hay cohortes ni entidad-tiempo longitudinal |
| public_portfolio_use | pass | Uso con atribución; filas fuera de Git |
| production_claims | fail | Sin evidencia operacional o temporal |

Los fallos no se ocultan ni compensan. Solo `academic_modeling` autoriza la
materialización posterior.

## Splits académicos

Hash estable por ID, semilla 42, estratificación por target y proporciones
70/15/15. No es un split temporal.

| Split | Filas | Negativas | Positivas |
|---|---:|---:|---:|
| train | 21000 | 16355 | 4645 |
| validation | 4500 | 3505 | 995 |
| test | 4500 | 3504 | 996 |

- Hash lógico conjunto:
  `d1e3ff1bbf3063a146e2d57f4a59c533cf89fa58f57f02cae45dd14e1202fade`.
- Intersección de ID: cero.
- Uso: baseline académico exclusivamente.

## Reproducción

```bash
python3 scripts/download_uci_credit_card.py
python3 scripts/evaluate_dataset_candidate.py \
  --acquisition data/raw/uci-default-credit-card/<acquisition_id>
```

Repetir descarga y evaluación conservó acquisition ID, hashes, snapshot,
decisiones y splits.

## Claims prohibidos

No se permiten claims de validación temporal, drift longitudinal, producción,
fairness, representatividad, utilidad crediticia, cumplimiento regulatorio ni
aptitud para decisiones reales.
