# MLOps Course Walkthrough

This walkthrough covers the complete Fashion-MNIST training, tracking, storage, notification, and serving lifecycle.

1. Edit `configs/training.toml` to configure the LeNet-style trainer.
2. Run the Compose stack. MLflow records the run and metrics, MinIO stores a versioned model, and a webhook is sent only after successful upload.
3. FastAPI loads the selected object from MinIO and exposes a multipart image prediction endpoint.
4. Streamlit calls the API and displays the class and probabilities.

The full installation, configuration, MLflow, MinIO, webhook, Docker Compose, API, UI, and test instructions are in the root [`README.md`](../README.md). The assignment specification is preserved in the root homework markdown file.
