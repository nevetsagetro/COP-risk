# ADR 0002: entorno inicial de ejecución

- Status: Accepted
- Date: 2026-07-25
- Accepted: 2026-07-25
- Decision owners: aprobación humana registrada

## Context

COP es una demo de portfolio local y de una sola persona. No existe proveedor
cloud aceptado, Docker no está verificado en el entorno actual y
`docker-compose.yml` sigue vacío. Los futuros componentes deberán poder
demostrarse sin convertir cloud en prerrequisito.

## Requirements

- Arranque y validación reproducibles en una máquina.
- Secretos fuera de Git y servicios no expuestos por defecto.
- Persistencia y limpieza explícitas.
- Health checks e imágenes fijadas cuando existan servicios.
- Código Python y checks utilizables fuera de contenedores.
- Ninguna elección de proveedor cloud en este ADR.

## Options

### Procesos locales en el host

Ventajas: mínima infraestructura, depuración sencilla y menor coste.

Inconvenientes: mayor dependencia del host y menor aislamiento entre
componentes.

Riesgos: divergencia entre máquinas y procesos o rutas locales no documentados.

Coste operativo: bajo.

### Docker Compose local e incremental

Ventajas:

- Topología declarativa y repetible sin elegir cloud.
- Aislamiento de procesos y volúmenes persistentes explícitos.
- Puede añadirse un servicio cada vez con health checks.

Inconvenientes:

- Docker es otra precondición y no está disponible en el entorno inspeccionado.
- Redes, volúmenes, imágenes y upgrades requieren mantenimiento.

Riesgos: publicar UIs o bases en `0.0.0.0`, usar tags flotantes, perder
volúmenes o presentar el archivo vacío actual como servicio funcional.

Coste operativo: bajo a medio.

### Cloud inicial

Ventajas: acceso remoto, colaboración y posibles servicios gestionados.

Inconvenientes: exige proveedor, IAM, red, secretos, costes, observabilidad y
operación antes de tener una vertical local.

Riesgos: decisión prematura, recursos expuestos, costes inesperados y
acoplamiento al proveedor.

Coste operativo: alto para el alcance actual.

## Decision

COP será local-first. Los comandos Python del dominio seguirán funcionando en
el host y Docker Compose se incorporará incrementalmente solo cuando existan
servicios concretos que lo justifiquen. El despliegue cloud permanece fuera de
alcance y no se selecciona proveedor.

Cuando se materialice Compose, cada servicio deberá usar imagen fijada, volumen
nombrado, health check, configuración mediante variables y binding a loopback
por defecto. Este ADR no define la topología completa ni afirma que el Compose
vacío actual funcione.

La aceptación de esta decisión no implementa Docker Compose, servicios,
infraestructura ni cloud.

## Consequences

- La primera demostración no tendrá dependencia de cloud.
- Podrán coexistir una ruta Python directa y una ruta contenedorizada.
- Habrá que documentar requisitos de Docker y restauración de volúmenes antes
  de introducir servicios persistentes.
- Acceso remoto, alta disponibilidad y operación multiusuario quedan fuera.

## Reversibility

Alta si configuración y persistencia se expresan mediante URI y variables de
entorno. Una migración futura a cloud sustituiría adaptadores, endpoints y
almacenamiento sin cambiar el dominio.

## Open questions

- ¿Docker será requisito obligatorio o una ruta opcional?
- ¿Qué sistemas operativos y recursos mínimos debe soportar la demo?
- ¿Qué servicios justifican entrar primero en Compose?
- ¿Qué puertos, volúmenes, backup y limpieza se permitirán?
- ¿Qué requisitos futuros justificarían iniciar una decisión cloud?

## Sources

- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Compose healthcheck reference](https://docs.docker.com/reference/compose-file/services/#healthcheck)
