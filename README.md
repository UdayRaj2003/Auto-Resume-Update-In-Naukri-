# NopeRi Enhanced

> ⚠️ This project is an enhanced version of the original **NopeRi** project by **Traverser25**.

## 🙏 Credits

This project is built on top of the excellent **NopeRi** project created by **Traverser25**.

**Original Repository:** https://github.com/Traverser25/NopeRi

The original project provides a lightweight Python API client for Naukri, including:

- Login & session management
- Resume upload
- Profile updates
- Job search
- Easy Apply
- Naukri API integration

Huge thanks to the original author for making this possible.

---

## What I Added

This repository contains my personal enhancements focused on making the workflow production-ready for unattended daily execution.

### Full Pipeline Runner

- **`run_all.py`** — single entry point for the daily workflow
- Runs **`apply_agent.py`** first, then **`resume_auto_update.py`**
- Automatically re-launches inside the project **`.venv`** when available
- Continues the pipeline even if one step fails (with a summary at the end)
- Forwards `--debug` to the resume updater

### Resume Automation

- Automatic download of the latest resume from Google Drive
- Daily resume update without manual intervention

### Reliability Improvements

- Retry mechanism
- Better exception handling
- Detailed logging
- Status tracking
- Execution reports
- Credential and API key validation before runs

### Automation

- Windows Task Scheduler integration
- Automatic daily execution
- Wake Timers support
- Automatic sleep after execution

### AI Job Apply Improvements

- OpenRouter support via `OPENAI_ENDPOINT`, `OPENAI_MODEL`, and OpenRouter headers
- External prompt file at `prompts/backend.txt` with in-code fallback
- Smaller configurable AI batches (`AI_BATCH_SIZE`, default `10`) to avoid slow/hanging requests
- Cache-aware scoring via `score_cache.json` — cached jobs skip redundant API calls
- Batch progress logging and configurable request timeouts (`AI_TIMEOUT`)
- Better backend-focused AI scoring with improved title/company/experience filters
- Questionnaire handling
- Applied job tracking in `applied_jobs.csv`
- Skips jobs already applied in previous runs
- Fixed score display and filtering using `ai_score` / `ai_reason` from the pipeline

---

## Quick Start

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
USERNAME=your_naukri_email
PASSWORD=your_naukri_password
OPEN_API_KEY=your_openai_or_openrouter_key

# Optional — AI scoring
OPENAI_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
OPENAI_MODEL=openai/gpt-4o-mini
OPENROUTER_SITE_URL=https://github.com/yourusername
OPENROUTER_SITE_NAME=NopeRi
AI_BATCH_SIZE=10
AI_TIMEOUT=120

# Optional — resume automation
GOOGLE_DRIVE_URL=https://drive.google.com/file/d/your_file_id/view
RESUME_NAME=Your_Name_Resume
```

### 3. Run the full daily pipeline

```powershell
python run_all.py
```

Or run scripts individually:

```powershell
.\.venv\Scripts\python.exe apply_agent.py
.\.venv\Scripts\python.exe resume_auto_update.py
```

---

## Entry Points

| Script | Purpose |
|---|---|
| `run_all.py` | Run apply agent + resume updater in one command |
| `apply_agent.py` | Search jobs, AI filter, auto-apply, track results |
| `resume_auto_update.py` | Download resume from Google Drive and upload to Naukri |
| `main.py` | Manual testing / exploratory Naukri API usage |

---

## Original Project

All core Naukri API functionality is provided by the original NopeRi project.

Please support the original repository:

https://github.com/Traverser25/NopeRi

---

## My Contributions

This repository mainly demonstrates how I extended the original project with:

- Google Drive integration
- Production logging
- Retry decorators
- Windows automation
- Daily unattended execution
- Full pipeline orchestration via `run_all.py`
- AI prompt customization via external prompt files
- OpenRouter migration
- Cache-aware AI batch scoring
- Applied job deduplication and CSV tracking
- Better error handling and run summaries

---

## Disclaimer

This repository is intended for educational and personal automation purposes.

The core API implementation belongs to the original NopeRi project by Traverser25.

This repository focuses on showcasing my enhancements built on top of that work.
