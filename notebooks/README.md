# Notebooks académicos

Los notebooks son una capa narrativa sobre artefactos reproducibles; no
contienen una ruta paralela de entrenamiento.

Preparación:

```bash
source .venv/bin/activate
python -m pip install -e '.[research]'
```

Ejecución:

```bash
jupyter lab
```

Abrir:

- `01_academic_study.ipynb`: cross-validation, comparación y threshold lab.
- `02_error_analysis.ipynb`: errores, incertidumbre y distribución de scores.

Todos los resultados usan train/validation. El test permanece cerrado.
