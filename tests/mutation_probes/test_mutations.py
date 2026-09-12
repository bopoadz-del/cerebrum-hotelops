"""Mutations that must stay refused / detected."""

from __future__ import annotations

from pathlib import Path

import pytest

from reasoning.guard import GuardError, guard_request
from reasoning.ppm_resolver import PPMRefuse, PPMResolver

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.mutation
def test_ksa_code_is_unsupported_not_a_pack():
    path = ROOT / "domain_kit/licensing/ksa.json"
    assert not path.exists()
    leftover = list((ROOT / "domain_kit").rglob("*ksa*")) + list((ROOT / "domain_kit").rglob("*KSA*"))
    assert leftover == []
    with pytest.raises(GuardError) as exc:
        guard_request(market="ksa")
    assert exc.value.code == "market_unsupported"


@pytest.mark.mutation
def test_empty_sop_never_issues():
    with pytest.raises(PPMRefuse):
        PPMResolver().resolve(market="uae", asset_type="elevator", operator_sop="   ")


@pytest.mark.mutation
def test_bim_source_refused():
    with pytest.raises(GuardError):
        guard_request(construction_pm=True)
