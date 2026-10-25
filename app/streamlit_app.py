"""Streamlit presentation for the local COP academic MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.metrics import roc_curve
from sklearn.pipeline import Pipeline

from cop.evaluation.academic import run_academic_study
from cop.features.uci import (
    UCI_APPROVED_FEATURES,
    UCI_CATEGORICAL_FEATURES,
)
from cop.training.config import BaselineConfig, load_baseline_config
from cop.training.uci_baseline import MODEL_NAMES, train_development

CONFIG_PATH = Path("configs/training/uci-baseline.yaml")

FEATURE_LABELS = {
    "LIMIT_BAL": "Límite de crédito",
    "PAY_0": "Estado de pago · septiembre",
    "PAY_2": "Estado de pago · agosto",
    "PAY_3": "Estado de pago · julio",
    "PAY_4": "Estado de pago · junio",
    "PAY_5": "Estado de pago · mayo",
    "PAY_6": "Estado de pago · abril",
    "BILL_AMT1": "Saldo del estado de cuenta · septiembre",
    "BILL_AMT2": "Saldo del estado de cuenta · agosto",
    "BILL_AMT3": "Saldo del estado de cuenta · julio",
    "BILL_AMT4": "Saldo del estado de cuenta · junio",
    "BILL_AMT5": "Saldo del estado de cuenta · mayo",
    "BILL_AMT6": "Saldo del estado de cuenta · abril",
    "PAY_AMT1": "Pago realizado · septiembre",
    "PAY_AMT2": "Pago realizado · agosto",
    "PAY_AMT3": "Pago realizado · julio",
    "PAY_AMT4": "Pago realizado · junio",
    "PAY_AMT5": "Pago realizado · mayo",
    "PAY_AMT6": "Pago realizado · abril",
}
PAYMENT_STATUS_LABELS = {
    -2: "Sin consumo",
    -1: "Pago puntual",
    0: "Crédito revolving / sin retraso",
    1: "Retraso de 1 mes",
    2: "Retraso de 2 meses",
    3: "Retraso de 3 meses",
    4: "Retraso de 4 meses",
    5: "Retraso de 5 meses",
    6: "Retraso de 6 meses",
    7: "Retraso de 7 meses",
    8: "Retraso de 8 meses",
    9: "Retraso de 9 meses o más",
}
METRIC_GUIDE = {
    "ROC-AUC": (
        "Capacidad de ordenar casos: cuánto separa el modelo a quienes tienen "
        "más riesgo de quienes tienen menos. 0.5 equivale aproximadamente al azar."
    ),
    "Average precision": (
        "Calidad de las alertas cuando buscamos primero los casos de mayor riesgo. "
        "Es especialmente útil cuando los casos positivos son minoría."
    ),
    "Precision": (
        "De todas las alertas de riesgo que lanza el modelo, cuántas son correctas."
    ),
    "Recall": (
        "De todos los casos que realmente presentan riesgo, cuántos consigue "
        "encontrar el modelo."
    ),
    "F1": (
        "Un equilibrio entre precision y recall. Ayuda a ver si el modelo solo "
        "encuentra pocos casos muy seguros o si también cubre más casos."
    ),
    "Brier score": (
        "Qué tan cerca están las probabilidades estimadas de lo que finalmente "
        "ocurre. Más bajo es mejor; aquí no es una nota de aprobación."
    ),
}


@st.cache_resource(show_spinner="Preparando el baseline académico...")
def load_demo_artifacts() -> tuple[
    BaselineConfig,
    Path,
    dict[str, Any],
    dict[str, Pipeline],
    Path,
    dict[str, Any],
]:
    config = load_baseline_config(CONFIG_PATH)
    run_directory = train_development(CONFIG_PATH)
    manifest = json.loads(
        (run_directory / "run-manifest.json").read_text(encoding="utf-8")
    )
    results = json.loads(
        (run_directory / "validation-results.json").read_text(encoding="utf-8")
    )
    models = {
        name: joblib.load(run_directory / manifest["models"][name]["artifact"]["path"])
        for name in MODEL_NAMES
    }
    if not all(isinstance(model, Pipeline) for model in models.values()):
        raise TypeError("Los artefactos no contienen pipelines sklearn válidos")
    study_directory = run_academic_study(CONFIG_PATH)
    study_results = json.loads(
        (study_directory / "study-results.json").read_text(encoding="utf-8")
    )
    return config, run_directory, results, models, study_directory, study_results


def _metric_table(results: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, metrics in results["models"].items():
        rows.append(
            {
                "Modelo": name,
                "¿Ordena bien? ROC-AUC": metrics["roc_auc"],
                "¿Acertó las alertas? Precision": metrics["precision"],
                "¿Encontró los casos? Recall": metrics["recall"],
                "¿Equilibrio? F1": metrics["f1"],
                "¿Probabilidades fiables? Brier": metrics["brier_score"],
            }
        )
    return pd.DataFrame(rows).set_index("Modelo")


def _show_metric_guide() -> None:
    st.subheader("Las tres preguntas importantes")
    st.markdown(
        "Imagina 100 casos que realmente presentan riesgo. Las métricas no son "
        "una nota: describen qué tipo de errores comete el modelo cuando cambia "
        "la línea de alerta."
    )
    columns = st.columns(3)
    cards = [
        (
            "Recall · cobertura",
            "¿Cuántos casos de riesgo encontramos? Si recall es 80%, encontramos "
            "aproximadamente 80 de cada 100 casos que realmente eran de riesgo.",
            "Prioriza no dejar casos fuera.",
        ),
        (
            "Precision · acierto",
            "¿Cuántas alertas son correctas? Si precision es 60%, 6 de cada 10 "
            "alertas corresponden a un caso que realmente presentó riesgo.",
            "Prioriza no generar falsas alarmas.",
        ),
        (
            "F1 · equilibrio",
            "Combina precision y recall en un solo número. Solo es alto cuando "
            "ambos están razonablemente bien; no premia optimizar uno ignorando "
            "el otro.",
            "Resume el compromiso, no decide por nosotros.",
        ),
    ]
    for column, (title, explanation, emphasis) in zip(columns, cards, strict=True):
        with column:
            st.markdown(f"**{title}**")
            st.caption(explanation)
            st.info(emphasis)
    with st.expander("¿Y el resto de nombres técnicos?"):
        st.markdown(
            "- **ROC-AUC:** mide si el modelo ordena los casos de menor a mayor "
            "riesgo mejor que el azar (0.5).\n"
            "- **Average precision:** resume la calidad de las alertas a lo largo "
            "de muchos thresholds.\n"
            "- **Brier:** mide si sus probabilidades están cerca de lo que acaba "
            "ocurriendo; más bajo es mejor."
        )
        for name, explanation in METRIC_GUIDE.items():
            if name not in {"Precision", "Recall", "F1"}:
                st.caption(f"**{name}:** {explanation}")


def _roc_curve_frame(predictions: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for name in MODEL_NAMES:
        fpr, tpr, thresholds = roc_curve(
            predictions["target"],
            predictions[f"{name}_probability"],
            drop_intermediate=False,
        )
        frames.append(
            pd.DataFrame(
                {
                    "FPR": fpr,
                    "TPR": tpr,
                    "Threshold": thresholds,
                    "Modelo": name,
                }
            )
        )
    return pd.concat(frames, ignore_index=True).set_index("FPR")


def _default_value(feature: str) -> float:
    if feature == "LIMIT_BAL":
        return 50000.0
    if feature in UCI_CATEGORICAL_FEATURES:
        return 0.0
    if feature.startswith("BILL_AMT"):
        return 20000.0
    return 2000.0


def _prediction_form() -> pd.DataFrame:
    values: dict[str, float] = {}
    left, right = st.columns(2)
    for index, feature in enumerate(UCI_APPROVED_FEATURES):
        column = left if index % 2 == 0 else right
        with column:
            label = FEATURE_LABELS[feature]
            if feature in UCI_CATEGORICAL_FEATURES:
                values[feature] = float(
                    st.selectbox(
                        label,
                        options=list(PAYMENT_STATUS_LABELS),
                        index=list(PAYMENT_STATUS_LABELS).index(0),
                        format_func=lambda value: (
                            f"{value}: {PAYMENT_STATUS_LABELS[value]}"
                        ),
                        help=f"Variable UCI {feature}. Mide el estado de pago del mes.",
                        key=f"input_{feature}",
                    )
                )
            else:
                values[feature] = st.number_input(
                    label,
                    value=_default_value(feature),
                    step=1000.0,
                    help=(
                        f"Variable UCI {feature}. Valor monetario en el "
                        "dataset académico."
                    ),
                    key=f"input_{feature}",
                )
    return pd.DataFrame([values], columns=UCI_APPROVED_FEATURES)


def _show_results(
    run_directory: Path,
    results: dict[str, Any],
    config: BaselineConfig,
    study_directory: Path,
    study_results: dict[str, Any],
) -> None:
    st.header("Resultados académicos")
    st.caption(f"Run reproducible: `{run_directory.name}`")
    st.markdown(
        "### La pregunta de esta pantalla\n"
        "¿Podemos usar la probabilidad estimada para poner primero los casos más "
        "arriesgados y explicar qué errores aparecen al cambiar la línea de alerta?"
    )
    _show_metric_guide()
    st.subheader("¿Qué modelo ordena mejor los casos?")
    st.info(
        "Estás viendo una evaluación académica descriptiva sobre validation. El "
        "test permanece cerrado y no existe ningún modelo promovido."
    )
    st.caption(
        "Esta tabla es un resumen de calidad; no es una autorización para tomar "
        "decisiones crediticias. Consulta la guía de métricas antes de leerla."
    )
    st.dataframe(
        _metric_table(results),
        width="stretch",
        column_config={
            "¿Ordena bien? ROC-AUC": st.column_config.NumberColumn(format="%.3f"),
            "¿Acertó las alertas? Precision": st.column_config.NumberColumn(
                format="%.1%"
            ),
            "¿Encontró los casos? Recall": st.column_config.NumberColumn(format="%.1%"),
            "¿Equilibrio? F1": st.column_config.NumberColumn(format="%.1%"),
            "¿Probabilidades fiables? Brier": st.column_config.NumberColumn(
                format="%.3f"
            ),
        },
    )
    predictions = pd.read_csv(run_directory / "validation-predictions.csv")
    st.subheader("Primero: ¿sabe ordenar los casos?")
    st.caption(
        "Cada punto representa una línea de alerta distinta. Al movernos hacia la "
        "esquina superior izquierda encontramos más casos de riesgo, pero también "
        "aceptamos más falsas alarmas. La diagonal punteada representa el azar."
    )
    st.info(
        "**¿Qué es la rodilla o el codo?** Es un punto orientativo donde la curva "
        "deja de ganar muchos casos de riesgo y empieza a pagar demasiadas falsas "
        "alarmas. Aquí sirve para leer la forma de la curva; no selecciona un "
        "threshold productivo."
    )
    roc_frame = _roc_curve_frame(predictions).reset_index()
    roc_chart = px.line(
        roc_frame,
        x="FPR",
        y="TPR",
        color="Modelo",
        hover_data={"FPR": ":.1%", "TPR": ":.1%", "Threshold": ":.2f"},
        markers=True,
        range_x=[0, 1],
        range_y=[0, 1],
        height=360,
    )
    roc_chart.update_layout(
        xaxis_title="Falsas alarmas permitidas (FPR)",
        yaxis_title="Casos de riesgo encontrados (TPR / recall)",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    for model in MODEL_NAMES:
        model_points = roc_frame[roc_frame["Modelo"] == model].copy()
        knee = model_points.loc[(model_points["TPR"] - model_points["FPR"]).idxmax()]
        roc_chart.add_annotation(
            x=float(knee["FPR"]),
            y=float(knee["TPR"]),
            text=f"Rodilla orientativa · {model}<br>threshold {knee['Threshold']:.2f}",
            showarrow=True,
            arrowhead=2,
            ax=45 if model == MODEL_NAMES[0] else -55,
            ay=-35,
            bgcolor="rgba(255,255,255,0.85)",
        )
    roc_chart.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=1,
        y1=1,
        line={"color": "#94a3b8", "dash": "dot", "width": 1},
    )
    roc_chart.add_annotation(
        x=0.78,
        y=0.76,
        text="Azar: 50/50",
        showarrow=False,
        font={"color": "#64748b"},
    )
    roc_chart.update_traces(
        hovertemplate=(
            "Modelo: %{fullData.name}<br>"
            "Falsas alarmas: %{x:.1%}<br>"
            "Riesgo encontrado: %{y:.1%}<extra></extra>"
        )
    )
    st.plotly_chart(
        roc_chart,
        width="stretch",
        config={"displayModeBar": False, "scrollZoom": False},
        alt="Curvas ROC de los modelos académicos",
    )
    st.subheader("Después: ¿qué significa una probabilidad?")
    st.caption(
        "Cada barra agrupa casos según la probabilidad estimada. Una probabilidad "
        "alta no es una certeza: es una señal que debe interpretarse con contexto."
    )
    probability_columns = [f"{name}_probability" for name in MODEL_NAMES]
    probability_frame = predictions[probability_columns].melt(
        var_name="Modelo", value_name="Probabilidad"
    )
    probability_bins = [index / 20 for index in range(21)]
    probability_counts = (
        probability_frame.assign(
            Rango=pd.cut(
                probability_frame["Probabilidad"],
                bins=probability_bins,
                include_lowest=True,
            )
        )["Rango"]
        .value_counts()
        .sort_values(ascending=False)
    )
    highest_bin = probability_counts.index[0]
    highest_bin_center = (highest_bin.left + highest_bin.right) / 2
    highest_bin_count = int(probability_counts.iloc[0])
    probability_chart = px.histogram(
        probability_frame,
        x="Probabilidad",
        color="Modelo",
        nbins=20,
        range_x=[0, 1],
        barmode="overlay",
        opacity=0.65,
        height=360,
    )
    probability_chart.update_layout(
        xaxis_title="Probabilidad estimada de riesgo",
        yaxis_title="Número de casos",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    probability_chart.add_vrect(
        x0=0,
        x1=0.3,
        fillcolor="#dbeafe",
        opacity=0.22,
        line_width=0,
        annotation_text="Señal baja",
        annotation_position="top left",
    )
    probability_chart.add_vrect(
        x0=0.7,
        x1=1,
        fillcolor="#fee2e2",
        opacity=0.22,
        line_width=0,
        annotation_text="Señal alta",
        annotation_position="top right",
    )
    probability_chart.add_vline(
        x=0.5,
        line_dash="dash",
        line_color="#64748b",
        annotation_text="Línea académica 0.50",
        annotation_position="top",
    )
    probability_chart.add_annotation(
        x=highest_bin_center,
        y=highest_bin_count,
        text=(
            "Barra más alta = aquí se concentran más casos,<br>"
            "no significa ‘más riesgo’"
        ),
        showarrow=True,
        arrowhead=2,
        ax=55,
        ay=-45,
        bgcolor="rgba(255,255,255,0.9)",
    )
    probability_chart.update_traces(
        hovertemplate=(
            "Modelo: %{fullData.name}<br>"
            "Probabilidad: %{x:.1%}<br>"
            "Casos: %{y}<extra></extra>"
        )
    )
    st.plotly_chart(
        probability_chart,
        width="stretch",
        config={"displayModeBar": False, "scrollZoom": False},
        alt="Distribución de probabilidades estimadas",
    )
    _show_academic_study(study_directory, study_results)
    with st.expander("Contrato y límites"):
        st.write(
            {
                "features": len(config.raw["features"]["approved"]),
                "fit_split": results["fit_split"],
                "evaluation_split": results["evaluation_split"],
                "threshold": results["threshold"],
                "authorized_use": results["authorized_use"],
                "claims_not_made": results["claims_not_made"],
            }
        )


def _threshold_story(row: pd.Series) -> tuple[str, str, str]:
    threshold = float(row["threshold"])
    if threshold <= 0.30:
        return (
            "Capturar más casos",
            "El modelo baja la línea de alerta. Encuentra más casos de riesgo, "
            "pero también puede generar más falsas alarmas.",
            "Más cobertura · menos selectividad",
        )
    if threshold >= 0.70:
        return (
            "Ser más selectivo",
            "El modelo sube la línea de alerta. Las alertas son más precisas, "
            "pero puede dejar fuera algunos casos de riesgo.",
            "Más precisión · menos cobertura",
        )
    return (
        "Buscar equilibrio",
        "El modelo busca un punto intermedio entre encontrar casos de riesgo y "
        "evitar falsas alarmas. F1 resume ese compromiso.",
        "Equilibrio entre precision y recall",
    )


def _show_threshold_cards(row: pd.Series) -> None:
    title, explanation, balance = _threshold_story(row)
    st.markdown(f"### Parada actual: {title}")
    st.caption(explanation)
    columns = st.columns(4)
    with columns[0]:
        st.metric(
            "Threshold",
            f"{float(row['threshold']):.2f}",
            help="La línea a partir de la cual el modelo marca una alerta académica.",
        )
    with columns[1]:
        st.metric(
            "Recall · cobertura",
            f"{float(row['recall']):.1%}",
            help="De los casos de riesgo reales, cuántos encuentra el modelo.",
        )
    with columns[2]:
        st.metric(
            "Precision · acierto",
            f"{float(row['precision']):.1%}",
            help="De las alertas del modelo, cuántas son casos de riesgo reales.",
        )
    with columns[3]:
        st.metric(
            "F1 · equilibrio",
            f"{float(row['f1']):.1%}",
            help="Resumen del equilibrio entre precision y recall.",
        )
    st.success(f"**Qué estás ganando y qué estás cediendo:** {balance}.")


def _show_academic_study(study_directory: Path, study_results: dict[str, Any]) -> None:
    st.subheader("¿La señal se mantiene si repetimos el experimento?")
    st.markdown(
        "Entrenamos el modelo varias veces con particiones diferentes de los "
        "datos de desarrollo. Si el resultado cambia poco, la señal es más "
        "consistente dentro de este dataset académico. **Validation** es un "
        "bloque reservado para comprobar el resultado al final; no se usó para "
        "elegir el modelo."
    )
    rows = []
    for name, value in study_results["models"].items():
        validation = value["validation"]
        row = {
            "Modelo": name,
            "Ordenación en bloque reservado": validation["roc_auc"],
            "Alertas útiles (AP)": validation["average_precision"],
            "Probabilidades calibradas (Brier)": validation["brier_score"],
        }
        aggregate = value.get("cross_validation", {}).get("aggregate", {})
        if aggregate:
            row["Media al repetir"] = aggregate["roc_auc"]["mean"]
            row["Variación entre repeticiones"] = aggregate["roc_auc"]["std"]
        rows.append(row)
    st.dataframe(
        pd.DataFrame(rows).set_index("Modelo"),
        width="stretch",
        column_config={
            "Ordenación en bloque reservado": st.column_config.NumberColumn(
                format="%.3f"
            ),
            "Alertas útiles (AP)": st.column_config.NumberColumn(format="%.3f"),
            "Probabilidades calibradas (Brier)": st.column_config.NumberColumn(
                format="%.3f"
            ),
            "Media al repetir": st.column_config.NumberColumn(format="%.3f"),
            "Variación entre repeticiones": st.column_config.NumberColumn(
                format="%.3f"
            ),
        },
    )
    st.info(
        "Cómo leerla: ‘Media al repetir’ es el resultado típico; ‘Variación entre "
        "repeticiones’ muestra cuánto se mueve. AP resume si las alertas de mayor "
        "riesgo suelen ser útiles y Brier evalúa si las probabilidades se parecen "
        "a lo que ocurrió. Nada de esto es una garantía para producción."
    )
    st.subheader("3 · Laboratorio visual: mover la línea de alerta")
    st.caption(
        "El threshold es la línea a partir de la cual llamamos ‘alerta’. Primero "
        "elige una parada narrativa y después mueve el control para ver el cambio."
    )
    threshold = pd.read_csv(study_directory / "threshold-sweep.csv")
    selected_model = st.selectbox(
        "Modelo para explorar thresholds", sorted(threshold["model"].unique())
    )
    selected = threshold[threshold["model"] == selected_model].copy()
    balance_row = selected.loc[selected["f1"].idxmax()]
    stop_options = {
        "① Capturar más casos": float(selected["threshold"].min()),
        "② Buscar equilibrio": float(balance_row["threshold"]),
        "③ Ser más selectivo": float(selected["threshold"].max()),
    }
    selected_stop = st.radio(
        "Paradas de la historia",
        list(stop_options),
        horizontal=True,
        help="Cada parada muestra una estrategia distinta para leer las alertas.",
    )
    threshold_value = st.select_slider(
        "Threshold · mueve la línea de alerta",
        options=[float(value) for value in sorted(selected["threshold"].unique())],
        value=stop_options[selected_stop],
        format_func=lambda value: f"{value:.2f}",
        help="Un valor bajo busca cobertura; un valor alto exige más evidencia.",
    )
    current_row = selected.loc[(selected["threshold"] - threshold_value).abs().idxmin()]
    _show_threshold_cards(current_row)

    st.markdown("#### El mapa completo del intercambio")
    st.caption(
        "Lee las líneas de izquierda a derecha: al subir el threshold exigimos "
        "más evidencia. Observa cómo normalmente baja recall y sube precision. "
        "El punto verde marca el mejor F1 dentro de este experimento descriptivo."
    )
    line_frame = selected[["threshold", "precision", "recall", "f1"]].melt(
        id_vars=["threshold"],
        value_vars=["precision", "recall", "f1"],
        var_name="Métrica",
        value_name="Valor",
    )
    line_frame["Métrica"] = line_frame["Métrica"].map(
        {
            "precision": "Precision · acierto",
            "recall": "Recall · cobertura",
            "f1": "F1 · equilibrio",
        }
    )
    tradeoff_chart = px.line(
        line_frame,
        x="threshold",
        y="Valor",
        color="Métrica",
        markers=True,
        range_y=[0, 1],
        height=400,
        labels={
            "threshold": "Threshold · exigencia para lanzar una alerta",
            "Valor": "Proporción (0–1)",
        },
        color_discrete_map={
            "Precision · acierto": "#2563eb",
            "Recall · cobertura": "#f59e0b",
            "F1 · equilibrio": "#16a34a",
        },
    )
    tradeoff_chart.add_vline(
        x=float(current_row["threshold"]),
        line_dash="dash",
        line_color="#111827",
        annotation_text=f"Ahora: {float(current_row['threshold']):.2f}",
        annotation_position="top",
    )
    tradeoff_chart.add_annotation(
        x=float(selected.iloc[0]["threshold"]),
        y=float(selected.iloc[0]["recall"]) + 0.08,
        text="Más cobertura",
        showarrow=True,
        arrowhead=2,
        ax=35,
        ay=-30,
    )
    tradeoff_chart.add_annotation(
        x=float(selected.iloc[-1]["threshold"]),
        y=float(selected.iloc[-1]["precision"]) + 0.08,
        text="Más precisión",
        showarrow=True,
        arrowhead=2,
        ax=-45,
        ay=-30,
    )
    tradeoff_chart.add_annotation(
        x=float(balance_row["threshold"]),
        y=float(balance_row["f1"]) + 0.08,
        text="Mejor F1 del sweep",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-35,
    )
    tradeoff_chart.update_traces(
        hovertemplate=(
            "%{fullData.name}<br>Threshold: %{x:.2f}<br>Valor: %{y:.1%}<extra></extra>"
        )
    )
    st.plotly_chart(
        tradeoff_chart,
        width="stretch",
        config={"displayModeBar": False, "scrollZoom": False},
        alt="Líneas anotadas del trade-off entre precision recall y F1",
    )

    st.markdown("#### Ahora mira cómo se mueve")
    motion_frame = selected.melt(
        id_vars=["threshold"],
        value_vars=["precision", "recall", "f1"],
        var_name="Métrica",
        value_name="Valor",
    )
    motion_chart = px.bar(
        motion_frame,
        x="Métrica",
        y="Valor",
        color="Métrica",
        animation_frame="threshold",
        custom_data=["threshold"],
        range_y=[0, 1],
        height=380,
        title="Dale a ▶ para recorrer la historia del threshold",
        text_auto=".0%",
        labels={
            "Métrica": "Qué estamos priorizando",
            "Valor": "Resultado relativo",
        },
        color_discrete_map={
            "precision": "#2563eb",
            "recall": "#f59e0b",
            "f1": "#16a34a",
        },
    )
    motion_chart.update_layout(
        showlegend=False,
        yaxis_title="Valor (0–1)",
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
    )
    motion_chart.update_traces(
        hovertemplate=(
            "Métrica: %{x}<br>"
            "Valor: %{y:.1%}<br>"
            "Threshold: %{customdata[0]:.2f}<extra></extra>"
        )
    )
    st.plotly_chart(
        motion_chart,
        width="stretch",
        config={"displayModeBar": False, "scrollZoom": False},
        alt="Animación que explica el trade-off entre precision, recall y F1",
    )


def _show_prediction(models: dict[str, Pipeline]) -> None:
    st.header("Demo de predicción")
    st.markdown(
        "### Una simulación para entender el flujo\n"
        "Piensa en esta pantalla como un laboratorio: introduces un perfil "
        "académico, los modelos calculan una probabilidad y luego comparamos "
        "sus señales. No estamos tomando una decisión sobre una persona real."
    )
    st.warning(
        "Esta predicción es ilustrativa y académica. No debe usarse para "
        "aprobar, denegar o modificar crédito real."
    )
    st.caption(
        "Introduce valores de las 19 variables académicas congeladas. Si no "
        "conoces el dataset, empieza con los valores precargados y cambia solo "
        "los estados de pago para observar el efecto."
    )
    with st.expander("¿Qué significan los campos?"):
        st.markdown(
            "Los estados de pago usan la codificación UCI: **-2** sin consumo, "
            "**-1** pago puntual, **0** crédito revolving sin retraso y valores "
            "positivos para meses de retraso. Los saldos y pagos están expresados "
            "en las unidades del dataset académico."
        )
    features = _prediction_form()
    if st.button("Calcular predicción descriptiva", type="primary"):
        st.subheader("Resultado de la simulación")
        st.caption(
            "La cifra es una probabilidad estimada por cada modelo. No significa "
            "que el evento vaya a ocurrir ni debe convertirse en una decisión."
        )
        columns = st.columns(len(MODEL_NAMES))
        for column, name in zip(columns, MODEL_NAMES, strict=True):
            probability = float(models[name].predict_proba(features)[0, 1])
            with column:
                st.metric(
                    name,
                    f"{probability:.1%}",
                    "probabilidad estimada",
                    help=(
                        "Una estimación académica del modelo, no una certeza ni "
                        "una recomendación de crédito."
                    ),
                )
                label = (
                    "por encima de 0.5" if probability >= 0.5 else "por debajo de 0.5"
                )
                st.caption(f"Clasificación descriptiva: {label}")


def main() -> None:
    st.set_page_config(page_title="COP · Academic MVP", page_icon="📊", layout="wide")
    st.title("COP · Credit-risk academic MVP")
    st.sidebar.header("Navegación")
    view = st.sidebar.radio("Vista", ["Resultados académicos", "Demo de predicción"])
    st.sidebar.markdown("**Uso:** portfolio y demostración local")
    st.sidebar.error("No autorizado para decisiones crediticias reales")
    try:
        (
            config,
            run_directory,
            results,
            models,
            study_directory,
            study_results,
        ) = load_demo_artifacts()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        st.error(f"No se pudo cargar el baseline local: {error}")
        st.stop()
    if view == "Resultados académicos":
        _show_results(run_directory, results, config, study_directory, study_results)
    else:
        _show_prediction(models)


if __name__ == "__main__":
    main()
