"""FastAPI response models for Fashion-MNIST prediction."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=("model_validate", "model_dump"))

    status: str = "ok"
    version: str = "0.1.0"
    model_available: bool


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=("model_validate", "model_dump"))

    predicted_class: str
    class_index: int
    confidence: float
    probabilities: dict[str, float]
    model_version: str