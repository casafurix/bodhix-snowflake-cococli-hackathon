import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="TrialOps Evidence Desk API",
    version="0.1.0",
    description="Clinical-trial pre-screening decision support over synthetic data.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

default_static_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
static_dir = Path(os.getenv("TRIALOPS_STATIC_DIR", default_static_dir))

if static_dir.is_dir():
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        requested = (static_dir / path).resolve()
        if requested.is_relative_to(static_dir.resolve()) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def root() -> dict:
        return {"service": "TrialOps Evidence Desk API", "docs": "/docs"}
