# Fast-dLLM Inference Visualization API

## Purpose

Build a minimal-change, decorator-based instrumentation API for the Fast-dLLM inference
pipeline, backed by a Flask SSE server and a Next.js visualization dashboard.
The workflow runs an initial build phase (cards 01–08) then enters a perpetual
5-card improvement loop (cards 09–13) that audits, tests, profiles, hardens, and
documents the system on every cycle.

## Workspace

All code work happens in: `C:\Users\MSI\Desktop\WinCoding\Fast-dllm`

## Branch Rules (CRITICAL)

- **Work branch (local only):** `user/xwu/inferenceAPI_dev`
- **Remote push target:** `origin/user/xwu/InferenceAPI_Infra` ONLY
- **Forbidden:** push to `main`, touch `users/jibf/decoding_stats`
- **Push command:** `git push origin user/xwu/inferenceAPI_dev:user/xwu/InferenceAPI_Infra`

**Before every card:** `git pull origin main`
**After every card:** commit + push to InferenceAPI_Infra

## Card Structure: 13 Cards, Two Loop Groups

```
loop_id: "build"    cards 01–08  — one-time; builds the full system
loop_id: "improve"  cards 09–13  — perpetual; 5-card improvement cycle
```

```
[BUILD]
card_01 → card_02 → card_03 → card_04 → card_05 → card_06 → card_07 → card_08
                                                                            ↓
[IMPROVE — repeats forever]
                                         card_09 (DRY Audit & Refactor)
                                             ↓
                                         card_10 (Test Suite)
                                             ↓
                                         card_11 (Performance Profiling)
                                             ↓
                                         card_12 (API Hardening & Docs)
                                             ↓
                                         card_13 (Analysis & Planning)
                                             ↑── next_card: card_09 (loop)
```

## DRY Shared Python Modules

| Module | Introduced | Contents |
|---|---|---|
| `llada/api/_base.py` | card_01 | `EventMixin` (shared `to_dict()`), `ReversibleMixin` (shared context manager) |
| `llada/api/utils.py` | card_01 | `utc_now()`, `emit_if_active()`, `make_sse_response()`, `make_route_guard()`, `ModuleClassSwapper` |
| `llada/api/constants.py` | card_01 | `DEFAULT_PORT`, `DEFAULT_MAXLEN`, `MASK_TOKEN_ID`, `KEEP_ALIVE_LINE` |
| `llada/api/decorators.py` | card_06 | `_require_model`, `_require_session` built from `make_route_guard()` |

## DRY Shared TypeScript Modules

| Module | Introduced | Contents |
|---|---|---|
| `viz/lib/api.ts` | card_07 | `API_BASE`, `apiUrl()`, `apiFetch<T>()` |
| `viz/lib/hooks/useEventStream.ts` | card_07 | Generic SSE hook with exponential backoff |
| `viz/lib/utils.ts` | card_07 | `confColor()`, `formatConf()`, `cn()` |
| `viz/components/ui/PlaybackControls.tsx` | card_07 | Extracted from BlockStepper; reusable |

## Architecture

```
Fast-dllm/
├── llada/
│   ├── api/
│   │   ├── __init__.py          Public: InferenceTrace, V1Adapter, V2Adapter, MockAdapter
│   │   ├── _base.py             EventMixin, ReversibleMixin (DRY foundations)
│   │   ├── constants.py         Shared constants
│   │   ├── utils.py             Shared utilities (emit_if_active, make_route_guard, ...)
│   │   ├── decorators.py        Flask guard decorators
│   │   ├── events.py            SK-3: event dataclasses using EventMixin
│   │   ├── bus.py               SK-1: EventBus (ContextVar)
│   │   ├── trace.py             SK-4: InferenceTrace (ring buffer + SSE generator)
│   │   ├── hooks.py             SK-2: HookPoint, HookSet using ReversibleMixin
│   │   ├── server.py            SK-5+6: Flask SSE server (InferenceRouter)
│   │   ├── config.py            capture.yaml loader
│   │   ├── capture.yaml         EV-2: config-driven capture settings
│   │   ├── openapi.yaml         API documentation (created in card_12)
│   │   ├── static/              Pre-built Next.js export (gitignored)
│   │   └── adapters/
│   │       ├── base.py          BaseAdapter ABC
│   │       ├── v1.py            SK-7: V1 pipeline adapter
│   │       ├── v2.py            SK-8: V2 pipeline adapter (zero changes to source)
│   │       └── mock.py          MockAdapter (no GPU needed)
│   └── generate.py              +3 lines only (H1 emit)
│
└── viz/                         Next.js 14 visualization dashboard
    ├── lib/
    │   ├── api.ts               Shared API client
    │   ├── utils.ts             confColor, formatConf, cn
    │   └── hooks/
    │       ├── useEventStream.ts  Generic SSE hook
    │       └── useInferenceStream.ts  Typed wrapper
    └── components/
        ├── ui/PlaybackControls.tsx  Reusable playback strip
        ├── TokenGrid.tsx
        ├── BlockStepper.tsx
        └── ConnectionBadge.tsx
```

## CardDealer Pattern Alignment

| CardDealer | Fast-dLLM API |
|---|---|
| `DashboardRouter` | `InferenceRouter` |
| `@_require_registry` | `@_require_model` |
| `@_require_tmux` | `@_require_session` |
| `DealerRegistry` | `SessionRegistry` |
| `stream_lines()` | `stream_events()` |
| `useAgentStream` | `useInferenceStream` |

## Stop Token

`![stop]!` — append on its own line when all deliverables for a card are complete.

## Living Documents

- `IMPROVEMENT_LOG.md` — per-cycle metrics, findings, next-cycle priorities
- `CHANGELOG.md` — conventional commits changelog
- `README.md` — quick-start, endpoint reference, architecture diagram

## Known Patterns (Updated Each Cycle)

*This section grows as the improve loop runs. Append findings here.*

## Schema Version History

| Version | Change | Card |
|---|---|---|
| 1 | Initial schema: UnmaskEvent, BlockStepSnapshot, LogitCapture | card_02 |
