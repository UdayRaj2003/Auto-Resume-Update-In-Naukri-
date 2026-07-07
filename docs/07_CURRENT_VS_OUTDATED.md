# 07 — Current vs Outdated

Classification based on **import tracing**, **entry-point analysis**, and **explicit source markers**. No runtime testing was performed.

---

## CURRENT IMPLEMENTATION

Production-path code used by `main.py`, `apply_agent.py`, or imported transitively from `src/`.

| File | Why Current |
|------|-------------|
| `src/client/naukri_client.py` | Core client; imported by all entry points |
| `src/client/job_client.py` | Job APIs; imported by `main.py`, `apply_agent.py` |
| `src/client/session.py` | Session factory for `NaukriLoginClient` |
| `src/client/jop_classifier.py` | Used by `apply_agent.py` |
| `src/config/constants.py` | Shared URL/key constants |
| `src/models/models.py` | Shared dataclasses |
| `src/exceptions/exceptions.py` | Error types for clients |
| `src/utils/nkparam_generator.py` | Default nkparam path in `job_client._get_nkparam()` |
| `src/utils/request_helper.py` | Retry decorator on `naukri_client` I/O |
| `src/utils/extractors.py` | formKey parsing for resume upload |
| `main.py` | Active demo entry (README: "Entry point") |
| `apply_agent.py` | AI agent entry (README documented) |
| `README.md` | Active documentation |
| `requirements.txt` | Matches imports |
| `.env` | Required runtime config |

### Current Methods (within naukri_client)

| Method | Status |
|--------|--------|
| `login()` | **Current** |
| `send_otp()` / `verify_otp()` | **Current** (API complete, no script wrapper) |
| `get_form_key2()` | **Current** — used by login cache + validate_file |
| `fetch_profile_id()` | **Current** |
| `validate_file()` / `update_resume()` | **Current** |
| `update_profile()` | **Current** |
| `get_application_history()` / `parse_history()` | **Current** (library API, unused by scripts) |

### Current nkparam Strategy

**Primary:** `generate_nkparam("srp")` in `nkparam_generator.py`  
**Fallback:** `NaukriJobClient(use_pool=True)` with hardcoded pool token  
**Manual backup:** Selenium harvester in `get_Nkparam.py`

---

## OUTDATED IMPLEMENTATION

Superseded by `src/` client but still present in repo.

| File | Why Outdated |
|------|--------------|
| **`updateDaily.py`** | Header `#outdated#`; embeds duplicate `NaukriLoginClient`; uses plain `requests.Session` instead of httpcloak; requires manual `form_key`; Google Drive workflow; **does not import `src/`** |
| **`get_form_key()`** in `naukri_client.py` | Older single-bundle parser; active path uses `get_form_key2()` exclusively |

### updateDaily.py vs Current Client

| Aspect | updateDaily.py | src/naukri_client.py |
|--------|----------------|----------------------|
| Session | `requests.Session` | `httpcloak.Session` |
| formKey | Manual global variable | Auto `get_form_key2()` |
| Resume source | Google Drive | Local file path |
| Retry logic | None | `@with_exponential_retry` |
| OTP support | No | Yes |
| Job APIs | No | Via job_client |

---

## LEGACY IMPLEMENTATION

Functional backup utilities, not on primary execution path.

| File | Why Legacy |
|------|------------|
| **`src/utils/get_Nkparam.py`** | README: "Selenium helper... backup utility"; README references `nk_param_getter.py` (filename mismatch — actual file is `get_Nkparam.py`); infinite Selenium loop |
| **nkparam pool mode** | `use_pool=True` on `NaukriJobClient`; comments reference `nkPool.txt` but file loading not implemented in code — only hardcoded token in `self.pool` |
| **`APPLY_SRC_MAP["recommended"]`** in `main.py` | `main.py` uses `source="recommended"` for search results — likely copy-paste; apply_agent correctly uses `source="search"` |

---

## EXPERIMENTAL IMPLEMENTATION

Incomplete, manual, or broken code not integrated into production flow.

| File | Why Experimental |
|------|------------------|
| **`src/utils/dbhandler.py`** | `NkparamDB` SQLite store — never imported; alternative to `nkPool.txt` that was never wired up |
| **`src/tests/test_session.py`** | Ad-hoc TLS fingerprint tests; runs network probes at import |
| **`src/tests/test_nkpram.py`** | Invalid `PUBLIC_KEY="search"`; incomplete duplicate of generator |
| **`models.FileValidationResult`** | Dataclass defined but never instantiated |

---

## DEMO IMPLEMENTATION

| File | Why Demo |
|------|----------|
| **`main.py`** | README explicitly: "Entry point — demo of all features"; most features commented out; **currently runs live apply loop** on all search hits (dangerous for accidental execution) |

---

## DEAD CODE

| Item | Evidence |
|------|----------|
| `NkparamDB` / `dbhandler.py` | Zero imports |
| `FileValidationResult` model | Zero usage |
| `get_form_key()` | Zero external callers; superseded |
| `load_applied_jobs()` dedup check | Set loaded but **not checked** before apply in `apply_agent.py` |
| `with_exponential_retry` import in `job_client.py` | Imported, never applied |
| `ThreadPoolExecutor` in `test_nkpram.py` | Imported, unused |
| `functools`, `time` imports in `naukri_client.py` | Imported, unused (verified via grep) |

---

## HELPER / UTILITY

| File | Role |
|------|------|
| `session.py` | Session factory |
| `request_helper.py` | Retry decorator |
| `extractors.py` | HTML/JS parsing |
| `constants.py` | Config constants |
| `exceptions.py` | Error types |
| `models.py` | Data containers |
| `assests/logo2.svg` | README branding |

---

## STANDALONE SCRIPTS

| File | Standalone? | Notes |
|------|-------------|-------|
| `main.py` | Yes | `if __name__ == "__main__"` |
| `apply_agent.py` | Yes | `if __name__ == "__main__"` |
| `updateDaily.py` | Yes | Runs at import (no guard) |
| `get_Nkparam.py` | Yes | Runs infinite loop at import |
| `test_session.py` | Yes | Runs at import |
| `test_nkpram.py` | Partial | Defines function only; broken if run |

---

## README vs Code Discrepancies

| README Claim | Code Reality |
|--------------|--------------|
| `nk_param_getter.py` | File is `src/utils/get_Nkparam.py` |
| `nkPool.txt` pool loading | Not implemented in `job_client.py` (hardcoded pool only) |
| `main.py` demo of all features | Most features commented; only login+search+apply active |
| Score threshold in apply_agent | `SCORE_THRESHOLD` mentioned in README but **not defined** in code; pipeline uses `min_apply_score=50` default in class |

---

## Production Readiness Assessment

| Component | Assessment | Basis |
|-----------|------------|-------|
| `NaukriLoginClient` | Production-ready | README + comprehensive API coverage |
| `NaukriJobClient` | Production-ready | README; questionnaire partial |
| `apply_agent.py` | Production-ready with caveats | Hardcoded PROFILE; CSV dedup incomplete; score display key mismatch |
| `main.py` | **Not safe for unattended run** | Applies to all search results |
| `updateDaily.py` | **Do not use** | Marked outdated |
| `get_Nkparam.py` | Backup only | Requires Chrome + manual run |
| `dbhandler.py` | Not ready | Unintegrated |

---

## Migration Path (Informational — Not Implemented)

If consolidating the codebase:
1. Delete or archive `updateDaily.py`
2. Wire `dbhandler.py` OR delete it
3. Implement `nkPool.txt` loading in `job_client` OR remove comments
4. Add `if __name__` guards to `updateDaily.py`, `get_Nkparam.py`, `test_session.py`
5. Fix `apply_agent.py` to use `ai_score`/`ai_reason` keys and check `applied_jobs_set` before apply

*This audit documents only; no changes were made.*
