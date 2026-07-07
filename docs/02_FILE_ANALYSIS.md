# 02 — File Analysis

Every file under `NopeRi/` (excluding `.venv/` and `__pycache__/`). Paths are relative to `NopeRi/`.

---

## Top-Level Files

### `main.py`

| Field | Value |
|-------|-------|
| **Purpose** | Demo / integration script — login, search, apply loop |
| **Responsibility** | Orchestrates `NaukriLoginClient` + `NaukriJobClient` for manual testing |
| **Status** | **Current**, **Demo** — README lists as "Entry point — demo of all features" |
| **Imports** | `NaukriLoginClient`, `NaukriJobClient`, `dotenv`, `colorama`, `os`, `time` |
| **Imported By** | None |
| **Dependencies** | `.env` (`USERNAME`, `PASSWORD`), full `src/` client stack |
| **Safe to ignore?** | No (primary demo entry) |
| **Safe to delete?** | No |

**Active behavior (verified):** Login → search `"Node.js developer"` in Hyderabad → apply to every result (skips questionnaire-only).

---

### `apply_agent.py`

| Field | Value |
|-------|-------|
| **Purpose** | AI-powered automated job application agent |
| **Responsibility** | Login, multi-query fetch, AI filter, apply with questionnaire handling, CSV dedup |
| **Status** | **Current**, **Production-ready** (per README; questionnaire partial) |
| **Imports** | `NaukriLoginClient`, `NaukriJobClient`, `JobFilterPipeline2`, exceptions, `dotenv`, `colorama`, `csv`, `logging`, `datetime` |
| **Imported By** | None |
| **Dependencies** | `.env` (`USERNAME`, `PASSWORD`, `OPEN_API_KEY`), creates `applied_jobs.csv` |
| **Safe to ignore?** | No (if using AI agent) |
| **Safe to delete?** | No |

---

### `updateDaily.py`

| Field | Value |
|-------|-------|
| **Purpose** | Legacy cron/Lambda resume updater from Google Drive |
| **Responsibility** | Self-contained login + Drive download + file upload + profile resume attach |
| **Status** | **Outdated / Legacy** — header comment `#outdated#`; duplicates `src/client/naukri_client.py` |
| **Imports** | `requests`, `json`, `BytesIO`, `datetime`, `os`, `random`, `re` only |
| **Imported By** | None |
| **Dependencies** | Global vars: `username`, `password`, `file_id`, `form_key` (all empty strings) |
| **Safe to ignore?** | **Yes** |
| **Safe to delete?** | Yes (if not using Lambda cron) — **but runs on import** (line 245) |

**Danger:** `print(handler("event", "context"))` executes at module import/run without `if __name__` guard.

---

### `README.md`

| Field | Value |
|-------|-------|
| **Purpose** | User documentation, feature matrix, quick start |
| **Status** | **Current** |
| **Imports** | N/A |
| **Imported By** | N/A |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

---

### `requirements.txt`

| Field | Value |
|-------|-------|
| **Purpose** | Python dependency list |
| **Status** | **Current** |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

---

### `.env`

| Field | Value |
|-------|-------|
| **Purpose** | Credentials storage |
| **Status** | **Current** (runtime config, gitignored) |
| **Expected keys** | `USERNAME`, `PASSWORD`, `OPEN_API_KEY` (agent only) |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

---

### `.gitignore`

| Field | Value |
|-------|-------|
| **Purpose** | Ignore `.env`, venv, cache |
| **Status** | **Current** |
| **Note** | Does NOT ignore `nkPool.txt`, `applied_jobs.csv`, `score_cache.json` |
| **Safe to delete?** | No |

---

### `assests/logo2.svg`

| Field | Value |
|-------|-------|
| **Purpose** | README header logo |
| **Status** | **Utility** (static asset) |
| **Imported By** | README markdown only |
| **Safe to ignore?** | **Yes** |
| **Safe to delete?** | Yes (breaks README image only) |

---

## `src/client/`

### `src/client/naukri_client.py`

| Field | Value |
|-------|-------|
| **Purpose** | Core Naukri auth, profile, resume, history client |
| **Responsibility** | All myNaukri/resman-aggregator and login APIs |
| **Status** | **Current**, **Production-ready** |
| **Imports** | `session.build_session`, `constants.*`, `exceptions.*`, `models.*`, `extractors`, `requests`, `request_helper.with_exponential_retry` |
| **Imported By** | `main.py`, `apply_agent.py`, `job_client.py` |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

**Classes:** `NaukriLoginClient` (only class)

---

### `src/client/job_client.py`

| Field | Value |
|-------|-------|
| **Purpose** | Job search, recommendations, apply, details |
| **Responsibility** | jobapi + apply-workflow endpoints |
| **Status** | **Current**, **Production-ready** |
| **Imports** | `Job`, `NaukriLoginClient`, exceptions, `with_exponential_retry` (imported, **not used on methods**), `generate_nkparam`, constants |
| **Imported By** | `main.py`, `apply_agent.py` |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

**Classes:** `NaukriJobClient`

---

### `src/client/jop_classifier.py`

| Field | Value |
|-------|-------|
| **Purpose** | AI + rule-based job filtering pipeline |
| **Responsibility** | Score/rank jobs via OpenAI; veto rules for title/company/stack |
| **Status** | **Current** (used exclusively by `apply_agent.py`) |
| **Imports** | `json`, `os`, `re`, `requests` |
| **Imported By** | `apply_agent.py` only |
| **Safe to ignore?** | Yes (unless using AI agent) |
| **Safe to delete?** | No (required by agent) |

**Classes:** `JobFilterPipeline2`  
**Note:** Filename typo `jop_classifier` (not `job_classifier`).

---

### `src/client/session.py`

| Field | Value |
|-------|-------|
| **Purpose** | HTTP session factory |
| **Responsibility** | Returns httpcloak Chrome-fingerprint session |
| **Status** | **Current**, **Helper** |
| **Imports** | `httpcloak` |
| **Imported By** | `naukri_client.py` |
| **Safe to ignore?** | No |
| **Safe to delete?** | No |

**Functions:** `build_session()`

---

## `src/config/`

### `src/config/constants.py`

| Field | Value |
|-------|-------|
| **Purpose** | URL constants, RSA public key, regex patterns |
| **Status** | **Current** |
| **Imports** | `re` |
| **Imported By** | `naukri_client.py`, `job_client.py`, `nkparam_generator.py` |
| **Safe to delete?** | No |

**Exports:** `LOGIN_URL`, `OTP_*`, `PROFILE_URL`, `FILE_VALIDATION_URL`, `DASHBOARD_URL`, `PROFILE_UPDATE_URL`, `RESUME_UPDATE_URL_TEMPLATE`, `JOB_SEARCH_URL`, `RECOMMENDED_JOBS_URL`, `APPLY_JOB_URL`, `HISTORY_URL`, `PUBLIC_KEY`, `FORM_KEY_PATTERNS`, `APP_JS_PATTERN`

---

## `src/exceptions/`

### `src/exceptions/exceptions.py`

| Field | Value |
|-------|-------|
| **Purpose** | Custom exception hierarchy |
| **Status** | **Current**, **Helper** |
| **Imported By** | `naukri_client.py`, `job_client.py`, `apply_agent.py` (partial) |
| **Safe to delete?** | No |

**Classes:** `NaukriClientError`, `NaukriAuthError`, `NaukriNetworkError`, `NaukriParseError`, `NaukriUploadError`

---

## `src/models/`

### `src/models/models.py`

| Field | Value |
|-------|-------|
| **Purpose** | Dataclass definitions |
| **Status** | **Current** |
| **Imported By** | `naukri_client.py`, `job_client.py` |
| **Safe to delete?** | No |

**Classes:** `NaukriSession`, `FileValidationResult`, `ResumeUpdateResult`, `Job`, `ProfileUpdateResult`, `ApplicationStatus`, `ApplicationHistory`

**Note:** `FileValidationResult` is defined but **not used** in codebase (dead model).

---

## `src/utils/`

### `src/utils/nkparam_generator.py`

| Field | Value |
|-------|-------|
| **Purpose** | Pure-Python nkparam token generation (RSA encrypt) |
| **Status** | **Current** (primary nkparam source per README) |
| **Imports** | `Crypto`, `base64`, `time`, `constants.PUBLIC_KEY` |
| **Imported By** | `job_client.py` |
| **Safe to delete?** | No |

**Functions:** `generate_nkparam(page_type="srp")`

---

### `src/utils/get_Nkparam.py`

| Field | Value |
|-------|-------|
| **Purpose** | Selenium-based nkparam token harvester |
| **Responsibility** | Infinite loop: Chrome → capture network nkparam → append `nkPool.txt` |
| **Status** | **Legacy / Utility** (backup per README) |
| **Imports** | `selenium`, `json`, `time` |
| **Imported By** | None |
| **Safe to ignore?** | Yes (unless generator breaks) |
| **Safe to delete?** | Yes (backup utility only) — **runs infinite loop on execution** |

---

### `src/utils/request_helper.py`

| Field | Value |
|-------|-------|
| **Purpose** | Exponential backoff retry decorator |
| **Status** | **Current**, **Helper** |
| **Imported By** | `naukri_client.py`, `job_client.py` (unused import in job_client) |
| **Safe to delete?** | No |

**Functions:** `with_exponential_retry`, `_should_retry`

---

### `src/utils/extractors.py`

| Field | Value |
|-------|-------|
| **Purpose** | Parse formKey from Naukri JS bundles and HTML |
| **Status** | **Current**, **Helper** |
| **Imported By** | `naukri_client.py` |
| **Safe to delete?** | No |

**Functions:** `extract_form_key2`, `extract_all_js_urls`

---

### `src/utils/dbhandler.py`

| Field | Value |
|-------|-------|
| **Purpose** | SQLite store for nkparam tokens |
| **Status** | **Dead code / Experimental** — zero imports anywhere |
| **Imports** | `sqlite3` |
| **Imported By** | **None** |
| **Safe to ignore?** | **Yes** |
| **Safe to delete?** | **Yes** |

**Classes:** `NkparamDB`

---

## `src/tests/`

### `src/tests/test_session.py`

| Field | Value |
|-------|-------|
| **Purpose** | Manual httpcloak/TLS fingerprint probing |
| **Status** | **Experimental** — executes network calls at import (lines 35–52) |
| **Imported By** | None |
| **Safe to ignore?** | **Yes** |
| **Safe to delete?** | Yes |

---

### `src/tests/test_nkpram.py`

| Field | Value |
|-------|-------|
| **Purpose** | Broken/incomplete nkparam experiment (`PUBLIC_KEY="search"` invalid) |
| **Status** | **Experimental / Dead** |
| **Imported By** | None |
| **Safe to ignore?** | **Yes** |
| **Safe to delete?** | Yes |

---

## Runtime-Generated Files (not in repo)

| File | Created By | Status |
|------|------------|--------|
| `applied_jobs.csv` | `apply_agent.py` | Runtime artifact |
| `score_cache.json` | `JobFilterPipeline2` | Runtime artifact |
| `nkPool.txt` | `get_Nkparam.py` | Runtime artifact (referenced in README/job_client comments) |
| `nkparams.db` | `NkparamDB` | Would be created if class were used |

---

## Import Graph Summary

```
main.py ──────────────┬──► naukri_client ──► session, constants, exceptions, models, extractors, request_helper
                      └──► job_client ──────► naukri_client, models, nkparam_generator, constants

apply_agent.py ───────┬──► (same as main)
                      └──► jop_classifier

updateDaily.py ───────► (standalone, no src imports)

job_client ───────────► nkparam_generator ──► constants

get_Nkparam.py ───────► (standalone selenium)

dbhandler.py ─────────► (orphan)
```

---

## Files With Zero Incoming References (Orphans)

| File | Reason |
|------|--------|
| `updateDaily.py` | Legacy standalone |
| `get_Nkparam.py` | Manual utility |
| `dbhandler.py` | Never integrated |
| `test_session.py` | Manual test |
| `test_nkpram.py` | Manual test |
| `assests/logo2.svg` | Static asset |

---

## Methods Defined But Never Called Externally

| Location | Method | Status |
|----------|--------|--------|
| `naukri_client.py` | `get_form_key()` | Superseded by `get_form_key2()` — internal legacy |
| `naukri_client.py` | `get_application_history()` | API exists; no script calls it |
| `naukri_client.py` | `parse_history()` | API exists; no script calls it |
| `naukri_client.py` | `send_otp()` / `verify_otp()` | API exists; no script wraps full OTP flow |
| `job_client.py` | `get_recommended_jobs()` | Commented out in `main.py` |
| `job_client.py` | `format_jobs()` | Called for side-effect only inside `search_jobs` |
| `models.py` | `FileValidationResult` | Unused dataclass |
