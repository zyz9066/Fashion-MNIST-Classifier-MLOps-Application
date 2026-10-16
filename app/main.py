"""FastAPI inference service; training runs separately in scripts/train_model.py."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, HTTPException, UploadFile, status
import torch

from app.config import settings
from app.model import CLASS_NAMES, FashionMNISTNet, preprocess_image
from app.schemas import HealthResponse, PredictResponse
from app.storage import download_selected_model

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name, version=settings.app_version)
model: FashionMNISTNet | None = None
model_version = "unavailable"
model_load_error: str | None = None


@app.on_event("startup")
def load_model() -> None:
    global model, model_version, model_load_error
    try:
        with TemporaryDirectory() as directory:
            model_path, model_version = download_selected_model(Path(directory))
            loaded_model = FashionMNISTNet()
            loaded_model.load_state_dict(
                torch.load(model_path, map_location="cpu", weights_only=True)
            )
            loaded_model.eval()
            model = loaded_model
            model_load_error = None
    except Exception as exc:
        model = None
        model_load_error = str(exc)
        logger.error("Model unavailable from MinIO: %s", exc)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok", version=settings.app_version, model_available=model is not None
    )


@app.get("/model/info", tags=["ml"])
def model_info() -> dict[str, object]:
    if model is None:
        raise HTTPException(status_code=503, detail=f"Model is not available: {model_load_error}")
    return {
        "model_type": "LeNet-5-style CNN",
        "input_shape": [1, 28, 28],
        "classes": list(CLASS_NAMES),
        "model_version": model_version,
    }


@app.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify one Fashion-MNIST image",
    tags=["ml"],
)
async def predict(image: UploadFile = File(...)) -> PredictResponse:
    if model is None:
        raise HTTPException(status_code=503, detail=f"Model is not available: {model_load_error}")
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=422, detail="Uploaded image is empty.")
    try:
        tensor = preprocess_image(image_bytes).unsqueeze(0)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
    class_index = int(probabilities.argmax().item())
    return PredictResponse(
        predicted_class=CLASS_NAMES[class_index],
        class_index=class_index,
        confidence=float(probabilities[class_index].item()),
        probabilities={name: float(probabilities[index].item()) for index, name in enumerate(CLASS_NAMES)},
        model_version=model_version,
    )