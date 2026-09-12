# cerebrum-hotelops

Pilot-ready hospitality AI platform. **Markets: UAE + generic only.** KSA is unsupported and stripped.

## Constraints

- UAE + generic ONLY — no KSA packs or branches
- No stubs/placeholders where implementable
- VENDOR.lock pin: `d7cff230453efd273388491e1cbf1d18f3ebefd5`
- Retrieval: hybrid lexical + structured (not full Blocks pgvector RAG unless proven)
- `render.yaml` = config-ready only unless deployed

## Quick start

```bash
pip install -r requirements.txt
HOTELOPS_FIXTURE_MODE=1 HOTELOPS_LLM_PROVIDER=fake \
  DATABASE_URL=sqlite+pysqlite:///:memory: pytest
python scripts/check_vendor_lock.py
```

See `AUDIT.md` for the honest status report.
