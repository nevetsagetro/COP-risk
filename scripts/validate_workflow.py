"""Validate the English wave/task workflow manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import yaml

REQUIRED_AGENTS = {
    "coordinator",
    "data_ml",
    "milestone_finisher",
    "mlops",
    "monitoring",
    "reviewer",
}
REQUIRED_TASK_FIELDS = {
    "id",
    "title",
    "agent",
    "depends_on",
    "allowed_paths",
    "prohibited_paths",
    "status",
}


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def validate_workflow(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("workflow root must be a mapping")
    workflow = cast(dict[str, Any], loaded)
    if workflow.get("workflow_version") != 1:
        raise ValueError("workflow_version must be 1")
    if workflow.get("language") != "en":
        raise ValueError("workflow language must be en")
    waves = _list(workflow.get("waves"), "waves")
    wave_ids: set[str] = set()
    task_ids: set[str] = set()
    tasks: list[dict[str, Any]] = []
    for wave_value in waves:
        if not isinstance(wave_value, dict):
            raise ValueError("each wave must be a mapping")
        wave = cast(dict[str, Any], wave_value)
        wave_id = wave.get("id")
        if not isinstance(wave_id, str) or wave_id in wave_ids:
            raise ValueError(f"duplicate or invalid wave id: {wave_id}")
        wave_ids.add(wave_id)
        for task_value in _list(wave.get("tasks"), f"{wave_id}.tasks"):
            if not isinstance(task_value, dict):
                raise ValueError(f"tasks in {wave_id} must be mappings")
            task = cast(dict[str, Any], task_value)
            if set(task) != REQUIRED_TASK_FIELDS:
                raise ValueError(f"task fields differ for {task.get('id')}")
            task_id = task["id"]
            if not isinstance(task_id, str) or task_id in task_ids:
                raise ValueError(f"duplicate or invalid task id: {task_id}")
            if task["agent"] not in REQUIRED_AGENTS:
                raise ValueError(f"unknown agent for {task_id}: {task['agent']}")
            task_ids.add(task_id)
            tasks.append(task)
    dependencies = {
        task["id"]: set(_list(task["depends_on"], task["id"])) for task in tasks
    }
    unknown_dependencies = {
        dependency for values in dependencies.values() for dependency in values
    } - task_ids
    if unknown_dependencies:
        raise ValueError(f"unknown task dependencies: {sorted(unknown_dependencies)}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError(f"dependency cycle includes {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependencies[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        visit(task_id)
    return {
        "workflow_id": workflow.get("workflow_id"),
        "waves": len(waves),
        "tasks": len(tasks),
        "agents": sorted({task["agent"] for task in tasks}),
        "task_ids": sorted(task_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        default=Path("docs/workflows/0031-home-credit-decision-lab.yaml"),
        nargs="?",
    )
    args = parser.parse_args()
    summary = validate_workflow(args.path)
    print(
        f"valid workflow={summary['workflow_id']} "
        f"waves={summary['waves']} tasks={summary['tasks']} "
        f"agents={','.join(summary['agents'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
