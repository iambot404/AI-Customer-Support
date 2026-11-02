# AI Customer Support Ticket Classifier (AutoTriage AI)

An intelligent, full-stack customer support triage platform powered by **Python Flask**, **Google Gemini 2.5**, and **SQLite / Supabase PostgreSQL**.

AutoTriage AI accepts incoming customer support tickets, dynamically classifies them into 5 standardized categories, assigns an objective priority level, generates an executive summary and diagnostic rationale, and empowers human support agents through an operations dashboard with override and status management capabilities.

---

## ✨ Features

- **Public Ticket Submission Portal**: Clean, accessible interface for customers with live input length validation and preset sample templates.
- **Autonomous Gemini AI Triage**:
  - Classifies tickets into: `Technical Issue`, `Billing & Payments`, `Account & Access`, `Feature Request`, `General Inquiry`.
  - Assesses severity: `Urgent`, `High`, `Medium`, `Low` (strictly impact-based, preventing emotional inflation).
  - Generates concise executive summaries and diagnostic reasoning.
  - Generates and validates confidence scores (clamped between `0.0` and `1.0`).
- **Resilient Fallback Handling**: If the Gemini API is unreachable, has quota issues, or is unconfigured, tickets are safely stored in the database and marked as `Pending` so no customer communication is ever lost.
- **Support Agent Authentication (Login/Signup Module)**: Secure session-based authentication with `pbkdf2:sha256` password hashing, protecting the triage dashboard and queue.
- **Live Operations Dashboard**: Executive metrics and breakdowns (by category, priority, and status) computed directly from live SQL records.
- **Filterable Ticket Queue**: Search by keyword (subject, message, customer) with multi-criteria dropdowns (category, priority, status) and pagination.
- **Human-in-the-Loop Overrides**: Detail page allowing support staff to override AI category and priority while preserving original model assessments.
- **On-Demand Reclassification**: Single-click re-evaluation with Gemini for pending or failed tickets.
- **Dual Database Architecture**: Zero-config local SQLite for rapid local development, and Supabase PostgreSQL for persistent cloud deployments.

---

## 🛠 Tech Stack

- **Backend**: Python 3.10+, Flask 3.1, Werkzeug
- **AI / LLM**: Google Gemini 2.5 Flash via official `google-genai` SDK
- **Database**: SQLite (local dev) / Supabase PostgreSQL (production)
- **Frontend**: HTML5, Vanilla CSS (Modern Dark Obsidian theme with glassmorphism), Vanilla JavaScript
- **Testing**: Pytest (23 automated unit & functional tests)
- **Deployment**: Vercel Serverless (`@vercel/python`)

---

## 📂 Project Structure

```text
AI Customer Support Ticket Classifier/
├── app.py                     # Flask application entry point & factory
├── config.py                  # Environment & taxonomy configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Template environment variables
├── .gitignore                 # Ignored files (secrets, caches, dbs)
├── README.md                  # Documentation & instructions
├── art.txt                    # Architecture & functionality fact-check report
├── keys.txt                   # Local API key storage helper
├── vercel.json                # Vercel serverless deployment configuration
├── database/
│   ├── __init__.py
│   └── db.py                  # Database operations (SQLite & Postgres)
├── services/
│   ├── __init__.py
│   └── gemini_service.py      # Gemini API client, prompts, and schema validation
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Agent registration, login, logout & session guards
│   └── tickets.py             # Public submit, dashboard, list, detail & overrides
├── templates/
│   ├── base.html              # Shell layout with flash alerts & navbar
│   ├── index.html             # Public customer portal & status card
│   ├── dashboard.html         # Real metrics, charts & recent tickets
│   ├── tickets.html           # Searchable & filterable ticket queue
│   ├── ticket_detail.html     # AI analysis breakdown & human override form
│   ├── login.html             # Agent login page
│   ├── register.html          # Agent registration page
│   └── 404.html               # 404 error page
├── static/
│   ├── css/
│   │   └── style.css          # Design system & dark mode aesthetics
│   └── js/
│       └── app.js             # Form validation, spinners, presets & counters
└── tests/
    ├── __init__.py
    ├── test_auth.py           # Authentication test suite
    ├── test_classifier.py     # Gemini service unit & mock tests
    └── test_tickets.py        # Functional endpoint & DB tests
```

---

## 🚀 Local Setup Instructions

### 1. Prerequisites
- Python 3.10+ installed
- Git (optional)

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template configuration:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API Key:
```env
SECRET_KEY=generate_a_random_secret_string
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional: configure Supabase Postgres if testing cloud DB locally
DATABASE_URL=
```
*(Note: If `GEMINI_API_KEY` is placed in `keys.txt`, the application will also detect it automatically as a fallback).*

### 5. Run the Application
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:5000`**

---

## 🧪 Running the Tests

The test suite runs with fully mocked Gemini API endpoints so it **does not require an active API key or incur API costs**:

```bash
python -m pytest tests/ -v
```

All 23 tests will execute across authentication, Gemini service parsing/validation/clamping, ticket lifecycle, and filtering.

---

## ☁️ Supabase Configuration

A dedicated Supabase project has been provisioned:
- **Project Name**: `support-ticket-classifier`
- **Project Ref**: `mcgbcmaybudlfowynvgi`
- **Region**: `ap-south-1`
- **Host**: `db.mcgbcmaybudlfowynvgi.supabase.co`

### Schema Migration
The `users` and `tickets` tables are created automatically on application startup. You can also run migrations manually in Supabase SQL editor using:
```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'agent',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    customer_name TEXT,
    customer_email TEXT,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    ai_category TEXT,
    ai_priority TEXT,
    ai_summary TEXT,
    ai_reason TEXT,
    confidence REAL,
    status TEXT NOT NULL DEFAULT 'Open',
    classification_status TEXT NOT NULL DEFAULT 'Pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

> **Security Advisory**: For production client-side direct access, enable Row Level Security (RLS) policies as recommended by Supabase. When accessing via backend server connection string, connections operate via standard PostgreSQL server credentials.

---

## 🌐 Vercel Deployment

### Database Persistence Caveat
Vercel functions run in ephemeral serverless containers. Any writes to a local SQLite `.db` file **will be discarded** when containers scale or recycle.
**For Vercel deployment, configure `DATABASE_URL` pointing to Supabase PostgreSQL.**

### Deployment Steps:
1. Push your repository to GitHub.
2. Import the repository into your Vercel account (`imortalclub01-4646`).
3. Set the following Environment Variables in the Vercel Dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API Key
   - `SECRET_KEY`: Random 32+ character string
   - `DATABASE_URL`: `postgresql://postgres:[PASSWORD]@db.mcgbcmaybudlfowynvgi.supabase.co:5432/postgres`
4. Deploy! Vercel will automatically use `vercel.json` with the `@vercel/python` runtime.

---

## 🔒 Security & Privacy

- **No Secrets in Code**: Secrets are never hardcoded and `.env` / `keys.txt` are included in `.gitignore`.
- **Untrusted User Content**: Customer input is strictly segregated in delimited prompts to prevent prompt injection.
- **Parameterized SQL**: All database operations use parameter substitution (`?` for SQLite, `%s` for Postgres) preventing SQL injection.
- **Password Protection**: Passwords hashed with `pbkdf2:sha256` salt rounds.
