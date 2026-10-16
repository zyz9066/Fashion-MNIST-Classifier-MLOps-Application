"""Strict HTTP delivery for training-complete notifications."""

from __future__ import annotations

import requests


def send_webhook(url: str, payload: dict[str, object], timeout: int = 10) -> None:
    """POST a JSON event and raise if the receiver does not accept it."""
    if not url:
        raise ValueError("A webhook URL is required")
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()