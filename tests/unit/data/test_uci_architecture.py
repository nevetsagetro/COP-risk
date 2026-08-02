from __future__ import annotations

import ast
from pathlib import Path

UCI_MODULE_ROOTS = (
    Path("src/cop/data/evaluation"),
    Path("src/cop/data/ingestion"),
)
UCI_ENTRYPOINTS = (
    Path("scripts/download_uci_credit_card.py"),
    Path("scripts/evaluate_dataset_candidate.py"),
)


def test_uci_vertical_does_not_import_synthetic_package() -> None:
    violations: list[str] = []
    paths = [
        *(path for root in UCI_MODULE_ROOTS for path in root.rglob("*.py")),
        *UCI_ENTRYPOINTS,
    ]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "cop.data.synthetic"
            ):
                violations.append(f"{path}:{node.lineno}")
            if isinstance(node, ast.Import):
                violations.extend(
                    f"{path}:{node.lineno}"
                    for alias in node.names
                    if alias.name.startswith("cop.data.synthetic")
                )
    assert violations == []
