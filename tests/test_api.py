"""API and preprocessing tests without Docker or external services."""

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
import torch

import app.main as main_module
from app.model import CLASS_NAMES, FashionMNISTNet, preprocess_image


def png_bytes() -> bytes:
    image = Image.new("L", (28, 28), color=128)
    data = BytesIO()
    image.save(data, format="PNG")
    return data.getvalue()


def test_preprocess_image_outputs_training_shape_and_range() -> None:
    tensor = preprocess_image(png_bytes())
    assert tensor.shape == (1, 28, 28)
    assert tensor.dtype == torch.float32
    assert 0 <= tensor.min() <= tensor.max() <= 1


def test_preprocess_image_rejects_invalid_data() -> None:
    try:
        preprocess_image(b"not an image")
    except ValueError as exc:
        assert "valid image" in str(exc)
    else:
        raise AssertionError("invalid image bytes should be rejected")


def test_health_reports_model_state(monkeypatch) -> None:
    def fake_download(destination):
        path = destination / "model.pt"
        torch.save(FashionMNISTNet().state_dict(), path)
        return path, "test-run"

    monkeypatch.setattr(main_module, "download_selected_model", fake_download)
    with TestClient(main_module.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["model_available"] is True


def test_predict_returns_class_and_probabilities(monkeypatch) -> None:
    def fake_download(destination):
        path = destination / "model.pt"
        torch.save(FashionMNISTNet().state_dict(), path)
        return path, "test-run"

    monkeypatch.setattr(main_module, "download_selected_model", fake_download)
    with TestClient(main_module.app) as client:
        response = client.post(
            "/predict", files={"image": ("garment.png", png_bytes(), "image/png")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_class"] in CLASS_NAMES
    assert body["class_index"] in range(10)
    assert set(body["probabilities"]) == set(CLASS_NAMES)
    assert abs(sum(body["probabilities"].values()) - 1) < 1e-5
    assert body["model_version"] == "test-run"


def test_predict_rejects_invalid_image(monkeypatch) -> None:
    def fake_download(destination):
        path = destination / "model.pt"
        torch.save(FashionMNISTNet().state_dict(), path)
        return path, "test-run"

    monkeypatch.setattr(main_module, "download_selected_model", fake_download)
    with TestClient(main_module.app) as client:
        response = client.post("/predict", files={"image": ("bad.txt", b"no", "text/plain")})
    assert response.status_code == 422


def test_prediction_returns_service_unavailable_without_model(monkeypatch) -> None:
    def fail_download(destination):
        raise RuntimeError("model object missing")

    monkeypatch.setattr(main_module, "download_selected_model", fail_download)
    with TestClient(main_module.app) as client:
        response = client.post(
            "/predict", files={"image": ("garment.png", png_bytes(), "image/png")}
        )
    assert response.status_code == 503
    assert "model object missing" in response.json()["detail"]
