---
title: "Technology Stack & Project Structure"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Technology Stack & Project Structure

---

## Technology Stack Summary

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.8+ | Data pipeline friendly; async-ready for Phase 2 |
| **Web Framework** | Flask | 2.3.0 | Lightweight, modular, supports CLI integration |
| **ORM** | SQLAlchemy | 2.0.0 | Mature, flexible queries, relationship management |
| **Database** | SQLite | 3.x | File-based, atomic transactions, no external deps |
| **CLI** | Click | 8.0+ | Modern, Flask 2.3+ compatible, composable |
| **Dep Management** | Poetry | Latest | Reproducible builds, lock files, modern standard |
| **Testing** | pytest | 7.0+ | Fixtures, mocking, 100% coverage target |
| **Code Quality** | black + isort + mypy | Latest | Automated formatting, import sorting, type checking |
| **Logging** | python-json-logger | Latest | Structured JSON logging for debugging |
| **LLM API** | google-generativeai | 0.3.0 | Gemini API integration |
| **Frontend** | Bootstrap 5 | Latest | CSS framework; already in codebase |

---

## Project Structure

```
tranotra-leads/
├── pyproject.toml                    # Poetry: dependencies, scripts, metadata
├── pytest.ini                        # pytest configuration
├── .env.example                      # Environment variables template
├── Makefile                          # Development commands
│
├── src/
│   └── tranotra/                     # Main package
│       ├── __main__.py               # CLI entry point: python -m tranotra
│       ├── __init__.py
│       ├── cli.py                    # Click CLI commands
│       ├── config.py                 # Configuration loading
│       │
│       ├── core/                     # ★ ONION CORE: Business logic
│       │   ├── models/
│       │   │   ├── company.py        # Company SQLAlchemy model
│       │   │   ├── contact.py        # Contact model
│       │   │   └── email.py          # Email model
│       │   ├── services/
│       │   │   ├── scoring.py        # 16-point scoring logic
│       │   │   └── validation.py     # Data validation
│       │   └── exceptions.py         # Custom exceptions
│       │
│       ├── pipeline/                 # ★ REUSABLE PIPELINE MODULES
│       │   ├── discover.py           # Stage 1: Gemini discovery
│       │   ├── profile.py            # Stage 2: Website scraping
│       │   ├── contacts.py           # Stage 3: Apollo + Hunter
│       │   ├── score.py              # Stage 4: Scoring + filtering
│       │   ├── draft_email.py        # Stage 5: Gemini email generation
│       │   ├── review.py             # Stage 6: CLI review
│       │   └── send.py               # Stage 7: DirectMail sending
│       │
│       ├── infrastructure/           # ★ EXTERNAL INTEGRATIONS
│       │   ├── database.py           # SQLAlchemy session + init_db()
│       │   ├── gemini_client.py      # Gemini API wrapper
│       │   ├── apollo_client.py      # Apollo API wrapper
│       │   ├── hunter_client.py      # Hunter API wrapper
│       │   ├── aliyun_client.py      # DirectMail wrapper
│       │   ├── logger.py             # Logging setup
│       │   └── api_client_base.py    # Base class for all clients
│       │
│       ├── presentation/             # ★ ONION OUTER LAYER: Interfaces
│       │   ├── app.py                # Flask app factory
│       │   ├── blueprints/
│       │   │   ├── search.py         # /api/search routes
│       │   │   ├── dashboard.py      # /dashboard + /api/companies
│       │   │   └── emails.py         # /api/emails review routes
│       │   ├── templates/
│       │   │   ├── base.html         # Base template
│       │   │   ├── index.html        # Home page
│       │   │   └── dashboard.html    # Dashboard page
│       │   └── static/
│       │       ├── css/
│       │       │   └── bootstrap.min.css
│       │       └── js/
│       │           └── dashboard.js
│       │
│       └── utils/                    # Shared helpers
│           ├── parsers.py            # Gemini response parsing
│           └── normalizers.py        # URL normalization
│
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_scoring.py
│   │   ├── test_parsers.py
│   │   └── test_validators.py
│   ├── integration/
│   │   ├── test_pipeline_discover.py
│   │   ├── test_pipeline_profile.py
│   │   └── test_db_operations.py
│   └── fixtures/
│       ├── gemini_responses.py       # Mock Gemini responses
│       └── sample_data.py            # Fixture data
│
├── docs/
│   ├── ARCHITECTURE.md               # Architecture guide
│   ├── API_INTEGRATION.md            # API-specific docs
│   └── DEVELOPMENT.md                # Setup + local dev
│
├── logs/                             # Runtime logs (gitignore'd)
│   └── .gitkeep
│
├── db/                               # SQLite database (gitignore'd)
│   └── .gitkeep
│
└── .github/workflows/
    └── ci.yml                        # GitHub Actions CI
```

---

## Implementation Roadmap (M0-M9)

### M0: Setup (Week 1, Day 1-2)
- Initialize Poetry project with pyproject.toml
- Create directory structure (src/tranotra/, tests/, docs/)
- Set up infrastructure/database.py with SQLAlchemy
- Configure .env.example + config.py

### M1: Database (Week 1, Day 3-5)
- Define Company, Contact, Email SQLAlchemy models
- Implement init_db() + CRUD operations
- Set up infrastructure/logger.py
- Write unit tests for models

### M2: Discovery (Week 2, Day 1-5)
- Implement infrastructure/gemini_client.py
- Implement utils/parsers.py (JSON/CSV/Markdown detection)
- Implement pipeline/discover.py with lenient parsing
- Write integration tests with mock Gemini

### M3: Profiling (Week 3, Day 1-5)
- Implement pipeline/profile.py with status transitions
- Add website scraping (BeautifulSoup or similar)
- Error logging + stack traces
- Integration tests

### M4: Contacts (Week 4, Day 1-5)
- Implement infrastructure/apollo_client.py + hunter_client.py
- Implement pipeline/contacts.py with API error handling
- Rate limit tracking + quota management
- Integration tests with mock APIs

### M5: Scoring (Week 4, Day 5 & Week 5, Day 1-3)
- Implement core/services/scoring.py (4-factor model)
- Implement pipeline/score.py with threshold filtering
- Unit tests for scoring logic
- Integration tests

### M6: Email Draft (Week 5, Day 4-5 & Week 6, Day 1)
- Implement pipeline/draft_email.py with Gemini
- Personalization logic (company context injection)
- Integration tests

### M7: Review + Send (Week 6, Day 2-4)
- Implement pipeline/review.py (CLI review interface)
- Implement infrastructure/aliyun_client.py
- Implement pipeline/send.py with DirectMail integration
- Batch summary reporting

### M8: Dashboard (Week 6, Day 5 & Week 7, Day 1-3)
- Implement presentation/app.py (Flask app factory)
- Implement presentation/blueprints/*.py (API routes)
- Create presentation/templates/*.html
- Add presentation/static/js/dashboard.js

### M9: Testing + Polish (Week 7, Day 4-5 & Week 8)
- Full test suite (80%+ coverage)
- All APIs mocked via conftest.py
- Code quality (black, isort, mypy)
- Documentation (README, ARCHITECTURE, DEVELOPMENT)

---

## Architectural Layers (Clean Architecture)

### Core Layer (Business Logic)
```
core/models/       — SQLAlchemy ORM models
core/services/     — Pure business logic (scoring, validation)
core/exceptions.py — Custom exceptions
```

Independent of Flask, Click, or external APIs. Easily testable in isolation.

### Pipeline Layer (Domain Logic)
```
pipeline/*.py      — Stage implementations (discover, profile, etc.)
```

Uses Core services; orchestrates external APIs. Handles status transitions.

### Infrastructure Layer (External Integration)
```
infrastructure/*.py — API wrappers, database setup, logging
```

Encapsulates all external dependencies. Exceptions bubble up to pipeline.

### Presentation Layer (User Interface)
```
presentation/app.py         — Flask app factory
presentation/blueprints/*.py — Routes and views
presentation/templates/     — HTML
presentation/static/        — CSS, JavaScript
cli.py                      — Click CLI commands
```

Consumes pipeline results; presents to user (web or CLI).

---

## Key Architectural Decisions by Layer

| Layer | Pattern | Benefits |
|-------|---------|----------|
| **Core** | Pure Functions | Testable without mocks |
| **Pipeline** | Orchestration | Coordinate stages + APIs |
| **Infrastructure** | Wrapper Pattern | Encapsulate external deps |
| **Presentation** | Blueprints (web) + Click (CLI) | Modular, reusable interfaces |

---

**Next:** Read [patterns.md](patterns.md) for consistency rules and implementation standards.
