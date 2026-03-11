# CardDealer Codebase Audit Report

**Cycle**: 2
**Timestamp**: 2026-03-11T00:05:00
**Auditor**: Autonomous Agent (card_01)

---

## 1. Executive Summary

### Overall Health Score: 8.1 / 10.0
- **Total FOUND Issues**: 7
- **Top 3 Priority Issues**:
  1. **Missing integration test** (P1) — No automated verification of the full deal-archive-advance loop.
  2. **DRY Violation** (P1) — Duplicated logic for file operations and process management across orchestrator and engine.
  3. **FRUIT_POOL size** (P2) — Only 24 names available; limits scaling of large multi-loop workflows.

---

## 2. File Metrics Table (Top 10 by max_func_len)

| file | lines | funcs | max_func_len | todos | magic | has_test |
|------|-------|-------|--------------|-------|-------|----------|
| frontend\components\ExpandableMarkdown.tsx | 518 | 6 | 255 | 0 | 107 | False |
| frontend\app\logs\page.tsx | 303 | 4 | 221 | 0 | 55 | False |
| frontend\app\workflows\page.tsx | 198 | 2 | 151 | 0 | 44 | False |
| frontend\lib\logParser.ts | 258 | 1 | 133 | 0 | 28 | False |
| frontend\components\Sidebar.tsx | 173 | 2 | 116 | 0 | 40 | False |
| frontend\components\BackgroundVideo.tsx | 193 | 2 | 101 | 0 | 16 | False |
| orchestrator.py | 403 | 12 | 77 | 0 | 27 | False |
| frontend\app\files\page.tsx | 88 | 1 | 76 | 0 | 28 | False |
| engine\planner.py | 414 | 15 | 68 | 0 | 16 | True |
| audit_metrics.py | 91 | 2 | 65 | 1 | 3 | False |

---

## 3. Known Issue Checklist

| # | issue | status | file:line | priority |
|---|-------|--------|-----------|----------|
| 1 | Log count inconsistency | **OK** | core/state_manager.py | P1 |
| 2 | Hook callback error isolation | **OK** | core/hook_manager.py | P1 |
| 3 | Picker private-dict mutation | **OK** | engine/planner.py | P1 |
| 4 | Hardcoded max_retries | **SKIP** | engine/planner.py | P1 |
| 5 | Missing integration test | **FOUND** | tests/ | P1 |
| 6 | DRY Violation (Logic Duplication) | **FOUND** | orchestrator.py / engine | P1 |
| 7 | Layer Violation | **OK** | engine / core | P1 |
| 8 | FRUIT_POOL size | **FOUND** | engine/planner.py:31 | P2 |
| 9 | reshuffle_card_names length | **FOUND** | engine/planner.py:331 | P2 |
| 10 | validate-workflow CLI | **FOUND** | orchestrator.py | P2 |
| 11 | pause-on-error option | **FOUND** | engine/planner.py | P2 |
| 12 | Rate limiting on control endpoints | **FOUND** | web/routes.py | P3 |

---

## 4. Additional Issues
- `frontend/components/ExpandableMarkdown.tsx` is excessively long and should be refactored into smaller sub-components.
- Frontend test coverage is non-existent (0%).
- `orchestrator.py` is becoming a "God Object" handling CLI, Flask, Next.js, and ngrok.

---

## 5. Test Coverage Gaps
- `core/hook_manager.py` (matching test missing)
- `engine/scanner.py` (matching test missing)
- `web/routes.py` (matching test missing)
- All `frontend/` components and hooks.

---

## 6. Cycle Details
- **Cycle number**: 2
- **Timestamp**: 2026-03-11T00:05:00Z

Write `![next]!` when `CARDDEALER_AUDIT.md` is complete and accurate.
