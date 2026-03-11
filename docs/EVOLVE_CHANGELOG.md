# CardDealer Evolve Changelog

## [cycle 1] 2026-03-10 — Log Buffer Consistency
- **Target**: `core/state_manager.py`
- **Change**: Added `LOG_BUFFER_SIZE = 300` and aligned `get_snapshot()` and `push_log()` to use it.
- **Tests**: n/a (passed existing)
- **Scope**: 5 lines changed
- **Health delta**: 7.20 -> 7.25 (+0.05)
- **Branch**: feat/evolve-log-buffer-consistency (merged)
