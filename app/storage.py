"""S3-compatible MinIO helpers for versioned model artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

LATEST_KEY = "model/latest.json"


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )


def ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)


def upload_model(model_path: Path, run_id: str) -> str:
    client = s3_client()
    ensure_bucket(client, settings.model_bucket)
    object_key = f"model/{run_id}/model.pt"
    client.upload_file(str(model_path), settings.model_bucket, object_key)
    manifest = json.dumps({"run_id": run_id, "object_key": object_key}).encode("utf-8")
    client.put_object(
        Bucket=settings.model_bucket,
        Key=LATEST_KEY,
        Body=manifest,
        ContentType="application/json",
    )
    return object_key


def download_selected_model(destination: Path) -> tuple[Path, str]:
    client = s3_client()
    if settings.model_object_key:
        object_key = settings.model_object_key
        version = object_key
    else:
        try:
            response = client.get_object(Bucket=settings.model_bucket, Key=LATEST_KEY)
        except ClientError as exc:
            raise RuntimeError(
                f"No model is available in bucket {settings.model_bucket!r}; "
                "run scripts/train_model.py first."
            ) from exc
        manifest = json.loads(response["Body"].read())
        object_key = manifest["object_key"]
        version = manifest["run_id"]

    model_path = destination / "model.pt"
    try:
        with model_path.open("wb") as model_file:
            client.download_fileobj(settings.model_bucket, object_key, model_file)
    except ClientError as exc:
        raise RuntimeError(
            f"Model object {object_key!r} was not found in bucket {settings.model_bucket!r}."
        ) from exc
    return model_path, version