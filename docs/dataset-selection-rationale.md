# Rationale de selección documental

## Decisión actual

No existe ningún dataset seleccionado o aprobado para entrenamiento. La
segunda búsqueda de Milestone 4B no identifica un candidato elegible:

| Candidato | Resultado |
|---|---|
| Home Credit — Credit Risk Model Stability | **Needs clarification** |
| Home Credit Default Risk | **Reject** |
| UCI Polish Companies Bankruptcy | **Reject** |

Freddie Mac SFLLD Sample 2019 permanece **Reject** tras Milestone 4A. No se
reinterpreta como aceptación parcial ni recomendación.

## Criterio decisivo

El gate exige términos compatibles con un portfolio público, target/horizonte
operacionales, unidad/entidad/decisión verificables, tiempo para un test
intacto, control de leakage, segregación de atributos protegidos y
post-outcome, madurez/censura y monitoring plausible.

Licencia clara no compensa ausencia de tiempo o entidad. Temporalidad
prometedora no compensa términos o target ambiguos.

## Candidato que requiere aclaración

### Home Credit — Credit Risk Model Stability

Es el candidato metodológicamente más prometedor porque la
[descripción oficial](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/data)
incluye caso, fecha de decisión, semanas y tablas históricas. Podría soportar
cohortes, split temporal y monitoring.

No es elegible. Antes de descargar deben verificarse en las
[reglas oficiales](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/rules),
sin aceptarlas durante esta tarea:

1. opción exacta de uso de Competition Data;
2. permiso para portfolio externo no comercial;
3. publicación de código, métricas, gráficos y documentación;
4. publicación/distribución de modelos y parámetros;
5. prohibición y alcance de redistribución;
6. target, horizonte, madurez y censura operacionales;
7. cliente estable y disponibilidad as-of de cada tabla.

Cualquier ambigüedad mantiene bloqueada la cuarentena. Aclarar no equivale a
aceptar reglas o seleccionar el dataset.

## Candidatos rechazados

### Home Credit Default Risk

**Reject.** El [diccionario oficial](https://www.kaggle.com/competitions/home-credit-default-risk/data)
define dificultades de pago mediante constantes `X`/`Y` ocultas y no publica
fecha calendario de decisión por solicitud. Los offsets no ordenan cohortes.
No se puede reproducir target/horizonte, reservar test temporal o demostrar
madurez. Las reglas también requieren aclaración, pero eso no subsana los
fallos duros.

### UCI Polish Companies Bankruptcy

**Reject.** La [ficha UCI](https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy)
ofrece bancarrota, horizontes de uno a cinco años y CC BY 4.0, compatible con
publicación y redistribución atribuida de datos/adaptaciones. El tratamiento de
un modelo entrenado requiere revisión específica. No publica ID de empresa ni
timestamp por fila, por lo que no puede controlarse solape entre casos, corte
as-of, censura o un test temporal intacto.

## Publicación del portfolio

Para Home Credit no se infieren permisos de notebooks, soluciones o mirrors:
solo reglas específicas pueden autorizar outputs. Para Polish, CC BY 4.0
permite compartir/adaptar con atribución, pero no aporta aptitud metodológica.

Datos crudos futuros permanecerían ignorados salvo permiso expreso. Código,
métricas y modelos se revisarían separadamente porque las reglas pueden
tratarlos de modo distinto.

## Próximo paso permitido

Solicitar aclaración documental humana sobre Credit Risk Model Stability,
conservando evidencia fechada de reglas sin aceptarlas ni descargar datos. Si
términos, outputs o target siguen ambiguos, el candidato pasa a `Reject`.

No procede ingesta, datos sintéticos, features, splits o entrenamiento. No se
crea ADR porque no se acepta una fuente.
