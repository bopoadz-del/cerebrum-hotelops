# HotelOps honest audit

Date: 2026-09-12  
HEAD at audit time: local `main` after **strip KSA completely — UAE+generic only**.  
Markets in product: **UAE + generic only**. KSA is unsupported and stripped.

This file is an audit, not a claim of live deploy or full Blocks RAG.

---

## A. Stubs / placeholders — **PASS** (product) / **NOTE** (vendored kit)

### Product code (in-scope)

| Check | Result |
| --- | --- |
| `*_stub.py` | **0** files |
| `NotImplementedError` on happy paths | **0** in product |
| Empty connector classes | **0** — all six connectors implement connect / fetch / normalise / emit |
| `TODO` / `FIXME` / `pass  # later` in product | **0** |

Fixture-driven connectors (OK):

- `connectors/opera.py`
- `connectors/micros.py`
- `connectors/loyalty_lms.py`
- `connectors/grms.py`
- `connectors/maximo.py`
- `connectors/gaming_cms.py`

---

## B. KSA leakage — **PASS**

| Check | Result |
| --- | --- |
| `ksa.json` / KSA market packs under `domain_kit/` | **ZERO** |
| `guard_request(market="ksa")` | **Refuses** with `GuardError.code == "market_unsupported"` |
| Router allowlist | **UAE + generic only**. No `ksa` branch |

---

## C. VENDOR.lock — **PASS**

- Pin SHA: `d7cff230453efd273388491e1cbf1d18f3ebefd5`
- Script: `scripts/check_vendor_lock.py`

---

## D. Reasoning layer — **PASS**

| Mechanism | Path |
| --- | --- |
| Evidence A/B/C/Unprovable | `reasoning/evidence.py` |
| Cascade / LRM | `reasoning/cascade_engine.py` |
| Market router | `reasoning/market_router.py` |
| PPM refuse | `reasoning/ppm_resolver.py` |
| Guard | `reasoning/guard.py` |

---

## E. Retrieval honesty — **PASS** (lexical + structured, not Blocks RAG)

`hotelops/retrieval.py` is hybrid lexical overlap + structured kit chunks. Not full Cerebrum-Blocks pgvector RAG.

---

## F. Render honesty — **PASS** (config-ready only)

`render.yaml` present. **Not deployed**. Config-ready only.

---

## G. Tests — **PASS** (when deps present)

Offline fixture mode: 45 passed historically in cloud-agent session.
