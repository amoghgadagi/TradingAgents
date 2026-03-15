from __future__ import annotations

import os

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
DEFAULT_OUTPUT_DIR = os.getenv("MAIMIS_OUTPUT_DIR", "outputs/maimis")
