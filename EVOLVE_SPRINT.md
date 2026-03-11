# Evolve Sprint: Fix Log Buffer Inconsistency

**Target file**: `core/state_manager.py`
**Issue**: Ring buffer size is 300 lines but `get_snapshot()` returns only 150 lines, causing dashboard to lose recent log data.
**Root cause**: The buffer size limit (300) is hardcoded in two places with inconsistent values—`push_log()` uses 300 but `get_snapshot()` uses 150.
**Priority**: P1

## Acceptance Criteria
1. The `get_snapshot()` method returns `self._state.log_lines[-LOG_BUFFER_SIZE:]` matching the ring buffer size of 300
2. A class-level constant `LOG_BUFFER_SIZE = 300` is defined and used by both `push_log()` and `get_snapshot()`
3. After the fix, both methods reference the same constant (no magic numbers)

## Files to Touch
- `core/state_manager.py`

## Estimated Scope
- Lines added: ~3 (constant definition at class level)
- Lines removed: ~2 (inline `300` and `150` values replaced with constant)
- Total delta: ~5 lines (well under 150 limit)

## Branch
feat/evolve-log-buffer-consistency

## Skipped Candidates
| File | Issue | Reason skipped |
|------|-------|----------------|
| `engine/planner.py` | Picker private-dict mutation | Requires refactoring to add public accessor; slightly larger scope |
| `engine/planner.py` | Hardcoded max_retries | Requires metadata schema change and propagation logic |
| `tests/` | Missing integration test | Would require mocking watchdog/planner; complex setup |
| `orchestrator.py` | validate-workflow CLI | New feature, not a bug fix; larger scope |
| `engine/planner.py` | FRUIT_POOL size | Trivial but lower priority (P2) |
| `engine/planner.py` | reshuffle_card_names length | Refactoring task; subjective metric |
| `engine/planner.py` | pause-on-error option | Requires new config option and state handling |
| `web/routes.py` | Rate limiting | Requires new dependency or middleware; larger scope |

![next]!
