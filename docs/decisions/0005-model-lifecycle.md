# ADR 0005: lifecycle challenger, champion y rollback

- Status: Accepted
- Date: 2026-07-25
- Accepted: 2026-07-25
- Decision owners: aprobación humana registrada

## Context

COP debe permitir que drift solicite o, en una fase futura, lance retraining
sin promover automáticamente. No existen modelos ni champion. La política debe
separar monitoring, entrenamiento, evaluación, aprobación, promoción y
rollback sin fijar aún dataset, target, métricas o umbrales.

## Requirements

- Drift nunca cambia la referencia del champion.
- Artefactos, versiones y evidencia son inmutables.
- Comparación challenger/champion bajo el mismo contrato y cohortes comparables.
- Promoción y rollback requieren acción humana explícita.
- Transiciones atómicas, idempotentes y auditadas.
- Test intacto protegido de consultas repetidas y selección adaptativa.
- Registro de dataset, split, código, lock, semillas, features, parámetros,
  métricas y artefactos sin PII.

## Options

### Retraining y promoción completamente manuales

Ventajas: máxima simplicidad, control y menor riesgo de carreras.

Inconvenientes: trabajo humano recurrente y menor demostración de
automatización.

Riesgos: procesos manuales inconsistentes si no se registran.

Coste operativo: infraestructura baja; coste humano alto.

### Drift solicita o lanza challenger; promoción manual

Ventajas:

- Automatiza trabajo repetible sin dar autoridad de despliegue al drift.
- Un fallo o rechazo conserva el champion.
- Permite empezar con autorización manual de retraining y automatizarla más
  tarde bajo otro ADR.

Inconvenientes:

- Requiere estados, idempotencia, deduplicación, concurrencia y evidencia.
- Puede crear challengers inútiles por falsos positivos.

Riesgos: sobreusar el test, comparar cohortes distintas, duplicar candidatos o
atribuir erróneamente una aprobación.

Coste operativo: medio.

### Retraining y promoción automáticos tras gates

Ventajas: respuesta rápida y poca intervención.

Inconvenientes: gates imperfectos adquieren autoridad operacional.

Riesgos: amplificar leakage, datos defectuosos o thresholds inestables. Además,
contradice la prohibición de promoción causada por drift.

Coste operativo: alto. Esta opción no es compatible con COP.

## Decision

Se adopta la segunda opción de forma escalonada:

1. Inicialmente, drift crea una solicitud; una acción explícita autoriza
   entrenar.
2. Una señal de drift puede solicitar o iniciar el entrenamiento de un
   challenger, pero nunca promocionarlo automáticamente.
3. Gates automáticos solo rechazan o dejan un challenger pendiente de
   aprobación.
4. Promoción y rollback requieren acción humana explícita, comparación contra
   el champion y registro auditable.
5. Monitoring y el orquestador no pueden mutar el champion.

La aceptación de esta política no implementa entrenamiento, monitoring,
promoción, rollback, scripts de aprobación ni un registry.

Estados lógicos mínimos:

- evento: `observed -> triaged -> linked_to_request | closed`;
- solicitud: `requested -> authorized | declined`, y después
  `running -> completed | failed | cancelled`;
- candidato: `candidate -> evaluating -> rejected | approval_pending`, y
  después `promoted | rejected | expired`;
- champion: `unset -> active(version)` y solo cambia mediante promoción o
  rollback explícitos.

Cada transición registrará de forma append-only actor, fecha, motivo, IDs,
champion anterior, candidate, evidencia revisada y resultado. Un alias mutable
no sustituye este registro.

### Bootstrap del primer champion

Con `champion = unset`, un `seed_candidate` se entrena mediante el pipeline
reproducible, se compara con el baseline no promocionable y pasa una evaluación
predeclarada y revisión humana. La inicialización se registra como
`champion_initialized`, no como una comparación challenger/champion ficticia.
Esta excepción no podrá reutilizarse cuando ya exista champion.

### Rollback

Rollback selecciona explícitamente una versión conservada y compatible; no
reentrena ni reevalúa silenciosamente. Registra actor, motivo, referencia
anterior y objetivo. El modelo retirado y su evidencia se conservan para
investigación. La retención exacta permanece abierta.

## Consequences

- Drift demuestra valor sin adquirir autoridad de despliegue.
- Se necesita conservar más estado, candidatos rechazados y evidencia.
- La promoción tendrá fricción y latencia humanas deliberadas.
- Sin métricas ni gates aprobados, la política controla transiciones pero no
  decide mérito modelístico.
- El mecanismo concreto de aliases depende de la futura implementación MLflow.

## Reversibility

Alta mientras los estados sean contratos lógicos independientes de MLflow,
monitoring y orquestación. Automatizar o desactivar el trigger de entrenamiento
no cambia el gate humano. Cambiar nombres o semántica tras implementar
historial requerirá migración.

## Open questions

- ¿Quién aprueba y cómo se atribuye/autentica la aprobación?
- ¿Es obligatoria revisión independiente para toda promoción?
- ¿Qué evidencia mínima y gates se exigirán?
- ¿Cómo se renuevan cohortes sin gastar repetidamente el test intacto?
- ¿Qué condiciones autorizan rollback y qué versiones se retienen?
- ¿Cómo se resuelven carreras y candidates incompatibles con serving?
- ¿Qué ocurre si no existe champion válido o falla el rollback?
- ¿Qué alias o referencia concreta se usará en MLflow?

## Sources

- [MLflow Model Registry workflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/)
