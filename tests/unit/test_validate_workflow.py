from __future__ import annotations

from pathlib import Path

from scripts.validate_workflow import validate_workflow


def test_home_credit_workflow_is_valid_and_assigns_multiple_agents() -> None:
    summary = validate_workflow(
        Path("docs/workflows/0031-home-credit-decision-lab.yaml")
    )

    assert summary["workflow_id"] == "home-credit-decision-lab"
    assert summary["waves"] == 5
    assert summary["tasks"] == 11
    assert {
        "coordinator",
        "data_ml",
        "mlops",
        "reviewer",
        "milestone_finisher",
    }.issubset(summary["agents"])
