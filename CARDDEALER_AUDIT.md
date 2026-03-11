# CardDealer Codebase Audit Report

**Cycle**: 0 (EVOLVE_CHANGELOG.md not found)  
**Timestamp**: 2026-03-10T22:30:00  
**Auditor**: Autonomous Agent (card_01)

---

## 1. Executive Summary

### Overall Health Score: **7.2/10**

The CardDealer codebase demonstrates solid architectural design with clear separation of concerns, comprehensive test coverage for core modules, and thoughtful patterns like the agent operating protocol. However, several robustness and maintainability issues were identified.

### Top 3 Priority Issues

| Priority | Issue | Impact |
|----------|-------|--------|
| **P1** | Log ring buffer inconsistency (300 vs 150 lines) | Dashboard may lose recent log data |
| **P1** | Private attribute access (`_picker._workflows`) | Fragile coupling, breaks encapsulation |
| **P1** | Hardcoded `_max_retries` not configurable per-card | Inflexible error handling for different card types |

### Issue Count Summary

| Priority | Count | Status |
|----------|-------|--------|
| P0 | 0 | — |
| P1 | 5 | FOUND |
| P2 | 4 | FOUND |
| P3 | 1 | FOUND |
| **Total** | **10** | |

---

## 2. File Metrics Table

### Top 10 Worst Files by `max_func_len`

| File | Lines | Funcs | Max Func Len | TODOs | Magic | Has Test |
|------|-------|-------|--------------|-------|-------|----------|
| `frontend/components/CurrentCardPanel.tsx` | 183 | 2 | 182 | 0 | 3 | ❌ |
| `frontend/app/settings/page.tsx` | 146 | 1 | 146 | 0 | 5 | ❌ |
| `frontend/app/page.tsx` | 113 | 2 | 112 | 0 | 0 | ❌ |
| `frontend/components/ProgressPanel.tsx` | 106 | 1 | 106 | 0 | 12 | ❌ |
| `engine/planner.py` | 530 | 21 | 99 | 0 | 24 | ✅ |
| `frontend/app/workflows/page.tsx` | 199 | 4 | 98 | 0 | 8 | ❌ |
| `frontend/app/files/page.tsx` | 89 | 2 | 88 | 0 | 0 | ❌ |
| `frontend/components/WorkspaceScan.tsx` | 85 | 1 | 85 | 0 | 0 | ❌ |
| `orchestrator.py` | 452 | 13 | 84 | 0 | 23 | ❌ |
| `frontend/components/CornerAccentVideo.tsx` | 83 | 1 | 83 | 0 | 2 | ❌ |

---

## 3. Known Issue Checklist

| # | Issue | Status | File:Line | Priority |
|---|-------|--------|-----------|----------|
| 1 | **Log count inconsistency** — Ring buffer size is 300 but `get_snapshot()` returns only 150 lines | **FOUND** | `core/state_manager.py`:91,128 | P1 |
| 2 | **Hook callback error isolation** — `trigger_hook()` wraps callbacks in try/except | **OK** | `core/hook_manager.py`:44-48 | — |
| 3 | **Picker private-dict mutation** — `_advance_workflow()` accesses `self._picker._workflows` directly | **FOUND** | `engine/planner.py`:414 | P1 |
| 4 | **Hardcoded max_retries** — `_max_retries: int = 2` cannot be overridden per-card | **FOUND** | `engine/planner.py`:103 | P1 |
| 5 | **Missing integration test** — No test drives complete cycle (deal → detect stop → archive → advance) | **FOUND** | `tests/test_planner.py` | P1 |
| 6 | **FRUIT_POOL size** — Only 24 items (should be ≥30) | **FOUND** | `engine/planner.py`:32-37 | P2 |
| 7 | **reshuffle_card_names length** — Method is ~70 lines (should be ≤60) | **FOUND** | `engine/planner.py`:407-476 | P2 |
| 8 | **validate-workflow CLI** — No `--validate` or `--validate-workflow` argument | **FOUND** | `orchestrator.py` | P2 |
| 9 | **pause-on-error option** — No option to pause after exhausting retries | **FOUND** | `engine/planner.py`:353-361 | P2 |
| 10 | **Rate limiting on control endpoints** — POST endpoints have no rate limiting | **FOUND** | `web/routes.py`:62-77 | P3 |

---

## 4. Additional Issues Found

### 4.1 Test Coverage Gaps

The following source files have no matching test file:

| File | Risk Level |
|------|------------|
| `core/agent_manager.py` | High — Multi-agent registry logic untested |
| `core/state_manager.py` | Medium — Core state management untested |
| `core/wrappers.py` | Medium — Instruction wrapper composition untested |
| `web/routes.py` | High — All HTTP route handlers untested |
| `web/app.py` | Low — Thin factory, but still untested |
| `orchestrator.py` | High — Main entry point untested |
| `engine/scanner.py` | Low — Simple scanner, but untested |
| All frontend `.tsx` and `.ts` files | Medium — No frontend tests |

### 4.2 Large Function Concerns

| File | Function | Lines | Recommendation |
|------|----------|-------|----------------|
| `frontend/components/CurrentCardPanel.tsx` | Component | 182 | Split into smaller sub-components |
| `frontend/app/settings/page.tsx` | Component | 146 | Extract settings form logic |
| `engine/planner.py` | `_reshuffle_card_names` | ~70 | Extract validation and file I/O helpers |

### 4.3 Magic Value Concentrations

| File | Magic Count | Notable Values |
|------|-------------|----------------|
| `engine/planner.py` | 24 | Port numbers, timeouts, buffer sizes |
| `orchestrator.py` | 23 | Port 5000, 3000, ngrok URLs |
| `frontend/components/ProgressPanel.tsx` | 12 | Status colors, thresholds |

---

## 5. Test Coverage Analysis

### Python Core Modules

| Module | Test File | Coverage Status |
|--------|-----------|-----------------|
| `core/base_card.py` | `tests/test_core.py` | ✅ Covered |
| `core/config.py` | `tests/test_core.py` | ✅ Covered |
| `core/exceptions.py` | `tests/test_core.py` | ✅ Covered |
| `core/state_manager.py` | — | ❌ Not tested |
| `core/hook_manager.py` | — | ❌ Not tested |
| `core/wrappers.py` | `tests/test_core.py` | ✅ Covered |
| `core/agent_manager.py` | — | ❌ Not tested |
| `engine/dealer.py` | `tests/test_dealer.py` | ✅ Covered |
| `engine/picker.py` | `tests/test_picker.py` | ✅ Covered |
| `engine/planner.py` | `tests/test_planner.py` | ⚠️ Partial (no integration test) |
| `engine/scanner.py` | — | ❌ Not tested |
| `web/app.py` | — | ❌ Not tested |
| `web/routes.py` | — | ❌ Not tested |
| `orchestrator.py` | — | ❌ Not tested |

### Frontend (TypeScript/TSX)

**No test files found** for any frontend components. All 56 TypeScript/TSX files lack test coverage.

---

## 6. Recommendations

### Immediate (P1)

1. **Fix log buffer inconsistency**: Change `get_snapshot()` to return `[-300:]` to match ring buffer size
2. **Add public accessor to CardsPicker**: Create `get_cached_workflow()` method instead of accessing `_workflows` directly
3. **Make max_retries configurable**: Read from `card.metadata.get("max_retries", 2)`
4. **Add integration test**: Create `test_planner_integration.py` that tests complete deal→archive→advance cycle

### Short-term (P2)

5. **Expand FRUIT_POOL**: Add 6+ more fruit names to support larger loops
6. **Refactor `_reshuffle_card_names`**: Extract into smaller helper methods
7. **Add `--validate-workflow` CLI**: Implement workflow validation command
8. **Add pause-on-error config**: Allow `card.metadata.pause_on_error` to override default behavior

### Long-term (P3)

9. **Add rate limiting**: Implement rate limiting on POST control endpoints
10. **Add frontend tests**: Set up Jest/React Testing Library for frontend components
11. **Add integration tests for web layer**: Test HTTP endpoints with Flask test client

---

## 7. Files Changed During Audit

| File | Action |
|------|--------|
| `audit_metrics.py` | Created (metrics collection script) |
| `CARDDEALER_AUDIT.md` | Created (this report) |

---

## 8. Commands Run

```bash
# Create virtual environment
python -m venv C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv

# Run metrics collection
C:\Users\MSI\Desktop\WinCoding\CardDealer\.venv\Scripts\python.exe audit_metrics.py

# Create git branch
git checkout -b card/card_01
```

---

## 9. Git Status

- **Branch**: `card/card_01`
- **Commit**: Pending review

---

## 10. Notes

- The codebase follows clean architectural patterns with good separation between core, engine, web, and frontend layers
- Test coverage is strong for basic unit tests but lacks integration tests
- Frontend has no test coverage at all
- The agent operating protocol is well-designed and self-contained
- Multi-loop support is a sophisticated feature with appropriate test coverage for reshuffle logic

![next]!
