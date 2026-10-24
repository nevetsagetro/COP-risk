from __future__ import annotations

import asyncio
from typing import Any

import httpx

from cop.api import app
from cop.features.uci import UCI_APPROVED_FEATURES


async def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


def request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    return asyncio.run(_request(method, path, **kwargs))


def test_health_and_static_frontend() -> None:
    health = request("GET", "/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "test_status": "unopened"}

    frontend = request("GET", "/")
    assert frontend.status_code == 200
    assert "COP · Credit-Risk Lab" in frontend.text
    assert 'id="roc-chart"' in frontend.text
    assert "Will a default be recorded next month?" in frontend.text
    assert "Average precision (AP)" in frontend.text
    assert "Brier score" in frontend.text
    assert 'data-preset="late"' in frontend.text
    assert "Edit the 19 academic variables" in frontend.text
    assert "You can change one field only" in frontend.text
    assert "Change only one variable" in frontend.text
    assert "Or use a public anonymized case" in frontend.text
    assert "Play the story" in frontend.text
    assert 'id="language-toggle"' in frontend.text
    assert 'id="model-lab-panel"' in frontend.text
    assert 'id="run-model-lab"' in frontend.text
    assert "Which trial performed best?" in frontend.text
    assert 'id="journey-panel"' in frontend.text
    assert "From dataset to final model decision" in frontend.text
    assert "/assets/language.js?v=toggle-2" in frontend.text
    app_script = request("GET", "/assets/app.js?v=model-lab-5")
    assert app_script.status_code == 200
    assert "Plotly.newPlot" in app_script.text
    language_script = request("GET", "/assets/language.js?v=toggle-2")
    assert language_script.status_code == 200
    assert "language-toggle" in language_script.text
    assert 'let language = stored === "es" ? "es" : "en";' in language_script.text
    assert "Change saved" in app_script.text
    plotly_asset = request("GET", "/assets/plotly.min.js?v=english-1")
    assert plotly_asset.status_code == 200
    assert len(plotly_asset.content) > 1_000_000


def test_read_only_analytical_endpoints_keep_test_closed() -> None:
    overview = request("GET", "/api/overview")
    assert overview.status_code == 200
    assert overview.json()["test_status"] == "unopened"
    assert overview.json()["description"].startswith("Local demo")
    assert overview.json()["target_event"] == "default recorded next month"
    assert overview.json()["disclaimer"] == "Not approved for real credit decisions."
    assert overview.json()["journey"]["dataset"]["rows"] == 30000
    assert overview.json()["journey"]["splits"]["test_status"] == "unopened"
    assert (
        overview.json()["journey"]["selection"]["primary_metric"] == "Average Precision"
    )

    metrics = request("GET", "/api/metrics")
    assert metrics.status_code == 200
    assert {row["model"] for row in metrics.json()["validation"]} == {
        "logistic_regression",
        "lightgbm",
    }

    roc = request("GET", "/api/roc")
    assert roc.status_code == 200
    assert len(roc.json()["curves"]) == 2
    assert all(curve["points"] for curve in roc.json()["curves"])

    probabilities = request("GET", "/api/probabilities")
    assert probabilities.status_code == 200
    assert len(probabilities.json()["distributions"]) == 2

    examples = request("GET", "/api/examples")
    assert examples.status_code == 200
    assert examples.json()["cases"]
    assert examples.json()["cases"][0]["summary"].startswith(
        "This public validation record"
    )
    assert examples.json()["cases"][0]["naming_convention"].startswith("UCI-VAL")
    assert set(examples.json()["cases"][0]["features"]) == set(UCI_APPROVED_FEATURES)

    sweep = request("GET", "/api/threshold-sweep", params={"model": "lightgbm"})
    assert sweep.status_code == 200
    assert len(sweep.json()["points"]) == 17

    lab = request("GET", "/api/model-lab")
    assert lab.status_code == 200
    assert lab.json()["test_status"] == "unopened"
    assert set(lab.json()["models"]) == {"logistic_regression", "lightgbm", "knn"}


def test_prediction_endpoint_uses_the_frozen_feature_contract() -> None:
    features = {feature: 0.0 for feature in UCI_APPROVED_FEATURES}
    response = request("POST", "/api/predict", json={"features": features})

    assert response.status_code == 200
    predictions = response.json()["predictions"]
    assert {prediction["model"] for prediction in predictions} == {
        "logistic_regression",
        "lightgbm",
    }
    assert all(0 <= prediction["probability"] <= 1 for prediction in predictions)
    assert response.json()["note"] == "Academic estimate, not a credit decision."


def test_prediction_endpoint_rejects_missing_features() -> None:
    response = request("POST", "/api/predict", json={"features": {}})

    assert response.status_code == 422


def test_prediction_endpoint_applies_only_case_overrides() -> None:
    examples = request("GET", "/api/examples").json()["cases"]
    case_id = examples[0]["case_id"]
    response = request(
        "POST",
        "/api/predict",
        json={"case_id": case_id, "overrides": {"PAY_AMT1": 0.0}},
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == case_id
    assert response.json()["overrides"] == {"PAY_AMT1": 0.0}
