"""Inspect ready tasks in an English wave/task workflow manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

import yaml

from scripts.validate_workflow import validate_workflow

READY_STATUS = "ready"
COMPLETED_STATUSES = {"complete"}


def _load(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("workflow root must be a mapping")
    return cast(dict[str, Any], loaded)


def _tasks(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for wave_value in workflow["waves"]:
        wave = cast(dict[str, Any], wave_value)
        for task_value in wave["tasks"]:
            task = dict(cast(dict[str, Any], task_value))
            task["wave_id"] = wave["id"]
            task["wave_name"] = wave["name"]
            result.append(task)
    return result


def ready_tasks(
    path: Path,
    *,
    agent: str | None = None,
    wave_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return tasks explicitly ready and whose dependencies are complete."""
    validate_workflow(path)
    tasks = _tasks(_load(path))
    by_id = {task["id"]: task for task in tasks}
    ready: list[dict[str, Any]] = []
    for task in tasks:
        if task["status"] != READY_STATUS:
            continue
        if agent is not None and task["agent"] != agent:
            continue
        if wave_id is not None and task["wave_id"] != wave_id:
            continue
        dependencies = task["depends_on"]
        if all(
            by_id[dependency]["status"] in COMPLETED_STATUSES
            for dependency in dependencies
        ):
            ready.append(task)
    return ready


def workflow_status(
    path: Path,
    *,
    agent: str | None = None,
    wave_id: str | None = None,
) -> dict[str, Any]:
    """Return a read-only status summary for coordinators and agents."""
    validate_workflow(path)
    workflow = _load(path)
    tasks = _tasks(workflow)
    filtered = [
        task
        for task in tasks
        if (agent is None or task["agent"] == agent)
        and (wave_id is None or task["wave_id"] == wave_id)
    ]
    return {
        "workflow_id": workflow["workflow_id"],
        "status": workflow.get("status"),
        "ready_tasks": ready_tasks(path, agent=agent, wave_id=wave_id),
        "tasks": filtered,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        default=Path("docs/workflows/0031-home-credit-decision-lab.yaml"),
        nargs="?",
    )
    parser.add_argument("--agent", help="Only show tasks owned by this agent.")
    parser.add_argument("--wave", dest="wave_id", help="Only show tasks in this wave.")
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON."
    )
    args = parser.parse_args()
    summary = workflow_status(args.path, agent=args.agent, wave_id=args.wave_id)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    ready = summary["ready_tasks"]
    if not ready:
        print(f"workflow={summary['workflow_id']} ready_tasks=0")
        return 0
    print(f"workflow={summary['workflow_id']} ready_tasks={len(ready)}")
    for task in ready:
        print(f"{task['id']} [{task['agent']}] {task['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
