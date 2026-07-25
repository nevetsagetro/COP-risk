# ADR 0003: persistencia inicial de MLflow

- Status: Accepted
- Date: 2026-07-25
- Accepted: 2026-07-25
- Decision owners: aprobación humana registrada

## Context

MLflow es una tecnología aceptada, pero no está instalada ni configurada. La
demo inicial tendrá un operador y una máquina. Esta decisión se limita al
backend de metadata y al artifact store de MLflow; no decide almacenamiento de
features ni feature store.

MLflow separa metadata de runs y modelos registrados de artefactos grandes. El
backend relacional de SQLite no debe confundirse con el backend de metadata
basado en archivos legado.

## Requirements

- Backend relacional compatible con Model Registry.
- Metadata y artefactos persistentes, separados y fuera de Git.
- URI y rutas explícitas; ningún default implícito.
- Backup y restore coordinados.
- Servicio limitado a loopback cuando exista.
- Migraciones de esquema registradas y precedidas por backup.
- Sin proveedor cloud ni secretos reales en este ADR.

## Options

### SQLite y filesystem local

Ventajas:

- Menor número de componentes, credenciales y puntos de fallo.
- Adecuado para una persona y baja concurrencia.
- SQLite satisface el requisito relacional del Model Registry.

Inconvenientes:

- Un solo host y disco son punto único de pérdida.
- Menor concurrencia y ninguna compartición multi-host.
- Metadata y artefactos requieren backup coordinado.

Riesgos: SQLite sobre filesystems con locking dudoso, copias inconsistentes
durante escritura, rutas absolutas no portables, disco lleno o `mlflow gc` sin
política.

Coste operativo: bajo.

### PostgreSQL y filesystem local

Ventajas:

- Mejor concurrencia y administración de metadata.
- Backups SQL estándar y ruta más cercana a operación multiusuario.

Inconvenientes:

- Servicio, credenciales, volumen, driver, health checks y migraciones.
- Los artefactos siguen ligados a una sola máquina.

Riesgos: exponer PostgreSQL, desalinear versiones o restaurar metadata sin sus
artefactos.

Coste operativo: medio.

### PostgreSQL y object storage

Ventajas:

- Artefactos compartidos, escalables y separados de una máquina.
- Mejor encaje futuro para varios hosts.

Inconvenientes:

- Requiere endpoint o proveedor, IAM, red, SDK, cifrado, lifecycle y costes.
- El modo proxy centraliza credenciales pero amplía el acceso del servidor; el
  modo directo distribuye credenciales.

Riesgos: bucket público, permisos excesivos, URIs históricas difíciles de
migrar, fallos de red y backup incompleto entre base y objetos.

Coste operativo: alto.

## Decision

MLflow usará inicialmente SQLite como backend explícito de metadata y
filesystem local como artifact store. Ambos serán persistentes, separados,
configurables e ignorados por Git. No se usará el backend de metadata basado
en archivos legado ni se dependerá de defaults.

La decisión presupone una sola máquina, un operador y baja concurrencia. No
define ni sustituye un feature store. Antes de tratar los runs como evidencia
durable deberá existir un procedimiento de backup/restore conjunto.

Una migración a PostgreSQL u object storage requerirá un ADR futuro cuando
exista concurrencia, uso multiusuario o despliegue remoto. También podrá
reevaluarse ante requisitos de recuperación que el host local no satisfaga.

La aceptación de esta decisión no instala MLflow o SQLite, no crea un
filesystem de artefactos y no implementa servicios ni bases de datos.

## Consequences

- Registry y aliases podrán evaluarse sin operar PostgreSQL.
- La durabilidad estará limitada al host y a la calidad del backup.
- El mecanismo de acceso directo o mediante Tracking Server deberá decidirse
  antes de crear experimentos duraderos.
- El feature store continúa completamente pendiente.

## Reversibility

Media. Es fácil usar otro backend para experimentos nuevos, pero preservar
historia, referencias y artifact URIs requiere una migración probada. MLflow no
debe asumirse como una conversión automática de SQLite a PostgreSQL ni de
filesystem a object storage.

## Open questions

- ¿Acceso directo o Tracking Server local desde el inicio?
- ¿Artefactos servidos por proxy o acceso directo?
- ¿Qué raíz portable se usará para estado y artefactos?
- ¿Qué RPO, RTO, frecuencia, retención y prueba de restore se requieren?
- ¿Cómo se comprobará integridad entre metadata y archivos?
- ¿Se conservará historia en el backend antiguo al migrar?
- ¿Qué límites de concurrencia o volumen dispararán una reevaluación?
- ¿Qué controles impedirán registrar PII o secretos en parámetros y artefactos?

## Sources

- [MLflow backend stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/)
- [MLflow artifact stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/)
- [MLflow Tracking Server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/)
- [MLflow network security](https://mlflow.org/docs/latest/self-hosting/security/network/)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/current/backup-dump.html)
- [SQLite Online Backup API](https://sqlite.org/backup.html)
