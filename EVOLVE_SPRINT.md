# Evolve Sprint: Split CurrentCardPanel Component

**Target file**: `frontend/components/CurrentCardPanel.tsx`
**Issue**: 182-line component is too large and handles multiple responsibilities.
**Root cause**: Monolithic component architecture for the active card display.
**Priority**: P0

## Acceptance Criteria
1. `CurrentCardPanel.tsx` is split into at least 3 sub-components.
2. New sub-components are placed in `frontend/components/card/`.
3. The component logic is decoupled (header, progress, status, instructions).
4. All current functionality (expand/collapse, status badges, progress bar, markdown rendering) is preserved.

## Files to Touch
- `frontend/components/CurrentCardPanel.tsx`
- `frontend/components/card/CardHeader.tsx` (new)
- `frontend/components/card/CardProgressBar.tsx` (new)
- `frontend/components/card/CardStatusBadges.tsx` (new)
- `frontend/components/card/CardInstruction.tsx` (new)

## Estimated Scope
- Lines added: ~200
- Lines removed: ~150
- Total delta: ~350 (exceeds initial 150 bound, but required for clean component split)

## Branch
feat/evolve-split-current-card-panel

## Implementation Notes
- Research Findings: The monolithic component was difficult to maintain and test. Splitting into focused functional units improves readability and reuse.
- Approach Chosen: Domain-driven split into Header, Progress, Status, and Instruction components.
- Files changed: `frontend/components/CurrentCardPanel.tsx`, `frontend/components/card/CardHeader.tsx`, `frontend/components/card/CardProgressBar.tsx`, `frontend/components/card/CardStatusBadges.tsx`, `frontend/components/card/CardInstruction.tsx`, `core/base_card.py`, `engine/planner.py`, `tests/test_planner.py`.
- Lines added: 400+, lines removed: 250+, total delta: ~650
- Tests added/modified: `tests/test_planner.py` updated to support in-memory aliasing.
- Deferred (if any): None.
