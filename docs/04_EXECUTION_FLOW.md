# 04 — Execution Flow

Step-by-step traces from entry to outcome for every feature.

---

## Entry Point Flows

### A. `main.py` (Demo — Search + Apply)

```
main.py __main__
  │
  ├─ load_dotenv() → USERNAME, PASSWORD
  │
  ├─ NaukriLoginClient(username, password)
  │    └─ build_session() → httpcloak.Session
  │
  ├─ client.login()
  │    ├─ _login_request() → POST LOGIN_URL
  │    ├─ extract nauk_at cookie → NaukriSession
  │    └─ get_form_key2() [best-effort cache]
  │
  ├─ NaukriJobClient(client)
  │
  ├─ jc.search_jobs("Node.js developer", "Hyderabad", experience=2)
  │    ├─ _build_seo_key()
  │    ├─ _search_headers() → generate_nkparam("srp")
  │    ├─ GET JOB_SEARCH_URL + params
  │    └─ _parse_job() × N → list[Job]
  │
  └─ FOR each job:
       ├─ jc.apply_job(job, tags, source="recommended")
       │    ├─ build payload (strJobsarr, logstr, skills, sid)
       │    └─ POST APPLY_JOB_URL
       ├─ IF questionnaire in response → skip
       └─ sleep(3)

OUTCOME: Terminal output of jobs + apply success/failure
```

---

### B. `apply_agent.py` (AI Auto-Apply)

```
apply_agent.py __main__
  │
  ├─ load_dotenv() → USERNAME, PASSWORD, OPEN_API_KEY
  │
  ├─ NaukriLoginClient.login()          [same as above]
  │
  ├─ fetch_all_jobs(jc)
  │    └─ FOR each BQUERIES entry:
  │         └─ jc.search_jobs(...) → dedupe by job_id
  │
  ├─ JobFilterPipeline2(api_key).run(jobs)
  │    ├─ normalize_jobs → dedup → hard_veto → experience_filter
  │    ├─ desc_red_flag_check → title_filter → company_veto
  │    ├─ tag_presort → limit ai_score_limit
  │    ├─ ai_score_batch → OpenAI API
  │    ├─ rank → select (score >= min_apply_score)
  │    └─ return list[dict] with ai_score, job_id, ...
  │
  ├─ load_applied_jobs() → set from CSV
  │
  └─ FOR each allowed job (job_id in score_map):
       ├─ IF jc.is_external_apply(job_id)
       │    └─ get_job_details() → check responseManager
       ├─ jc.apply_job(..., source="search")
       ├─ IF questionnaire:
       │    └─ jc.handle_static_questionnaire_and_apply(...)
       ├─ save_applied_job() → append applied_jobs.csv
       └─ sleep(3)

OUTCOME: Terminal dashboard + applied_jobs.csv + score_cache.json
```

---

### C. `updateDaily.py` (Legacy — runs on import)

```
updateDaily.py (module level line 245)
  │
  └─ handler("event", "context")
       └─ update_resume()
            ├─ validate globals (username, password, file_id, form_key)
            ├─ NaukriLoginClient [LOCAL CLASS].login()
            ├─ GET Google Drive PDF
            ├─ POST filevalidation.naukri.com/file
            ├─ fetch_profile_id()
            └─ POST advResume endpoint

OUTCOME: dict {success, file_key, message} printed to stdout
FAILURE: Empty global credentials → immediate error dict
```

---

### D. `get_Nkparam.py` (Selenium Harvester)

```
get_Nkparam.py (module level)
  │
  └─ while True:
       ├─ driver.get(naukri search URL)
       ├─ sleep(5)
       ├─ parse performance logs for nkparam header
       ├─ append to nkPool.txt
       ├─ clear_session(cookies, localStorage)
       └─ sleep(2)

OUTCOME: nkPool.txt grows until KeyboardInterrupt
```

---

## Feature Traces

### 1. Password Login

```
NaukriLoginClient.login()
  ↓
_login_request()  [@with_exponential_retry]
  ↓
POST https://www.naukri.com/central-login-services/v1/login
  Headers: DEFAULT_HEADERS (appid=105, clientid=d3skt0p, systemid=jobseeker)
  Body: {"username", "password"}
  ↓
Response OK?
  ├─ NO → raise NaukriAuthError("Login failed")
  └─ YES → scan session.cookies for "nauk_at"
       ↓
       NaukriSession(bearer_token, cookie_dict)
       ↓
       get_form_key2() [try/catch, cache form_key]
       ↓
       return NaukriSession
```

---

### 2. OTP Login (Send + Verify)

**Send:**
```
send_otp(username, is_mobile)
  ↓
_send_otp_request()
  ↓
POST OTP_SEND_URL
  Headers: DEFAULT_HEADERS + appid=100
  Body: {username, flowId:"login", isLoginByEmail, isLoginByMobile}
  ↓
return res.json()
```

**Verify:**
```
verify_otp(otp, username, is_mobile)
  ↓
_verify_otp_request()
  ↓
POST OTP_VERIFY_URL
  Headers: OTP_HEADERS (appid=100)
  Body: {username, token:otp, flowId:"login", ...}
  ↓
Extract nauk_at cookie OR authToken/token from JSON
  ↓
NaukriSession + get_form_key2() cache warm
```

---

### 3. Form Key Extraction (formKey2)

```
get_form_key2()
  ↓
Check cache["form_key"] → return if hit
  ↓
_fetch_profile_html_auth()
  GET PROFILE_URL + Bearer header
  ↓
extract_all_js_urls(html)
  ↓
FOR each js_url containing "mnj":
  fetch JS → extract_form_key2(js_content)
  ↓
Fallback: GET https://static.naukimg.com/s/5/105/j/mnj_v299.min.js
  ↓
Cache + return key OR raise NaukriParseError
```

---

### 4. Resume Update (Full Pipeline)

```
update_resume(resume_file)
  ↓
fetch_profile_id()
  GET DASHBOARD_URL (Bearer)
  → profileId cached
  ↓
validate_file(resume_file)
  ├─ get_form_key2()
  ├─ file_key = "U" + generate_file_key(13)
  ├─ read PDF bytes (path or file-like)
  └─ _validate_file_request()
       POST FILE_VALIDATION_URL (plain requests, UPLOAD_HEADERS)
       multipart: file + formKey + fileName + fileKey
  → [file_key, form_key]
  ↓
_update_resume_request()
  POST RESUME_UPDATE_URL_TEMPLATE.format(profile_id)
  Headers: Bearer + x-http-method-override: PUT
  Body: {"textCV": {"formKey", "fileKey"}}
  ↓
return ResumeUpdateResult(profile_id, json, status_code)
```

---

### 5. Profile Update

```
update_profile(headline?, name?, summary?)
  ↓
fetch_profile_id()
  ↓
Build profile_fields dict (only non-None args)
  ↓
IF empty → raise ValueError
  ↓
_update_profile_request()
  POST PROFILE_UPDATE_URL
  Headers: Bearer + x-http-method-override: PUT
  Body: {"profile": {...}, "profileId": pid}
  ↓
return ProfileUpdateResult
```

---

### 6. Recommended Jobs

```
get_recommended_jobs()
  ↓
POST RECOMMENDED_JOBS_URL
  Headers: _headers() [Bearer, systemid=Naukri]
  Body: {clusterId:null, src:"recommClusterApi", clusterSplitDate:{...}}
  ↓
Parse jobDetails[] → _parse_job() each
  ↓
return list[Job]
```

---

### 7. Job Search

```
search_jobs(keyword, location, page, job_age, experience, ...)
  ↓
_build_seo_key(keyword, location, page)
  e.g. "node-js-developer-jobs-in-hyderabad-2"
  ↓
_get_nkparam()
  ├─ use_pool=True → rotate self.pool
  └─ default → generate_nkparam("srp")
       RSA encrypt "v0|{ms_timestamp}|121_srp"
  ↓
_search_headers() → appid=109, gid=..., nkparam=...
  ↓
GET JOB_SEARCH_URL
  params: keyword, k, pageNo, experience, jobAge, seoKey, src, ...
  ↓
403 → NaukriAuthError (nkparam expired)
406 → return []
  ↓
Parse jobDetails/jobs → _parse_job() → list[Job]
```

---

### 8. Job Details

```
get_job_details(job_id, sid)
  ↓
sid = timestamp sid if empty
  ↓
GET https://www.naukri.com/jobapi/v1/job/{job_id}
  params: microsite, src, sid, xp, px
  headers: Bearer + nkparam + appid=121
  ↓
401/403 → NaukriAuthError
  ↓
return JSON dict
```

---

### 9. Easy Apply

```
apply_job(job, mandatory_skills, optional_skills, sid, source)
  ↓
sid = generated if empty
  ↓
APPLY_SRC_MAP[source] → applySrc + logstr template
  ↓
POST APPLY_JOB_URL
  Headers: Bearer, appid=121, systemid=jobseeker
  Body: {
    strJobsarr: [job_id],
    logstr, flowtype:"show", mandatory_skills, optional_skills,
    applyTypeId:"107", applySrc, sid, ...
  }
  ↓
return JSON (may contain questionnaire in jobs[0])
```

---

### 10. Questionnaire Apply

```
handle_static_questionnaire_and_apply(job, questionnaire, sid, ...)
  ↓
build_smart_answers(questionnaire, PROFILE)
  → map questionId → answer (text or [option_key])
  ↓
POST APPLY_JOB_URL
  Body: previous fields + applyData: { job_id: { answers: {...} } }
  ↓
return JSON or {success:False, error}
```

---

### 11. Application History

```
get_application_history(page_size, days, page_number, mobile)
  ↓
_fetch_history_request()
  GET HISTORY_URL
  Headers: Bearer, appid/systemid 107 or 135
  params: pageSize, days, pageNumber, [filterInfo=2 desktop]
  ↓
return raw JSON

Optional:
parse_history(raw) → list[ApplicationHistory] dataclasses
```

---

### 12. AI Filter Pipeline

```
JobFilterPipeline2.run(jobs)
  ↓
normalize_jobs     → extract tags, exp range, days_old
  ↓
dedup              → by job_id
  ↓
hard_veto          → title blacklist
  ↓
experience_filter  → exp_min <= 4, exp_max > 0
  ↓
desc_red_flag_check → walk-in regex
  ↓
title_filter       → software keywords required
  ↓
company_veto       → Accenture, TCS, etc.
  ↓
tag_presort        → stack overlap scoring
  ↓
[:ai_score_limit]  → default 300
  ↓
ai_score_batch     → OpenAI gpt-4o-mini batches of 50
  ↓
rank               → ai_score + recency bonus
  ↓
select             → score >= min_apply_score (50), cap daily_apply_limit (50)
  ↓
return apply_list
```

---

## Object Creation Timeline (`apply_agent.py`)

| Step | Objects Created |
|------|-----------------|
| Start | `NaukriLoginClient`, `NaukriSession` (via login) |
| After login | `NaukriJobClient` |
| Fetch | `list[Job]` |
| Filter | `JobFilterPipeline2`, `score_cache.json` updates |
| Apply loop | `sid` strings, CSV rows |

---

## Object Creation Timeline (`main.py`)

| Step | Objects Created |
|------|-----------------|
| Start | `NaukriLoginClient`, `NaukriSession` |
| Jobs | `NaukriJobClient`, `list[Job]` |
| Apply | API responses (dict) per job |
