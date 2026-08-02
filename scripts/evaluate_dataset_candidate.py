#!/usr/bin/env python3
"""Evaluate UCI by capability and materialize its academic-only snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cop.data.evaluation.academic_splits import create_academic_splits
from cop.data.evaluation.contract import EvaluationError, load_dataset_contract
from cop.data.evaluation.evaluator import evaluate_candidate, load_evaluation
from cop.data.ingestion.uci_credit_card import (
    materialize_academic_snapshot,
    read_source_frame,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/datasets/uci-default-credit-card.yaml"),
    )
    args = parser.parse_args(argv)
    try:
        contract = load_dataset_contract(args.config)
        frame = read_source_frame(contract, args.acquisition)
        evaluation = evaluate_candidate(
            contract, args.acquisition, frame, contract.snapshot_root / "evaluations"
        )
        report = load_evaluation(evaluation)
        print(json_summary(report))
        if not report["academic_snapshot_authorized"]:
            raise EvaluationError("academic snapshot blocked by required gates")
        snapshot = materialize_academic_snapshot(
            contract, args.acquisition, frame, evaluation
        )
        splits = create_academic_splits(
            contract,
            args.acquisition,
            snapshot,
            evaluation,
            contract.snapshot_root / "splits",
        )
        print(f"Academic snapshot: {snapshot}")
        print(f"Academic splits: {splits}")
        return 0
    except (OSError, ValueError, KeyError, EvaluationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def json_summary(report: dict[str, object]) -> str:
    capabilities = report["capabilities"]
    if not isinstance(capabilities, dict):
        raise EvaluationError("evaluation capabilities are invalid")
    return "\n".join(
        f"{name}: {decision['status']}"
        for name, decision in capabilities.items()
        if isinstance(decision, dict)
    )


if __name__ == "__main__":
    raise SystemExit(main())
