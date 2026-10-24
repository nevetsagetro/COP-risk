"""FastAPI entrypoint for the local academic analytical lab."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import plotly  # type: ignore[import-untyped]
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from cop.serving.academic import AcademicService

CONFIG_PATH = Path(
    os.environ.get("COP_CONFIG_PATH", "configs/training/uci-baseline.yaml")
)
WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "app" / "web"
PLOTLY_ASSET = Path(plotly.__file__).resolve().parent / "package_data" / "plotly.min.js"


class PredictionRequest(BaseModel):
    features: dict[str, float] | None = Field(
        None, description="Complete vector of the 19 approved features."
    )
    case_id: str | None = Field(
        None, description="Validation case used as the base for partial changes."
    )
    overrides: dict[str, float] | None = Field(
        None, description="Only the variables the user wants to modify."
    )


@lru_cache(maxsize=1)
def get_service() -> AcademicService:
    return AcademicService(CONFIG_PATH)


app = FastAPI(
    title="COP Academic Credit-Risk API",
    version="0.1.0",
    description=(
        "Local serving for the UCI academic baseline. Not approved for "
        "real credit decisions."
    ),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "test_status": "unopened"}


@app.get("/api/overview")
async def overview() -> dict[str, Any]:
    return get_service().overview()


@app.get("/api/metrics")
async def metrics() -> dict[str, Any]:
    return get_service().metrics()


@app.get("/api/roc")
async def roc() -> dict[str, Any]:
    return get_service().roc()


@app.get("/api/probabilities")
async def probabilities() -> dict[str, Any]:
    return get_service().probability_distribution()


@app.get("/api/examples")
async def examples() -> dict[str, Any]:
    return get_service().examples()


@app.get("/api/threshold-sweep")
async def threshold_sweep(
    model: str = Query("lightgbm", description="Academic model to explore."),
) -> dict[str, Any]:
    try:
        return get_service().threshold_sweep(model)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/model-lab")
async def model_lab() -> dict[str, Any]:
    try:
        return get_service().model_lab()
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/predict")
async def predict(request: PredictionRequest) -> dict[str, Any]:
    try:
        if request.case_id is not None:
            return get_service().predict_example(
                request.case_id, request.overrides or {}
            )
        if request.features is None:
            raise ValueError("Provide either features or case_id")
        return get_service().predict(request.features)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/assets/{asset_name}", include_in_schema=False)
async def asset(asset_name: str) -> PlainTextResponse:
    assets = {
        "app.js": ("application/javascript; charset=utf-8", WEB_DIRECTORY / "app.js"),
        "language.js": (
            "application/javascript; charset=utf-8",
            WEB_DIRECTORY / "language.js",
        ),
        "styles.css": ("text/css; charset=utf-8", WEB_DIRECTORY / "styles.css"),
        "plotly.min.js": ("application/javascript; charset=utf-8", PLOTLY_ASSET),
    }
    content_type, path = assets.get(asset_name, ("", Path("")))
    if not content_type or not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return PlainTextResponse(
        path.read_text(encoding="utf-8"),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/", include_in_schema=False)
async def index() -> HTMLResponse:
    return HTMLResponse((WEB_DIRECTORY / "index.html").read_text(encoding="utf-8"))
