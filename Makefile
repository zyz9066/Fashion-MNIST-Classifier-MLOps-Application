PYTHON ?= python
API_APP ?= app.main:app
API_PORT ?= 8000
MLFLOW_PORT ?= 5000

.PHONY: train test run-api run-mlflow compose-up compose-down compose-smoke

train:
	docker compose run --rm train-model

test:
	$(PYTHON) -m pytest -q

run-api:
	docker compose up --build ml-api streamlit

run-mlflow:
	docker compose up --build mlflow minio

compose-up:
	docker compose up --build

compose-down:
	docker compose down

compose-smoke:
	./scripts/smoke_test.sh