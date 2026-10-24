from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[2] / "app" / "streamlit_app.py"


def test_results_view_explains_threshold_tradeoff() -> None:
    app = AppTest.from_file(APP_PATH).run(timeout=60)

    assert not app.exception
    assert any(
        "Parada actual: Capturar más casos" in item.value for item in app.markdown
    )
    assert len(app.metric) == 4
    assert len(app.select_slider) == 1

    app.radio[0].set_value("③ Ser más selectivo").run(timeout=60)

    assert not app.exception
    assert any(
        "Parada actual: Ser más selectivo" in item.value for item in app.markdown
    )


def test_prediction_view_keeps_a_guided_story() -> None:
    app = AppTest.from_file(APP_PATH).run(timeout=60)
    app.radio[1].set_value("Demo de predicción").run(timeout=60)

    assert not app.exception
    assert any(
        "Una simulación para entender el flujo" in item.value for item in app.markdown
    )

    app.button[0].click().run(timeout=60)

    assert not app.exception
    assert any("Resultado de la simulación" in item.value for item in app.subheader)
