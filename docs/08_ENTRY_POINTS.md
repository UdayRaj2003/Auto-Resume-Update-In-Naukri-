# 08 — Entry Points

Every runnable file in the repository with execution analysis.

---

## Summary Table

| File | Entry Mechanism | Safe to Run? | Primary Outcome |
|------|-----------------|--------------|-----------------|
| `main.py` | `if __name__ == "__main__"` | ⚠️ **Caution** — applies to jobs | Search + apply loop |
| `apply_agent.py` | `if __name__ == "__main__"` | ⚠️ **Caution** — auto-applies | AI-filtered apply run |
| `updateDaily.py` | Module-level `print(handler(...))` | ❌ **No** — outdated, empty creds | Failed resume update |
| `get_Nkparam.py` | Module-level infinite loop | ⚠️ Opens Chrome forever | nkPool.txt tokens |
| `test_session.py` | Module-level network calls | ⚠️ External TLS probes | Console fingerprint output |
| `test_nkpram.py` | No auto-run | ⚠️ Broken if invoked | NOT VERIFIED |

**Library modules** (`src/client/*`, `src/utils/*` except above) are **not** entry points.

---

## 1. `main.py`

### Purpose
Demo script demonstrating login, job search, and easy apply. README describes as integration demo.

### How to Execute
```bash
cd NopeRi
pip install -r requirements.txt
# Create .env with USERNAME and PASSWORD
python main.py
```

### Execution Flow (Active Code Path)

| Step | Action |
|------|--------|
| 1 | `load_dotenv(override=True)` |
| 2 | Read `USERNAME`, `PASSWORD` from environment |
| 3 | `NaukriLoginClient(username, password)` |
| 4 | `client.login()` |
| 5 | `NaukriJobClient(client)` |
| 6 | `jc.search_jobs(keyword="Node.js developer", location="Hyderabad", experience=2)` |
| 7 | For each `Job`: print metadata |
| 8 | `jc.apply_job(job, mandatory_skills, optional_skills, source="recommended")` |
| 9 | Skip if `questionnaire` in response |
| 10 | `time.sleep(3)` between applies |

### Commented-Out Paths (Inactive)
- `update_resume(path)`
- `update_profile(headline=...)`, `update_profile(summary=...)`
- `fetch_profile_id()`, `get_form_key2()`
- `get_recommended_jobs()`
- Paginated search loop with `input()`

### Modules Imported
| Module | Objects/Functions Used |
|--------|------------------------|
| `src.client.naukri_client` | `NaukriLoginClient` |
| `src.client.job_client` | `NaukriJobClient` |
| `dotenv` | `load_dotenv` |
| `colorama` | `Fore`, `Style`, `init` |
| `os` | `getenv` |
| `time` | `sleep` |

### API Endpoints Hit
1. `POST /central-login-services/v1/login`
2. `GET /jobapi/v3/search` (+ nkparam)
3. `POST /apply-workflow/v1/apply` (per job)

### Final Outcome
Colored terminal output; real job applications submitted for each non-questionnaire search result.

---

## 2. `apply_agent.py`

### Purpose
Fully automated AI-powered job search, scoring, and application pipeline.

### How to Execute
```bash
cd NopeRi
# .env: USERNAME, PASSWORD, OPEN_API_KEY
python apply_agent.py
```

### Execution Flow

| Step | Function/Method |
|------|-----------------|
| 1 | `load_dotenv()` |
| 2 | `NaukriLoginClient.login()` |
| 3 | `fetch_all_jobs(jc)` — 4 keyword/location queries |
| 4 | `JobFilterPipeline2(openai_api_key).run(jobs)` |
| 5 | Build `score_map`, `allow` set from pipeline output |
| 6 | `load_applied_jobs()` from CSV |
| 7 | Filter `allowed_jobs` by AI pass |
| 8 | For each job: `is_external_apply()` → skip if external |
| 9 | `apply_job(..., source="search")` |
| 10 | If questionnaire: `handle_static_questionnaire_and_apply()` |
| 11 | `save_applied_job()` → `applied_jobs.csv` |
| 12 | `print_summary()` |

### Modules Imported
| Module | Usage |
|--------|-------|
| `NaukriLoginClient` | Auth |
| `NaukriJobClient` | Search, details, apply |
| `JobFilterPipeline2` | AI filter |
| `NaukriAuthError`, `NaukriParseError` | Imported, **not used** in main block |
| `csv`, `datetime`, `logging` | Persistence/display |

### Configuration (Hardcoded in `fetch_all_jobs`)
| Variable | Value |
|----------|-------|
| `BQUERIES` | 4 backend keyword/location pairs |
| `EXPERIENCE_LEVELS` | `[2]` |
| `PAGES` | `1` |
| `JOB_AGE` | `2` |

### Pipeline Defaults (`JobFilterPipeline2.__init__`)
| Param | Default |
|-------|---------|
| `min_apply_score` | 50 |
| `daily_apply_limit` | 50 |
| `ai_score_limit` | 300 |

### API Endpoints Hit
- Naukri login, search, job details, apply
- OpenAI chat completions

### Artifacts Created
- `applied_jobs.csv` (append)
- `score_cache.json` (read/write)

### Final Outcome
Terminal dashboard + CSV log of successful applications.

---

## 3. `updateDaily.py`

### Purpose
Legacy AWS Lambda/cron handler to download resume from Google Drive and upload to Naukri.

### How to Execute
```bash
cd NopeRi
python updateDaily.py
```
**Runs immediately** — no `if __name__` guard.

### Execution Flow
```
handler("event", "context")
  → update_resume()
    → validate empty globals → likely error
    → legacy NaukriLoginClient.login()
    → Google Drive download
    → file validation POST
    → profile resume POST
```

### Required Configuration (Globals — All Empty)
```python
username = ""
password = ""
file_id = ""      # Google Drive ID
form_key = ""     # Manual from network tab
filename = ""     # Optional
```

### Final Outcome
Prints `{"status": {...}, "message": "Cron executed successfully"}`

### Status
**OUTDATED — should not be executed**

---

## 4. `src/utils/get_Nkparam.py`

### Purpose
Selenium harvester for nkparam tokens.

### How to Execute
```bash
cd NopeRi
# Requires Chrome + chromedriver
python src/utils/get_Nkparam.py
```

### Execution Flow
Infinite loop until Ctrl+C:
1. Open Chrome to hardcoded Naukri search URL
2. Wait 5s, read performance logs
3. Extract `nkparam` request header
4. Append to `nkPool.txt`
5. Clear cookies/storage
6. Sleep 2s, repeat

### Prerequisites
- Chrome installed
- Selenium 4.x
- Writable `nkPool.txt` in CWD

### Final Outcome
Growing `nkPool.txt` file

### Status
**Legacy backup utility**

---

## 5. `src/tests/test_session.py`

### Purpose
Manual httpcloak TLS fingerprint verification.

### How to Execute
```bash
cd NopeRi
python src/tests/test_session.py
```

### Execution Flow (runs at import)
1. Create httpcloak session
2. GET `tls.peet.ws/api/all` — print JA3/JA4
3. GET `cf.erisa.uk/` — Cloudflare check
4. GET `cloudflare.com/cdn-cgi/trace`

### Final Outcome
Console TLS/fingerprint diagnostics

### Status
**Experimental — not a pytest test**

---

## 6. `src/tests/test_nkpram.py`

### Purpose
Incomplete nkparam generation experiment.

### How to Execute
```bash
python src/tests/test_nkpram.py
```
Defines `generate_nkparam()` but does not call it at module level.

### Status
**Broken** — `PUBLIC_KEY="search"` is invalid RSA key

---

## Non-Entry Library Usage Pattern

For features without dedicated scripts, use Python interactively:

```bash
cd NopeRi
python
```

```python
from dotenv import load_dotenv
import os
load_dotenv()
from src.client.naukri_client import NaukriLoginClient
from src.client.job_client import NaukriJobClient

client = NaukriLoginClient(os.getenv("USERNAME"), os.getenv("PASSWORD"))
client.login()

# Feature-specific calls here
```

---

## Entry Point Dependency: Working Directory

All entry points assume execution from `NopeRi/` directory because imports use `from src.client...`.

**Alternative:**
```bash
set PYTHONPATH=D:\Test jobbot\NopeRi
python D:\Test jobbot\NopeRi\main.py
```

---

## Danger Ranking

| Rank | File | Risk |
|------|------|------|
| 1 | `main.py` | Submits real applications without AI filter |
| 2 | `apply_agent.py` | Submits up to 50 AI-approved applications |
| 3 | `get_Nkparam.py` | Infinite browser loop, resource consumption |
| 4 | `updateDaily.py` | Failed API calls with empty creds |
| 5 | `test_session.py` | External network probes only |
