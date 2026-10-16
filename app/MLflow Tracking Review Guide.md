# Fashion-MNIST MLflow Tracking

The training process in [`scripts/train_model.py`](../scripts/train_model.py) owns the MLflow lifecycle. API startup does not create runs or retrain the model.

Each run records:

- Parameters from `configs/training.toml`, dataset and architecture, selected device, and train/validation sample counts.
- `training_loss`, `validation_loss`, and `validation_accuracy` at every epoch, with epoch number as the MLflow step.
- `training/training_summary.json` and `model/model.pt` artifacts.
- MinIO bucket and versioned object key as run tags after upload succeeds.

Training fails if tracking setup, parameter/metric/artifact logging, or model logging fails. The model upload follows MLflow logging; the success webhook is sent only after both systems have accepted the run and model. The webhook payload includes the run ID, bucket, object key, and final validation accuracy.

For a local Compose deployment, open http://localhost:5000 and select the `fashion-mnist` experiment. The tracking database and MLflow artifacts persist in the `mlflow-data` volume. The serving model is separately stored in MinIO at `fashion-minst-bucket/model/<run-id>/model.pt`; see the root README for startup, selection, and troubleshooting steps.
