# Changelog

## Unreleased

- Añadido estudio académico reproducible con cross-validation, calibración,
  threshold sweep, predicciones OOF y dos notebooks narrativos con Plotly.
- Añadida interfaz opcional Streamlit con resultados académicos, tablas,
  gráficas, predicción ilustrativa sobre las 19 features UCI y threshold lab
  narrativo con paradas, tarjetas, tooltips, anotaciones en los puntos clave y
  animación Plotly.
- Añadidos servicio FastAPI local y frontend HTML/Plotly con contrato de
  overview, métricas, ROC, probabilidades, threshold sweep y predicción
  académica; Streamlit permanece como fallback.
- Añadida CLI de demo MVP local que ejecuta o reutiliza el baseline UCI y
  muestra métricas de validation sin abrir el test.
- Añadidos baselines académicos UCI con Logistic Regression y LightGBM,
  configuración fija, preprocessing train-only y finalización consumible del
  test sin resampling, tuning o MLflow.
- Añadido cierre seguro de milestones mediante allowlist, agente dedicado y
  staging literal sin commit automático.

Todos los cambios relevantes de este proyecto se documentarán en este archivo.

- Añadido un framework machine-readable de evaluación independiente por
  capacidad y aplicado a UCI Default of Credit Card Clients.
- Añadida adquisición oficial UCI reproducible, snapshot académico y splits
  estratificados, sin autorizar temporalidad, monitoring o producción.

- Aprobado el contrato metodológico de `synthetic-v1` para demostración local,
  con configuración congelada, snapshot reproducible y cinco splits temporales
  disjuntos por borrower.
- Eliminado el ajuste del mecanismo de riesgo sobre el snapshot completo y el
  gate de prevalencia; añadidos purga, fingerprints y manifests verificables.
- ADR 0007 Accepted y evidencia de aceptación de `synthetic-v1`, limitada a
  ingeniería y entrenamiento sintético local.

### Added

- Estructura inicial del repositorio para documentación, código fuente, tests y
  futuros componentes.
- Documentación de visión, estado verificable, decisiones y límites de
  seguridad del proyecto.
- Convención normativa para mantener ExecPlans y roadmap inicial.
- Paquete Python mínimo `cop` y smoke test de importación.
- Configuración de packaging y herramientas de desarrollo para Python 3.12.
- Plantilla ficticia de entorno y exclusiones de Git para secretos, datos y
  artefactos locales.
- Perfiles de agentes para coordinación, datos/ML, MLOps, monitoring y revisión
  de solo lectura.
- ADR aceptados para Prefect diferido, ejecución local-first, persistencia
  inicial de MLflow con SQLite y filesystem, estrategia `uv.lock` diferida y
  lifecycle challenger/champion con promoción y rollback humanos.
- ADR aceptado y especificación documental para usar datos sintéticos
  deterministas como fuente principal inicial, sin aceptar todavía target,
  horizonte, población, tamaño, prevalencia, ventanas ni gates cuantitativos.
- Generador sintético mínimo determinista con configuración YAML, applications,
  ledger, target derivado, estados de madurez/censura, `audit_only`, Parquet,
  manifest verificable, hashes físicos/lógicos, CLI segura y tests.

No se han versionado datos ni artefactos de modelos. El baseline académico se
materializa solo localmente; serving, monitoring, orquestación, MLflow, uv,
lock, Docker Compose e infraestructura funcional siguen sin implementarse.
