# Changelog

Todos los cambios relevantes de este proyecto se documentarán en este archivo.

## Unreleased

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

No se han versionado datos ni añadido modelos, entrenamiento, serving,
monitoring, orquestación, MLflow, uv, lock, Docker Compose ni infraestructura
funcional. Los snapshots locales de validación permanecen ignorados por Git.
