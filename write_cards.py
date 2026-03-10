import json, pathlib

WF = pathlib.Path(r"c:\Users\MSI\Desktop\WinCoding\CardDealer\workflows\jobscrap_v2\v1")
WS = r"C:\Users\MSI\Desktop\WinCoding\jobScrap\job-war-room"
BOARD = rf"{WS}\rabiuk-job-scraper"

cards = {}

# ─────────────────────────────────────────────────────────────────────────────
# s1 · fig  ·  Main JobSpy Scrape (LinkedIn / Indeed / Glassdoor)
# ─────────────────────────────────────────────────────────────────────────────
cards["fig"] = {
    "id": "fig", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "kiwi",
    "metadata": {"priority": "normal", "tags": ["ops", "scrape", "jobspy"]},
    "instruction": (
        "## s1 · Main JobSpy Scrape  (LinkedIn / Indeed / Glassdoor)\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Run the primary scraper that queries LinkedIn, Indeed, and Glassdoor via JobSpy.\n"
        "Record every metric needed for s2 analysis. Detect yield collapse early.\n\n"

        "### Pre-flight\n"
        "1. Activate the venv and pull latest main:\n"
        "   ```\n"
        f"   cd {WS}\n"
        "   .venv\\Scripts\\activate\n"
        "   git checkout main\n"
        "   git pull origin main\n"
        "   ```\n"
        "2. Confirm `config.json` exists (never print credentials):\n"
        "   ```\n"
        "   python -c \"from src.utils.config_loader import ConfigLoader; c=ConfigLoader.load(); print('config OK')\"\n"
        "   ```\n\n"

        "### Run the Scraper\n"
        "```\n"
        "python -m src.main\n"
        "```\n"
        "Observe full terminal output:\n"
        "- Total scraped per site\n"
        "- Passed filters count\n"
        "- Tier breakdown (S / A / B / C)\n"
        "- Alerts sent\n"
        "- Any exceptions or WARN/ERROR lines\n\n"

        "### Log Collection\n"
        "```\n"
        "type job_war_room.log | findstr /I \"ERROR WARNING CRITICAL\"\n"
        "```\n"
        "Note every WARN/ERROR line — include them in the ops_log entry.\n\n"

        "### Write ops_log.md Entry\n"
        "Append a new structured entry to `ops_log.md` (create the file if missing):\n"
        "```markdown\n"
        "## Run: <ISO datetime>  [source: jobspy]\n"
        "- Total scraped : <N>  (linkedin: <N>, indeed: <N>, glassdoor: <N>)\n"
        "- Passed filters: <N>\n"
        "- S: <N> | A: <N> | B: <N> | C: <N>\n"
        "- Alerts sent   : <N>\n"
        "- seen_jobs size: <N>  (after dedup)\n"
        "- Sites scraped : linkedin, indeed, glassdoor\n"
        "- Errors/warnings: <list or 'none'>\n"
        "```\n\n"

        "### Zero-Yield Guard\n"
        "Count how many of the last 5 ops_log `[source: jobspy]` entries have `Passed filters: 0`.\n"
        "- If 3 or more: append this line to today's entry:\n"
        "  ```\n"
        "  - ⚠️  CRITICAL: 3+ consecutive zero-match runs from JobSpy — s7 MUST expand search terms\n"
        "  ```\n\n"

        "### Failure Handling\n"
        "If a fatal exception prevented scraping:\n"
        "- Record `Passed filters: 0` in ops_log\n"
        "- Note the full exception class and first line under Errors/warnings\n"
        "- Advance to kiwi anyway — the board scraper is independent\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s2 · kiwi  ·  Board Scrape (SimplifyJobs GitHub + Simplify.jobs)
# ─────────────────────────────────────────────────────────────────────────────
cards["kiwi"] = {
    "id": "kiwi", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "lemon",
    "metadata": {"priority": "normal", "tags": ["ops", "scrape", "board"]},
    "instruction": (
        "## s2 · Board Scrape  (SimplifyJobs GitHub + Simplify.jobs)\n\n"
        f"Board scraper location: `{BOARD}`\n\n"
        "### Goal\n"
        "Pull fresh job postings from:\n"
        "  1. **GitHub SimplifyJobs/New-Grad-Positions** — the canonical new-grad repo\n"
        "  2. **Simplify.jobs** — aggregated intern/new-grad board\n"
        "  3. **LinkedIn Canada/US** (board scraper path, independent from JobSpy)\n"
        "Write results to `board_results.json` for s5 aggregation.\n\n"

        "### Setup Check\n"
        "```\n"
        f"cd {BOARD}\n"
        "pip install -r requirements.txt --quiet\n"
        "```\n"
        "Confirm `.env.local` exists with `LINKEDIN_WEBHOOK_URL` set.\n\n"

        "### Run Board Scraper\n"
        "```\n"
        "python board_scraper/scraper.py --once\n"
        "```\n"
        "If the scraper has no `--once` flag, run it and Ctrl+C after first full pass.\n"
        "Save all raw results to `board_results_<YYYYMMDD>.json`:\n"
        "```python\n"
        "# Quick export after scraper finishes\n"
        "import json, pathlib\n"
        "from datetime import date\n"
        "# Read from board_scraper/seen_jobs.json — new entries since last run\n"
        "# Write to board_results_YYYYMMDD.json in job-war-room root\n"
        "out = pathlib.Path(r'" + WS + r"') / f'board_results_{date.today().isoformat()}.json'\n"
        "# Load new jobs from board scraper output and save\n"
        "```\n\n"

        "### Manual GitHub Fetch (fallback if scraper fails)\n"
        "If the board scraper fails, fetch the SimplifyJobs repo directly:\n"
        "```python\n"
        "import urllib.request, json\n"
        "url = 'https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json'\n"
        "with urllib.request.urlopen(url) as r:\n"
        "    listings = json.loads(r.read())\n"
        "# Filter for hardware/ML/embedded roles posted in last 48h\n"
        "from datetime import datetime, timezone, timedelta\n"
        "cutoff = datetime.now(timezone.utc) - timedelta(hours=48)\n"
        "relevant = [\n"
        "    j for j in listings\n"
        "    if j.get('date_posted') and datetime.fromisoformat(j['date_posted'].replace('Z','+00:00')) > cutoff\n"
        "    and any(kw.lower() in (j.get('title','') + j.get('description','')).lower()\n"
        "            for kw in ['hardware','embedded','firmware','fpga','ml','machine learning',\n"
        "                        'computer vision','edge ai','tinyml','neural','cuda'])\n"
        "]\n"
        "print(f'SimplifyJobs new-grad relevant: {len(relevant)}')\n"
        "# Save to board_results_YYYYMMDD.json\n"
        "```\n\n"

        "### Log the Results\n"
        "Append to ops_log.md (same day's entry if exists, else new entry):\n"
        "```markdown\n"
        "### Board Scrape\n"
        "- SimplifyJobs new-grad fetched: <N>\n"
        "- Simplify.jobs fetched        : <N>\n"
        "- LinkedIn (board) fetched     : <N>\n"
        "- Total board results saved    : <N>  → board_results_<date>.json\n"
        "- Errors: <list or 'none'>\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s3 · lemon  ·  Company Career Page Scrape
# ─────────────────────────────────────────────────────────────────────────────
cards["lemon"] = {
    "id": "lemon", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "nectarine",
    "metadata": {"priority": "normal", "tags": ["ops", "scrape", "company"]},
    "instruction": (
        "## s3 · Company Career Page Scrape\n\n"
        f"Board scraper location: `{BOARD}`\n"
        f"Workspace            : `{WS}`\n\n"
        "### Goal\n"
        "Run the company career-page monitor to catch direct postings that never\n"
        "appear on job boards. Target companies: Google, Amazon, Apple, NVIDIA, Tesla,\n"
        "Meta, Microsoft, Waymo, Cruise, Anthropic, OpenAI, Qualcomm, Texas Instruments,\n"
        "Broadcom, Marvell, DJI, ByteDance, TikTok, Pony.ai, Plus.ai, NIO, Xpeng.\n\n"

        "### Run Company Scraper\n"
        "```\n"
        f"cd {BOARD}\n"
        "python company_scraper/company_script.py --once\n"
        "```\n"
        "If no `--once` flag: run for one polling cycle, then Ctrl+C.\n\n"

        "### Manual Career Page Check (supplement)\n"
        "For companies not in `companies.csv`, manually visit their careers pages\n"
        "and note any relevant Hardware / ML / Embedded intern roles:\n"
        "```\n"
        "# Companies to check manually if not in csv:\n"
        "# - careers.anthropic.com\n"
        "# - openai.com/careers\n"
        "# - jobs.nvidia.com\n"
        "# - jobs.qualcomm.com\n"
        "# - ti.com/careers\n"
        "# - careers.waymo.com\n"
        "```\n"
        "For each relevant role found manually, add to `manually_added_jobs.json`:\n"
        "```python\n"
        "import json, pathlib, datetime\n"
        "man_file = pathlib.Path(r'" + WS + r"') / 'manually_added_jobs.json'\n"
        "jobs = json.loads(man_file.read_text()) if man_file.exists() else []\n"
        "jobs.append({\n"
        "    'title': 'TITLE',\n"
        "    'company': 'COMPANY',\n"
        "    'url': 'https://...',\n"
        "    'location': 'LOCATION',\n"
        "    'description': 'PASTE FULL JD HERE',\n"
        "    'source': 'manual',\n"
        "    'added_at': datetime.datetime.now().isoformat()\n"
        "})\n"
        "man_file.write_text(json.dumps(jobs, indent=2))\n"
        "```\n\n"

        "### Expand companies.csv (if needed)\n"
        "If `company_scraper/companies.csv` has fewer than 20 companies:\n"
        "Open the file and add the missing companies from the target list above.\n"
        "Format: `CompanyName,careersPageURL,Country`\n\n"

        "### Log the Results\n"
        "Append to ops_log.md:\n"
        "```markdown\n"
        "### Company Scrape\n"
        "- Companies monitored       : <N>\n"
        "- New roles found (scraped) : <N>\n"
        "- New roles found (manual)  : <N>  (see manually_added_jobs.json)\n"
        "- Errors: <list or 'none'>\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s4 · nectarine  ·  Manual Enrichment  (Handshake, WayUp, LinkedIn search)
# ─────────────────────────────────────────────────────────────────────────────
cards["nectarine"] = {
    "id": "nectarine", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "tangerine",
    "metadata": {"priority": "normal", "tags": ["ops", "manual", "enrich"]},
    "instruction": (
        "## s4 · Manual Enrichment  (Handshake, WayUp, LinkedIn, direct sites)\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Capture high-value postings from sources that cannot be scraped automatically:\n"
        "Handshake, WayUp, university job boards, Discord servers, company newsletters.\n"
        "Add them to `manually_added_jobs.json` for s5 aggregation and scoring.\n\n"

        "### Sources to Check (in priority order)\n"
        "1. **Handshake** (app.joinhandshake.com) — Filter: Internship, Engineering,\n"
        "   sorted by Most Recent. Look for roles tagged Hardware, Embedded, FPGA, ML.\n"
        "2. **WayUp** (wayup.com) — Search 'embedded intern', 'hardware intern', 'ML intern'\n"
        "3. **LinkedIn Easy Apply** — Search '(Hardware OR Embedded OR ML) Intern' past 24h\n"
        "4. **AngelList / Wellfound** (wellfound.com) — Startup hardware/ML intern roles\n"
        "5. **University Career Portals** — UWaterloo, UofT, UBC, MIT, Stanford, CMU\n"
        "6. **Discord channels** — ElectricalEngineering, ML, Embedded, FPGA communities\n\n"

        "### Add Roles to manually_added_jobs.json\n"
        "For each relevant role found:\n"
        "```python\n"
        "import json, pathlib, datetime\n"
        "man_file = pathlib.Path(r'" + WS + r"') / 'manually_added_jobs.json'\n"
        "jobs = json.loads(man_file.read_text()) if man_file.exists() else []\n"
        "# Append one dict per role:\n"
        "jobs.append({\n"
        "    'title'      : 'Embedded Software Intern',\n"
        "    'company'    : 'Acme Robotics',\n"
        "    'url'        : 'https://...',\n"
        "    'location'   : 'San Jose, CA',\n"
        "    'description': '<full job description text>',\n"
        "    'source'     : 'handshake',   # or 'wayup','linkedin','wellfound','university','discord'\n"
        "    'added_at'   : datetime.datetime.now().isoformat()\n"
        "})\n"
        "man_file.write_text(json.dumps(jobs, indent=2))\n"
        "print(f'manually_added_jobs.json now has {len(jobs)} entries')\n"
        "```\n\n"

        "### Deduplication Pre-check\n"
        "Before adding a role, check if the URL already exists in `seen_jobs_orchestrator.json`:\n"
        "```python\n"
        "import json, pathlib\n"
        "seen = set(json.loads(pathlib.Path(r'" + WS + r"/seen_jobs_orchestrator.json').read_text()))\n"
        "# Only add if url not in seen\n"
        "```\n\n"

        "### Minimum Viable Enrichment\n"
        "Even if you find zero new roles manually — write the log entry and advance.\n"
        "Do NOT spend more than 15 minutes on manual searching per cycle.\n\n"

        "### Log the Results\n"
        "Append to ops_log.md:\n"
        "```markdown\n"
        "### Manual Enrichment\n"
        "- Handshake checked : yes/no\n"
        "- WayUp checked     : yes/no\n"
        "- Wellfound checked : yes/no\n"
        "- New roles added   : <N>  (total entries in manually_added_jobs.json)\n"
        "- Sources that had relevant postings: <list or 'none'>\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s5 · tangerine  ·  Aggregate All Sources → Filter → Score → Alert
# ─────────────────────────────────────────────────────────────────────────────
cards["tangerine"] = {
    "id": "tangerine", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "ugli",
    "metadata": {"priority": "high", "tags": ["ops", "aggregate", "alert"]},
    "instruction": (
        "## s5 · Aggregate All Sources → Filter → Score → Alert\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Merge jobs from all 3 sources (JobSpy, board scraper, manual), run every job\n"
        "through the FilterEngine and RelevanceScorer, send alerts for S/A-tier finds,\n"
        "and persist the unified results for analysis in s6.\n\n"

        "### Step 1 — Load all source data\n"
        "```python\n"
        "import json, pathlib\n"
        "from datetime import date\n"
        "ws = pathlib.Path(r'" + WS + r"')\n"
        "\n"
        "# 1a. Board results (from s2)\n"
        "board_file = ws / f'board_results_{date.today().isoformat()}.json'\n"
        "board_jobs = json.loads(board_file.read_text()) if board_file.exists() else []\n"
        "\n"
        "# 1b. Manually added (from s3/s4)\n"
        "man_file = ws / 'manually_added_jobs.json'\n"
        "manual_jobs = json.loads(man_file.read_text()) if man_file.exists() else []\n"
        "\n"
        "# 1c. JobSpy results (already processed by s1, read from seen_jobs for count)\n"
        "seen = set(json.loads((ws / 'seen_jobs_orchestrator.json').read_text()))\n"
        "print(f'Board: {len(board_jobs)}, Manual: {len(manual_jobs)}, Seen: {len(seen)}')\n"
        "```\n\n"

        "### Step 2 — Deduplicate by URL\n"
        "```python\n"
        "all_new = []\n"
        "for job in board_jobs + manual_jobs:\n"
        "    url = job.get('url', '')\n"
        "    if url and url not in seen:\n"
        "        all_new.append(job)\n"
        "        seen.add(url)\n"
        "print(f'New unique jobs to score: {len(all_new)}')\n"
        "```\n\n"

        "### Step 3 — Filter and Score\n"
        "```python\n"
        "from src.core.filters import FilterEngine\n"
        "from src.core.scorer import RelevanceScorer\n"
        "from src.models.job import Job\n"
        "from src.core.company_service import CompanyService\n"
        "\n"
        "filter_engine = FilterEngine()\n"
        "scorer        = RelevanceScorer()\n"
        "company_svc   = CompanyService()\n"
        "passed, tiers = [], {'S':0,'A':0,'B':0,'C':0}\n"
        "\n"
        "for raw in all_new:\n"
        "    company = company_svc.identify_company(raw.get('company',''), raw.get('description',''))\n"
        "    job = Job(\n"
        "        title=raw.get('title','No Title'),\n"
        "        company=company,\n"
        "        url=raw.get('url',''),\n"
        "        description=raw.get('description',''),\n"
        "        location=raw.get('location'),\n"
        "        job_type=raw.get('job_type','internship')\n"
        "    )\n"
        "    if not filter_engine.apply(job):\n"
        "        continue\n"
        "    scored = scorer.score(job)\n"
        "    passed.append(scored)\n"
        "    tiers[scored.score.tier] += 1\n"
        "\n"
        "print(f'Passed: {len(passed)}  S:{tiers[\"S\"]} A:{tiers[\"A\"]} B:{tiers[\"B\"]} C:{tiers[\"C\"]}')\n"
        "```\n\n"

        "### Step 4 — Send Alerts for S and A tier\n"
        "```python\n"
        "from src.services.alert_service import EmailNotifier\n"
        "notifier = EmailNotifier()\n"
        "alerts_sent = 0\n"
        "for sj in passed:\n"
        "    if sj.score.tier in ('S', 'A'):\n"
        "        notifier.notify(sj)\n"
        "        alerts_sent += 1\n"
        "print(f'Alerts sent: {alerts_sent}')\n"
        "```\n\n"

        "### Step 5 — Persist updated seen_jobs\n"
        "```python\n"
        "import json\n"
        "(ws / 'seen_jobs_orchestrator.json').write_text(json.dumps(list(seen), indent=2))\n"
        "print('seen_jobs saved')\n"
        "```\n\n"

        "### Step 6 — Write Aggregate Results File\n"
        "```python\n"
        "agg_file = ws / f'aggregated_results_{date.today().isoformat()}.json'\n"
        "agg_file.write_text(json.dumps([\n"
        "    {'title': sj.job.title, 'company': sj.job.company.name,\n"
        "     'tier': sj.score.tier, 'score': sj.score.total_score,\n"
        "     'url': sj.job.url, 'source': 'aggregated'}\n"
        "    for sj in passed\n"
        "], indent=2))\n"
        "print(f'Saved {len(passed)} scored jobs → {agg_file.name}')\n"
        "```\n\n"

        "### Log the Results\n"
        "Append to ops_log.md:\n"
        "```markdown\n"
        "### Aggregation\n"
        "- Total new unique jobs evaluated : <N>\n"
        "- Passed filters                  : <N>\n"
        "- S: <N> | A: <N> | B: <N> | C: <N>\n"
        "- Alerts sent (S+A tier)          : <N>\n"
        "- Results saved → aggregated_results_<date>.json\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s6 · ugli  ·  Analyze Combined Results
# ─────────────────────────────────────────────────────────────────────────────
cards["ugli"] = {
    "id": "ugli", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "zucchini",
    "metadata": {"priority": "normal", "tags": ["ops", "analyze"]},
    "instruction": (
        "## s6 · Analyze Combined Results\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Compute aggregate quality metrics across ALL sources, identify systemic issues,\n"
        "and write a concrete action-item list for s7 to execute.\n\n"

        "### Step 1 — Extract Last 10 Cycles from ops_log.md\n"
        "Read `ops_log.md` — collect up to 10 most recent `## Run:` entries.\n"
        "For each entry extract:\n"
        "  - `Total scraped` (JobSpy section)\n"
        "  - `Passed filters` (Aggregation section)\n"
        "  - `S + A tier` count\n"
        "  - `Alerts sent`\n\n"

        "### Step 2 — Compute Metrics\n"
        "  - **Overall yield rate** = avg(Passed / scraped × 100) across 10 runs\n"
        "  - **S+A rate** = avg(S+A / Passed × 100)\n"
        "  - **Zero-match run count** = entries where Passed = 0\n"
        "  - **Best source** = which source (jobspy / board / manual) contributed most S/A jobs\n"
        "  - **Trend** = compare yield of runs 1-5 vs 6-10 (improving / stable / declining)\n"
        "  - **Alert rate** = % of runs where at least one alert was sent\n\n"

        "### Step 3 — Keyword Audit\n"
        "Read `keywords/v1_keywords.json` (or highest version):\n"
        "  - Count terms per category\n"
        "  - Flag any category with fewer than 15 terms as **under-seeded**\n"
        "  - List 5+ specific missing terms to add next cycle:\n"
        "    Hardware: FPGA, SoC, TinyML, MLIR, Vitis AI, Neuromorphic, RISC-V, HLS\n"
        "    ML: quantization, ONNX, edge inference, model compression, distillation\n"
        "    Titles: Silicon Engineer, Chip Design Intern, Hardware Architect, AI Compiler\n\n"

        "### Step 4 — Source Quality Audit\n"
        "  - Is the board scraper returning results? If 0 board jobs — flag as CRITICAL\n"
        "  - Is manually_added_jobs.json growing? If unchanged for 3 cycles — recommend\n"
        "    expanding manual sources (add WayUp, AngelList, university boards)\n"
        "  - Is `companies.csv` in rabiuk-job-scraper >= 20 companies? Flag if fewer.\n\n"

        "### Step 5 — Config Audit\n"
        "Read `config.example.json` (never log credentials from config.json):\n"
        "  - `results_wanted` >= 50? Flag if lower\n"
        "  - `hours_old` >= 48? Flag if lower\n"
        "  - Only one search_term? Suggest adding broader variations\n\n"

        "### Write Analysis Section\n"
        "Append `### Analysis` to the most recent ops_log.md Aggregation section:\n"
        "```markdown\n"
        "### Analysis\n"
        "- Overall yield rate (10-run avg): X%\n"
        "- S+A rate                       : X%\n"
        "- Zero-match runs                : N/10\n"
        "- Trend                          : [improving / stable / declining]\n"
        "- Alert rate                     : X%\n"
        "- Best source this cycle         : [jobspy / board / manual]\n"
        "- Under-seeded keyword categories: [list or 'none']\n"
        "- Board scraper status           : [OK / CRITICAL: 0 results]\n"
        "- Config issues                  : [specific findings or 'none']\n"
        "- s7 Action Items:\n"
        "  1. <exact change — be specific>\n"
        "  2. <exact change — be specific>\n"
        "  3. <exact change — be specific>\n"
        "```\n"
        "Prefix any action item with CRITICAL if yield < 5% or 3+ consecutive zero runs.\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s7 · zucchini  ·  Tune Keywords, Scoring, Filters, Sources
# ─────────────────────────────────────────────────────────────────────────────
cards["zucchini"] = {
    "id": "zucchini", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "apple",
    "metadata": {"priority": "normal", "tags": ["ops", "tune"]},
    "instruction": (
        "## s7 · Tune Keywords, Scoring, Filters, and Sources\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Implement every action item from the s6 Analysis section.\n"
        "No action item should carry over to the next cycle unsolved.\n\n"

        "### Step 1 — Read Action Items\n"
        "Open ops_log.md, find the most recent `### Analysis` → `s7 Action Items`.\n"
        "Implement them in priority order: CRITICAL first, then the rest.\n\n"

        "### Keyword Expansion (most common fix)\n"
        "Open `keywords/v1_keywords.json` (or highest version).\n"
        "Add missing terms to the correct category (lowercase, no duplicates).\n"
        "If adding more than 8 new terms: create `keywords/v2_keywords.json` with\n"
        "all terms (old + new) — do not modify the current live version in place.\n"
        "Verify the new version loads:\n"
        "```\n"
        ".venv\\Scripts\\python.exe -c \"from src.utils.keyword_loader import load_keywords; print(load_keywords())\"\n"
        "```\n\n"

        "### Config Tuning (if volume is the issue)\n"
        "Edit `config.json` (NEVER commit it):\n"
        "  - `results_wanted` → at least 50 per site (try 100)\n"
        "  - `hours_old` → at least 48 (try 72 if zero-yield persists)\n"
        "  - If only one search_term: add broader variations like:\n"
        "    `'Hardware Engineer Intern OR FPGA Intern OR Embedded Intern OR ML Intern'`\n\n"

        "### Filter Adjustments (if over-filtering)\n"
        "Open `src/core/filters.py` (or job_filter.py if it still exists):\n"
        "  - Remove blacklist terms that catch valid hardware/ML roles\n"
        "  - Ensure the hardware_ml_filter is not too restrictive\n"
        "  - Never remove internship, visa, or seniority filters\n\n"

        "### Scoring Adjustments (if tier distribution wrong)\n"
        "Open `src/core/scorer.py` (or relevance_scorer.py):\n"
        "  - If no S-tier in last 5 cycles: lower S-tier threshold by 5 points\n"
        "  - Check hardware / ml / title weights — raise hardware weight if yield is low\n\n"

        "### Expand companies.csv (if company scraper is thin)\n"
        f"Open `{BOARD}/company_scraper/companies.csv`.\n"
        "Add any of these target companies not already listed:\n"
        "  Google, Amazon, Apple, NVIDIA, Tesla, Meta, Microsoft, Waymo, Cruise,\n"
        "  Anthropic, OpenAI, Qualcomm, TI, Broadcom, Marvell, DJI, ByteDance,\n"
        "  NIO, Xpeng, Pony.ai, Plus.ai, SambaNova, Groq, d-Matrix, Tenstorrent\n\n"

        "### Run Tests After Every File Edit\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v\n"
        "```\n"
        "All tests must pass. Fix any failure before the next edit.\n\n"

        "### Append Tuning Log\n"
        "Append to ops_log.md:\n"
        "```markdown\n"
        "### Tuning\n"
        "- Keywords added    : [list]\n"
        "- Config changes    : [list]\n"
        "- Filter changes    : [list]\n"
        "- Score changes     : [list]\n"
        "- companies.csv adds: [list]\n"
        "- Tests             : X passed / 0 failed\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# s8 · apple  ·  Commit Ops Changes
# ─────────────────────────────────────────────────────────────────────────────
cards["apple"] = {
    "id": "apple", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "banana",
    "metadata": {"priority": "normal", "tags": ["ops", "commit"]},
    "instruction": (
        "## s8 · Commit Ops Changes\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Run the full test suite, stage only safe ops files (never credentials),\n"
        "commit with the ops convention, push, and trim the seen_jobs cache if bloated.\n\n"

        "### Step 1 — Final Test Gate\n"
        "```\n"
        f"cd {WS}\n"
        ".venv\\Scripts\\activate\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v\n"
        "```\n"
        "100% pass required. If any test fails: fix it first, then come back here.\n\n"

        "### Step 2 — Stage Only Safe Files\n"
        "**NEVER** stage: `config.json`, `.env`, `.env.local`, `*.key`, `*.pem`\n"
        "Safe to stage:\n"
        "```\n"
        "git add ops_log.md EVOLUTION_LOG.md EVOLUTION_BACKLOG.md\n"
        "git add keywords/ src/ tests/ requirements.txt\n"
        "git add manually_added_jobs.json  # if it changed\n"
        "```\n"
        "Only add files that were actually modified this cycle. Check with `git diff --name-only`.\n\n"

        "### Step 3 — Commit\n"
        "```\n"
        "git commit -m \"ops: daily run and tuning $(date +%Y-%m-%d)\"\n"
        "```\n\n"

        "### Step 4 — Push\n"
        "```\n"
        "git push origin main\n"
        "```\n\n"

        "### Step 5 — Trim seen_jobs Cache\n"
        "If `seen_jobs_orchestrator.json` has more than 500 entries:\n"
        "```python\n"
        "import json, pathlib\n"
        "f = pathlib.Path(r'" + WS + r"/seen_jobs_orchestrator.json')\n"
        "items = json.loads(f.read_text())\n"
        "if len(items) > 500:\n"
        "    items = items[-200:]  # keep last 200\n"
        "    f.write_text(json.dumps(items, indent=2))\n"
        "    print(f'Trimmed to {len(items)} entries')\n"
        "```\n"
        "Then: `git add seen_jobs_orchestrator.json && git commit -m 'ops: trim seen_jobs cache'`\n\n"

        "### Step 6 — Confirm\n"
        "```\n"
        "git log --oneline -5\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# f1 · banana  ·  Discover Next Feature Sprint
# ─────────────────────────────────────────────────────────────────────────────
cards["banana"] = {
    "id": "banana", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "cherry",
    "metadata": {"priority": "normal", "tags": ["feature", "discover"]},
    "instruction": (
        "## f1 · Discover and Plan the Next Feature Sprint\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Select the single highest-impact unshipped improvement, research its feasibility,\n"
        "and write a complete `SPRINT_DECISION.md` so f2 can start immediately.\n\n"

        "### Step 1 — Gather Context\n"
        "1. Read `EVOLUTION_BACKLOG.md` (create if missing — populate in step 3)\n"
        "2. Read `EVOLUTION_LOG.md` — know what has already shipped\n"
        "3. Read the last 3 `### Analysis` sections from `ops_log.md`\n\n"

        "### Step 2 — Select Highest-Priority Item\n"
        "Priority ranking:\n"
        "  **P0** — breaks production or causes zero yield (fix immediately)\n"
        "  **P1** — reduces manual work, improves reliability, or fixes alert failures\n"
        "  **P2** — expands scraper coverage or adds a new data source\n"
        "  **P3** — nice-to-have quality improvements\n\n"
        "Common high-value P1/P2 items to consider if backlog is empty:\n"
        "  - Integrate async scraping (fetch multiple sources concurrently)\n"
        "  - Build Handshake scraper (Selenium-based) to automate s4\n"
        "  - Add WayUp API integration\n"
        "  - Auto-refresh companies.csv from a curated remote source\n"
        "  - Add Discord notification (webhook) for S-tier alerts\n"
        "  - Add job deduplication by title+company (catch same role on multiple boards)\n"
        "  - Build a CLI dashboard (rich) showing live pipeline stats\n"
        "  - Scheduled auto-run via Windows Task Scheduler integration guide\n\n"

        "### Step 3 — Feasibility Check\n"
        "Before writing SPRINT_DECISION.md:\n"
        "  - Read the relevant source files\n"
        "  - Confirm the change fits in ~200 lines of new code\n"
        "  - List exactly which files change\n\n"

        "### Step 4 — Write SPRINT_DECISION.md\n"
        "```markdown\n"
        "# Sprint Decision\n\n"
        "## Selected: <feature title>\n"
        "## Priority: <P0/P1/P2/P3>\n"
        "## Branch: feat/<kebab-case-name>\n\n"
        "## Problem\n"
        "<What is broken or missing — cite specific ops_log data>\n\n"
        "## Proposed Solution\n"
        "<3-5 sentence implementation plan — be concrete>\n\n"
        "## Files to Change\n"
        "- <file1.py>: <what changes>\n"
        "- <file2.py>: <what changes>\n\n"
        "## Acceptance Criteria\n"
        "- [ ] <verifiable criterion 1>\n"
        "- [ ] <verifiable criterion 2>\n"
        "- [ ] <verifiable criterion 3>\n"
        "- [ ] All existing tests still pass\n"
        "- [ ] New tests cover the changed code\n\n"
        "## Out of Scope\n"
        "<What you will NOT do in this sprint>\n"
        "```\n\n"

        "### Step 5 — Seed Backlog if Missing\n"
        "If `EVOLUTION_BACKLOG.md` was missing or empty: create it with the top 5\n"
        "improvements identified from ops_log pain points and the suggestions in step 2.\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# f2 · cherry  ·  Implement the Sprint Feature
# ─────────────────────────────────────────────────────────────────────────────
cards["cherry"] = {
    "id": "cherry", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "date",
    "metadata": {"priority": "high", "tags": ["feature", "implement"]},
    "instruction": (
        "## f2 · Implement the Sprint Feature\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Implement the feature selected in SPRINT_DECISION.md. Commit incrementally.\n"
        "Never accumulate broken tests.\n\n"

        "### Step 1 — Read the Brief\n"
        "Read `SPRINT_DECISION.md` completely before writing a single line of code.\n"
        "Understand every acceptance criterion.\n\n"

        "### Step 2 — Create Feature Branch\n"
        "```\n"
        f"cd {WS}\n"
        ".venv\\Scripts\\activate\n"
        "git checkout main && git pull origin main\n"
        "git checkout -b <branch name from SPRINT_DECISION.md>\n"
        "```\n\n"

        "### Step 3 — Implement File by File\n"
        "Follow `## Files to Change` exactly:\n"
        "  - After EACH file edit: run `pytest tests/ -q` — fix any red test immediately\n"
        "  - Commit after each meaningful chunk:\n"
        "    `git commit -m 'feat(<scope>): <imperative description>'`\n\n"

        "### Code Standards (enforced — no exceptions)\n"
        "  - Type hints on every parameter and return value\n"
        "  - Function body ≤ 40 lines — split if longer\n"
        "  - No `print()` — use `logging.getLogger(__name__)`\n"
        "  - No magic numbers — define named constants at top of file\n"
        "  - Every new public function: one-line docstring\n"
        "  - No bare `except:` — always catch specific exception types\n\n"

        "### If the Feature Touches Scraping Pipeline\n"
        "  - Update `config.example.json` with any new config keys (with defaults)\n"
        "  - Never touch `config.json` (live credentials)\n"
        "  - If adding a new scraper source: add it to the `## Sources` section of guidance.md\n\n"

        "### Step 4 — Final Test Run\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v --tb=short\n"
        "```\n"
        "All tests must pass. Record the total pass count for f3.\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# f3 · date  ·  Test and Verify the Sprint Feature
# ─────────────────────────────────────────────────────────────────────────────
cards["date"] = {
    "id": "date", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "elderberry",
    "metadata": {"priority": "normal", "tags": ["feature", "test"]},
    "instruction": (
        "## f3 · Test and Verify the Sprint Feature\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Write comprehensive tests, achieve 100% pass, tick every acceptance criterion.\n"
        "Do not advance to f4 until all criteria are verified.\n\n"

        "### Step 1 — Confirm You Are on the Feature Branch\n"
        "```\n"
        f"cd {WS}\n"
        ".venv\\Scripts\\activate\n"
        "git branch --show-current\n"
        "```\n\n"

        "### Step 2 — Extract Acceptance Criteria\n"
        "Read `SPRINT_DECISION.md` — list every `- [ ]` criterion.\n"
        "These are your pass/fail conditions.\n\n"

        "### Step 3 — Write Tests (minimum 3 per changed function)\n"
        "  - **Happy path**: valid input → correct output\n"
        "  - **Edge case**: empty input, zero results, boundary values\n"
        "  - **Error path**: invalid input raises the correct exception\n"
        "  - All external calls (scraper, email, file I/O) must be mocked with `unittest.mock`\n"
        "  - Tests go in `tests/test_<module_name>.py`\n\n"

        "### Step 4 — Integration Test (if sprint touched >1 module)\n"
        "Place in `tests/test_integration.py`:\n"
        "  - Mock the JobSpy scraper but let filters and scorer run real logic\n"
        "  - Assert a known-good job DataFrame produces correct tier assignment\n"
        "  - Assert the new feature integrates correctly end-to-end\n\n"

        "### Step 5 — Run Full Suite\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v --tb=long\n"
        "```\n"
        "100% pass required. Fix any failure before proceeding.\n\n"

        "### Step 6 — Tick Off Criteria in SPRINT_DECISION.md\n"
        "For each verified criterion: change `- [ ]` → `- [x]`\n\n"

        "### Step 7 — Hard Stop if Any Criterion Unchecked\n"
        "If ANY criterion remains `[ ]`: fix the gap, re-run, repeat.\n"
        "Do NOT advance to f4 with unmet criteria.\n\n"

        "### Step 8 — Append Verification Summary\n"
        "Append to `SPRINT_DECISION.md`:\n"
        "```markdown\n"
        "## Verification\n"
        "- Tests added     : <N>\n"
        "- Total suite     : <N> passed / 0 failed\n"
        "- All criteria    : OK\n"
        "- Verified by card: f3 (date)\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# f4 · elderberry  ·  Ship the Feature to Main
# ─────────────────────────────────────────────────────────────────────────────
cards["elderberry"] = {
    "id": "elderberry", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "mango",
    "metadata": {"priority": "normal", "tags": ["feature", "ship"]},
    "instruction": (
        "## f4 · Ship the Feature to Main\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Merge the verified feature branch to main, update EVOLUTION_LOG, tag the release,\n"
        "and clean up sprint artifacts.\n\n"

        "### Step 1 — Verify Ready to Ship\n"
        "Read `SPRINT_DECISION.md` — confirm `## Verification` is present and\n"
        "ALL criteria are `[x]`. If not: return to f3.\n\n"

        "### Step 2 — Merge to Main\n"
        "```\n"
        f"cd {WS}\n"
        ".venv\\Scripts\\activate\n"
        "git checkout main && git pull origin main\n"
        "git merge --no-ff <feature-branch> -m \"feat(<scope>): <description>\"\n"
        "```\n\n"

        "### Step 3 — Final Test on Main\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v\n"
        "```\n"
        "If any regression: `git revert HEAD`, fix on the branch, retry.\n\n"

        "### Step 4 — Push Main\n"
        "```\n"
        "git push origin main\n"
        "```\n\n"

        "### Step 5 — Update EVOLUTION_LOG.md\n"
        "Append:\n"
        "```markdown\n"
        "## <version> — <date>\n"
        "**Feature**: <title from SPRINT_DECISION>\n"
        "**Branch**: <branch name>\n"
        "**Summary**: <2-3 sentences: what was built and why it matters>\n"
        "**Tests added**: <N>\n"
        "**Commit**: <git hash>\n"
        "```\n\n"

        "### Step 6 — Clean Up Sprint Artifacts\n"
        "```\n"
        "del SPRINT_DECISION.md\n"
        "git add -u\n"
        "git commit -m \"chore: close sprint — <feature title>\"\n"
        "git push origin main\n"
        "```\n\n"

        "### Step 7 — Tag the Release\n"
        "```\n"
        "# Get current version: git describe --tags --abbrev=0\n"
        "# Bump: patch for ops/audit-only, minor for any new capability\n"
        "git tag v<new-version>\n"
        "git push origin --tags\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# e1 · mango  ·  Comprehensive System Audit
# ─────────────────────────────────────────────────────────────────────────────
cards["mango"] = {
    "id": "mango", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "orange",
    "metadata": {"priority": "normal", "tags": ["evolution", "audit"]},
    "instruction": (
        "## e1 · Comprehensive System Audit\n\n"
        f"Workspace      : `{WS}`\n"
        f"Board scraper  : `{BOARD}`\n\n"
        "### Goal\n"
        "Full-system quality review: code health, dependency status, pipeline yield,\n"
        "source coverage, and evolution history. Output: `AUDIT_REPORT.md`.\n\n"

        "### Step 1 — Pull Latest\n"
        "```\n"
        f"cd {WS}\n"
        ".venv\\Scripts\\activate\n"
        "git checkout main && git pull origin main\n"
        "```\n\n"

        "### Step 2 — Full Test Suite\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pytest tests/ -v --tb=short\n"
        "```\n"
        "Record pass/fail counts and any uncovered functions.\n\n"

        "### Step 3 — Code Health Audit (ALL .py files)\n"
        "Read every `.py` file in `src/`, root workspace, and `tests/`:\n"
        "  - **Function length** > 40 lines → flag\n"
        "  - **Type hints** missing on any public function → flag\n"
        "  - **Dead code**: unused imports, commented-out blocks, unreachable branches\n"
        "  - **Magic numbers**: unexplained numeric literals\n"
        "  - **Security**: hardcoded secrets, API keys outside config.json\n"
        "  - **Logging**: remaining `print()` calls in core logic\n"
        "  - **Docstrings**: public functions without a one-line docstring\n\n"

        "### Step 4 — Source Coverage Audit\n"
        "Evaluate the scraping pipeline coverage:\n"
        "  - Is JobSpy returning jobs from all 3 configured sites?\n"
        "  - Is the board scraper operational and returning results?\n"
        "  - Is `companies.csv` comprehensive (target: 25+ companies)?\n"
        "  - Are there major scraping sources still missing?\n"
        "    (Handshake, Greenhouse API, Lever API, Ashby, Workday, iCIMS)\n"
        "  - What % of S/A-tier jobs came from each source over the last 5 cycles?\n\n"

        "### Step 5 — Dependency Check\n"
        "```\n"
        ".venv\\Scripts\\python.exe -m pip list --outdated\n"
        "```\n"
        "Focus on: jobspy, pandas, rapidfuzz, rich, pydantic, pytest, requests, bs4.\n\n"

        "### Step 6 — Yield Analysis\n"
        "Read ALL ops_log entries — compute:\n"
        "  - Overall average yield rate (all sources combined)\n"
        "  - Per-source average yield: jobspy vs board vs manual\n"
        "  - Zero-match run rate (% of cycles with 0 alerts)\n"
        "  - Trend over last 10 cycles\n\n"

        "### Step 7 — Write AUDIT_REPORT.md\n"
        "```markdown\n"
        "# Audit Report — <date>\n\n"
        "## Test Suite\n"
        "- Result: <N> passed / <N> failed\n"
        "- Coverage gaps: <list uncovered functions or 'none'>\n\n"
        "## Code Quality Issues\n"
        "| File | Issue | Severity |\n"
        "|------|-------|----------|\n"
        "| ...  | ...   | high/med/low |\n\n"
        "## Source Coverage\n"
        "- JobSpy sites active    : [linkedin, indeed, glassdoor]\n"
        "- Board scraper status   : [OK / CRITICAL]\n"
        "- companies.csv count    : <N>\n"
        "- Missing major sources  : [list]\n"
        "- Best-performing source : [name, X% of S/A jobs]\n\n"
        "## Yield Analysis (all sources)\n"
        "- Overall average yield   : X%\n"
        "- Per-source yield        : jobspy X%, board X%, manual X%\n"
        "- Zero-alert cycle rate   : X%\n"
        "- Trend                   : [improving / stable / declining]\n\n"
        "## Dependency Status\n"
        "- Up to date: [list]\n"
        "- Outdated  : [pkg: current -> latest]\n\n"
        "## Features Shipped This Cycle\n"
        "<from EVOLUTION_LOG>\n\n"
        "## Top 5 Improvements (ranked by impact × feasibility)\n"
        "1. **[TITLE]** (P0/P1/P2) — <problem> | <proposed fix>\n"
        "2. ...\n"
        "5. ...\n"
        "```\n"
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# e2 · orange  ·  Refresh Evolution Backlog and Close the Cycle
# ─────────────────────────────────────────────────────────────────────────────
cards["orange"] = {
    "id": "orange", "loop_id": "main", "workflow": "jobscrap_v2", "version": "v1",
    "next_card": "fig",
    "metadata": {"priority": "normal", "tags": ["evolution", "backlog"]},
    "instruction": (
        "## e2 · Refresh Evolution Backlog and Close the Cycle\n\n"
        f"Workspace: `{WS}`\n\n"
        "### Goal\n"
        "Merge audit findings into the backlog, version-bump, tag, and clean up.\n"
        "The engine immediately returns to fig (s1) after this card — leave a clean state.\n\n"

        "### Step 1 — Read Audit Findings\n"
        "Read `AUDIT_REPORT.md` — extract the **Top 5 Improvements** list.\n\n"

        "### Step 2 — Read Current Backlog and Log\n"
        "Read `EVOLUTION_BACKLOG.md` (create if missing).\n"
        "Read `EVOLUTION_LOG.md` — know what has already shipped (never re-add shipped items).\n\n"

        "### Step 3 — Merge and Re-rank\n"
        "  - Remove items already shipped (in EVOLUTION_LOG)\n"
        "  - Add new items from AUDIT_REPORT not already in backlog\n"
        "  - Re-rank all items: P0 > P1 > P2 > P3\n"
        "  - Keep max 10 items — cut lowest-priority if over limit\n"
        "  - Each item: title, priority, one-sentence description, affected files\n\n"

        "### Step 4 — Rewrite EVOLUTION_BACKLOG.md\n"
        "```markdown\n"
        "# Evolution Backlog — updated <date>\n\n"
        "| Priority | Item | Description | Files |\n"
        "|----------|------|-------------|-------|\n"
        "| P0 | <title> | <1 sentence> | <files> |\n"
        "| P1 | <title> | <1 sentence> | <files> |\n"
        "...max 10 rows...\n"
        "```\n\n"

        "### Step 5 — Determine Version Bump\n"
        "```\n"
        "git describe --tags --abbrev=0  # current version (default v0.1.0 if none)\n"
        "```\n"
        "  - Any new feature shipped this cycle → bump minor (0.X.0)\n"
        "  - Only ops/audit work → bump patch (0.1.X)\n\n"

        "### Step 6 — Commit Evolution State\n"
        "```\n"
        "git add EVOLUTION_BACKLOG.md EVOLUTION_LOG.md ops_log.md\n"
        "git commit -m \"audit: system evolution pass v<version>\"\n"
        "git push origin main\n"
        "```\n\n"

        "### Step 7 — Delete Audit Report and Commit\n"
        "```\n"
        "del AUDIT_REPORT.md\n"
        "git add -u\n"
        "git commit -m \"chore: clean up audit artifacts\"\n"
        "git push origin main\n"
        "```\n\n"

        "### Step 8 — Tag the Release\n"
        "```\n"
        "git tag v<version>\n"
        "git push origin --tags\n"
        "```\n\n"

        "### Step 9 — Archive Daily Result Files\n"
        "Move today's result files into archive to prevent workspace clutter:\n"
        "```python\n"
        "import shutil, pathlib, datetime\n"
        "ws = pathlib.Path(r'" + WS + r"')\n"
        "today = datetime.date.today().isoformat()\n"
        "archive = ws / 'data_archive'\n"
        "archive.mkdir(exist_ok=True)\n"
        "for pattern in [f'board_results_{today}.json', f'aggregated_results_{today}.json']:\n"
        "    f = ws / pattern\n"
        "    if f.exists():\n"
        "        shutil.move(str(f), str(archive / pattern))\n"
        "        print(f'Archived {pattern}')\n"
        "```\n\n"
        "The cycle is complete. The engine returns to fig (s1) for the next iteration."
    )
}

# ── Write all cards ──────────────────────────────────────────────────────────
order = ["fig","kiwi","lemon","nectarine","tangerine","ugli","zucchini",
         "apple","banana","cherry","date","elderberry","mango","orange"]

for name in order:
    path = WF / f"{name}.json"
    path.write_text(json.dumps(cards[name], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {name}.json")

print("\n14-card topology:")
for name in order:
    d = json.loads((WF / f"{name}.json").read_text())
    tags = ", ".join(d["metadata"]["tags"])
    print(f"  {d['id']:12} → {d['next_card']:12}  [{tags}]")
