from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("HOTELOPS_FIXTURE_MODE", "1")
os.environ.setdefault("HOTELOPS_LLM_PROVIDER", "fake")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("HOTELOPS_OPERATOR_TOKEN", "operator-pilot")
os.environ.setdefault("HOTELOPS_REVIEWER_TOKEN", "reviewer-pilot")

from domain_kit.loader import load_kit  # noqa: E402
from hotelops.db import init_db, reset_engine  # noqa: E402
from hotelops.event_bus import reset_bus  # noqa: E402
from hotelops.settings import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_state(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{tmp_path}/t.db")
    get_settings.cache_clear()
    load_kit.cache_clear()
    reset_engine()
    reset_bus()
    init_db()
    yield
    reset_bus()
    reset_engine()
    get_settings.cache_clear()
