# Convención de ExecPlans

Un ExecPlan es un documento ejecutable y autocontenido para un cambio
multi-componente, una decisión arquitectónica o trabajo que pueda abarcar más
de una sesión. Debe permitir que una persona sin contexto previo determine qué
se pretende cambiar, qué existe realmente y cómo verificar el resultado.

`AGENTS.md` conserva autoridad sobre identidad, seguridad, decisiones aceptadas
y decisiones pendientes. Un ExecPlan no sustituye un ADR ni convierte una
propuesta en decisión aceptada.

## Ubicación, nombre y estado

Los planes viven en `docs/plans/` y usan el nombre
`NNNN-descripcion-breve.md`. Deben declarar uno de estos estados:

- `propuesto`: listo para revisión, todavía no autorizado;
- `activo`: trabajo autorizado y en curso;
- `completado`: criterios de aceptación satisfechos y resultados registrados;
- `supersedido`: reemplazado por otro plan identificado explícitamente.

Un roadmap puede agrupar milestones futuros, pero no debe presentarse como un
plan activo de implementación. Cada milestone ejecutado debe tener alcance
pequeño, límites claros y, cuando proceda, su propio ExecPlan.

## Secciones obligatorias

Cada ExecPlan debe contener, en este orden:

1. **Estado del documento**: estado, fecha inicial, última actualización,
   responsable, alcance y fuente normativa.
2. **Propósito y resultado observable**: comportamiento o evidencia que verá
   una persona al terminar.
3. **Base verificada**: inspección real del repositorio, con fecha y comandos
   relevantes; separa archivos existentes de carpetas nominales o trabajo
   planificado.
4. **Alcance**: archivos o componentes permitidos.
5. **Fuera de alcance**: límites explícitos que previenen expansión accidental.
6. **Decisiones**: decisiones aceptadas aplicables, decisiones pendientes y
   propuestas. Cada categoría debe estar diferenciada.
7. **Seguridad y restricciones**: datos, secretos, cumplimiento, compatibilidad
   y restricciones específicas del cambio.
8. **Plan de ejecución**: pasos ordenados, concretos y suficientemente
   detallados para reanudar el trabajo.
9. **Validación y criterios de aceptación**: comandos exactos, resultado
   esperado y condiciones de finalización.
10. **Registro de progreso**: lista fechada con estados pendiente, en curso o
    completado.
11. **Hallazgos inesperados**: hechos observados que afecten el plan.
12. **Registro de decisiones del plan**: decisiones operativas tomadas durante
    la ejecución, con fecha y justificación; las decisiones arquitectónicas
    requieren además un ADR.
13. **Resultados y retrospectiva**: resultados reales, desviaciones,
    validaciones ejecutadas y riesgos restantes.
14. **Version-control allowlist**: rutas concretas que pueden formar parte del
    cierre, artefactos generados prohibidos y mensaje de commit esperado.

Si una sección no aplica, debe permanecer con una explicación breve; no se
elimina.

## Formato obligatorio de la allowlist

Cada ExecPlan técnico contiene exactamente esta sección, con rutas POSIX
relativas. Un directorio termina en `/` y autoriza solo sus descendientes. No
se permiten globs en la lista permitida.

```markdown
## Version-control allowlist

Tracked files or directories allowed:

- path/example.py
- docs/example.md

Generated artifacts forbidden:

- data/**
- models/**
- reports/local/**

Expected commit message:

- feat(scope): description
```

La allowlist es la única fuente del staging automatizado y nunca autoriza
datos, secretos, entornos, caches, modelos, predicciones o runs. El commit
requiere autorización humana explícita; nunca se usa `git add .`.

## Reglas de mantenimiento

- Actualizar el plan en la misma sesión en que cambia el estado del trabajo.
- Registrar hechos y resultados observados, no expectativas redactadas en
  pasado.
- Mantener separados visión, estado verificable, decisiones aceptadas,
  decisiones pendientes y propuestas.
- Marcar cada paso al iniciarlo y completarlo; no cerrar trabajo que dependa de
  una validación no ejecutada.
- Anotar comandos exactos y sus resultados relevantes, incluida cualquier
  validación bloqueada y la causa.
- Incorporar cambios de alcance antes de implementarlos. Si alteran una
  decisión pendiente, detenerse hasta obtener aprobación y registrar el ADR.
- Conservar contexto útil cuando el plan cambie; explicar qué se sustituyó en
  lugar de borrar el rastro de la decisión.
- Actualizar rutas, nombres y criterios cuando el árbol real diverja del plan.
- No afirmar capacidades, servicios, datos o integraciones que no se hayan
  verificado en el working tree.

## Validación

Los comandos dependen del alcance, pero todo ExecPlan debe incluir:

```bash
git diff --check
git status --short
```

Un cambio Python debe incluir, como mínimo:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src tests
python3 -m pytest
```

Cuando cambie configuración TOML, debe parsearse cada archivo afectado. Cuando
el plan introduzca un servicio o integración, debe añadir una comprobación
específica que pruebe su existencia y funcionamiento; la presencia de archivos
de configuración no basta.

## Criterios de finalización

Un ExecPlan solo puede marcarse `completado` cuando:

- todos los pasos dentro de alcance están terminados;
- los criterios de aceptación se satisfacen con evidencia;
- lint, tipos y tests aplicables pasan;
- el diff completo fue revisado y no contiene secretos ni cambios ajenos;
- la documentación describe el estado real resultante;
- el registro de progreso, decisiones, hallazgos y resultados está actualizado;
- las validaciones no ejecutadas se indican como riesgos o bloqueos y no se
  presentan como exitosas;
- no quedan cambios necesarios dentro del alcance acordado.

Una validación bloqueada por el entorno impide afirmar que el plan está
plenamente validado. El plan puede documentar que la implementación está
terminada, pero debe conservar estado `activo` hasta ejecutar las comprobaciones
obligatorias o recibir un criterio de cierre explícito.
