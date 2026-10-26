"""Streamlit image-upload UI backed by the FastAPI prediction service."""

import os

import requests
import streamlit as st
from PIL import Image


st.set_page_config(page_title="Fashion-MNIST Classifier", page_icon="👕")
st.title("Fashion-MNIST Classifier")
st.write("Upload a clothing image to classify it with the trained model.")

api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
uploaded_file = st.file_uploader(
    "Choose an image", type=["png", "jpg", "jpeg", "bmp", "webp"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image to classify", width=280)
        if st.button("Predict", type="primary"):
            with st.spinner("Running prediction..."):
                response = requests.post(
                    f"{api_url}/predict",
                    files={
                        "image": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    timeout=60,
                )
            if response.ok:
                result = response.json()
                st.subheader(result["predicted_class"])
                st.metric("Confidence", f"{result['confidence']:.1%}")
                st.bar_chart(result["probabilities"])
                st.caption(f"Model run: {result['model_version']}")
            else:
                try:
                    message = response.json().get("detail", response.text)
                except ValueError:
                    message = response.text
                st.error(f"Prediction service returned {response.status_code}: {message}")
    except (OSError, requests.RequestException) as exc:
        st.error(f"Could not load the image or reach the prediction service: {exc}")

try:
    health = requests.get(f"{api_url}/health", timeout=3)
    health.raise_for_status()
    if not health.json().get("model_available"):
        st.warning("The model is not available yet. Run training, then retry.")
except requests.RequestException:
    st.warning("The FastAPI service is unavailable. Start the Compose prediction stack.")