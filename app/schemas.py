"""FastAPI response models for Fashion-MNIST prediction."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    model_available: bool


class PredictResponse(BaseModel):
    predicted_class: str
    class_index: int
    confidence: float
    probabilities: dict[str, float]
    model_version: str