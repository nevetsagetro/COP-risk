from pathlib import Path

from scripts.workflow_status import ready_tasks, workflow_status

WORKFLOW = Path("docs/workflows/0031-home-credit-decision-lab.yaml")


def test_current_workflow_has_no_ready_tasks_before_review() -> None:
    assert ready_tasks(WORKFLOW) == []


def test_status_can_filter_by_agent_without_mutating_manifest() -> None:
    summary = workflow_status(WORKFLOW, agent="reviewer")

    assert summary["workflow_id"] == "home-credit-decision-lab"
    assert summary["ready_tasks"] == []
    assert all(task["agent"] == "reviewer" for task in summary["tasks"])
