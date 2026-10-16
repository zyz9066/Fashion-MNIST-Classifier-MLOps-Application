"""Load and validate the TOML training settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class TrainingConfig:
    epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    loss_function: str
    random_seed: int
    validation_split: float
    momentum: float
    weight_decay: float
    num_workers: int
    data_dir: str


def load_training_config(path: Path) -> TrainingConfig:
    values = tomllib.loads(path.read_text(encoding="utf-8"))["training"]
    config = TrainingConfig(**values)
    if config.epochs < 1 or config.batch_size < 1:
        raise ValueError("epochs and batch_size must be positive integers")
    if config.learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if not 0 < config.validation_split < 1:
        raise ValueError("validation_split must be between 0 and 1")
    if config.optimizer.lower() not in {"adam", "sgd"}:
        raise ValueError("optimizer must be 'Adam' or 'SGD'")
    if config.loss_function.lower() != "crossentropyloss":
        raise ValueError("loss_function must be 'CrossEntropyLoss'")
    if config.num_workers < 0:
        raise ValueError("num_workers cannot be negative")
    return config