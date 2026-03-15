from __future__ import annotations

import requests

BASE_URL = "https://www.alphavantage.co/query"


def av_get(params: dict, timeout: int = 20) -> dict:
    response = requests.get(BASE_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()
