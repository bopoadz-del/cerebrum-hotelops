"""KSA is unsupported and stripped. No pack may exist."""

from __future__ import annotations

from pathlib import Path

import pytest

from reasoning.guard import GuardError, guard_request

ROOT = Path(__file__).resolve().parents[1]


def test_ksa_pack_absent():
    assert not (ROOT / "domain_kit" / "licensing" / "ksa.json").exists()
    assert not (ROOT / "domain_kit" / "licensing" / "branches" / "ksa.json").exists()


def test_ksa_market_refused():
    with pytest.raises(GuardError) as exc:
        guard_request(market="ksa")
    assert exc.value.code == "market_unsupported"
