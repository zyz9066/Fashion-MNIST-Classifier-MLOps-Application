#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
MLFLOW_BASE="${MLFLOW_BASE:-http://localhost:5000}"

printf '1. Check model readiness\n'
health=$(curl -sf "${API_BASE}/health")
printf '%s\n' "$health"
grep -q '"model_available":true' <<<"$health"

printf '2. Check model metadata and MLflow UI\n'
curl -sf "${API_BASE}/model/info"
curl -sf "${MLFLOW_BASE}/" >/dev/null

printf '3. Upload a single image and verify a class prediction\n'
image_path=$(mktemp --suffix=.png)
trap 'rm -f "$image_path"' EXIT
python -c "from PIL import Image; Image.new('L', (28, 28), 128).save('$image_path')"
prediction=$(curl -sf -X POST "${API_BASE}/predict" -F "image=@${image_path};type=image/png")
printf '%s\n' "$prediction"
grep -q '"predicted_class"' <<<"$prediction"
grep -q '"probabilities"' <<<"$prediction"

printf '4. Confirm invalid image data is rejected\n'
status_code=$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "${API_BASE}/predict" -F "image=@scripts/smoke_test.sh;type=image/png")
test "$status_code" = "422"

printf '5. Confirm the training notification reached the local receiver\n'
docker compose logs --no-color webhook-receiver 2>&1 | grep -q 'training_completed'

printf 'Smoke test completed.\n'
