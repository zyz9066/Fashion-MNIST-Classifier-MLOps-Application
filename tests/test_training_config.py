from pathlib import Path

import pytest

from app.training_config import load_training_config


def test_example_training_configuration_is_valid() -> None:
    config = load_training_config(Path("configs/training.toml"))
    assert config.epochs > 0
    assert config.optimizer == "Adam"
    assert config.loss_function == "CrossEntropyLoss"


def test_invalid_validation_split_is_rejected(tmp_path) -> None:
    config_path = tmp_path / "training.toml"
    config_path.write_text(
        '[training]\nepochs=1\nbatch_size=1\nlearning_rate=0.001\n'
        'optimizer="Adam"\nloss_function="CrossEntropyLoss"\nrandom_seed=1\n'
        'validation_split=1.0\nmomentum=0.0\nweight_decay=0.0\n'
        'num_workers=0\ndata_dir="data"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="validation_split"):
        load_training_config(config_path)