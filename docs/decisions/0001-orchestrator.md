# ADR 0001: orquestador para la demo local

- Status: Accepted
- Date: 2026-07-25
- Accepted: 2026-07-25
- Decision owners: aprobación humana registrada

## Context

COP necesitará coordinar en el futuro detección de drift, creación de un
challenger y evaluación. Hoy no existe todavía un caso de uso de dominio que
orquestar. La demo será local, mantenida por una sola persona, y la promoción
debe permanecer fuera del flujo de retraining.

## Requirements

- Ejecución local reproducible con Python 3.12.
- Scheduling, retries, historial y observabilidad cuando exista esa necesidad.
- Bajo coste operativo para una sola persona.
- Casos de uso invocables y testeables sin el orquestador.
- Idempotencia, límites de concurrencia y secretos fuera del código.
- Ningún flujo puede promover o hacer rollback de un modelo.

## Options

### Posponer selección e implementación

Ventajas:

- Cero dependencias, servicios o estado adicional.
- Permite demostrar primero un comando Python manual e idempotente.
- Evita decidir a partir de requisitos hipotéticos.

Inconvenientes:

- Scheduling, UI e historial aparecen más tarde.
- Los problemas de integración también se descubren más tarde.

Riesgos: crear scripts ad hoc que después sean difíciles de adaptar.

Coste operativo: muy bajo.

### Prefect

Ventajas:

- API orientada a Python y adopción incremental.
- Puede ejecutarse localmente y reservar workers o infraestructura dinámica
  para cuando exista una necesidad real.
- Menor superficie inicial que un despliegue completo de Airflow.

Inconvenientes:

- Añade servidor, estado y un proceso de ejecución.
- Puede acoplar el dominio a decorators, contexto o resultados de Prefect.
- Requiere controlar compatibilidad entre cliente y servidor.

Riesgos: exponer la UI fuera de loopback, reintentar operaciones no
idempotentes o confundir historial de ejecución con evidencia de MLflow.

Coste operativo: bajo a medio.

### Airflow

Ventajas:

- Scheduler, UI e historial maduros.
- Modelo DAG conocido y adecuado para muchas dependencias y equipos.
- Constraints oficiales para instalaciones reproducibles.

Inconvenientes:

- Aplicación multicomponente con mayor consumo y mantenimiento.
- Gestión adicional de metadata, scheduler, DAG processor y providers.
- Su operación local completa es excesiva para un único flujo inicial.

Riesgos: adoptar complejidad de plataforma antes de validar el dominio o usar
XCom y estados de Airflow como contratos de negocio.

Coste operativo: medio a alto.

## Decision

Prefect será el orquestador de COP cuando se introduzca orquestación, por su
adopción incremental y menor carga para una demo Python mantenida por una
persona. Su implementación queda pospuesta hasta que exista un pipeline Python
manual, reproducible, probado e idempotente.

El primer adaptador deberá ser delgado, mantener los imports de Prefect fuera
del dominio y enlazar cualquier UI únicamente a loopback. La elección entre
`serve()` y un process work pool no forma parte de este ADR.

La aceptación de esta decisión no instala Prefect, no añade dependencias y no
demuestra que exista orquestación.

## Consequences

- En el futuro habrá una dependencia y un proceso adicional.
- El estado del orquestador no sustituirá MLflow, manifests ni auditoría de
  promoción.
- Airflow seguirá siendo alternativa si aparecen muchos DAG, varios equipos o
  una plataforma Airflow preexistente.
- No se introduce ahora ninguna dependencia ni configuración.

## Reversibility

Alta si dominio y casos de uso conservan interfaces neutrales. Cambiar a
Airflow exigiría reescribir flows, schedules y operación, pero no metodología
ML. La reversibilidad disminuye si el dominio recibe objetos del orquestador.

## Open questions

- ¿Se necesita scheduling en la primera vertical o basta ejecución manual?
- ¿Qué frecuencia, duración, concurrencia, retries y política de catch-up se
  esperan?
- ¿Qué zona horaria y clave de idempotencia se usarán?
- ¿Qué retención y backup necesita el estado del orquestador?
- ¿Prima simplicidad local o demostrar experiencia específica con Airflow?
- ¿Qué evidencia del pipeline manual autorizará iniciar la implementación?

## Sources

- [Prefect installation](https://docs.prefect.io/v3/get-started/install)
- [Prefect deployments](https://docs.prefect.io/v3/concepts/deployments)
- [Prefect self-hosted server](https://docs.prefect.io/v3/concepts/server)
- [Airflow architecture](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Airflow installation](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html)
- [Airflow reproducible installation](https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html)
