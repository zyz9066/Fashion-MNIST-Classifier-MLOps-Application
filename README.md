<<<<<<< HEAD
# Fashion-MNIST-Classifier-MLOps-Application
An end-to-end MLOps application that trains a LeNet-5-style model on Fashion-MNIST, tracks experiments in MLflow, stores the trained model in MinIO, and serves single-image predictions through a FastAPI backend with a Streamlit user interface. Use Docker Compose to run the system’s services.
=======
# Fashion-MNIST MLOps Classifier

End-to-end training and serving for Fashion-MNIST: a LeNet-5-style PyTorch CNN, MLflow experiment tracking, versioned model storage in MinIO, a training-complete webhook, a FastAPI inference API, and a Streamlit upload UI.

## Workflow

```text
configs/training.toml -> Fashion-MNIST train/validation -> MLflow run
        -> MinIO model/<run-id>/model.pt + model/latest.json
        -> training-complete webhook -> FastAPI -> Streamlit
```

Training and inference are separate processes. The API never trains a model during startup. Training writes an immutable model object for each MLflow run and updates `model/latest.json` only after the model upload succeeds. The API loads the object referenced by that manifest at startup.

## Prerequisites

- Docker Desktop with Docker Compose v2
- Git
- Python 3.11+ for local tests or development

## Configure and start

Copy `.env.example` to `.env`, then set a private local MinIO username and password in `.env`. Compose uses those values for S3 access by default; optional `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` can override them. The example values are placeholders, not credentials. `.env` is ignored by Git and excluded from Docker build contexts.

```powershell
Copy-Item .env.example .env
```

Start the complete stack from the repository root:

```powershell
docker compose up --build
```

Compose starts MinIO and MLflow, creates the model bucket, runs the one-shot training service, then starts FastAPI and Streamlit only after training succeeds. The first training run downloads Fashion-MNIST and may take several minutes. Keep the Compose logs open to see epoch metrics and the webhook payload.

Open:

- Streamlit: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs
- FastAPI health: http://localhost:8000/health
- MLflow UI: http://localhost:5000
- MinIO console: http://localhost:9001

Stop services with `Ctrl+C`, or run `docker compose down`. Named volumes preserve MLflow metadata, MinIO model artifacts, and the dataset. `docker compose down -v` also deletes those volumes and their data.

## Training configuration

Edit `configs/training.toml` before starting a new run. No source edits are needed to change the supported settings:

| Setting | Purpose |
| --- | --- |
| `epochs`, `batch_size`, `learning_rate` | Main training schedule |
| `optimizer` | `Adam` or `SGD` |
| `loss_function` | `CrossEntropyLoss` |
| `random_seed` | Python, NumPy, PyTorch, and split seed |
| `validation_split` | Fraction of the training set reserved for validation |
| `momentum`, `weight_decay` | SGD momentum and optimizer regularization |
| `num_workers`, `data_dir` | DataLoader processes and dataset location |

Each run records all settings, model/dataset metadata, per-epoch training and validation loss, per-epoch validation accuracy, the final validation accuracy, a JSON summary, and model artifacts in MLflow. Supported optimizers and loss are deliberately validated to avoid recording a configuration that the trainer cannot execute.

To run another training job against the running dependencies:

```powershell
docker compose run --rm train-model
docker compose restart ml-api
```

The second command makes the API reload the latest manifest. Each run is stored at `model/<mlflow-run-id>/model.pt`; older model objects are not overwritten.

## MLflow

Open http://localhost:5000 and select the `fashion-mnist` experiment. Each row is a training run. Compare parameters and the loss/accuracy metrics across epochs. Model and training-summary artifacts are attached to each run; MinIO bucket and object-key references are stored as run tags.

MLflow uses a persistent local backend/artifact volume for this Compose setup. The independently uploaded inference artifact lives in MinIO.

## MinIO model storage

The required bucket is spelled **`fashion-minst-bucket`** (`minst` is intentional to match the assignment). Model objects use the `model/` prefix and include the MLflow run ID. A small `model/latest.json` manifest points to the newest successfully uploaded model.

The endpoint and credentials are supplied through `MINIO_ENDPOINT_URL`, `MINIO_ACCESS_KEY`, and `MINIO_SECRET_KEY`. Compose sets the endpoint to the internal MinIO service and reads credentials from `.env`. To pin inference to a particular object, set `MODEL_OBJECT_KEY=model/<run-id>/model.pt` in `.env`, then recreate the API service. Leave it blank to use the latest manifest.

If MinIO or the selected object is missing, `/health` reports `model_available: false` and `/predict` returns HTTP 503 with a readable detail message. Training creates the bucket if necessary and fails before notifying if upload or MLflow logging fails.

## Training webhook

After MLflow logging and MinIO upload both succeed, training POSTs this payload to `WEBHOOK_URL`:

```json
{
  "status": "success",
  "event": "training_completed",
  "mlflow_run_id": "<run-id>",
  "model_bucket": "fashion-minst-bucket",
  "model_object_key": "model/<run-id>/model.pt",
  "validation_accuracy": 0.88
}
```

Compose runs a local receiver at `http://localhost:5001/notify`; the received payload appears in `docker compose logs webhook-receiver`. Set `WEBHOOK_URL` to your own receiver when running training outside Compose. An unset URL or unsuccessful POST makes the training command fail rather than silently reporting success.

## Prediction API

`POST /predict` accepts one multipart file field named `image`. The service converts supported image data to grayscale, resizes it to 28 × 28, scales pixels to `[0, 1]`, and returns the ten Fashion-MNIST probabilities.

```powershell
curl.exe -X POST http://localhost:8000/predict -F "image=@path\to\garment.png"
```

A response includes `predicted_class`, `class_index`, `confidence`, per-class `probabilities`, and the loaded model run identifier. Invalid or empty uploads return HTTP 422. `GET /health` is the liveness check; `GET /model/info` reports the selected architecture and model version.

## Streamlit UI

Open http://localhost:8501, upload one PNG/JPEG/BMP/WebP image, preview it, and select **Predict**. The UI calls FastAPI; it does not load or run the model itself. If the API or model is unavailable, the page displays the service error.

## Local development and tests

Install dependencies from the TOML-based project manifest with Poetry, or use the pinned pip list:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

The tests cover preprocessing shape/range, invalid image rejection, API health and response behavior, missing-model errors, configuration validation, and warning-free response schemas. Run the trainer locally with `python scripts/train_model.py --config configs/training.toml` after starting MinIO, MLflow, and a webhook receiver and setting the corresponding environment variables.

## Troubleshooting

- Training or startup errors: `docker compose logs train-model`
- API model-loading errors: `docker compose logs ml-api`
- Webhook payload: `docker compose logs webhook-receiver`
- Service state: `docker compose ps`
- Validate Compose syntax: `docker compose config`
>>>>>>> 68f3065 (Initial commit)
