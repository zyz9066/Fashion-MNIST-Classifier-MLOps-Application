"""Train, track, store, then notify for a Fashion-MNIST model."""

import argparse
import json
import logging
import os
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mlflow
import mlflow.pytorch
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

from app.config import settings
from app.model import FashionMNISTNet
from app.storage import upload_model
from app.training_config import TrainingConfig, load_training_config
from app.webhook import send_webhook

logger = logging.getLogger("fashion_mnist_training")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_optimizer(name: str, model: torch.nn.Module, config: TrainingConfig):
    if name.lower() == "adam":
        return torch.optim.Adam(
            model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
        )
    return torch.optim.SGD(
        model.parameters(),
        lr=config.learning_rate,
        momentum=config.momentum,
        weight_decay=config.weight_decay,
    )


def evaluate(model, loader, loss_fn, device) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    count = 0
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            total_loss += float(loss_fn(logits, labels).item()) * labels.size(0)
            correct += int((logits.argmax(dim=1) == labels).sum().item())
            count += labels.size(0)
    return total_loss / count, correct / count


def train(config: TrainingConfig) -> dict[str, object]:
    webhook_url = os.getenv("WEBHOOK_URL", "")
    if not webhook_url:
        raise RuntimeError("WEBHOOK_URL must be set; successful training requires notification.")

    set_seed(config.random_seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = datasets.FashionMNIST(
        root=config.data_dir, train=True, download=True, transform=transforms.ToTensor()
    )
    validation_size = max(1, int(len(dataset) * config.validation_split))
    training_size = len(dataset) - validation_size
    training_data, validation_data = random_split(
        dataset,
        [training_size, validation_size],
        generator=torch.Generator().manual_seed(config.random_seed),
    )
    training_loader = DataLoader(
        training_data, batch_size=config.batch_size, shuffle=True,
        num_workers=config.num_workers,
    )
    validation_loader = DataLoader(
        validation_data, batch_size=config.batch_size, shuffle=False,
        num_workers=config.num_workers,
    )

    model = FashionMNISTNet().to(device)
    optimizer = build_optimizer(config.optimizer, model, config)
    loss_fn = nn.CrossEntropyLoss()
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "fashion-mnist"))

    with TemporaryDirectory() as directory, mlflow.start_run(
        run_name=os.getenv("MLFLOW_RUN_NAME") or None
    ) as run:
        run_id = run.info.run_id
        parameters = {
            **config.__dict__,
            "model_architecture": "LeNet-5-style CNN",
            "dataset": "Fashion-MNIST",
            "device": str(device),
            "training_samples": training_size,
            "validation_samples": validation_size,
        }
        mlflow.log_params(parameters)

        for epoch in range(config.epochs):
            model.train()
            epoch_loss = 0.0
            sample_count = 0
            for images, labels in training_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(images), labels)
                loss.backward()
                optimizer.step()
                epoch_loss += float(loss.item()) * labels.size(0)
                sample_count += labels.size(0)

            training_loss = epoch_loss / sample_count
            validation_loss, validation_accuracy = evaluate(
                model, validation_loader, loss_fn, device
            )
            mlflow.log_metrics(
                {
                    "training_loss": training_loss,
                    "validation_loss": validation_loss,
                    "validation_accuracy": validation_accuracy,
                },
                step=epoch + 1,
            )
            logger.info(
                "epoch=%s/%s train_loss=%.4f val_loss=%.4f val_accuracy=%.4f",
                epoch + 1, config.epochs, training_loss, validation_loss, validation_accuracy,
            )

        model_path = Path(directory) / "model.pt"
        torch.save(model.cpu().state_dict(), model_path)
        summary_path = Path(directory) / "training_summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "configuration": parameters,
                    "validation_accuracy": validation_accuracy,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        mlflow.log_artifact(str(summary_path), artifact_path="training")
        mlflow.log_artifact(str(model_path), artifact_path="model")
        object_key = upload_model(model_path, run_id)
        mlflow.set_tag("minio.bucket", settings.model_bucket)
        mlflow.set_tag("minio.object_key", object_key)

    payload = {
        "status": "success",
        "event": "training_completed",
        "mlflow_run_id": run_id,
        "model_bucket": settings.model_bucket,
        "model_object_key": object_key,
        "validation_accuracy": validation_accuracy,
    }
    send_webhook(webhook_url, payload)
    logger.info("Training complete; model=%s/%s", settings.model_bucket, object_key)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=PROJECT_ROOT / "configs" / "training.toml"
    )
    args = parser.parse_args()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    print(json.dumps(train(load_training_config(args.config)), indent=2))


if __name__ == "__main__":
    main()