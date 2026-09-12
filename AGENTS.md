# Agent notes

- Markets: UAE + generic only. KSA is unsupported and stripped.
- Sheet facts stay evidence_class=B until the owner uploads artefacts.
- Never edit `blocks/` without bumping `VENDOR.lock`.
- Default LLM is fake. Live Kimi/Azure must skip honestly if secrets are missing.
- Asset register = CSV / JSON / Maximo only. No Aconex/Procore/BIM.
- Run `pytest` before claiming the pilot is green.
