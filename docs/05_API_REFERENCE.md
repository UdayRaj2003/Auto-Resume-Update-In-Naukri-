# 05 — API Reference

All HTTP endpoints extracted from source code. Payload/response shapes are documented as observed in code; live API behavior may differ.

---

## Naukri — Authentication

### POST Login

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/central-login-services/v1/login` |
| **Constant** | `LOGIN_URL` |
| **Method** | POST |
| **File** | `src/config/constants.py`, `src/client/naukri_client.py` |
| **Feature** | Password login |
| **Authentication** | None (credentials in body) |

**Headers:**
```json
{
  "accept": "application/json",
  "appid": "105",
  "clientid": "d3skt0p",
  "content-type": "application/json",
  "referer": "https://www.naukri.com/nlogin/login",
  "systemid": "jobseeker",
  "x-requested-with": "XMLHttpRequest"
}
```

**Payload:**
```json
{
  "username": "<email or phone>",
  "password": "<password>"
}
```

**Response:** Sets cookies including `nauk_at` (Bearer token). JSON body NOT VERIFIED as primary token source.

**Used by:** `NaukriLoginClient._login_request()`, `updateDaily.py` (legacy)

---

### POST Send OTP

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/central-login-services/v1/otp` |
| **Constant** | `OTP_SEND_URL` |
| **Method** | POST |
| **Feature** | OTP send |

**Headers:** `DEFAULT_HEADERS` with `appid: "100"`

**Payload:**
```json
{
  "username": "<phone or email>",
  "flowId": "login",
  "isLoginByEmail": false,
  "isLoginByMobile": true
}
```

**Used by:** `NaukriLoginClient._send_otp_request()`

---

### POST Verify OTP

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/central-login-services/v0/otp-login` |
| **Constant** | `OTP_VERIFY_URL` |
| **Method** | POST |
| **Feature** | OTP verify / MFA login |

**Headers:** `OTP_HEADERS` (appid=100, specific referer/sec-ch-ua)

**Payload:**
```json
{
  "username": "<phone or email>",
  "token": "<6-digit OTP>",
  "flowId": "login",
  "isLoginByEmail": false,
  "isLoginByMobile": true
}
```

**Response:** `nauk_at` cookie and/or `authToken`/`token` in JSON body.

**Used by:** `NaukriLoginClient._verify_otp_request()`

---

## Naukri — Profile & Dashboard

### GET Dashboard (Profile ID)

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/self/dashboard` |
| **Constant** | `DASHBOARD_URL` |
| **Method** | GET |
| **Authentication** | `Authorization: Bearer {nauk_at}` |

**Headers (auth):** `appid=105`, `systemid=Naukri`

**Response fields used:** `profileId` or `dashBoard.profileId`

**Used by:** `NaukriLoginClient.fetch_profile_id()`

---

### GET Profile Page (HTML — formKey extraction)

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/mnjuser/profile` |
| **Constant** | `PROFILE_URL` |
| **Method** | GET |
| **Authentication** | Bearer (for `get_form_key2`) or none (legacy `get_form_key`) |

**Used by:** `_fetch_profile_html()`, `_fetch_profile_html_auth()`

---

### GET Static JS Bundles

| Field | Value |
|-------|-------|
| **URL** | Dynamic from HTML + fallback `https://static.naukimg.com/s/5/105/j/mnj_v299.min.js` |
| **Method** | GET |
| **Purpose** | Extract `formKey` for file upload |

**Used by:** `get_form_key()`, `get_form_key2()`

---

### POST Full Profile Update

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v1/users/self/fullprofiles` |
| **Constant** | `PROFILE_UPDATE_URL` |
| **Method** | POST with `X-HTTP-Method-Override: PUT` |
| **Feature** | Headline, name, summary update |
| **Authentication** | Bearer |

**Payload:**
```json
{
  "profile": {
    "resumeHeadline": "...",
    "name": "...",
    "summary": "..."
  },
  "profileId": "<profile_id>"
}
```

**Used by:** `NaukriLoginClient.update_profile()`

---

### POST Resume Attach

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/cloudgateway-mynaukri/resman-aggregator-services/v0/users/self/profiles/{profile_id}/advResume` |
| **Constant** | `RESUME_UPDATE_URL_TEMPLATE` |
| **Method** | POST with `X-HTTP-Method-Override: PUT` |
| **Feature** | Resume update |
| **Authentication** | Bearer |

**Payload:**
```json
{
  "textCV": {
    "formKey": "<from JS bundle>",
    "fileKey": "<from file validation>"
  }
}
```

**Used by:** `NaukriLoginClient.update_resume()`, `updateDaily.py`

---

## Naukri — File Upload

### POST File Validation

| Field | Value |
|-------|-------|
| **URL** | `https://filevalidation.naukri.com/file` |
| **Constant** | `FILE_VALIDATION_URL` |
| **Method** | POST (multipart) |
| **Authentication** | formKey (not Bearer) |
| **HTTP client** | Plain `requests.post` (NOT httpcloak session) |

**Headers:**
```json
{
  "accept": "application/json, text/javascript, */*; q=0.01",
  "appid": "105",
  "origin": "https://www.naukri.com",
  "referer": "https://www.naukri.com/",
  "systemid": "fileupload"
}
```

**Form data:**
- `file`: PDF binary
- `formKey`: string
- `fileName`: string
- `uploadCallback`: `"true"`
- `fileKey`: `"U" + 13 random chars`

**Response:** JSON map of fileKey → validation result

**Used by:** `NaukriLoginClient._validate_file_request()`

---

## Naukri — Jobs

### POST Recommended Jobs

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/jobapi/v2/search/recom-jobs` |
| **Constant** | `RECOMMENDED_JOBS_URL` |
| **Method** | POST |
| **Authentication** | Bearer |

**Payload:**
```json
{
  "clusterId": null,
  "src": "recommClusterApi",
  "clusterSplitDate": {
    "apply": "<ISO UTC>",
    "preference": "<ISO UTC>",
    "profile": "<ISO UTC>",
    "similar_jobs": "<ISO UTC>"
  }
}
```

**Response field:** `jobDetails[]`

**Used by:** `NaukriJobClient.get_recommended_jobs()`

---

### GET Job Search

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/jobapi/v3/search` |
| **Constant** | `JOB_SEARCH_URL` |
| **Method** | GET |
| **Authentication** | **`nkparam` header required** (403 if invalid) |

**Headers (additional):**
```json
{
  "appid": "109",
  "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
  "nkparam": "<RSA base64 token>"
}
```

**Query params:**
| Param | Example |
|-------|---------|
| `noOfResults` | 20 |
| `urlType` | `search_by_keyword` |
| `searchType` | `adv` |
| `keyword` / `k` | search term |
| `pageNo` | 2 (default in code) |
| `experience` | 2 |
| `jobAge` | 3 |
| `seoKey` | `node-js-developer-jobs-in-hyderabad-2` |
| `src` | `jobsearchDesk` |
| `nignbevent_src` | `jobsearchDeskGNB` |
| `latLong` | optional |

**Response fields:** `jobDetails` or `jobs`

**Used by:** `NaukriJobClient.search_jobs()`

---

### GET Job Details

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/jobapi/v1/job/{job_id}` |
| **Method** | GET |
| **Authentication** | Bearer + nkparam |

**Query params:** `microsite=y`, `src=jobsearchDesk`, `sid`, `xp=1`, `px=1`

**Headers:** `appid=121`, `systemid=Naukri`, `clientid=d3skt0p`

**Response field used:** `job.responseManager` (`"companyUrl"` = external apply)

**Used by:** `NaukriJobClient.get_job_details()`, `is_external_apply()`

---

### POST Apply Job

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply` |
| **Constant** | `APPLY_JOB_URL` |
| **Method** | POST |
| **Authentication** | Bearer |

**Payload (easy apply):**
```json
{
  "strJobsarr": ["<job_id>"],
  "logstr": "--srp-1-F-0-1--{sid}-" ,
  "flowtype": "show",
  "crossdomain": true,
  "jquery": 1,
  "rdxMsgId": "",
  "chatBotSDK": true,
  "mandatory_skills": ["tag1", "tag2"],
  "optional_skills": ["tag3"],
  "applyTypeId": "107",
  "closebtn": "y",
  "applySrc": "srp",
  "sid": "<YYYYMMDDHHMMSS>0000000",
  "mid": ""
}
```

**Payload (with questionnaire):** Same + `"applyData": { "<job_id>": { "answers": { "<questionId>": "value" | ["optionKey"] } } }`

**Response:** JSON with `jobs[0].questionnaire` when employer requires questions.

**Used by:** `apply_job()`, `handle_static_questionnaire_and_apply()`

---

## Naukri — Application History

### GET Application History

| Field | Value |
|-------|-------|
| **URL** | `https://www.naukri.com/cloudgateway-apply/whtma-services/v0/applyapi/v5/history` |
| **Constant** | `HISTORY_URL` |
| **Method** | GET |
| **Authentication** | Bearer |

**Query params:**
| Param | Desktop | Mobile |
|-------|---------|--------|
| `pageSize` | 10 | 10 |
| `days` | 90 | 90 |
| `pageNumber` | 1 | 1 |
| `filterInfo` | 2 | absent |

**Headers:** `appid/systemid` = `107` (desktop) or `135` (mobile); mobile adds `clientid=m0b5`

**Response field:** `applyDetails[]`

**Used by:** `NaukriLoginClient.get_application_history()`

---

## External APIs

### OpenAI Chat Completions

| Field | Value |
|-------|-------|
| **URL** | `https://api.openai.com/v1/chat/completions` |
| **Method** | POST |
| **Authentication** | `Authorization: Bearer {OPEN_API_KEY}` |
| **Model** | `gpt-4o-mini` |
| **Used by** | `JobFilterPipeline2._call_ai()` |

---

### Google Drive Download (Legacy only)

| Field | Value |
|-------|-------|
| **URL** | `https://drive.google.com/uc?export=download&id={file_id}` |
| **Method** | GET |
| **Used by** | `updateDaily.py` only |

---

## TLS / Debug Endpoints (test_session.py only)

| URL | Purpose |
|-----|---------|
| `https://tls.peet.ws/api/all` | JA3/JA4 fingerprint check |
| `https://cf.erisa.uk/` | Cloudflare bot score |
| `https://www.cloudflare.com/cdn-cgi/trace` | TLS trace |

**Not part of production features.**

---

## Endpoint Summary Table

| # | Method | URL Path | Auth | Feature |
|---|--------|----------|------|---------|
| 1 | POST | `/central-login-services/v1/login` | Body creds | Login |
| 2 | POST | `/central-login-services/v1/otp` | None | Send OTP |
| 3 | POST | `/central-login-services/v0/otp-login` | OTP | Verify OTP |
| 4 | GET | `/mnjuser/profile` | Optional Bearer | formKey |
| 5 | GET | `.../users/self/dashboard` | Bearer | Profile ID |
| 6 | POST | `.../v1/users/self/fullprofiles` | Bearer | Profile update |
| 7 | POST | `.../profiles/{id}/advResume` | Bearer | Resume attach |
| 8 | POST | `filevalidation.naukri.com/file` | formKey | PDF validate |
| 9 | POST | `/jobapi/v2/search/recom-jobs` | Bearer | Recommended |
| 10 | GET | `/jobapi/v3/search` | nkparam | Search |
| 11 | GET | `/jobapi/v1/job/{id}` | Bearer+nkparam | Details |
| 12 | POST | `.../apply-workflow/v1/apply` | Bearer | Apply |
| 13 | GET | `.../applyapi/v5/history` | Bearer | History |
| 14 | POST | `api.openai.com/v1/chat/completions` | API key | AI score |
