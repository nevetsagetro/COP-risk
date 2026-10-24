# ExecPlan 0018: frontend narrativo y laboratorio de trade-off

## Estado del documento

- Estado: completado.
- Fecha inicial: 2026-10-24.
- Última actualización: 2026-10-24.
- Responsable: agente `coordinator`.
- Alcance: mejorar la presentación del demo Streamlit para una audiencia no
  técnica y hacer explícito el trade-off entre precision, recall y F1.
- Fuente normativa: `AGENTS.md`, `PLANS.md`, ExecPlan 0017 y solicitud del
  usuario.

## Propósito y resultado observable

Una persona que no conozca el proyecto debe poder responder, al recorrer la
app:

1. qué problema académico se está explorando;
2. qué significa una probabilidad estimada;
3. qué significa encontrar más casos de riesgo o generar falsas alarmas;
4. por qué subir el threshold suele aumentar precision y reducir recall;
5. por qué F1 resume un equilibrio y no representa una “nota final” del modelo.

El resultado será un demo guiado con un relato corto, pasos numerados, estados
destacados del threshold y tooltips/annotations en los gráficos. El usuario
podrá detener la animación en thresholds concretos y comparar los valores de
precision, recall y F1 en una tarjeta legible.

## Base verificada

El repositorio contiene una app Streamlit en `app/streamlit_app.py` con dos
vistas: resultados académicos y demo de predicción. La vista académica ya
incluye un gráfico Plotly animado del threshold sweep, pero actualmente la
interpretación depende principalmente del texto que acompaña al gráfico. El
estudio genera `threshold-sweep.csv` con thresholds entre 0.10 y 0.90 y las
métricas precision, recall y F1. Los artefactos `runs/**` son locales e
ignorados por Git.

## Alcance

- Reorganizar la vista de resultados como un recorrido de presentación:
  pregunta, evidencia, interpretación y límite.
- Convertir el threshold lab en un componente pedagógico con:
  - threshold actual visible;
  - tres tarjetas para precision, recall y F1;
  - estados explicativos para thresholds bajo, intermedio y alto;
  - marcadores o anotaciones que indiquen “más cobertura”, “más precisión” y
    “equilibrio”.
- Añadir un selector o control de pausa que permita explorar un threshold
  concreto además de la reproducción automática.
- Mejorar tooltips y títulos de los gráficos para evitar abreviaturas sin
  explicación.
- Hacer la vista de predicción más narrativa, mostrando el flujo de entrada,
  estimación y lectura responsable del resultado.
- Añadir tests de Streamlit AppTest para comprobar que las nuevas tarjetas,
  controles y vistas renderizan sin excepciones.
- Actualizar README, CHANGELOG y este plan con capacidades verificadas.

## Fuera de alcance

- Cambiar el modelo, sus hiperparámetros o el dataset.
- Seleccionar un threshold productivo o declarar un champion.
- Convertir el resultado en una decisión de aprobación o denegación.
- Añadir explicabilidad causal, SHAP, fairness cuantitativa o datos reales.
- Añadir API, serving, MLflow, monitoring, autenticación o despliegue cloud.

## Decisiones

### Aceptadas

- El componente visual usará los resultados existentes de `threshold-sweep.csv`.
- Precision, recall y F1 se explicarán con lenguaje cotidiano y se mostrarán
  juntos porque expresan trade-offs distintos.
- El test final continuará cerrado; la mejora será exclusivamente de
  presentación y no alterará el protocolo de evaluación.
- Plotly seguirá siendo la librería de visualización y Streamlit el frontend
  local.

### Pendientes

- Los thresholds exactos que se etiquetarán como bajo, intermedio y alto deben
  derivarse de los valores disponibles, sin presentarlos como gates de negocio.
- La redacción final de las anotaciones debe mantenerse descriptiva y no
  prometer utilidad operativa.

### Propuestas

- Usar tres escenas narrativas: “capturar más casos”, “equilibrar” y “ser más
  selectivo”.
- Mostrar el threshold como una regla de lectura (“por encima de esta línea,
  el modelo marca una alerta académica”), no como una regla de crédito.

## Seguridad y restricciones

- No abrir el test ni generar nuevos claims de rendimiento.
- No usar atributos `audit_only` como inputs.
- Mantener la advertencia de que la app es académica y no está autorizada para
  decisiones crediticias reales.
- No versionar runs, modelos, predicciones ni datos.

## Plan de ejecución

1. Inspeccionar la estructura actual del threshold sweep y elegir thresholds
   representativos disponibles en los artefactos locales.
2. Extraer helpers de presentación para describir el estado del threshold y
   calcular el texto de interpretación sin duplicarlo en la UI.
3. Rediseñar el threshold lab con slider/selectbox, tarjetas métricas,
   anotaciones, reproducción y tooltips.
4. Reordenar la vista de resultados y predicción en escenas cortas que puedan
   explicarse durante una presentación de portfolio.
5. Añadir o actualizar AppTest para validar ambas vistas, el control de
   threshold y la acción de predicción.
6. Ejecutar formato, lint, tipos, tests, `git diff --check` y una comprobación
   visual mediante el servidor local.
7. Actualizar README/CHANGELOG y cerrar este plan solo con evidencia.

## Validación y criterios de aceptación

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy src tests scripts
.venv/bin/pytest -q
.venv/bin/python - <<'PY'
from streamlit.testing.v1 import AppTest

app = AppTest.from_file("app/streamlit_app.py").run(timeout=60)
assert not app.exception
app.radio[0].set_value("Resultados académicos").run(timeout=60)
assert not app.exception
app.radio[0].set_value("Demo de predicción").run(timeout=60)
assert not app.exception
PY
git diff --check
git status --short
```

La aceptación requiere que las dos vistas rendericen sin excepciones, que el
threshold seleccionado actualice las explicaciones y tarjetas, y que el texto
no presente precision, recall o F1 como criterios productivos.

## Registro de progreso

- [x] 2026-10-24: alcance y base verificada.
- [x] 2026-10-24: threshold lab con tres paradas narrativas, selector manual,
  tarjetas y animación Plotly.
- [x] 2026-10-24: escenas guiadas para resultados y predicción.
- [x] 2026-10-24: validación AppTest y comprobación visual mediante ejecución
  local de la app.
- [x] 2026-10-24: README, CHANGELOG y plan actualizados.

## Hallazgos inesperados

Plotly mantiene la animación y el selector manual como dos recorridos
complementarios: la parada narrativa actualiza las tarjetas, mientras que el
botón de reproducción recorre todos los thresholds del sweep.

## Registro de decisiones del plan

- 2026-10-24: se separa esta mejora de la lógica de evaluación porque el
  objetivo es de comunicación y UX, no de modelado.

## Resultados y retrospectiva

La app ahora presenta el threshold como una historia con tres escenas: capturar
más casos, buscar equilibrio y ser más selectivo. La cobertura se explica con
recall, el acierto de las alertas con precision y el compromiso con F1. La
tabla académica ahora formula preguntas comprensibles en lugar de mostrar
encabezados sin contexto. El gráfico del trade-off incluye puntos, etiquetas
para cobertura/precisión/mejor F1, línea del threshold actual y animación con
los valores sobre las barras. La validación final ejecutó 106 tests, Ruff,
mypy, `git diff --check` y AppTest para cambiar de escena y ejecutar la
predicción. La curva ROC ahora muestra thresholds en hover, una línea de azar y
una rodilla orientativa; la distribución de probabilidades anota que la barra
más alta significa concentración de casos, no mayor riesgo. No se modificó el
protocolo del modelo ni se abrió el test.

## Version-control allowlist

Tracked files or directories allowed:

- CHANGELOG.md
- README.md
- app/streamlit_app.py
- docs/plans/0018-frontend-storytelling-and-threshold-lab.md
- tests/integration/test_streamlit_app.py

Generated artifacts forbidden:

- data/**
- models/**
- artifacts/**
- predictions/**
- runs/**
- reports/local/**

Expected commit message:

- feat(frontend): improve academic storytelling and threshold lab
