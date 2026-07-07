# NopeRi Repository Audit — Master Index

**Audit date:** 2026-07-07  
**Scope:** `D:\Test jobbot\NopeRi\` (entire Python codebase, excluding `.venv/`)  
**Method:** Static reverse-engineering via source read, import tracing, and entry-point analysis. No code was modified.

---

## Executive Summary

**NopeRi** is a Python API client for [Naukri.com](https://www.naukri.com) that automates login, profile/resume management, job search, and easy-apply workflows without browser automation for core features. The repository contains **17 Python files**, **3 top-level executables**, **2 implicit executables** (run on import), and **2 manual test scripts**.

| Layer | Current Implementation | Status |
|-------|------------------------|--------|
| Auth & profile | `src/client/naukri_client.py` | Production-ready (per README) |
| Jobs & apply | `src/client/job_client.py` | Production-ready (per README) |
| AI auto-apply | `apply_agent.py` + `src/client/jop_classifier.py` | Production-ready (partial questionnaire) |
| Demo / integration | `main.py` | Demo — currently applies to all search results |
| nkparam (search token) | `src/utils/nkparam_generator.py` | Current (primary) |
| nkparam fallback | `src/utils/get_Nkparam.py` | Legacy backup (Selenium) |
| Daily resume cron | `updateDaily.py` | **Outdated / legacy** — self-contained duplicate client |
| SQLite nkparam store | `src/utils/dbhandler.py` | **Dead code** — zero imports |
| Tests | `src/tests/*` | Experimental / manual only |

---

## Documentation Index

| # | Document | Description |
|---|----------|-------------|
| 1 | [01_PROJECT_ARCHITECTURE.md](./01_PROJECT_ARCHITECTURE.md) | System overview, layers, data flow |
| 2 | [02_FILE_ANALYSIS.md](./02_FILE_ANALYSIS.md) | Per-file purpose, status, imports, safe-to-delete |
| 3 | [03_FEATURE_ANALYSIS.md](./03_FEATURE_ANALYSIS.md) | Every feature with classes, methods, endpoints |
| 4 | [04_EXECUTION_FLOW.md](./04_EXECUTION_FLOW.md) | Step-by-step traces for all features |
| 5 | [05_API_REFERENCE.md](./05_API_REFERENCE.md) | All HTTP endpoints, headers, payloads |
| 6 | [06_DEPENDENCY_GRAPH.md](./06_DEPENDENCY_GRAPH.md) | File, class, feature, execution graphs |
| 7 | [07_CURRENT_VS_OUTDATED.md](./07_CURRENT_VS_OUTDATED.md) | Current vs legacy vs experimental classification |
| 8 | [08_ENTRY_POINTS.md](./08_ENTRY_POINTS.md) | Every runnable file and execution paths |
| 9 | [09_CLASS_REFERENCE.md](./09_CLASS_REFERENCE.md) | All classes, methods, lifecycle |
| 10 | [10_RECOMMENDED_USAGE.md](./10_RECOMMENDED_USAGE.md) | Which file to run for each task |

---

## Important Questions — Quick Answers

| Question | Answer |
|----------|--------|
| **Login only?** | No dedicated script. Use Python REPL or a 3-line script calling `NaukriLoginClient.login()`. See [10_RECOMMENDED_USAGE.md](./10_RECOMMENDED_USAGE.md). |
| **Resume update only?** | Uncomment `client.update_resume(...)` in `main.py`, or call `NaukriLoginClient.update_resume()` programmatically. |
| **Profile update only?** | Uncomment `client.update_profile(...)` in `main.py`, or call `NaukriLoginClient.update_profile()` programmatically. |
| **Resume upload only?** | Same as resume update — `update_resume()` performs validate + upload + profile attach. |
| **Job search only?** | `main.py` (active path) or `NaukriJobClient.search_jobs()` after login. |
| **Recommended jobs only?** | Uncomment `jc.get_recommended_jobs()` in `main.py`. |
| **Job details only?** | `NaukriJobClient.get_job_details(job_id)` — no standalone script. |
| **Application history only?** | `NaukriLoginClient.get_application_history()` — no standalone script. |
| **Auto-applies to jobs?** | **`apply_agent.py`** (AI-filtered) and **`main.py`** (currently applies to every search result — **dangerous**). |
| **AI Agent?** | **`apply_agent.py`** |
| **Demo?** | **`main.py`** (README describes it as demo of all features) |
| **Never run accidentally?** | **`main.py`** (applies to jobs), **`updateDaily.py`** (runs on import with empty creds), **`get_Nkparam.py`** (infinite Selenium loop), **`test_session.py`** (network probes on import) |
| **Safe to ignore?** | `updateDaily.py`, `dbhandler.py`, `src/tests/*`, `assests/logo2.svg` |
| **No longer used?** | `updateDaily.py`, `dbhandler.py`, `get_form_key()` (superseded by `get_form_key2()`), `NkparamDB` |

---

## Repository Layout

```
Test jobbot/
├── docs/                          ← This audit (generated)
└── NopeRi/                        ← Application root
    ├── main.py                    ← Demo entry (CURRENT, DEMO)
    ├── apply_agent.py             ← AI auto-apply (CURRENT, PRODUCTION)
    ├── updateDaily.py             ← Legacy cron resume updater (OUTDATED)
    ├── .env                       ← Credentials (USERNAME, PASSWORD, OPEN_API_KEY)
    ├── requirements.txt
    ├── README.md
    ├── assests/logo2.svg
    └── src/
        ├── client/
        │   ├── naukri_client.py   ← Core auth/profile/resume/history
        │   ├── job_client.py      ← Search, recommend, apply, details
        │   ├── jop_classifier.py  ← AI job filter (apply_agent only)
        │   └── session.py         ← httpcloak session factory
        ├── config/constants.py    ← URLs, RSA key, regex patterns
        ├── exceptions/exceptions.py
        ├── models/models.py
        ├── utils/
        │   ├── nkparam_generator.py  ← Primary nkparam (CURRENT)
        │   ├── get_Nkparam.py        ← Selenium harvester (LEGACY)
        │   ├── request_helper.py
        │   ├── extractors.py
        │   └── dbhandler.py          ← Dead code
        └── tests/
            ├── test_session.py
            └── test_nkpram.py
```

**Note:** No `__init__.py` files exist. Imports use `from src.client...` — run scripts from `NopeRi/` directory or set `PYTHONPATH`.

---

## Feature Map (Verified)

| Feature | Current | Primary Class | Primary Method |
|---------|---------|---------------|----------------|
| Password login | ✅ | `NaukriLoginClient` | `login()` |
| OTP send | ✅ | `NaukriLoginClient` | `send_otp()` |
| OTP verify | ✅ | `NaukriLoginClient` | `verify_otp()` |
| Resume upload | ✅ | `NaukriLoginClient` | `update_resume()` |
| Profile update | ✅ | `NaukriLoginClient` | `update_profile()` |
| Recommended jobs | ✅ | `NaukriJobClient` | `get_recommended_jobs()` |
| Job search | ✅ | `NaukriJobClient` | `search_jobs()` |
| Job details | ✅ | `NaukriJobClient` | `get_job_details()` |
| Easy apply | ✅ | `NaukriJobClient` | `apply_job()` |
| Questionnaire apply | ⚠️ Partial | `NaukriJobClient` | `handle_static_questionnaire_and_apply()` |
| Application history | ✅ | `NaukriLoginClient` | `get_application_history()` |
| nkparam generation | ✅ | `generate_nkparam()` | `nkparam_generator.py` |
| nkparam Selenium harvest | ✅ Backup | module-level | `get_Nkparam.py` |
| AI job scoring | ✅ | `JobFilterPipeline2` | `run()` |
| External apply detection | ✅ | `NaukriJobClient` | `is_external_apply()` |

---

## Authentication Requirements

| Feature | Auth Required |
|---------|---------------|
| Login | `USERNAME`, `PASSWORD` from `.env` |
| OTP flow | Same + manual OTP input (no script wraps full flow) |
| Resume / profile | Bearer token (`nauk_at` cookie) after login |
| Recommended jobs | Bearer token |
| Job search | **nkparam header** (generated, not session-bound); cookies optional |
| Job details | Bearer token + nkparam |
| Apply | Bearer token |
| AI agent | Naukri creds + `OPEN_API_KEY` (OpenAI) |

---

## External Dependencies (requirements.txt)

| Package | Used By |
|---------|---------|
| `requests` | `naukri_client`, `jop_classifier`, `updateDaily`, `request_helper` |
| `httpcloak` | `session.py` — TLS/browser fingerprint impersonation |
| `python-dotenv` | `main.py`, `apply_agent.py` |
| `selenium` | `get_Nkparam.py` only |
| `pycryptodome` | `nkparam_generator.py` |
| `colorama` | `main.py`, `apply_agent.py` |
| `urllib3` | Transitive (requests) |

---

## Runtime Artifacts (created at execution, not in repo)

| File | Created By | Purpose |
|------|------------|---------|
| `applied_jobs.csv` | `apply_agent.py` | Dedup log of applied jobs |
| `score_cache.json` | `JobFilterPipeline2` | AI score cache |
| `nkPool.txt` | `get_Nkparam.py` | Harvested nkparam tokens (README; not in repo) |
| `nkparams.db` | `NkparamDB` (if used) | SQLite token store (unused) |

---

## Verification Notes

- **README status "Working (July 2026)"** — documented claim, not independently verified in this audit.
- **`apply_agent.py` score display** — pipeline returns `ai_score`/`ai_reason`; agent reads `score`/`ai_detail`. Display may show `None`. Verified in source; behavior at runtime NOT VERIFIED.
- **`main.py` default page for search** — `search_jobs()` default `page=2` in `job_client.py`; `main.py` does not override. Verified in source.
- **No pytest/unittest harness** — tests are ad-hoc scripts, not automated test suite.

---

*End of master index. See linked documents for full reverse-engineering detail.*
