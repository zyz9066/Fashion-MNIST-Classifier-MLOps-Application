"""Environment-backed settings for the prediction service."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Fashion-MNIST Classifier API"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    minio_endpoint_url: str = "http://localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    model_bucket: str = "fashion-minst-bucket"
    model_object_key: str = ""


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Fashion-MNIST Classifier API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        minio_endpoint_url=os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000"),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", ""),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", ""),
        model_bucket=os.getenv("MODEL_BUCKET", "fashion-minst-bucket"),
        model_object_key=os.getenv("MODEL_OBJECT_KEY", ""),
    )


settings = load_settings()