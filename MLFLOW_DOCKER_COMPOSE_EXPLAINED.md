# MLflow in the Fashion-MNIST Compose Stack

The MLflow service in `docker-compose.yml` stores run metadata in a SQLite database and MLflow artifacts under a persistent Docker volume. The trainer connects to it at `http://mlflow:5000` from inside the Compose network; the browser uses `http://localhost:5000`.

Run the complete dependency-ordered workflow from the repository root:

```powershell
Copy-Item .env.example .env
# Set local MinIO credentials in .env
docker compose up --build
```

Compose waits for MLflow health before training. The one-shot `train-model` service logs the configured parameters, per-epoch training/validation metrics, JSON summary, and model to the `fashion-mnist` experiment. It then uploads a versioned model to MinIO and sends the success webhook. The FastAPI service depends on successful completion of that job; Streamlit waits for API health.

Open http://localhost:5000 and select the `fashion-mnist` experiment. The `mlflow-data` volume preserves the backend database and MLflow artifact files across container restarts. MinIO stores the separately uploaded inference model in `fashion-minst-bucket/model/<run-id>/model.pt`.

Useful commands:

```powershell
docker compose logs -f mlflow
docker compose logs train-model
docker compose run --rm train-model
docker compose restart ml-api
```

The run command retrains and updates MinIO's `model/latest.json`; restarting the API reloads that selected model. See the root README for complete configuration, MinIO selection, webhook payload, and prediction instructions.
