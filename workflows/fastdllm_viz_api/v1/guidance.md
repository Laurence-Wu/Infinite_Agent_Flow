# Fast-dLLM Inference Visualization API

## Purpose

Build a minimal-change, decorator-based instrumentation API for the Fast-dLLM inference
pipeline, backed by a Flask SSE server and a Next.js visualization dashboard.

## Workspace

All code work happens in: `C:\Users\MSI\Desktop\WinCoding\Fast-dllm`

## Branch Rules (CRITICAL)

- **Work branch (local only):** `user/xwu/inferenceAPI_dev`
- **Remote push target:** `origin/user/xwu/InferenceAPI_Infra` ONLY
- **Forbidden:** push to `main`, touch `users/jibf/decoding_stats`
- **Push command:** `git push origin user/xwu/inferenceAPI_dev:user/xwu/InferenceAPI_Infra`

**Before every card:** `git pull origin main` (to stay in sync)
**After every card:** commit + `git push origin user/xwu/inferenceAPI_dev:user/xwu/InferenceAPI_Infra`

## Architecture Summary

```
Fast-dllm/
├── llada/api/           ← Python instrumentation layer
│   ├── events.py        SK-3: event dataclasses
│   ├── bus.py           SK-1: EventBus (ContextVar)
│   ├── trace.py         SK-4: InferenceTrace / TraceRecorder
│   ├── hooks.py         SK-2: HookPoint / HookSet
│   ├── server.py        SK-5+6: Flask SSE + static
│   ├── capture.yaml     EV-2: config-driven capture
│   └── adapters/        SK-7+8+mock
└── viz/                 ← Next.js dashboard
```

## CardDealer Pattern Alignment

| CardDealer | Fast-dLLM API |
|---|---|
| DashboardRouter | InferenceRouter |
| @_require_registry | @_require_model |
| @_require_tmux | @_require_session |
| DealerRegistry | SessionRegistry |
| stream_lines() | stream_events() |
| useAgentStream | useInferenceStream |

## Stop Token

Append `![stop]!` on its own line when all deliverables for a card are complete.
