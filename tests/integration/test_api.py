from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

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
    assert "COP · Credit Risk Model Labs" in frontend.text
    assert 'id="roc-chart"' in frontend.text
    assert (
        "Can the supplied application be associated with the source target?"
        in frontend.text
    )
    assert "Average precision (AP)" in frontend.text
    assert "Brier score" in frontend.text
    assert 'id="probability-chart-comparison"' in frontend.text
    assert "Logistic Regression vs LightGBM" in frontend.text
    assert 'data-preset="late"' in frontend.text
    assert "Edit the 19 academic variables" in frontend.text
    assert "Every field is optional" in frontend.text
    assert "What-if scenario" in frontend.text
    assert "Quick change a variable" in frontend.text
    assert 'id="focus-value" type="number" step="any"' in frontend.text
    assert "Or use a public anonymized case" in frontend.text
    assert 'id="case-summary"' in frontend.text
    assert "case-summary" in frontend.text
    assert "Loading cases" in frontend.text
    assert "Play the story" in frontend.text
    assert 'id="capacity-panel"' in frontend.text
    assert "Precision@capacity" in frontend.text
    assert 'id="calibration-panel"' in frontend.text
    assert "Perfect calibration" in frontend.text
    assert 'id="language-toggle"' in frontend.text
    assert 'id="model-lab-panel"' in frontend.text
    assert 'id="home-credit-panel"' in frontend.text
    assert 'id="home-academic-story"' in frontend.text
    assert 'id="home-academic-status"' in frontend.text
    assert 'id="home-trial-chart"' in frontend.text
    assert 'id="home-iteration-table"' in frontend.text
    assert 'id="home-data-summary"' in frontend.text
    assert 'id="home-feature-comparison"' in frontend.text
    assert 'id="home-feature-ablation-chart"' in frontend.text
    assert 'id="home-classical-benchmark"' in frontend.text
    assert 'id="home-classical-benchmark-chart"' in frontend.text
    assert 'id="home-chapter-neural"' in frontend.text
    assert 'id="home-deep-learning-chart"' in frontend.text
    assert 'id="home-deep-learning-comparison"' in frontend.text
    assert 'id="home-reproducibility"' in frontend.text
    assert "academic-process" in frontend.text
    assert 'id="home-audit-only"' in frontend.text
    assert 'id="home-policy-chart"' in frontend.text
    assert 'id="home-validation-chart"' in frontend.text
    assert 'id="home-calibration-chart"' in frontend.text
    assert 'id="home-policy-lift-chart"' in frontend.text
    assert "What can we conclude?" in frontend.text
    assert 'aria-live="polite"' in frontend.text
    assert "data-story-chapter" in frontend.text
    assert 'id="tab-home-button"' in frontend.text
    assert 'id="tab-uci-button"' in frontend.text
    assert 'id="tab-home"' in frontend.text
    assert 'id="tab-uci"' in frontend.text
    assert "static benchmark" in frontend.text
    assert "Home Credit Default Risk" in frontend.text
    assert 'id="run-model-lab"' in frontend.text
    assert "Which trial performed best?" in frontend.text
    assert 'id="journey-panel"' in frontend.text
    assert "From dataset to final model decision" in frontend.text
    assert "/assets/app.js?v=model-lab-44" in frontend.text
    assert 'id="roc-chart" class="chart uci-chart chart-wide"' in frontend.text
    assert 'id="model-lab-chart" class="model-lab-chart-shell"' in frontend.text
    assert 'href="#tab-uci-button"' not in frontend.text
    assert "3 · UCI reference" not in frontend.text
    assert 'id="tab-home" class="dataset-tab-panel"' in frontend.text
    assert 'id="tab-uci" class="dataset-tab-panel"' in frontend.text
    assert 'id="home-iteration-result"' in frontend.text
    assert "/assets/language.js?v=toggle-5" in frontend.text
    app_script = request("GET", "/assets/app.js?v=model-lab-5")
    assert app_script.status_code == 200
    assert "Plotly.newPlot" in app_script.text
    assert "function resizeCharts(scope)" in app_script.text
    assert "chartRows.length * 38 + 100" in app_script.text
    assert "xshift: 12" in app_script.text
    language_script = request("GET", "/assets/language.js?v=toggle-3")
    assert language_script.status_code == 200
    assert "language-toggle" in language_script.text
    assert 'let language = stored === "es" ? "es" : "en";' in language_script.text
    styles = request("GET", "/assets/styles.css?v=home-academic-1")
    assert styles.status_code == 200
    assert "prefers-reduced-motion" in styles.text
    assert ".home-chapter.is-visible" in styles.text
    assert "You can apply more changes before calculating" in app_script.text
    assert "renderCaseSummary" in app_script.text
    assert "await setupExamples()" in app_script.text
    assert "Academic evidence unavailable" in app_script.text
    assert "Academic evidence loaded" in app_script.text
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

    calibration = request("GET", "/api/calibration")
    assert calibration.status_code == 200
    assert calibration.json()["test_status"] == "unopened"
    assert {row["model"] for row in calibration.json()["models"]} == {
        "logistic_regression",
        "lightgbm",
    }
    assert all(row["points"] for row in calibration.json()["models"])

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

    home_credit = request("GET", "/api/home-credit")
    assert home_credit.status_code == 200
    assert home_credit.json()["authorized_use"] == "academic_static_benchmark_only"
    assert home_credit.json()["test_status"] == "unopened"
    assert {row["model"] for row in home_credit.json()["models"]} == {
        "logistic_regression",
        "lightgbm",
    }

    home_credit_academic = request("GET", "/api/home-credit/academic")
    assert home_credit_academic.status_code == 200
    academic = home_credit_academic.json()
    assert academic["test_status"] == "unopened"
    assert academic["evidence_boundary"]["fit_split"] == "train"
    assert academic["evidence_boundary"]["evaluation_split"] == "validation"
    assert academic["reproducibility"]["split_seed"] == 42
    assert academic["reproducibility"]["experiment_seed"] == 42
    assert academic["reproducibility"]["cross_validation_folds"] == 3
    assert academic["reproducibility"]["feature_version"] == "features-v0"
    if academic["feature_comparison"]["status"] == "available":
        assert academic["feature_comparison"]["baseline_feature_count"] == 44
        assert academic["feature_comparison"]["challenger_feature_count"] == 62
        assert all(
            row["validation_average_precision_delta"]
            == pytest.approx(
                row["challenger_validation_average_precision"]
                - row["baseline_validation_average_precision"]
            )
            for row in academic["feature_comparison"]["models"]
        )
    assert academic["feature_groups"]
    assert academic["iterations"]
    if academic["classical_benchmark"]["status"] == "available":
        assert academic["classical_benchmark"]["test_status"] == "unopened"
        assert academic["classical_benchmark"]["selection_split"] == (
            "train_cross_validation"
        )
        assert academic["classical_benchmark"]["models"]
    if academic["deep_learning"]["status"] == "available":
        assert academic["deep_learning"]["test_status"] == "unopened"
        assert academic["deep_learning"]["architecture"] == [128, 64]
        assert academic["deep_learning"]["validation"]["average_precision"] > 0
    assert all(
        row["iteration_comparison"]["selected_trial"] == row["selected_trial"]
        for row in academic["models"]
    )
    assert all(
        "average_precision_delta" in row["iteration_comparison"]
        for row in academic["models"]
    )
    for row in academic["models"]:
        comparison = row["iteration_comparison"]
        assert comparison["average_precision_delta"] == pytest.approx(
            comparison["selected_average_precision"]
            - comparison["baseline_average_precision"]
        )
    assert academic["calibration"]["status"] == "available"
    assert all(row["points"] for row in academic["calibration"]["models"])
    assert set(academic["policy"]["capacities"]) == {0.01, 0.05, 0.1, 0.2}

    policy = request("GET", "/api/policy-capacity", params={"capacity": 0.1})
    assert policy.status_code == 200
    assert policy.json()["test_status"] == "unopened"
    assert {row["model"] for row in policy.json()["models"]} == {
        "logistic_regression",
        "lightgbm",
    }
    assert all(0 <= row["recall_at_capacity"] <= 1 for row in policy.json()["models"])


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
    payload = response.json()
    assert {row["model"] for row in payload["baseline_predictions"]} == {
        "logistic_regression",
        "lightgbm",
    }
    assert {row["model"] for row in payload["probability_changes"]} == {
        "logistic_regression",
        "lightgbm",
    }
    assert all(
        row["scenario_probability"]
        == next(
            prediction["probability"]
            for prediction in payload["predictions"]
            if prediction["model"] == row["model"]
        )
        for row in payload["probability_changes"]
    )
