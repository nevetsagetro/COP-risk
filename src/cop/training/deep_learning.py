"""Offline, reproducible tabular MLP benchmark for Home Credit."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.model_selection import (  # type: ignore[import-untyped]
    StratifiedShuffleSplit,
)

from cop.evaluation.binary import binary_classification_metrics
from cop.training.home_credit import (
    HOME_CREDIT_EXPERIMENT_SEED,
    _preprocessor,
    load_static_development_data,
)

MLP_ARCHITECTURE = (128, 64)
MLP_EPOCHS = 12
MLP_BATCH_SIZE = 4096
MLP_LEARNING_RATE = 0.001
MLP_WEIGHT_DECAY = 0.0001
MLP_DROPOUT = 0.2
MLP_EARLY_STOPPING_PATIENCE = 3
MLP_INTERNAL_HOLDOUT = 0.10


def mlp_parameter_count(
    input_features: int, hidden_layers: tuple[int, ...] = MLP_ARCHITECTURE
) -> int:
    """Return the number of trainable parameters for the declared MLP."""
    dimensions = (input_features, *hidden_layers, 1)
    return int(
        sum((left + 1) * right for left, right in zip(dimensions, dimensions[1:]))
    )


def _dense_float32(values: Any) -> npt.NDArray[np.float32]:
    if hasattr(values, "toarray"):
        values = values.toarray()
    return np.asarray(values, dtype=np.float32)


def _positive_probability(
    network: Any, features: npt.NDArray[np.float32], torch: Any
) -> npt.NDArray[np.float64]:
    network.eval()
    with torch.no_grad():
        logits = network(torch.from_numpy(features)).squeeze(1)
        probability = torch.sigmoid(logits).cpu().numpy()
    return np.asarray(probability, dtype=np.float64)


def _classical_comparison(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"status": "unavailable", "reason": "No cached classical benchmark."}
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for name, payload in report.get("models", {}).items():
        validation = payload.get("validation")
        if isinstance(validation, dict) and "average_precision" in validation:
            rows.append(
                {
                    "model": name,
                    "validation_average_precision": float(
                        validation["average_precision"]
                    ),
                }
            )
    return {
        "status": "available",
        "primary_metric": report.get("primary_metric", "average_precision"),
        "models": rows,
    }


def run_deep_learning_benchmark(
    snapshot_directory: Path,
    *,
    output_directory: Path,
    classical_report: Path | None = None,
    seed: int = HOME_CREDIT_EXPERIMENT_SEED,
    epochs: int = MLP_EPOCHS,
    batch_size: int = MLP_BATCH_SIZE,
    patience: int = MLP_EARLY_STOPPING_PATIENCE,
) -> dict[str, Any]:
    """Train an MLP using train-only early stopping and closed validation."""
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as error:  # pragma: no cover - optional dependency
        return {
            "status": "unavailable",
            "reason": str(error),
            "test_status": "unopened",
        }

    if epochs < 1 or batch_size < 1 or patience < 1:
        raise ValueError("epochs, batch_size and patience must be positive")
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)

    data = load_static_development_data(snapshot_directory)
    train_features = data.train.loc[:, list(data.feature_columns)]
    validation_features = data.validation.loc[:, list(data.feature_columns)]
    train_target = data.train["TARGET"].to_numpy(dtype=np.int64)
    validation_target = data.validation["TARGET"].to_numpy(dtype=np.int64)
    preprocessor = _preprocessor(train_features, scale_numeric=True)
    encoded_train = _dense_float32(preprocessor.fit_transform(train_features))
    encoded_validation = _dense_float32(preprocessor.transform(validation_features))
    splitter = StratifiedShuffleSplit(
        n_splits=1, test_size=MLP_INTERNAL_HOLDOUT, random_state=seed
    )
    fit_indices, early_indices = next(splitter.split(encoded_train, train_target))
    fit_x = torch.from_numpy(encoded_train[fit_indices])
    fit_y = torch.from_numpy(train_target[fit_indices].astype(np.float32))
    early_x = encoded_train[early_indices]
    early_y = train_target[early_indices]
    positive_weight = float((fit_y == 0).sum() / (fit_y == 1).sum())

    layers: list[Any] = []
    input_features = encoded_train.shape[1]
    previous = input_features
    for hidden in MLP_ARCHITECTURE:
        layers.extend([nn.Linear(previous, hidden), nn.ReLU(), nn.Dropout(MLP_DROPOUT)])
        previous = hidden
    layers.append(nn.Linear(previous, 1))
    network = nn.Sequential(*layers)
    optimizer = torch.optim.AdamW(
        network.parameters(), lr=MLP_LEARNING_RATE, weight_decay=MLP_WEIGHT_DECAY
    )
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(positive_weight, dtype=torch.float32)
    )
    loader = DataLoader(
        TensorDataset(fit_x, fit_y),
        batch_size=batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
        num_workers=0,
    )

    best_ap = -1.0
    best_epoch = 0
    stale_epochs = 0
    best_state: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        network.train()
        losses: list[float] = []
        for batch_x, batch_y in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(network(batch_x).squeeze(1), batch_y)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        network.eval()
        with torch.no_grad():
            early_logits = network(torch.from_numpy(early_x)).squeeze(1)
            early_loss = float(
                nn.functional.binary_cross_entropy_with_logits(
                    early_logits,
                    torch.from_numpy(early_y.astype(np.float32)),
                    pos_weight=torch.tensor(positive_weight, dtype=torch.float32),
                )
                .cpu()
                .item()
            )
        early_probability = _positive_probability(network, early_x, torch)
        early_ap = float(
            binary_classification_metrics(early_y, early_probability)[
                "average_precision"
            ]
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": float(np.mean(losses)),
                "early_stopping_loss": early_loss,
                "early_stopping_average_precision": early_ap,
            }
        )
        if early_ap > best_ap:
            best_ap, best_epoch, stale_epochs = early_ap, epoch, 0
            best_state = copy.deepcopy(network.state_dict())
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break
    if best_state is None:
        raise RuntimeError("MLP did not produce a checkpoint")
    network.load_state_dict(best_state)
    validation_probability = _positive_probability(network, encoded_validation, torch)
    output_directory.mkdir(parents=True, exist_ok=True)
    torch.save(network.state_dict(), output_directory / "mlp-state.pt")
    manifest = json.loads(
        (snapshot_directory / "manifest.json").read_text(encoding="utf-8")
    )
    report: dict[str, Any] = {
        "status": "available",
        "authorized_use": "academic_static_benchmark_only",
        "test_status": "unopened",
        "feature_version": manifest.get("feature_version", "unknown"),
        "fit_split": "train_internal_fit",
        "early_stopping_split": "train_internal_holdout",
        "evaluation_split": "validation",
        "experiment_seed": seed,
        "raw_feature_count": len(data.feature_columns),
        "encoded_feature_count": input_features,
        "architecture": list(MLP_ARCHITECTURE),
        "parameter_count": mlp_parameter_count(input_features),
        "hyperparameters": {
            "epochs_requested": epochs,
            "epochs_completed": len(history),
            "batch_size": batch_size,
            "learning_rate": MLP_LEARNING_RATE,
            "weight_decay": MLP_WEIGHT_DECAY,
            "dropout": MLP_DROPOUT,
            "early_stopping_patience": patience,
            "internal_holdout_fraction": MLP_INTERNAL_HOLDOUT,
            "positive_weight": positive_weight,
        },
        "best_epoch": best_epoch,
        "best_internal_average_precision": best_ap,
        "learning_curve": history,
        "validation": binary_classification_metrics(
            validation_target, validation_probability
        ),
        "classical_comparison": _classical_comparison(classical_report),
        "human_explanation": (
            "The MLP learns a nonlinear representation from the same Home Credit "
            "features. Early stopping uses a holdout carved from train; validation "
            "is only evaluated after the network is frozen. The neural architecture "
            "is evidence to compare, not a reason to promote it automatically."
        ),
    }
    (output_directory / "deep-learning-results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pd.DataFrame(
        {
            "SK_ID_CURR": data.validation["SK_ID_CURR"],
            "TARGET": validation_target,
            "mlp_probability": validation_probability,
        }
    ).to_csv(output_directory / "validation-predictions.csv", index=False)
    return report
