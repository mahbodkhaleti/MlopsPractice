"""app.main — FastAPI entrypoint for HW3_B.

Endpoints:
  GET  /              — service root
  GET  /health        — bundle + Qdrant + PG reachability
  GET  /model-info    — bundle metadata + Qdrant vector count
  POST /embed         — text(s) → 384-dim vectors
  POST /predict       — single text → predicted emotion label
  POST /search        — query → Qdrant ANN + PG audit
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, status

from . import client_pg, client_qdrant, config
from . import predictor as predictor_mod
from .model_loader import ModelService
from .schemas import (
    EmbedRequest,
    EmbedResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    RootResponse,
    SearchRequest,
    SearchResponse,
)
from .search import hybrid_search

log = logging.getLogger("hw3_b")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


# TODO: create a global ModelService instance
# HINT: model_service = ModelService()
model_service = ModelService()


# TODO: define the lifespan context manager for FastAPI
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     log.info("HW3_B starting. BUNDLE_DIR=%s", config.BUNDLE_DIR)
#     model_service.load()
#     if model_service.state.loaded:
#         log.info("Bundle loaded: %s", model_service.state.bundle_dir)
#     else:
#         log.error("Bundle load FAILED: %s", model_service.state.error)
#     yield
#     log.info("HW3_B shutting down.")
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("HW3_B starting. BUNDLE_DIR=%s", config.BUNDLE_DIR)
    model_service.load()
    if model_service.state.loaded:
        log.info("Bundle loaded: %s", model_service.state.bundle_dir)
    else:
        log.error("Bundle load FAILED: %s", model_service.state.error)
    yield
    log.info("HW3_B shutting down.")


# TODO: create the FastAPI app instance
# HINT: app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION, lifespan=lifespan)
app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION, lifespan=lifespan)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


# TODO: implement GET / endpoint
# @app.get("/", response_model=RootResponse, tags=["service"])
# Return RootResponse with service name, version, and endpoint list
# HINT: RootResponse(message="QBC12 HW3 Encoder API", docs="/docs", health="/health", version=config.APP_VERSION)
@app.get("/", response_model=RootResponse, tags=["service"])
def root() -> RootResponse:
    return RootResponse(
        message="QBC12 HW3 Encoder API",
        docs="/docs",
        health="/health",
        version=config.APP_VERSION,
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


# TODO: implement GET /health endpoint
# @app.get("/health", response_model=HealthResponse, tags=["service"])
# Check bundle loaded status, Qdrant reachability, and Postgres reachability.
# Return 200 with status="ok" when all three are healthy,
# status="degraded" when some are down (do NOT raise 5xx — health is a probe).
# HINT: use client_qdrant.ping() and client_pg.ping()
# HINT: bundle_ok = model_service.state.loaded
# HINT: format bundle_dir as string from model_service.state.bundle_dir
@app.get("/health", response_model=HealthResponse, tags=["service"])
def health() -> HealthResponse:
    bundle_ok = model_service.state.loaded
    qdrant_ok = client_qdrant.ping()
    pg_ok = client_pg.ping()
    status_value = "ok" if bundle_ok and qdrant_ok and pg_ok else "degraded"
    return HealthResponse(
        status=status_value,
        bundle_loaded=bundle_ok,
        bundle_dir=str(model_service.state.bundle_dir or ""),
        qdrant_reachable=qdrant_ok,
        pg_reachable=pg_ok,
        error=model_service.state.error,
    )


@app.get("/healthz/live", tags=["service"])
def live() -> dict:
    return {"status": "ok"}


@app.get("/healthz/ready", tags=["service"])
def ready() -> dict:
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail=model_service.state.error or "model not loaded")
    return {"status": "ok", "bundle_loaded": True}


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------


# TODO: implement GET /model-info endpoint
# @app.get("/model-info", response_model=ModelInfoResponse, tags=["model"])
# Return bundle metadata + Qdrant vector count.
# If bundle not loaded, raise HTTPException(status_code=503, detail=...)
# HINT: use client_qdrant.vector_count(config.QDRANT_COLLECTION)
# HINT: read metadata from model_service.metadata dict
# HINT: model_service.metadata.get("model_name", "unknown")
# HINT: model_service.metadata.get("embedding_dim", 384)
@app.get("/model-info", response_model=ModelInfoResponse, tags=["model"])
def model_info() -> ModelInfoResponse:
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail=model_service.state.error or "model not loaded")
    metadata = model_service.metadata
    return ModelInfoResponse(
        bundle_version=str(metadata.get("bundle_version", "unknown")),
        model_id=str(metadata.get("model_name", metadata.get("model_id", "unknown"))),
        model_revision=str(metadata.get("model_revision", "unknown")),
        device=str(metadata.get("device", config.BUNDLE_DEVICE)),
        max_seq_len=int(metadata.get("max_seq_len", metadata.get("max_sequence_length", config.EMBED_MAX_SEQ_LEN))),
        embedding_dim=int(metadata.get("embedding_dim", config.EMBED_DIM)),
        bundle_dir=str(model_service.state.bundle_dir or ""),
        qdrant_collection=config.QDRANT_COLLECTION,
        qdrant_vector_count=client_qdrant.vector_count(config.QDRANT_COLLECTION),
    )


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


# TODO: implement POST /embed endpoint
# @app.post("/embed", response_model=EmbedResponse, tags=["embedding"])
# Accept EmbedRequest, call predictor_mod.embed_texts() to get numpy array,
# convert to list of lists, return EmbedResponse.
# If bundle not loaded, raise HTTPException(503, detail="model not loaded")
# If batch exceeds hard cap (config.EMBED_BATCH_HARD_CAP), raise HTTPException(413)
# HINT: t0 = time.perf_counter()
# HINT: vectors = predictor_mod.embed_texts(model_service.require_predictor(), req.texts)
# HINT: embeddings_list = vectors.tolist()
# HINT: return EmbedResponse(count=len(req.texts), dim=vectors.shape[1], embeddings=embeddings_list)
@app.post("/embed", response_model=EmbedResponse, tags=["embedding"])
def embed(req: EmbedRequest) -> EmbedResponse:
    if len(req.texts) > config.EMBED_BATCH_HARD_CAP:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="batch too large")
    try:
        vectors = predictor_mod.embed_texts(model_service.require_predictor(), req.texts)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return EmbedResponse(count=len(req.texts), dim=vectors.shape[1], embeddings=vectors.tolist())


# ---------------------------------------------------------------------------
# /predict — single text → emotion label via nearest neighbor
# ---------------------------------------------------------------------------

# TODO: implement POST /predict endpoint
# @app.post("/predict", response_model=PredictResponse, tags=["embedding"])
# Single text → embed → Qdrant top-1 → return predicted label + confidence.
# If bundle not loaded, raise HTTPException(503, detail="model not loaded")
# If no match found, raise HTTPException(404, detail="no match found in corpus")
# HINT: vec = model_service.embed(req.text).tolist()
# HINT: qc = config.get_qdrant_client(read=True)
# HINT: hits = qc.search(collection_name=config.QDRANT_COLLECTION, query_vector=vec, limit=1)
# HINT: best = hits[0]; label = best.payload.get("primary_label", "unknown")
# HINT: return PredictResponse(text=req.text, predicted_label=label, confidence=best.score, matched_text=best.payload["text"], elapsed_ms=elapsed)
@app.post("/predict", response_model=PredictResponse, tags=["embedding"])
def predict(req: PredictRequest) -> PredictResponse:
    t0 = time.perf_counter()
    try:
        vec = predictor_mod.embed_texts(model_service.require_predictor(), [req.text])[0].tolist()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    hits = client_qdrant.search(
        collection=config.QDRANT_COLLECTION,
        vector=vec,
        top_k=1,
        lang="en",
        primary=None,
        exclude_neutral=True,
    )
    if not hits:
        raise HTTPException(status_code=404, detail="no match found in corpus")
    best = hits[0]
    payload = best.payload or {}
    elapsed = (time.perf_counter() - t0) * 1000.0
    return PredictResponse(
        text=req.text,
        predicted_label=str(payload.get("primary_label", payload.get("primary", "unknown"))),
        confidence=float(best.score),
        matched_text=str(payload.get("text", "")),
        elapsed_ms=elapsed,
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


# TODO: implement POST /search endpoint
# @app.post("/search", response_model=SearchResponse, tags=["search"])
# Accept SearchRequest, embed the query text, call hybrid_search(),
# return SearchResponse with hits and timing.
# If bundle not loaded, raise HTTPException(503, detail="model not loaded")
# HINT: query_vec = predictor_mod.embed_texts(model_service.require_predictor(), [req.query])
# HINT: query_vec_list = query_vec[0].tolist()
# HINT: hits, took_ms = hybrid_search(query_vec_list, req.top_k, req.lang, req.primary, req.exclude_neutral)
# HINT: return SearchResponse(query=req.query, count=len(hits), top_k=req.top_k, took_ms=took_ms, hits=hits)
@app.post("/search", response_model=SearchResponse, tags=["search"])
def search(req: SearchRequest) -> SearchResponse:
    try:
        query_vec = predictor_mod.embed_texts(model_service.require_predictor(), [req.query])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    hits, took_ms = hybrid_search(
        query_vec[0].tolist(),
        req.top_k,
        req.lang,
        req.primary,
        req.exclude_neutral,
    )
    return SearchResponse(query=req.query, count=len(hits), top_k=req.top_k, took_ms=took_ms, hits=hits)
