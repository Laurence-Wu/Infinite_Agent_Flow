# Evolve Sprint: Add Integration Test for Planner Loop

**Target file**: `tests/test_planner_integration.py`
**Issue**: No automated verification of the full deal-archive-advance loop.
**Root cause**: Testing focus was on unit tests for individual components.
**Priority**: P1

## Acceptance Criteria
1. Create `tests/test_planner_integration.py`.
2. Implement a test that instantiates the full engine stack (State, Picker, Dealer, Planner) using a temporary workspace and mock workflows.
3. Fix the auto-advance bug in `core/config.py` by making `stop_token_regex` more strict (require exclamations and start-of-line).
4. Simulate an agent completing a task by appending `![next]!` to `current_task.md`.
5. Verify that the Planner:
   - Detects the completion.
   - Archives the task correctly to the `archive/` folder.
   - Advances the workflow to the next card.
   - Updates the global state in `StateManager`.
6. The test must run and pass with `pytest tests/test_planner_integration.py`.

## Files to Touch
- `tests/test_planner_integration.py` (new)
- `core/config.py`

## Estimated Scope
- Lines added: ~100
- Lines removed: ~5
- Total delta: ~105

## Branch
feat/evolve-planner-integration-test

## Skipped Candidates
| File | Issue | Reason skipped |
|------|-------|----------------|
| `orchestrator.py` | DRY Violation | Larger scope, involves refactoring multiple modules. |
| `engine/planner.py` | FRUIT_POOL size | Low priority compared to testing infrastructure. |
| `frontend/` | ExpandableMarkdown complexity | Pure UI improvement; backend stability takes precedence for this cycle. |
