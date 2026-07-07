# 03 — Feature Analysis

Complete feature inventory with verified file/class/method locations.

**Legend:**  
- **Current** = implemented in `src/` and referenced by README or active entry points  
- **Production Ready** = README claims "Working" (July 2026); runtime not re-verified in this audit  
- **Can run independently?** = Has dedicated executable script for that feature alone  

---

## 1. Password Login

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Class** | `NaukriLoginClient` |
| **Entry Method** | `login()` |
| **Internal Methods** | `_login_request()`, `_build_headers()` |
| **Dependencies** | `build_session()`, `LOGIN_URL`, credentials |
| **Authentication** | `username`, `password` constructor args |
| **API Endpoints** | `POST https://www.naukri.com/central-login-services/v1/login` |
| **Can run independently?** | **No** — no login-only script |
| **Called by** | `main.py`, `apply_agent.py`, `updateDaily.py` (legacy class) |

---

## 2. OTP Send

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `send_otp(username=None, is_mobile=True)` |
| **Internal Methods** | `_send_otp_request()` |
| **Authentication** | Username/phone/email; no prior login required |
| **API Endpoints** | `POST https://www.naukri.com/central-login-services/v1/otp` |
| **Can run independently?** | **No** |
| **Called by** | NOT VERIFIED — no script in repo calls this |

---

## 3. OTP Verify / MFA Login

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `verify_otp(otp, username=None, is_mobile=True)` |
| **Internal Methods** | `_verify_otp_request()` |
| **Authentication** | OTP token from SMS/email |
| **API Endpoints** | `POST https://www.naukri.com/central-login-services/v0/otp-login` |
| **Can run independently?** | **No** |
| **Called by** | NOT VERIFIED — no script wraps send+verify flow |

**Typical manual flow:**
```python
client = NaukriLoginClient(user, pass)
try:
    client.login()
except NaukriAuthError:
    client.send_otp()
    client.verify_otp(input("OTP: "))
```

---

## 4. Session / Bearer Token Management

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/naukri_client.py`, `src/models/models.py` |
| **Entry Class** | `NaukriSession` dataclass |
| **Created by** | `login()`, `verify_otp()` |
| **Token source** | `nauk_at` cookie |
| **Used by** | All `auth=True` API calls |

---

## 5. Form Key Extraction (formKey2)

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `get_form_key2()` |
| **Supporting Files** | `src/utils/extractors.py`, `src/config/constants.py` |
| **Internal Methods** | `_fetch_profile_html_auth()`, `_fetch_js()` |
| **Legacy Method** | `get_form_key()` — older single-JS-bundle parser, **not called by active paths** |
| **Authentication** | Bearer token required |
| **API Endpoints** | `GET /mnjuser/profile`, `GET static.naukimg.com/.../mnj_*.js` |
| **Can run independently?** | **No** |
| **Called by** | `login()` (cache warm), `validate_file()` |

---

## 6. Profile ID Fetch

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `fetch_profile_id()` |
| **Internal Methods** | `_fetch_dashboard()` |
| **Authentication** | Bearer token |
| **API Endpoints** | `GET .../resman-aggregator-services/v0/users/self/dashboard` |
| **Can run independently?** | **No** |
| **Called by** | `update_resume()`, `update_profile()` |

---

## 7. Resume Upload (Validate + Attach)

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `update_resume(resume_file)` |
| **Supporting Methods** | `validate_file()`, `fetch_profile_id()`, `get_form_key2()`, `generate_file_key()` |
| **Internal Methods** | `_validate_file_request()`, `_update_resume_request()` |
| **Authentication** | Bearer token + formKey |
| **API Endpoints** | See [05_API_REFERENCE.md](./05_API_REFERENCE.md) |
| **Can run independently?** | **No** — uncomment block in `main.py` or write script |
| **Called by** | `main.py` (commented), `updateDaily.py` (legacy duplicate logic) |

**Note:** `_validate_file_request` uses standalone `requests.post`, not httpcloak session.

---

## 8. Profile Update (Headline / Name / Summary)

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `update_profile(headline=None, name=None, summary=None)` |
| **Internal Methods** | `_update_profile_request()` |
| **Authentication** | Bearer token |
| **API Endpoints** | `POST .../v1/users/self/fullprofiles` (X-HTTP-Method-Override: PUT) |
| **Can run independently?** | **No** |
| **Called by** | `main.py` (commented) |

---

## 9. Recommended Jobs

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `get_recommended_jobs()` |
| **Supporting Methods** | `_parse_job()`, `_cluster_dates()`, `_headers()` |
| **Authentication** | Bearer token |
| **API Endpoints** | `POST https://www.naukri.com/jobapi/v2/search/recom-jobs` |
| **Can run independently?** | **No** |
| **Called by** | NOT VERIFIED in active entry points (`main.py` has it commented) |

---

## 10. Job Search

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `search_jobs(keyword, location="", page=2, job_age=3, experience=2, ...)` |
| **Supporting Methods** | `_build_seo_key()`, `_search_headers()`, `_get_nkparam()`, `_parse_job()` |
| **Authentication** | nkparam header (via `generate_nkparam`); session cookies attached but search uses `auth=False` base headers |
| **API Endpoints** | `GET https://www.naukri.com/jobapi/v3/search` |
| **Can run independently?** | **Partially** — `main.py` runs search; no search-only isolation |
| **Called by** | `main.py`, `apply_agent.py` (`fetch_all_jobs`) |

---

## 11. nkparam Generation (Pure API)

| Field | Value |
|-------|-------|
| **Status** | Current (primary) |
| **Primary File** | `src/utils/nkparam_generator.py` |
| **Entry Function** | `generate_nkparam(page_type="srp")` |
| **Algorithm** | RSA PKCS1_v1_5 encrypt `v0|{timestamp_ms}|121_{page_type}` with `PUBLIC_KEY` from constants |
| **Dependencies** | `pycryptodome`, `constants.PUBLIC_KEY` |
| **Called by** | `NaukriJobClient._get_nkparam()` when `use_pool=False` (default) |

---

## 12. nkparam Pool / Selenium Harvester

| Field | Value |
|-------|-------|
| **Status** | Legacy backup |
| **Primary File** | `src/utils/get_Nkparam.py` |
| **Mechanism** | Chrome performance logs → extract `nkparam` header → append `nkPool.txt` |
| **Pool mode** | `NaukriJobClient(login_client, use_pool=True)` reads `self.pool` list (hardcoded 1 token + optional file load NOT VERIFIED in code) |
| **Can run independently?** | **Yes** — `python src/utils/get_Nkparam.py` (requires Chrome) |
| **Called by** | Manual execution only |

**Note:** `job_client.py` comments reference loading `nkPool.txt` but code only has hardcoded pool array — file loading NOT VERIFIED in implementation.

---

## 13. Job Details

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `get_job_details(job_id, sid="")` |
| **Authentication** | Bearer + nkparam |
| **API Endpoints** | `GET https://www.naukri.com/jobapi/v1/job/{job_id}` |
| **Can run independently?** | **No** |
| **Called by** | `is_external_apply()` |

---

## 14. External Apply Detection

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `is_external_apply(job_id, sid="")` |
| **Logic** | `get_job_details()` → `job.responseManager == "companyUrl"` |
| **Called by** | `apply_agent.py` |

---

## 15. Easy Apply (One-Click)

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Production Ready** | Yes (per README) |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `apply_job(job, mandatory_skills, optional_skills, sid, source)` |
| **Authentication** | Bearer token |
| **API Endpoints** | `POST .../apply-workflow/v1/apply` |
| **Can run independently?** | **No** — bundled in `main.py` / `apply_agent.py` |
| **Called by** | `main.py`, `apply_agent.py` |

**Source mapping (`APPLY_SRC_MAP`):**
- `"recommended"` → `applySrc: drecomm_apply`
- `"search"` → `applySrc: srp`

---

## 16. Questionnaire Apply (Static Answers)

| Field | Value |
|-------|-------|
| **Status** | Current, **Partial** (hardcoded PROFILE dict) |
| **Primary File** | `src/client/job_client.py` |
| **Entry Method** | `handle_static_questionnaire_and_apply(job, questionnaire, sid, ...)` |
| **Internal** | Nested `build_smart_answers()`, `pick_yes()`, `pick_notice()` |
| **Authentication** | Bearer token |
| **API Endpoints** | Same apply endpoint with `applyData` payload |
| **Called by** | `apply_agent.py` only (`main.py` skips questionnaire jobs) |

---

## 17. Application History

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/naukri_client.py` |
| **Entry Method** | `get_application_history(page_size, days, page_number, mobile)` |
| **Parser** | `parse_history(raw)` → `list[ApplicationHistory]` |
| **Authentication** | Bearer token |
| **API Endpoints** | `GET .../applyapi/v5/history` |
| **Can run independently?** | **No** |
| **Called by** | NOT VERIFIED — no script calls this |

---

## 18. AI Job Scoring & Filtering

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/client/jop_classifier.py` |
| **Entry Class** | `JobFilterPipeline2` |
| **Entry Method** | `run(jobs)` |
| **Pipeline Steps** | `normalize_jobs` → `dedup` → `hard_veto` → `experience_filter` → `desc_red_flag_check` → `title_filter` → `company_veto` → `tag_presort` → `ai_score_batch` → `rank` → `select` |
| **External API** | `POST https://api.openai.com/v1/chat/completions` (model: `gpt-4o-mini`) |
| **Authentication** | `OPEN_API_KEY` env var |
| **Can run independently?** | **No** — only via `apply_agent.py` |
| **Artifacts** | `score_cache.json` |

---

## 19. Applied Jobs CSV Dedup

| Field | Value |
|-------|-------|
| **Status** | Current (agent feature) |
| **Primary File** | `apply_agent.py` |
| **Functions** | `load_applied_jobs()`, `save_applied_job()` |
| **File** | `applied_jobs.csv` |
| **Note** | Loaded into `applied_jobs_set` but **NOT VERIFIED** used to skip jobs in apply loop (set is updated but not checked before apply) |

---

## 20. HTTP Retry / Resilience

| Field | Value |
|-------|-------|
| **Status** | Current |
| **Primary File** | `src/utils/request_helper.py` |
| **Decorator** | `@with_exponential_retry` |
| **Applied to** | Most `_`*`_request` methods in `naukri_client.py` only |

---

## 21. Legacy Google Drive Resume Cron

| Field | Value |
|-------|-------|
| **Status** | **Outdated** |
| **Primary File** | `updateDaily.py` |
| **Entry** | `handler(event, context)` → `update_resume()` |
| **Authentication** | Hardcoded globals (empty) |
| **External** | Google Drive download URL |
| **Can run independently?** | **Yes** — `python updateDaily.py` (runs immediately, will fail with empty creds) |

---

## 22. SQLite nkparam Database

| Field | Value |
|-------|-------|
| **Status** | **Dead / Experimental** |
| **Primary File** | `src/utils/dbhandler.py` |
| **Class** | `NkparamDB` |
| **Methods** | `add_nkparam()`, `get_nkparam()` |
| **Integrated?** | **No** — zero callers |

---

## Feature × Entry Point Matrix

| Feature | main.py | apply_agent.py | updateDaily.py | Library only |
|---------|---------|----------------|----------------|--------------|
| Login | ✅ active | ✅ active | ✅ legacy | ✅ |
| Resume upload | commented | ❌ | ✅ legacy | ✅ |
| Profile update | commented | ❌ | ❌ | ✅ |
| Job search | ✅ active | ✅ active | ❌ | ✅ |
| Recommended jobs | commented | ❌ | ❌ | ✅ |
| Apply | ✅ active | ✅ active | ❌ | ✅ |
| AI filter | ❌ | ✅ active | ❌ | ✅ |
| Questionnaire | skips | ✅ handles | ❌ | ✅ |
| OTP | ❌ | ❌ | ❌ | ✅ |
| History | ❌ | ❌ | ❌ | ✅ |
