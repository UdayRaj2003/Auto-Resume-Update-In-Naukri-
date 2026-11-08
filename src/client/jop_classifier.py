import json
import os
import re
import requests





class JobFilterPipeline2:

    # ── your stack — AI scores against this ──────────────────────────────────
    MY_STACK = [
        # ── Core backend ──────────────────────────────────────────────
        "node", "node.js", "nodejs", "python", "javascript", "typescript",

        # ── Frameworks ───────────────────────────────────────────────
        "express", "express.js", "fastapi", "flask", "nestjs", "nest.js",
        "django", "hapi", "koa",

        # ── Databases ────────────────────────────────────────────────
        "mongodb", "mongoose", "postgresql", "mysql", "redis", "sqlite", 
        "sql", "nosql",

        # ── Cloud & DevOps ───────────────────────────────────────────
        "aws",  "docker", "kubernetes", "ci/cd",
        "github actions"  , "linux", 
        "ec2", "s3", "lambda",  

        # ── APIs & Messaging ─────────────────────────────────────────
        "rest", "rest api", "restful", "websocket",

        # ── Automation & Scraping ────────────────────────────────────
        "selenium", "playwright", "puppeteer" , "scrapy",
        "web scraping", "automation", "n8n", "trigger.dev", "zapier",

        # ── Tools & Practices ────────────────────────────────────────
        "git", "github", "postman" , "jwt", "oauth",
        "microservices", "system design", "api design",
    ]

    # ── hard veto BEFORE ai — title only, zero ambiguity ────────────────────
    VETO_TITLES = [ 
        "android developer", "ios developer", "flutter developer",
        "principal engineer" , "architect",
        "vp of", "head of engineering", "head of technology",
        "founder", "tutor", 
        "data scientist", "ml engineer", "data engineer",
        "engineering manager", "etl engineer", 
        "infra engineer","sales",   
        "observability engineer","Manager"
    ]


    VETO_COMPANIES = {
    "accenture" 
}

    # ── red flag sniff on description (cheap, pre-ai) ───────────────────────
    # Only the things AI genuinely can't infer from tags alone
    DESC_RED_FLAGS = {
        "walk-in":      r"walk.?in|walkin",
        "venue listed": r"venue\s*:|interview venue|bring your resume|carry your resume",
    }




    SOFTWARE_KEYWORDS = {
        "software", "developer", "engineer", "engineering",
        "backend", "full stack", "fullstack", 
        "python", "node", "nodejs", "javascript", "typescript",
        "django", "fastapi", "flask", 
        "devops", "cloud", "sre", "platform","Associate" , "AI" ,"AI Engineer",
        "api", "microservices", "infrastructure","Analyst","IT fresher","Trainee",
        "tech lead", "sde", "swe", "mts", "programmer","react"
    }

    # if ANY of these appear in title → drop it
    FRONTEND_VETO_KEYWORDS = {
        "frontend", "front-end", "front end",
      "angular", "vue", 
        "android", "ios", "flutter", "mobile", "kotlin", "swift",
         "firmware",
        "ml engineer", "data scientist", "lead","Golang","MLops", "mlops", "golang"
        ," Member of Technical Staff - MTS"
    }

    def __init__(
        self,
        openai_api_key,
        prompt=None,
        cache_file="score_cache.json",
        daily_apply_limit=70,
        min_apply_score=30,
        ai_score_limit=300,
        batch_size=None,
    ):
    
        self.api_keys = []
        if isinstance(openai_api_key, list):
            self.api_keys = [str(k).strip() for k in openai_api_key if k and str(k).strip()]
        elif isinstance(openai_api_key, str):
            for k in openai_api_key.replace("\n", ",").split(","):
                k_clean = k.strip()
                if k_clean:
                    self.api_keys.append(k_clean)

        # Fallback to OPEN_API_KEYS / OPEN_API_KEY from environment if empty
        if not self.api_keys:
            env_keys = os.getenv("OPEN_API_KEYS") or os.getenv("OPEN_API_KEY") or ""
            for k in env_keys.replace("\n", ",").split(","):
                k_clean = k.strip()
                if k_clean:
                    self.api_keys.append(k_clean)

        self.current_key_index = 0
        self.custom_prompt = prompt or self._default_prompt()

        self.url = os.getenv(
            "OPENAI_ENDPOINT",
            "https://api.openai.com/v1/chat/completions"
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini"
        )

        self.site_url = os.getenv(
            "OPENROUTER_SITE_URL",
            ""
        )

        self.site_name = os.getenv(
            "OPENROUTER_SITE_NAME",
            "NopeRi"
        )
        
        self.cache_file        = cache_file
        self.daily_apply_limit = daily_apply_limit
        self.min_apply_score   = min_apply_score
        self.ai_score_limit    = ai_score_limit
        self.batch_size        = batch_size or int(os.getenv("AI_BATCH_SIZE", "10"))
        self.ai_timeout        = int(os.getenv("AI_TIMEOUT", "120"))
        self.cache             = self._load_cache()
    

    # =========================================================
    # MAIN
    # =========================================================
    def run(self, jobs):
        print("\nRAW JOBS:", len(jobs))

        jobs = self.normalize_jobs(jobs)
        print("AFTER NORMALIZE:", len(jobs))

        jobs = self.dedup(jobs)
        print("AFTER DEDUP:", len(jobs))

        jobs = self.hard_veto(jobs)
        print("AFTER HARD VETO:", len(jobs))

        jobs = self.experience_filter(jobs)
        print("AFTER EXP FILTER:", len(jobs))

        jobs = self.desc_red_flag_check(jobs)
        print("AFTER RED FLAG CHECK:", len(jobs))

        jobs=self.title_filter(jobs)
        print("AFTER TITLE FILTER:", len(jobs))

        jobs = self.company_veto(jobs)        # ← add here
        print("AFTER COMPANY VETO:", len(jobs))


        jobs = self.tag_presort(jobs)

        jobs = jobs[:self.ai_score_limit]
        print("AFTER LIMIT:", len(jobs))

        jobs = self.ai_score_batch(jobs)

        jobs = self.rank(jobs)
        print("AFTER RANK:", len(jobs))

        jobs = self.select(jobs)
        print("FINAL SELECTED:", len(jobs))

        for j in jobs:
            print(f"  {j.get('ai_score'):>3}  {j.get('title')} @ {j.get('company')}"
                  f"  |  {j.get('ai_reason', '')}")

        return jobs

    # =========================================================
    # NORMALIZE  — tags are the star, keep them clean
    # =========================================================
    def normalize_jobs(self, jobs):
        normalized = []

        for j in jobs:
            job = j if isinstance(j, dict) else j.__dict__

            # days old
            posted   = (job.get("posted_date") or "").lower()
            days_old = 7
            if "today" in posted or "hour" in posted or "just now" in posted:
                days_old = 0
            elif "yesterday" in posted:
                days_old = 1
            else:
                m = re.search(r"(\d+)\s*day", posted)
                if m:
                    days_old = int(m.group(1))
                else:
                    m = re.search(r"(\d+)\s*week", posted)
                    if m:
                        days_old = int(m.group(1)) * 7

            # experience range
            exp = job.get("experience") or ""
            exp_min, exp_max = 0, 10
            nums = re.findall(r"\d+", exp)
            if len(nums) >= 2:
                exp_min, exp_max = int(nums[0]), int(nums[1])
            elif len(nums) == 1:
                exp_min = exp_max = int(nums[0])

            # tags — normalize once, use everywhere
            raw_tags = job.get("tags") or job.get("skills") or []
            if isinstance(raw_tags, str):
                raw_tags = re.split(r"[,;|]", raw_tags)
            tags = [t.strip().lower() for t in raw_tags if t.strip()]

            normalized.append({
                "job_id":         job.get("job_id"),
                "title":          (job.get("title")       or "").strip(),
                "company":        (job.get("company")     or "").strip(),
                "location":       (job.get("location")    or "").strip(),
                "description":    (job.get("description") or "").strip(),
                "tags":           tags,
                "mandatory_tags": tags[:2],   # site signals these as primary
                "optional_tags":  tags[2:],
                "days_old":       days_old,
                "experience_min": exp_min,
                "experience_max": exp_max,
            })

        return normalized

    # =========================================================
    # DEDUP
    # =========================================================
    def dedup(self, jobs):
        seen, result = set(), []
        for j in jobs:
            job_id = j.get("job_id")
            if job_id is None:
                result.append(j)  # can't dedup without an id, just keep it
                continue
            if job_id in seen:
                continue
            seen.add(job_id)
            result.append(j)
        return result

    # =========================================================
    # HARD VETO  — title only, no ambiguity allowed
    # =========================================================
    def hard_veto(self, jobs):
        clean = []
        for j in jobs:
            title = (j.get("title") or "").lower()
            if any(kw in title for kw in self.VETO_TITLES):
                print(f"  [VETO] {j.get('title')}")
                continue
            clean.append(j)
        return clean

    # =========================================================
    # EXPERIENCE FILTER
    # =========================================================
    def experience_filter(self, jobs):
        return [
            j for j in jobs
            if j.get("experience_min", 0) <= 4
            and j.get("experience_max", 10) > 0
        ]

    # =========================================================
    # DESC RED FLAG CHECK  — one cheap regex pass, nothing more
    # =========================================================
    def desc_red_flag_check(self, jobs):
        clean = []
        for j in jobs:
            desc = (j.get("description") or "").lower()
            flagged = [
                label for label, pat in self.DESC_RED_FLAGS.items()
                if re.search(pat, desc)
            ]
            if flagged:
                print(f"  [RED FLAG {flagged}] {j.get('title')}")
                continue
            clean.append(j)
        return clean

    # =========================================================
    # TAG PRESORT  — rough stack overlap count, no AI cost
    # Keeps best candidates at the front before we hit the limit
    # =========================================================

    def title_filter(self, jobs):
        result = []
        for j in jobs:
            title = (j.get("title") or "").lower()

            # must have at least one software keyword
            if not any(kw in title for kw in self.SOFTWARE_KEYWORDS):
                print(f"  [TITLE FILTER - not software] {j.get('title')}")
                continue

            # must NOT be frontend/mobile/ml
            if any(kw in title for kw in self.FRONTEND_VETO_KEYWORDS):
                print(f"  [TITLE FILTER - frontend/mobile] {j.get('title')}")
                continue

            result.append(j)
        return result


    def company_veto(self, jobs):
        clean = []
        for j in jobs:
            company = (j.get("company") or "").lower()
            if any(vc in company for vc in self.VETO_COMPANIES):
                print(f"  [COMPANY VETO] {j.get('title')} @ {j.get('company')}")
                continue
            clean.append(j)
        return clean

    def tag_presort(self, jobs):
        my_stack = set(self.MY_STACK)

        def overlap(j):
            tags     = set(j.get("tags", []))
            mandatory_hit = sum(1 for t in j.get("mandatory_tags", []) if t in my_stack)
            total_hit     = len(tags & my_stack)
            recency_bonus = max(0, 7 - j.get("days_old", 7))
            # mandatory tags weighted 3x — they represent the job's core ask
            return mandatory_hit * 3 + total_hit + recency_bonus

        return sorted(jobs, key=overlap, reverse=True)

    # =========================================================
    # AI SCORING  — tags go in, score + reason come out
    # =========================================================
    def ai_score_batch(self, jobs):
        result = []
        total_batches = max(1, (len(jobs) + self.batch_size - 1) // self.batch_size)

        for batch_num, i in enumerate(range(0, len(jobs), self.batch_size), 1):
            batch = jobs[i:i + self.batch_size]
            uncached = []

            for job in batch:
                jid  = str(job.get("job_id") or "")
                data = self.cache.get(jid) if jid else None
                if data:
                    job["ai_score"]  = data.get("score", 0)
                    job["ai_reason"] = data.get("reason", "")
                else:
                    uncached.append(job)

            if uncached:
                print(
                    f"  AI batch {batch_num}/{total_batches}: "
                    f"scoring {len(uncached)} jobs "
                    f"({len(batch) - len(uncached)} cached)..."
                )
                scores = self._call_ai(uncached)
                if not scores:
                    print("  [AI WARNING] Batch scoring failed; applying uncached jobs by default without caching 0.")
                for idx, job in enumerate(uncached):
                    jid  = str(job.get("job_id") or "")
                    data = scores.get(str(idx)) if scores else None
                    if data:
                        score = data.get("score", 0)
                        if not isinstance(score, (int, float)):
                            data = {"score": 0, "reason": "parse error"}
                        else:
                            data["score"] = int(score)
                        if jid:
                            self.cache[jid] = data
                        job["ai_score"]  = data.get("score", 0)
                        job["ai_reason"] = data.get("reason", "")
                    else:
                        # Fallback: if AI failed to score, set high enough score (80)
                        # so that it is applied to by default, without caching to disk.
                        job["ai_score"]  = 80
                        job["ai_reason"] = "AI unavailable (applied by default)"
            else:
                print(
                    f"  AI batch {batch_num}/{total_batches}: "
                    f"all {len(batch)} jobs loaded from cache"
                )

            result.extend(batch)

        self._save_cache()
        return result

    def _default_prompt(self):
        return (
            "Score each job 0-100 for a backend software engineer.\n"
            "Return ONLY valid JSON like:\n"
            '{{"0": {{"score": 85, "reason": "short reason"}}, "1": {{"score": 20, "reason": "short reason"}}}}\n\n'
            "Jobs:\n{job_block}"
        )

    def _call_ai(self, jobs):
        if not self.api_keys:
            print("AI ERROR: No API keys configured in OPEN_API_KEYS / OPEN_API_KEY")
            return {}

        job_block = ""
        for i, j in enumerate(jobs):
            mandatory = ", ".join(j.get("mandatory_tags", [])) or "none"
            optional  = ", ".join(j.get("optional_tags",  [])) or "none"
            exp       = f"{j.get('experience_min', 0)}-{j.get('experience_max', 10)} yrs"

            job_block += (
                f"Job {i}:\n"
                f"  Title:     {j.get('title')}\n"
                f"  Company:   {j.get('company')}\n"
                f"  Mandatory: {mandatory}\n"
                f"  Optional:  {optional}\n"
                f"  Exp:       {exp}\n"
                f"  Days old:  {j.get('days_old', 7)}\n"
                f"---\n"
            )

        prompt2 = self.custom_prompt.format(job_block=job_block)
        attempts = 0
        total_keys = len(self.api_keys)

        while attempts < total_keys:
            current_key = self.api_keys[self.current_key_index]
            masked_key = f"{current_key[:12]}...{current_key[-4:]}" if len(current_key) > 16 else "key"

            try:
                headers = {
                    "Authorization": f"Bearer {current_key}",
                    "Content-Type": "application/json",
                }

                if "openrouter.ai" in self.url.lower():
                    if self.site_url:
                        headers["HTTP-Referer"] = self.site_url
                    headers["X-Title"] = self.site_name

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt2
                        }
                    ],
                    "temperature": 0.2,
                }

                res = requests.post(
                    self.url,
                    headers=headers,
                    json=payload,
                    timeout=(15, self.ai_timeout),
                )

                if res.status_code in (429, 401, 402, 403):
                    print(f"  [AI KEY ROTATION] Key {self.current_key_index + 1}/{total_keys} ({masked_key}) failed (HTTP {res.status_code}). Rotating to next key...")
                    self.current_key_index = (self.current_key_index + 1) % total_keys
                    attempts += 1
                    continue

                if res.status_code != 200:
                    print("AI HTTP ERROR:", res.status_code)
                    print(res.text[:500])
                    # Rotate key in case it's account/key specific
                    self.current_key_index = (self.current_key_index + 1) % total_keys
                    attempts += 1
                    continue

                content = res.json()["choices"][0]["message"]["content"]
                content = re.sub(r"```json|```", "", content).strip()
                match = re.search(r"\{.*\}", content, re.S)

                if not match:
                    print("AI PARSE ERROR")
                    print(content[:500])
                    return {}

                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else {}

            except requests.Timeout:
                print(f"AI call error: request timed out after {self.ai_timeout}s on key {masked_key}")
                self.current_key_index = (self.current_key_index + 1) % total_keys
                attempts += 1
            except requests.RequestException as e:
                print(f"AI call error on key {masked_key}:", e)
                self.current_key_index = (self.current_key_index + 1) % total_keys
                attempts += 1
            except Exception as e:
                print(f"AI call unexpected error on key {masked_key}:", e)
                return {}

        print("  [AI] All configured API keys exhausted.")
        return {}

    # =========================================================
    # RANK  — ai score + small recency bump
    # =========================================================
    def rank(self, jobs):
        return sorted(
            jobs,
            key=lambda j: j.get("ai_score", 0) + max(0, 3 - j.get("days_old", 7)),
            reverse=True,
        )

    # =========================================================
    # SELECT
    # =========================================================
    def select(self, jobs):
        apply_list  = [j for j in jobs if j.get("ai_score", 0) >= self.min_apply_score]
        review_list = [j for j in jobs if 10 <= j.get("ai_score", 0) < self.min_apply_score]

        if review_list:
            print(f"\n── REVIEW MANUALLY ({len(review_list)}) ──")
            for j in review_list:
                print(f"  score={j.get('ai_score')}  {j.get('title')} @ {j.get('company')}"
                      f"  |  {j.get('ai_reason', '')}")

        return apply_list[:self.daily_apply_limit]

    # =========================================================
    # CACHE
    # =========================================================
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)