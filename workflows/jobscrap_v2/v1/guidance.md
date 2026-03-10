# Job War Room — Self-Evolving Workflow (jobscrap_v2/v1)

## Purpose

This workflow drives an autonomous, self-evolving job-scraping system.
Each full cycle (10 cards) executes daily operations, builds one new feature,
and performs a system-wide quality pass — then immediately starts the next cycle.
The system compounds improvements every iteration.

---

## Repository

`C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room`

---

## Cycle Structure (single loop, 10 cards)

```
s1_scrape → s2_analyze → s3_tune → s4_commit
                                        ↓
                            f1_discover → f2_implement → f3_verify → f4_ship
                                                                         ↓
                                                          e1_audit → e2_evolve
                                                                         ↓
                                                                  (s1_scrape)
```

| Card | Phase | What it does |
|------|-------|-------------|
| `s1_scrape` | Ops | Run `main_orchestrator.py`, record metrics to `ops_log.md` |
| `s2_analyze` | Ops | Spot-check results, flag false positives/negatives |
| `s3_tune` | Ops | Adjust keywords, scoring weights, filters based on analysis |
| `s4_commit` | Ops | Run tests, commit ops artifacts to `main` |
| `f1_discover` | Feature | Read `EVOLUTION_BACKLOG.md` + `ops_log.md`, write `SPRINT_DECISION.md` |
| `f2_implement` | Feature | Create feature branch, implement chosen improvement |
| `f3_verify` | Feature | Write ≥3 tests per changed function, 100% suite pass required |
| `f4_ship` | Feature | Commit, push, open PR via `gh`, update `EVOLUTION_LOG.md` |
| `e1_audit` | Evolution | Full system audit → write `AUDIT_REPORT.md` |
| `e2_evolve` | Evolution | Refresh `EVOLUTION_BACKLOG.md`, bump deps, tag release |

---

## Persistent State Files (connect cycles — make it self-evolving)

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `ops_log.md` | s1, s2, s3 | f1, e1 | Operational metrics and tuning history |
| `SPRINT_DECISION.md` | f1 | f2, f3, f4 | Current sprint plan (ephemeral — deleted by f4) |
| `EVOLUTION_LOG.md` | f4 | f1, e1 | History of all features built |
| `AUDIT_REPORT.md` | e1 | e2 | System audit findings (ephemeral — deleted by e2) |
| `EVOLUTION_BACKLOG.md` | e2 | f1 | Prioritized improvement queue |

---

## Git Conventions

| Phase | Branch | Commit format |
|-------|--------|--------------|
| Ops | `main` (direct) | `ops: daily run and tuning YYYY-MM-DD` |
| Feature | `feat/<topic>` → PR | `feat(<scope>): <imperative description ≤72 chars>` |
| Evolution | `main` (direct) | `audit: system evolution pass vX.Y.Z` |

- **Never** commit `config.json` (live credentials)
- **Never** push feature work directly to `main` — always open a PR
- Semantic versioning: patch for ops/audit only, minor for any merged feature

---

## Stop Token

When all deliverables for the card are complete, append to `current_task.md`:

```
## Summary
<one or two sentences describing what was actually done>

![stop]!
```

## Workspace Boundary

All file reads/writes must stay within `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room`
unless a card explicitly instructs pushing to GitHub.
