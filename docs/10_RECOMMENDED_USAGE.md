# 10 — Recommended Usage

Practical guide for which file to execute for each task. Based on verified source analysis.

---

## Quick Reference

| Task | Execute This | Command / Code |
|------|--------------|----------------|
| **Login only** | No dedicated script | See § Login Only |
| **Resume upload/update** | Library call or uncomment `main.py` | See § Resume |
| **Profile update** | Library call or uncomment `main.py` | See § Profile |
| **Job search only** | Modify `main.py` or library | See § Search |
| **Recommended jobs** | Uncomment in `main.py` or library | See § Recommended |
| **Job details** | Library call only | See § Job Details |
| **Application history** | Library call only | See § History |
| **Auto-apply (AI)** | `apply_agent.py` | `python apply_agent.py` |
| **Demo all features** | `main.py` | `python main.py` ⚠️ applies to jobs |
| **Harvest nkparam tokens** | `get_Nkparam.py` | `python src/utils/get_Nkparam.py` |

---

## Prerequisites (All Flows)

```bash
cd NopeRi
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `NopeRi/.env`:
```env
USERNAME=your_email@example.com
PASSWORD=your_password
OPEN_API_KEY=sk-...           # apply_agent.py only
```

Run from `NopeRi/` directory (required for `from src...` imports).

---

## Login Only

**No dedicated script exists.**

```python
from dotenv import load_dotenv
import os
load_dotenv()

from src.client.naukri_client import NaukriLoginClient

client = NaukriLoginClient(os.getenv("USERNAME"), os.getenv("PASSWORD"))
session = client.login()
print("Token:", session.bearer_token[:20], "...")
```

### OTP Login (Manual Two-Step)

```python
client = NaukriLoginClient(os.getenv("USERNAME"), os.getenv("PASSWORD"))

try:
    client.login()
except Exception:
    client.send_otp(is_mobile=True)  # or False for email
    otp = input("Enter OTP: ")
    client.verify_otp(otp, is_mobile=True)
```

**Why no script:** OTP requires interactive input; not wrapped in any entry point.

---

## Resume Upload / Update Only

`update_resume()` performs **validate + attach** (full upload pipeline).

### Option A — Uncomment in `main.py` (lines 26–28)

```python
print(client.update_resume(r"C:/path/to/resume.pdf"))
```

Comment out search/apply section first to avoid accidental applications.

### Option B — Standalone script

```python
from dotenv import load_dotenv
import os
load_dotenv()

from src.client.naukri_client import NaukriLoginClient

client = NaukriLoginClient(os.getenv("USERNAME"), os.getenv("PASSWORD"))
client.login()
result = client.update_resume("path/to/resume.pdf")
print(result)
```

### Do NOT Use
- **`updateDaily.py`** — outdated, requires manual `form_key`, Google Drive, empty globals

---

## Profile Update Only

Updates headline, name, and/or summary independently.

```python
client.login()
client.update_profile(headline="Backend Engineer | Python · Node.js")
client.update_profile(summary="2 years building scalable APIs.")
client.update_profile(name="Your Name")  # optional
```

Or uncomment lines 34–37 in `main.py`.

---

## Job Search Only

### Option A — Modify `main.py`

Comment out the apply loop (lines 66–90). Keep search block (lines 58–64).

### Option B — Library

```python
from src.client.job_client import NaukriJobClient

client.login()
jc = NaukriJobClient(client)
jobs = jc.search_jobs(
    keyword="Python backend developer",
    location="Bangalore",
    experience=2,
    page=1,        # Note: default in job_client is page=2
    job_age=3,
)
for j in jobs:
    print(j.title, j.company, j.job_id)
```

---

## Recommended Jobs Only

```python
client.login()
jc = NaukriJobClient(client)
jobs = jc.get_recommended_jobs()
for j in jobs:
    print(j.title, "—", j.company)
```

Or uncomment lines 49–50 in `main.py`.

---

## Job Details Only

No standalone script.

```python
client.login()
jc = NaukriJobClient(client)
details = jc.get_job_details("123456789")
print(details)

# Check external apply:
if jc.is_external_apply("123456789"):
    print("External apply — cannot use API")
```

---

## Application History Only

No standalone script.

```python
client.login()
raw = client.get_application_history(page_size=20, days=90, page_number=1)
history = client.parse_history(raw)
for h in history:
    print(h.job_title, h.company, h.apply_type)
```

---

## Auto-Apply to Jobs

### Recommended: AI Agent

```bash
python apply_agent.py
```

**What it does:**
- Searches 4 curated queries
- AI scores with OpenAI (`min score 50`, max 50 applies/day)
- Skips external apply jobs
- Handles questionnaires with static answers
- Logs to `applied_jobs.csv`

**Requires:** `OPEN_API_KEY` in `.env`

### Not Recommended: Raw Demo

```bash
python main.py
```

Applies to **every** search result without AI filtering. Use only for controlled testing.

---

## nkparam Token Harvesting (Fallback)

Only if `generate_nkparam()` starts failing (403 on search):

```bash
python src/utils/get_Nkparam.py
# Ctrl+C to stop
```

Then optionally use pool mode:
```python
jc = NaukriJobClient(client, use_pool=True)
# Note: must manually add tokens to jc.pool — nkPool.txt auto-load NOT VERIFIED
```

---

## Files You Should NEVER Run Accidentally

| File | Reason |
|------|--------|
| `main.py` | Submits real job applications |
| `apply_agent.py` | Submits up to 50 AI-approved applications |
| `updateDaily.py` | Outdated; executes on import |
| `get_Nkparam.py` | Infinite Chrome loop |
| `test_session.py` | External network probes at import |

---

## Files Safe to Ignore

| File | Unless... |
|------|-----------|
| `updateDaily.py` | You maintain legacy Lambda cron |
| `dbhandler.py` | You plan to integrate SQLite nkparam store |
| `src/tests/*` | You need TLS debugging |
| `assests/logo2.svg` | Never (README asset only) |

---

## Files No Longer Used

| File | Replacement |
|------|-------------|
| `updateDaily.py` | `NaukriLoginClient.update_resume()` |
| `dbhandler.py` | `nkparam_generator.py` or `get_Nkparam.py` |
| `get_form_key()` | `get_form_key2()` |
| `test_nkpram.py` | `test_nkparam` superseded by `nkparam_generator.py` |

---

## Decision Tree

```
What do you want to do?
│
├─ Just authenticate?
│   └─ Python REPL + NaukriLoginClient.login()
│
├─ Update resume/profile?
│   └─ Python REPL + update_resume() / update_profile()
│
├─ Browse jobs (no apply)?
│   └─ Python REPL + search_jobs() or get_recommended_jobs()
│
├─ Auto-apply intelligently?
│   └─ python apply_agent.py
│
├─ Test apply mechanism manually?
│   └─ python main.py (CAUTION: real applications)
│
└─ Fix broken search (403)?
    └─ python src/utils/get_Nkparam.py → use_pool=True
```

---

## Environment / IP Guidance

From `naukri_client.py` and README:
- Run from **home/residential IP** when possible
- Avoid Azure, GitHub Actions, datacenter IPs
- Session cookies are **IP-bound** — don't switch IPs mid-session

---

## Customization Points

| Goal | Edit Location |
|------|---------------|
| Search keywords (agent) | `apply_agent.py` → `fetch_all_jobs()` → `BQUERIES` |
| AI score threshold | `jop_classifier.py` → `min_apply_score` (default 50) |
| Daily apply cap | `jop_classifier.py` → `daily_apply_limit` (default 50) |
| Questionnaire answers | `job_client.py` → `PROFILE` dict in `handle_static_questionnaire_and_apply` |
| Demo search terms | `main.py` → `search_jobs(...)` args |

---

## Known Gaps (Use Library, Not Scripts)

These features exist in the API client but have **no dedicated executable**:

- OTP full automation (needs interactive OTP input)
- Application history viewer
- Job details fetcher
- Recommended jobs-only runner
- Login-only runner

Create small one-off scripts if needed, following the patterns above.
