"""KSA is unsupported and stripped. Demo geography is UAE + generic only."""

from __future__ import annotations

from pathlib import Path

import pytest

from guest_intelligence.crm import GuestCRM
from reasoning.guard import GuardError, guard_request
from reasoning.licensing import LicensingEngine

ROOT = Path(__file__).resolve().parents[1]


def test_ksa_pack_file_does_not_exist():
    assert not (ROOT / "domain_kit" / "licensing" / "ksa.json").exists()
    assert not (ROOT / "domain_kit" / "licensing" / "branches" / "ksa.json").exists()
    leftover = list((ROOT / "domain_kit").rglob("*ksa*")) + list((ROOT / "domain_kit").rglob("*KSA*"))
    assert leftover == []


def test_guard_refuses_ksa():
    with pytest.raises(GuardError) as exc:
        guard_request(market="ksa")
    assert exc.value.code == "market_unsupported"


def test_licensing_engine_refuses_ksa():
    with pytest.raises(GuardError):
        LicensingEngine().evaluate("ksa", {})


def test_demo_guest_fixtures_remain_uae_and_generic():
    markets = {p["market"] for p in GuestCRM().list_profiles()}
    assert markets == {"uae", "generic"}
    assert "ksa" not in markets
