# MetaHIA clean source package

This archive contains the active Python implementation, tests, protocols, current roadmap and consolidated documentation. Historical backups and caches are intentionally excluded.

## Quick start
```bash
python -m pytest -q
python main.py --demo
```

Expected local regression at release construction: 157 passed.

**Addendum 2026-09-17**: M6 — Structural Learning v0.1 has since been implemented, fed with
a real (small) M4/M5 corpus, and has a third-party validation protocol prepared — see
`MetaHIA_M6_Structural_Learning_V0_1.md` and
`MetaHIA_ThirdParty_Validation_Protocol_M6_V0_1.md`. Current local regression: 319 passed.

## Scope
The release is a structured-input research core. Text parsing and live LLM communication are specified but not implemented. M6 was the next development gate at release construction; see the addendum above for its current status.
