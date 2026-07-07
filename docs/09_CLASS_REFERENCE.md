# 09 — Class Reference

All classes defined in the repository.

---

## `NaukriLoginClient`

**File:** `src/client/naukri_client.py`  
**Purpose:** Authenticate and manage Naukri profile, resume, and application history.

### Constructor
```python
def __init__(self, username, password):
```
| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | str | Naukri email/phone |
| `password` | str | Account password |
| `session` | httpcloak.Session | From `build_session()` |
| `naukri_session` | NaukriSession \| None | Set after login |
| `profile_id` | str \| None | Cached profile ID |
| `cache` | dict | e.g. `form_key` |

### Public Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `login()` | `NaukriSession` | Password authentication |
| `send_otp(username=None, is_mobile=True)` | `dict` | Trigger OTP delivery |
| `verify_otp(otp, username=None, is_mobile=True)` | `NaukriSession` | Complete OTP login |
| `get_form_key()` | `str` | Legacy formKey extractor |
| `get_form_key2()` | `str` | Current formKey extractor (cached) |
| `fetch_profile_id()` | `str` | Dashboard profile ID (cached) |
| `validate_file(file)` | `[file_key, form_key]` | Upload PDF to validation service |
| `update_resume(resume_file)` | `ResumeUpdateResult` | Full resume update pipeline |
| `update_profile(headline, name, summary)` | `ProfileUpdateResult` | Update profile fields |
| `get_application_history(page_size, days, page_number, mobile)` | `dict` | Raw history JSON |
| `parse_history(raw)` | `list[ApplicationHistory]` | Parse history to dataclasses |
| `generate_file_key(length)` | `str` | Random alphanumeric key |

### Private / Internal Methods

| Method | Decorator | Purpose |
|--------|-----------|---------|
| `_build_headers(auth, extra)` | — | Assemble request headers |
| `_login_request()` | `@with_exponential_retry` | POST login |
| `_verify_otp_request()` | `@with_exponential_retry` | POST OTP verify |
| `_send_otp_request()` | `@with_exponential_retry` | POST OTP send |
| `_fetch_profile_html()` | `@with_exponential_retry` | GET profile (legacy formKey) |
| `_fetch_profile_html_auth()` | `@with_exponential_retry` | GET profile (auth) |
| `_fetch_js(js_url)` | `@with_exponential_retry` | GET JS bundle |
| `_fetch_dashboard()` | `@with_exponential_retry` | GET dashboard |
| `_validate_file_request()` | `@with_exponential_retry` | POST file validation |
| `_update_resume_request()` | `@with_exponential_retry` | POST resume attach |
| `_update_profile_request()` | `@with_exponential_retry` | POST profile update |
| `_fetch_history_request()` | `@with_exponential_retry` | GET apply history |

### Lifecycle
```
__init__ → login()/verify_otp() → naukri_session populated
         → fetch_profile_id() [lazy]
         → update_resume()/update_profile() [on demand]
```

### Created By
`main.py`, `apply_agent.py`, user scripts

### Used By
`NaukriJobClient` (holds reference as `_client`)

---

## `NaukriJobClient`

**File:** `src/client/job_client.py`  
**Purpose:** Job discovery, details, and application.

### Constructor
```python
def __init__(self, login_client: NaukriLoginClient, use_pool: bool = False):
```
| Attribute | Description |
|-----------|-------------|
| `_session` | Shared httpcloak session from login client |
| `_client` | Reference to `NaukriLoginClient` |
| `use_pool` | If True, use token pool instead of generator |
| `pool_idx` | Rotation index for pool |
| `pool` | List of pre-captured nkparam strings |

### Public Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_recommended_jobs()` | `list[Job]` | Personalized recommendations |
| `search_jobs(keyword, location, page, job_age, experience, ...)` | `list[Job]` | Keyword search |
| `get_job_details(job_id, sid)` | `dict` | Full job JSON |
| `is_external_apply(job_id, sid)` | `bool` | External redirect detection |
| `apply_job(job, mandatory_skills, optional_skills, sid, source)` | `dict` | Submit application |
| `handle_static_questionnaire_and_apply(...)` | `dict` | Apply with hardcoded answers |
| `format_jobs(raw_jobs)` | `list[dict]` | Flatten job dicts for display |

### Private Methods

| Method | Purpose |
|--------|---------|
| `_parse_job(raw)` | API dict → `Job` dataclass |
| `_cluster_dates()` | UTC timestamps for recommend payload |
| `_headers()` | Auth headers shortcut |
| `_build_seo_key(keyword, location, page)` | SEO slug for search |
| `_get_nkparam()` | Generator or pool token |
| `_search_headers()` | Search-specific headers |

### Nested Functions (in `handle_static_questionnaire_and_apply`)
- `build_smart_answers(questionnaire, profile)` → `dict`
- `pick_yes(options)` → str
- `pick_notice(options, notice_days)` → str

### Lifecycle
```
NaukriLoginClient (logged in) → NaukriJobClient.__init__
  → search_jobs / get_recommended_jobs / apply_job
```

### Created By
`main.py`, `apply_agent.py`

---

## `JobFilterPipeline2`

**File:** `src/client/jop_classifier.py`  
**Purpose:** Rule-based pre-filter + OpenAI scoring for job relevance.

### Constructor
```python
def __init__(
    self,
    openai_api_key,
    cache_file="score_cache.json",
    daily_apply_limit=50,
    min_apply_score=50,
    ai_score_limit=300,
    batch_size=50,
):
```

### Class Constants
- `MY_STACK` — candidate technology keywords
- `VETO_TITLES` — title blacklist
- `VETO_COMPANIES` — company blacklist
- `DESC_RED_FLAGS` — regex patterns
- `SOFTWARE_KEYWORDS` — title must match one
- `FRONTEND_VETO_KEYWORDS` — title must not match

### Public Methods

| Method | Description |
|--------|-------------|
| `run(jobs)` | Full pipeline entry point |

### Pipeline Methods (Public on Class)

| Method | Stage |
|--------|-------|
| `normalize_jobs(jobs)` | Standardize job dicts |
| `dedup(jobs)` | Remove duplicate job_ids |
| `hard_veto(jobs)` | Title blacklist filter |
| `experience_filter(jobs)` | Exp range filter |
| `desc_red_flag_check(jobs)` | Description regex filter |
| `title_filter(jobs)` | Software/frontend filter |
| `company_veto(jobs)` | Outsourcing company filter |
| `tag_presort(jobs)` | Stack overlap sort |
| `ai_score_batch(jobs)` | OpenAI batch scoring |
| `rank(jobs)` | Sort by score + recency |
| `select(jobs)` | Threshold + daily cap |

### Private Methods

| Method | Purpose |
|--------|---------|
| `_call_ai(jobs)` | OpenAI HTTP request |
| `_load_cache()` | Read score_cache.json |
| `_save_cache()` | Write score_cache.json |

### Created By
`apply_agent.py` only

---

## `NaukriSession`

**File:** `src/models/models.py`  
**Purpose:** Hold authenticated session state.

| Field | Type |
|-------|------|
| `bearer_token` | str |
| `cookies` | dict |
| `login_time` | float |

**Created by:** `login()`, `verify_otp()`  
**Used by:** `_build_headers(auth=True)`

---

## `Job`

**File:** `src/models/models.py`  
**Purpose:** Normalized job listing.

| Field | Type | Default |
|-------|------|---------|
| `job_id` | str | required |
| `title` | str | required |
| `company` | str | required |
| `location` | str | required |
| `experience` | str | required |
| `salary` | str | required |
| `posted_date` | str | required |
| `apply_link` | str | required |
| `description` | str | `""` |
| `tags` | list | `[]` |

**Created by:** `NaukriJobClient._parse_job()`  
**Used by:** `apply_job()`, agent display functions

---

## `ResumeUpdateResult`

| Field | Type |
|-------|------|
| `profile_id` | str |
| `raw_response` | dict |
| `status_code` | int |

---

## `ProfileUpdateResult`

| Field | Type |
|-------|------|
| `profile_id` | str |
| `response` | dict |
| `status_code` | int |

---

## `ApplicationStatus`

| Field | Type |
|-------|------|
| `status_id` | int |
| `status_value` | str |
| `date_time` | str |

---

## `ApplicationHistory`

| Field | Type |
|-------|------|
| `job_id` | str |
| `job_title` | str |
| `company` | str |
| `location` | str |
| `apply_type` | str |
| `is_open` | bool |
| `ars_score` | int |
| `star_rating` | str |
| `job_type` | str |
| `statuses` | list[ApplicationStatus] |
| `company_rating` | float \| None |
| `logo_path` | str \| None |

**Created by:** `parse_history()`

---

## `FileValidationResult`

**Status:** **Defined but unused** in codebase.

| Field | Type |
|-------|------|
| `file_key` | str |
| `raw_response` | dict |
| `was_key_remapped` | bool |

---

## Exception Classes

**File:** `src/exceptions/exceptions.py`

| Class | Parent | Purpose |
|-------|--------|---------|
| `NaukriClientError` | Exception | Base |
| `NaukriAuthError` | NaukriClientError | Auth/session failures |
| `NaukriNetworkError` | NaukriClientError | Network failures |
| `NaukriParseError` | NaukriClientError | Response parse failures |
| `NaukriUploadError` | NaukriClientError | File upload failures |

---

## `NkparamDB`

**File:** `src/utils/dbhandler.py`  
**Status:** **Dead code**

### Constructor
```python
def __init__(self, db_path="nkparams.db"):
```

### Public Methods
| Method | Description |
|--------|-------------|
| `add_nkparam(nkparam)` | INSERT OR IGNORE |
| `get_nkparam()` | Get one active token, mark inactive |

### Private Methods
| Method | Description |
|--------|-------------|
| `_connect()` | sqlite3.connect |
| `_init_db()` | CREATE TABLE IF NOT EXISTS |

---

## Legacy `NaukriLoginClient` (updateDaily.py)

**File:** `updateDaily.py`  
**Status:** Outdated duplicate — **NOT** the same class as `src/client/naukri_client.py`

### Methods
| Method | Notes |
|--------|-------|
| `login()` | Plain requests, no retry |
| `get_cookies()` | Cookie dict |
| `get_bearer_token()` | From cookies |
| `fetch_profile_id()` | Dashboard GET |
| `build_required_cookies()` | Subset for resume POST |

---

## Module-Level Functions

| Function | File | Purpose |
|----------|------|---------|
| `build_session()` | `session.py` | httpcloak session factory |
| `generate_nkparam(page_type)` | `nkparam_generator.py` | RSA nkparam token |
| `extract_form_key2(js_text)` | `extractors.py` | Parse formKey from JS |
| `extract_all_js_urls(html)` | `extractors.py` | Find script src URLs |
| `with_exponential_retry(...)` | `request_helper.py` | Decorator factory |
| `_should_retry(exc_or_response)` | `request_helper.py` | Retry predicate |

---

## apply_agent.py Functions (Not Classes)

| Function | Purpose |
|----------|---------|
| `load_applied_jobs()` | Read CSV → set of job_ids |
| `save_applied_job(job)` | Append CSV row |
| `print_section_title(text)` | Terminal UI |
| `print_job_header(...)` | Terminal UI |
| `_score_bar(score)` | ASCII bar |
| `print_status_applied/skipped/failed` | Terminal UI |
| `print_pipeline_results(final_jobs)` | Ranked table |
| `print_fetch_progress(...)` | Search progress line |
| `print_summary(...)` | Final stats |
| `fetch_all_jobs(jc)` | Multi-query search |
