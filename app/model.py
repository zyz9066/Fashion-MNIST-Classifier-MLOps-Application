"""LeNet-5-style model and shared image preprocessing."""

from io import BytesIO

import numpy as np
from PIL import Image, UnidentifiedImageError
import torch
from torch import nn


CLASS_NAMES = (
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot",
)


class FashionMNISTNet(nn.Module):
    """LeNet-5-style CNN for grayscale 28 by 28 Fashion-MNIST images."""

    def __init__(self) -> None:
        super().__init__()
        self._features = nn.Sequential(
            nn.Conv2d(1, 6, 5),
            nn.BatchNorm2d(6),
            nn.ReLU(),
            nn.MaxPool2d(2, stride=2),
            nn.Conv2d(6, 16, 5),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, stride=2),
        )
        self._classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(16 * 4 * 4, 120),
            nn.ReLU(),
            nn.Linear(120, 84),
            nn.ReLU(),
            nn.Linear(84, len(CLASS_NAMES)),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self._classifier(self._features(images))


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """Convert any supported image to the same 1x28x28 tensor used in training."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            grayscale = image.convert("L").resize((28, 28), Image.Resampling.LANCZOS)
            pixels = np.asarray(grayscale, dtype=np.float32) / 255.0
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Upload a valid image file.") from exc
    return torch.from_numpy(pixels).unsqueeze(0)