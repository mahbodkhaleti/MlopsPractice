"""app.config — environment variable contract for HW3_B.

Mirrors the bundle's contract. If you add an env var here, add it to:
  1. .env.example
  2. entrypoint.sh  (if it's a runtime knob, not a build-time secret)
  3. tests/test_env_contract.py  (if it affects determinism)
"""
from __future__ import annotations

import os
from typing import List

# --- App identity ---
# TODO: read APP_TITLE and APP_VERSION strings (hardcode these constants)
# HINT: APP_TITLE = "QBC12 HW03-B Encoder Embedding & Search API"
# HINT: APP_VERSION = "0.1.0"
APP_TITLE = "QBC12 HW03-B Encoder Embedding & Search API"
APP_VERSION = "0.1.0"

# --- Bundle location (BUNDLE_DIR is the source of truth) ---
# In container: /app/bundle (baked into image)
# In dev:       ../HW3_A/bundle
# TODO: read BUNDLE_DIR from environment, default "/app/bundle"
# HINT: use os.getenv("BUNDLE_DIR", "/app/bundle")
BUNDLE_DIR = os.getenv("BUNDLE_DIR", "/app/bundle")

# TODO: read BUNDLE_DEVICE from environment, default "cpu"
# HINT: use os.getenv("BUNDLE_DEVICE", "cpu")
BUNDLE_DEVICE = os.getenv("BUNDLE_DEVICE", "cpu")

# --- Qdrant (shared, read-only) ---
# TODO: read QDRANT_URL from environment
# HINT: os.getenv("QDRANT_URL", "http://qbc12-qdrant:6333")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qbc12-qdrant:6333")

# TODO: read QDRANT_API_KEY from environment, default ""
# HINT: os.getenv("QDRANT_API_KEY", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# TODO: read QDRANT_COLLECTION from environment, default "qbc12_corpus"
# HINT: os.getenv("QDRANT_COLLECTION", "qbc12_corpus")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "qbc12_corpus")

# --- Postgres (shared, read-only) ---
# TODO: read DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_API_RO_PASSWORD from env
# TODO: assemble DATABASE_URL from the components above
# HINT: f"postgresql://qbc12_hw03_api_ro:{password}@{host}:{port}/{dbname}"
# HINT: also support a direct DATABASE_URL env var as a fallback
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "qbc12_hw03_encoder")
DATABASE_API_RO_PASSWORD = os.getenv("DATABASE_API_RO_PASSWORD", "")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://qbc12_hw03_api_ro:{DATABASE_API_RO_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}",
)

# --- MLflow (for the /model-info endpoint) ---
# TODO: read MLFLOW_TRACKING_URI, MLFLOW_TRACKING_USERNAME, MLFLOW_TRACKING_PASSWORD from env
# HINT: use os.getenv with appropriate defaults
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://185.50.38.163:33014")
MLFLOW_TRACKING_USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME", "")
MLFLOW_TRACKING_PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD", "")

# TODO: read STUDENT_USERNAME from env, fallback to MLFLOW_TRACKING_USERNAME or "student_unknown"
# TODO: read MLFLOW_EXPERIMENT_NAME and MODEL_NAME from env
STUDENT_USERNAME = os.getenv("STUDENT_USERNAME", MLFLOW_TRACKING_USERNAME or "student_unknown")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", f"qbc12_hw03_encoder_{STUDENT_USERNAME}")
MODEL_NAME = os.getenv("MODEL_NAME", MLFLOW_EXPERIMENT_NAME)

# --- Search knobs ---
# TODO: define SEARCH_DEFAULT_TOP_K = 10, SEARCH_MAX_TOP_K = 100, SEARCH_MAX_BATCH_TEXTS = 256
SEARCH_DEFAULT_TOP_K = 10
SEARCH_MAX_TOP_K = 100
SEARCH_MAX_BATCH_TEXTS = 256

# --- Embedding knobs ---
# TODO: define EMBED_MAX_SEQ_LEN = 256, EMBED_BATCH_HARD_CAP = 256, EMBED_DIM = 384
EMBED_MAX_SEQ_LEN = 256
EMBED_BATCH_HARD_CAP = 256
EMBED_DIM = 384
