# CardDealer Evolve Backlog

Updated: 2026-03-10 (cycle 2)

| Priority | File | Issue | Effort estimate |
|----------|------|-------|-----------------|
| P0 | `frontend/components/CurrentCardPanel.tsx` | Split 182-line component into smaller sub-components (Website Improvement) | ~100 lines |
| P1 | `engine/planner.py` | Private attribute access (`_picker._workflows`) — needs `get_cached_workflow()` | ~15 lines |
| P1 | `engine/planner.py` | Hardcoded `_max_retries` not configurable per-card metadata | ~20 lines |
| P1 | `tests/test_planner_integration.py` | Missing integration test for deal \u2192 archive \u2192 advance loop | ~100 lines |
| P2 | `frontend/app/settings/page.tsx` | Extract settings form logic (Website Improvement) | ~50 lines |
| P2 | `engine/planner.py` | FRUIT_POOL size (24 < 30) | ~10 lines |
| P2 | `orchestrator.py` | Missing `--validate-workflow` CLI argument | ~40 lines |
| P2 | `web/` | Consolidate or clarify Flask vs Next.js relationship (Website Improvement) | ~50 lines |
