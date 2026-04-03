---
project_name: '08B2B_AIfind - Tranotra Leads'
user_name: 'Ailong'
date: '2026-04-03'
sections_completed: ['discovery']
existing_patterns_found: 7
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Discovery Summary

**Project:** Tranotra Leads - Automated customer discovery and outreach pipeline for plasticizer suppliers

**Status:** Phase 1 MVP complete with Flask + Gemini API + SQLAlchemy ORM. Ready for architecture documentation and Phase 2+ implementation planning.

---

## Technology Stack & Versions

### Backend Framework
- **Flask** 2.3.0 - Web framework for API and templates
- **SQLAlchemy** 2.0.0 - ORM for database access
- **Werkzeug** 2.3.0 - WSGI utilities

### AI/LLM
- **google-generativeai** 0.3.0 - Gemini API client
- **Model:** gemini-2.5-flash (confirmed working 2026-03-31)

### Database
- **SQLite** - File-based database at `./db/tranotra_leads.db`
- **python-dotenv** 1.0.0 - Environment variable management

### Testing
- **pytest** 7.4.0 - Test framework
- **pytest-cov** 4.1.0 - Coverage reporting
- **pytest-mock** 3.11.1 - Mocking utilities

### Python Version
- Python 3.8+

---

## Project Structure & Organization

```
tranotra-leads/
├── src/
│   ├── config.py           # Environment + API configuration
│   ├── db.py               # SQLAlchemy models (Company, SearchHistory)
│   ├── gemini_client.py    # Gemini API wrapper
│   ├── parser.py           # Response parsing (JSON/CSV/Markdown)
│   ├── main.py             # Flask app + routes
│   └── __init__.py
├── tests/
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_config.py
│   ├── test_db.py
│   ├── test_gemini_client.py
│   ├── test_main.py
│   ├── test_parser.py
│   ├── test_prompts.py
│   └── test_api_integration.py
├── templates/
│   └── index.html          # Flask template
├── static/                 # CSS/JS assets
├── db/                     # SQLite database directory
├── README.md
├── TESTING.md
├── requirements.txt
├── pytest.ini
└── .env                    # Environment variables (not in git)
```

---

## Critical Implementation Rules

### 1. Configuration Management
- **Rule:** All API keys and sensitive config must use `.env` file loaded via `python-dotenv`
- **Pattern:** Use `config.py` as central source of truth for all settings
- **Why:** Enables local development, testing, and production environments without code changes

### 2. Database Models & Constraints
- **Rule:** Use SQLAlchemy declarative models with explicit constraints (CHECK, UNIQUE, NOT NULL)
- **Pattern:** Company model has 23 fields with:
  - `linkedin_normalized` as unique constraint for deduplication
  - `prospect_score` checked as 1-10 range
  - `priority` enum-like check for HIGH/MEDIUM/LOW
  - Timestamps: `created_at`, `updated_at` with UTC defaults
- **Why:** Prevents invalid data and duplicate LinkedIn entries

### 3. Gemini API Integration
- **Rule:** Always use `gemini-2.5-flash` model; responses may come as JSON, CSV, or Markdown
- **Pattern:** Parse Gemini responses flexibly in `parser.py`:
  - Detect format automatically
  - Handle partial/incomplete responses
  - Log raw responses for debugging
- **Why:** Gemini output format is not guaranteed; robustness required

### 4. API Endpoint Design
- **Pattern:** POST to `/api/search` with country + query → returns parsed companies
- **Rule:** All endpoint responses must include error handling with HTTP status codes
- **Why:** Client expects consistent error messages and status codes

### 5. Testing Requirements
- **Rule:** 100% test coverage goal - tests make development safe
- **Pattern:** 
  - `conftest.py` provides shared fixtures (DB session, mock Gemini responses)
  - Test files mirror `src/` structure: `test_<module_name>.py`
  - Use `pytest-mock` for Gemini API mocking
- **Why:** Safety and confidence when refactoring or adding features

### 6. Logging & Debugging
- **Rule:** Use Python `logging` module with level set via `LOG_LEVEL` env var
- **Pattern:** Each module logs with `logger = logging.getLogger(__name__)`
- **Why:** Production debugging and error tracking

### 7. Code Organization
- **Rule:** Separate concerns into `pipeline/` modules (discover, profile, contacts, score, draft_email)
- **Rule:** Flask routes in `main.py` stay thin; logic in `gemini_client.py` and `parser.py`
- **Why:** Maintainability and clear responsibility boundaries

---

## Code Naming Conventions

- **Files:** snake_case (e.g., `gemini_client.py`, `test_config.py`)
- **Classes:** PascalCase with descriptive names (e.g., `Company`, `SearchHistory`)
- **Functions:** snake_case (e.g., `parse_gemini_response`, `get_session`)
- **Variables:** snake_case (e.g., `prospect_score`, `linkedin_normalized`)
- **Database columns:** snake_case (e.g., `contact_email`, `year_established`)

---

## Known Decisions & Constraints

- **No Cloud Scheduling:** Runs locally, not via Google Apps Script or serverless
- **Manual Email Review:** No auto-send; human review required before Aliyun DirectMail dispatch
- **Local SQLite:** No external database required, enables offline operation
- **CLI MVP:** No web UI yet; Phase 1 is API + dashboard only

---

## Next Steps for AI Agents

When implementing new features or modules:
1. Follow the pipeline architecture (discover → profile → contacts → score → draft → review)
2. Add models to `db.py` following existing Company pattern
3. Test all new code with pytest; mock external APIs
4. Update `.env.example` when adding new configuration
5. Run full test suite with coverage before PR

---

_Document initialized: 2026-04-03. Ready for collaborative generation with user._
