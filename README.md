# Auto-Apply Backend Engine

The backend API and autonomous orchestration engine for the **Auto-Apply** internship application system.

Built with **FastAPI**, **SQLAlchemy** (Async), **Gemini API**, and **Playwright Browser Automation**, providing compliant public ATS discovery, semantic candidate matching, tailored materials generation, email reply tracking via Gmail API, and direct functional browser pre-filling with human review gates.

---

## 5-Phase Architecture Overview

1. **Phase 1: Database & Real-Time SSE Stream**
   - Async database models: `candidates`, `job_listings`, `applications`, `email_logs`, `activity_logs`, `system_settings`.
   - Live Server-Sent Events (SSE) stream on `/api/stream/activity`.
2. **Phase 2: Master Resume Parser & ATS Job Discovery**
   - Ingests PDF/DOCX resumes and parses structured JSON candidate profiles with Gemini.
   - Public API discovery clients for **Greenhouse**, **Lever**, **Ashby**, and **SmartRecruiters** (No LinkedIn/Indeed scraping).
   - Numerical semantic matching ($0-100\%$) and fit rationale evaluation per job.
3. **Phase 3: Gemini Tailoring Engine & Traceability Validator**
   - Generates role-specific cover letters connecting candidate's verified projects to the target company.
   - Re-orders skills and optimizes bullet point emphasis without fabricating facts.
   - Compiles pristine single-page ATS PDF resumes via Playwright.
   - ATS Custom Question Pre-Filler strictly sources from candidate profile, flags missing fields for manual entry, and cross-references answers for traceability.
4. **Phase 4: Gmail Reply-Watcher & Recruiter Intent Classifier**
   - Ingests incoming recruiter emails via Gmail API.
   - Classifies recruiter intent (`INTERVIEW_INVITE`, `REJECTION`, `ASSESSMENT`, `ACK`) and automatically updates application status.
5. **Phase 5: Playwright Direct Pre-Fill & Manual Submit Gate**
   - Direct functional filling of ATS forms (Greenhouse, Lever, Ashby, SmartRecruiters, Direct).
   - Pre-fills form fields, uploads tailored PDF resume, takes pre-fill screenshot, and stops for human review.
   - Final submit is executed exclusively upon explicit candidate approval from the dashboard.

---

## Prerequisites

- **Python**: 3.10+
- **Playwright Chromium Binaries**: `playwright install chromium`
- **Gemini API Key**: (Optional for LLM features; offline fallbacks available)

---

## Installation & Setup

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```env
PORT=8000
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./auto_apply.db
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
STORAGE_DIR=./storage
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### 4. Run the Server
```bash
python run.py
```
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running Unit & Integration Tests

```bash
# Phase 1: Database & Seed
python test_db.py

# Phase 2: Resume Parser & ATS Discovery
python test_phase2.py

# Phase 3: Gemini Tailoring, Traceability & ATS PDF
python test_phase3.py

# Phase 4: Gmail Watcher & Intent Classifier
python test_phase4.py

# Phase 5: Direct Form Filler & Submission Gate
python test_phase5.py
```
