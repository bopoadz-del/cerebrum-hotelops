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
| `NotImplementedError` on happy paths | **0** in product (`api/`, `reasoning/`, `connectors/`, `hotelops/`, `agents/`, `guest_intelligence/`, `vision/`, `domain_kit/`, `workers/`) |
| Empty connector classes | **0** — all six connectors implement connect / fetch / normalise / emit |
| `TODO` / `FIXME` / `pass  # later` in product | **0** |

Fixture-driven connectors (OK — fully implemented against `fixtures/connectors/`):

- `connectors/opera.py`
- `connectors/micros.py`
- `connectors/loyalty_lms.py`
- `connectors/grms.py`
- `connectors/maximo.py`
- `connectors/gaming_cms.py`

Base path: `connectors/base.py` (`connect`, `fetch`, `fetch_fixture`, `fetch_live`, `normalise`, `emit`).

### Vendored Cerebrum-Blocks leftovers (frozen; do not edit `blocks/` without a `VENDOR.lock` bump)

These are **upstream kit skeletons**, not HotelOps product stubs:

1. `blocks/hotel_management/knowledge.py` — `# TODO: add non-negotiable domain rules`
2. `blocks/hotel_management/types.py` — `# TODO: domain-specific dataclasses`
3. `blocks/hotel_management/bundle/app/core/universal_base.py` — `NotImplementedError` on unknown generic action dispatch

Count: **3 vendor files**. Product does not import those happy-path stubs for Opera/Micros; product connectors live under `connectors/`.

---

## B. KSA leakage — **PASS**

Hard owner gate after strip (2026-09-12):

| Check | Result |
| --- | --- |
| `ksa.json` / KSA market packs under `domain_kit/` | **ZERO**. `find domain_kit -iname '*ksa*'` is empty. Deleted `domain_kit/licensing/ksa.json`. |
| `guard_request(market="ksa")` | **Refuses** with `GuardError.code == "market_unsupported"` (`reasoning/guard.py`) |
| Router allowlist | **UAE + generic only**. `MarketRouter` has no `ksa` branch (`reasoning/market_router.py`) |
| API | `GET /licensing/ksa` **removed**. `GET /licensing/pack/ksa` returns the refuse payload. |

### Grep (`ksa` / `KSA` / `saudi`) after strip

**Removed (were product packs / allowlists):**

- `domain_kit/licensing/ksa.json` (deleted)
- `domain_kit/loader.py` `licensing_ksa` load
- `hotelops/retrieval.py` KSA chunk source
- `api/routes/licensing.py` `/ksa` route
- `reasoning/licensing.py` `KSA-CD` / `KSA-STAR` ids
- `domain_kit/ppm/refuse_policy.json` `"ksa"` in `supported_markets`
- CI assert that `ksa.json` exists

**Kept (honest refusal only — not a pack):**

| Path | Why kept |
| --- | --- |
| `reasoning/guard.py` | `UNSUPPORTED_MARKETS = {"ksa", "saudi", "saudi_arabia"}` + refuse message |
| `reasoning/market_router.py` | docstring: KSA is refused |
| `tests/mutation_probes/test_mutations.py` | `test_ksa_code_is_unsupported_not_a_pack` (file must **not** exist) |
| `tests/test_no_ksa_branch.py` | pack-absent + `guard_request(market="ksa")` raises |
| `tests/test_reasoning.py` | `guard_request(market="ksa")` raises |
| `README.md`, `AGENTS.md`, `ACCEPTANCE.md`, `KNOWN_LIMITATIONS.md`, `domain_kit/licensing/README.md`, `domain_kit/licensing/generic_conditional_notes.md`, `.github/workflows/ci.yml` | docs/CI saying KSA is unsupported / stripped |

No KSA fixtures, seed profiles, or UI market options (`frontend/` grep: **0** hits). Guest CRM markets remain `{uae, generic}`.

---

## C. VENDOR.lock — **PASS**

- Pin SHA: `d7cff230453efd273388491e1cbf1d18f3ebefd5`
- Script: `scripts/check_vendor_lock.py` exists
- Local run: `VENDOR.lock OK — Cerebrum-Blocks@d7cff230453efd273388491e1cbf1d18f3ebefd5`

---

## D. Reasoning layer — **PASS**

| Mechanism | Path | Status |
| --- | --- | --- |
| Evidence A/B/C/Unprovable + PASS/FAIL/UNPROVABLE | `reasoning/evidence.py` (`EvidenceClass`, `Verdict`) | implemented |
| Cascade / critical path / LRM | `reasoning/cascade_engine.py` (`compute_critical_path`, `compute_master_pacer`, LRM alerts) | implemented |
| Market router | `reasoning/market_router.py` — UAE + generic; others refuse | implemented |
| PPM refuse | `reasoning/ppm_resolver.py` (`PPMRefuse` on empty/unnamed SOP) | implemented |
| Fire-pump covers/clips | `tests/test_reasoning.py`, `tests/test_sheet_mechanisms.py`, fixture `fixtures/engineering/fire_pump_covers_clips.json` | green |
| GRMS invalidity (room map + cert≠config) | `tests/test_reasoning.py`, `tests/test_sheet_mechanisms.py` | green |
| Test-to-tank + unit≠integrated | `tests/test_sheet_mechanisms.py` | green |

---

## E. Retrieval honesty — **PASS** (lexical + structured, not Blocks RAG)

`hotelops/retrieval.py` is **hybrid lexical overlap + structured kit chunks**. It tokenises query/chunk text and ranks by overlap. It does **not** call Blocks pgvector, embeddings, or a remote embedder.

Comment at file head: `Hybrid retrieval: lexical overlap + structured kit chunks. No remote embedder.`

This is **not** the full Cerebrum-Blocks pgvector RAG kit.

---

## F. Render honesty — **PASS** (config-ready only)

`render.yaml` is present (web + worker + Postgres wiring). **Not deployed** from this session. Treat as config-ready only. Do not claim a live Render URL.

---

## G. Tests — **PASS**

Command:

```bash
HOTELOPS_FIXTURE_MODE=1 HOTELOPS_LLM_PROVIDER=fake \
  DATABASE_URL=sqlite+pysqlite:///:memory: pytest
```

**Result line:** `45 passed in 1.38s`

| Skipped | xfailed |
| --- | --- |
| **0** | **0** |

Acceptance A01–A05 + guest: recorded in `tests/RUNLOG.md` (all PASS on fixtures).

Mutation: `test_ksa_code_is_unsupported_not_a_pack` **PASS** (`domain_kit/licensing/ksa.json` does not exist).

---

## H. Gaps vs blueprint

Still thin / out of scope (honest, not stubs):

1. **Live systems** — Opera / Micros / LMS / GRMS / Maximo / Jetson / Kimi-Azure stay fixture or skip unless env secrets are set (`KNOWN_LIMITATIONS.md`).
2. **Retrieval** — lexical+structured only; no pgvector RAG index in this pilot.
3. **Render** — `render.yaml` only; no live service.
4. **Vendor hotel kit** — upstream TODOs / `NotImplementedError` remain frozen under `blocks/` (see A).
5. **UI** — five panes (Ops, Guest, Documents, Actions, Audit). No extra market-picker for stripped KSA. No separate “licensing desk” beyond Ops.
6. **Construction PM** — Aconex / Procore / BIM parse refused by guard (owner constraint).
7. **Class A promotion** — Domain Encoding Sheet rows stay Class B until the owner uploads artefacts.

Acceptance A01–A05 exist and pass offline. They are fixture-backed, not live-property proof.

---

## Strip record (KSA)

Deleted:

- `domain_kit/licensing/ksa.json`

Changed to refuse-only / UAE+generic:

- `reasoning/guard.py`
- `reasoning/market_router.py`
- `reasoning/licensing.py`
- `domain_kit/loader.py`
- `domain_kit/ppm/refuse_policy.json`
- `domain_kit/licensing/README.md`
- `hotelops/retrieval.py`
- `api/routes/licensing.py`
- `tests/test_no_ksa_branch.py`
- `tests/mutation_probes/test_mutations.py`
- `tests/test_reasoning.py`
- `tests/test_sheet_mechanisms.py` (removed pack-evaluate test)
- `.github/workflows/ci.yml`
- `README.md`, `AGENTS.md`, `ACCEPTANCE.md`, `KNOWN_LIMITATIONS.md`
