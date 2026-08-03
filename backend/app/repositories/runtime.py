"""Runtime repository selection without importing secrets into application code."""

from __future__ import annotations

import os

from app.repositories.demo import repository as demo_repository


def build_repository():
    backend = os.getenv("ATLAS_DATA_BACKEND", os.getenv("TRIALOPS_DATA_BACKEND", "demo")).casefold()
    if backend == "snowflake":
        from app.repositories.snowflake import SnowflakeRepository

        return SnowflakeRepository()
    if backend != "demo":
        raise ValueError("ATLAS_DATA_BACKEND must be 'demo' or 'snowflake'")
    return demo_repository


repository = build_repository()
