"""Regression checks for schema import warnings and public response fields."""

import subprocess
import sys
from pathlib import Path

from app.schemas import PredictResponse


def test_schema_import_is_warning_free() -> None:
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", "import app.schemas"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_prediction_response_exposes_image_classification_fields() -> None:
    response = PredictResponse(
        predicted_class="Sneaker",
        class_index=7,
        confidence=0.9,
        probabilities={"Sneaker": 0.9},
        model_version="test-run",
    )
    assert response.model_dump()["predicted_class"] == "Sneaker"
    assert response.model_dump()["model_version"] == "test-run"