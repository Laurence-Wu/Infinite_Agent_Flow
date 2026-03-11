# Job War Room — Self-Evolving Workflow (jobscrap_v2/v1)

## Purpose

This workflow drives an autonomous, self-evolving job-scraping system that pulls
from **four distinct data sources**, scores every result through a unified pipeline,
and compounds improvements every iteration.

Each full cycle (15 cards) executes multi-source daily operations, builds one new
feature, and performs a system-wide quality pass — then immediately starts the next cycle.

---

## Repositories

| Role | Path |
|------|------|
| Main scraper / workspace | `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room` |
| Board + company scraper  | `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room\rabiuk-job-scraper` |

---

## Cycle Structure (single loop, 15 cards)

```text
s1_jobspy → s2_board → s3_company → s4_manual → s5_aggregate
                                                      ↓
                               s6_analyze → s7_tune → s8_commit
                                                           ↓
                              f1_discover → f2_implement → f3_verify → f4_ship → f5_merge_all
                                                                                           ↓
                                                                          e1_audit → e2_evolve
                                                                           ↓
                                                                    (s1_jobspy)
```

| Card | Fruit | Phase | What it does |
|------|-------|-------|-------------|
| s1_jobspy    | `fig`        | Ops         | JobSpy scrape: LinkedIn + Indeed + Glassdoor → ops_log |
| s2_board     | `kiwi`       | Ops         | Board scrape: SimplifyJobs GitHub + Simplify.jobs + LinkedIn board |
| s3_company   | `lemon`      | Ops         | Company career pages (rabiuk scraper + manual additions) |
| s4_manual    | `nectarine`  | Ops         | Manual enrichment: Handshake, WayUp, Wellfound, Discord |
| s5_aggregate | `tangerine`  | Ops         | Merge all sources → deduplicate → filter → score → alert S/A |
| s6_analyze   | `ugli`       | Ops         | Compute yield metrics, keyword audit, source quality audit |
| s7_tune      | `zucchini`   | Ops         | Apply action items: keywords, config, filters, companies.csv |
| s8_commit    | `apple`      | Ops         | Tests gate → stage safe files → commit + push → trim cache |
| f1_discover  | `banana`     | Feature     | Read backlog + ops_log → select sprint → write SPRINT_DECISION.md |
| f2_implement | `cherry`     | Feature     | Feature branch → implement → incremental commits |
| f3_verify    | `date`       | Feature     | ≥3 tests/function → 100% pass → tick acceptance criteria |
| f4_ship      | `elderberry` | Feature     | Merge to main → EVOLUTION_LOG → tag → clean up SPRINT_DECISION |
| f5_merge_all | `raspberry`  | Feature     | Merge remaining ready `feat/*` branches safely → report + cleanup |
| e1_audit     | `mango`      | Evolution   | Full audit: code health + source coverage + yield → AUDIT_REPORT |
| e2_evolve    | `orange`     | Evolution   | Refresh EVOLUTION_BACKLOG → version bump → tag → archive → → fig |

---

## Data Sources

| Source | Card | Method | Priority |
|--------|------|--------|----------|
| LinkedIn, Indeed, Glassdoor | s1 (fig) | JobSpy library | Primary |
| SimplifyJobs GitHub repo | s2 (kiwi) | GitHub raw JSON API | Secondary |
| Simplify.jobs + LinkedIn boards | s2 (kiwi) | rabiuk board_scraper | Secondary |
| Company career pages (25+ companies) | s3 (lemon) | rabiuk company_scraper | Tertiary |
| Handshake, WayUp, Wellfound | s4 (nectarine) | Manual + CLI research | Enrichment |
| University portals, Discord | s4 (nectarine) | Manual | Enrichment |

---

## Persistent State Files

| File | Written by | Read by | Purpose |
|------|-----------|---------|---------|
| `ops_log.md` | s1–s7 | f1, e1 | Operational metrics and tuning history |
| `board_results_YYYYMMDD.json` | s2 | s5 | Raw board scrape output (archived by e2) |
| `manually_added_jobs.json` | s3, s4 | s5 | Manually curated job entries |
| `aggregated_results_YYYYMMDD.json` | s5 | s6, e1 | Scored results from all sources (archived by e2) |
| `SPRINT_DECISION.md` | f1 | f2, f3, f4 | Current sprint plan (ephemeral — deleted by f4) |
| `EVOLUTION_LOG.md` | f4 | f1, e1 | History of all features built |
| `AUDIT_REPORT.md` | e1 | e2 | System audit findings (ephemeral — deleted by e2) |
| `EVOLUTION_BACKLOG.md` | e2 | f1 | Prioritized improvement queue (max 10 items) |

---

## Git Conventions

| Phase | Branch | Commit format |
|-------|--------|--------------|
| Ops | `main` (direct) | `ops: daily run and tuning YYYY-MM-DD` |
| Feature | `feat/<topic>` → PR | `feat(<scope>): <imperative description ≤72 chars>` |
| Evolution | `main` (direct) | `audit: system evolution pass vX.Y.Z` |

**Security rules:**
- **Never** commit `config.json`, `.env`, `.env.local` (live credentials)
- **Never** commit `run_orchestrator.ps1` (contains ngrok auth)
- **Never** push feature work directly to `main` — always merge via `--no-ff`
- Semantic versioning: patch for ops/audit only, minor for any merged feature

---

## Execution Gates (All Cards)

Before writing `![next]!`, every card must pass these gates:

1. **Command gate**: all required commands were executed (or explicitly documented as blocked).
2. **Evidence gate**: files/log updates requested by the card were written and verified.
3. **Safety gate**: no secrets were staged/committed, and no destructive action was taken without explicit instruction.
4. **State gate**: if git was used, `git status` was checked and outcomes were recorded.

If any gate fails, do not advance. Record blocker details in logs and stop.

---

## Merge and Prune Timing Policy

Feature integration timing for this workflow:

1. `f4 (elderberry)` merges the primary sprint branch only after f3 verification is complete.
2. `f5 (raspberry)` is the controlled consolidation window for additional `feat/*` branches.
3. Branch pruning is allowed only after merged branches are confirmed on remote `main`.
4. If tests fail or conflicts occur during f5, stop batch consolidation and carry blockers to the next cycle.

This keeps ops cards predictable while still consolidating feature work at a dedicated point.

---

## Command Portability Standard

Cards may contain Windows-style examples, but execution should use the host shell semantics:

- On Windows PowerShell: use `.venv\Scripts\activate`, `Get-Content`, `Remove-Item`.
- On Linux/macOS bash: use `source .venv/bin/activate`, `cat`/`grep`, `rm -f`.

When a command in a card is platform-specific, apply the equivalent command on the current OS and continue.

---

## Stop Token

When all deliverables for the card are complete, **use your file-edit tool** to append
the following block directly to `current_task.md` on disk (do NOT print it in chat):

```text
## Summary
<one or two sentences describing what was actually done>

![next]!
```

The engine watches `current_task.md` on disk. The `![next]!` token must be
physically written into that file to trigger the next card.

---

## Workspace Boundary

All file reads/writes must stay within:
- `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room`
- `C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room\rabiuk-job-scraper`

Unless a card explicitly instructs pushing to GitHub.
