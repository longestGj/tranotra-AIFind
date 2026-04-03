# Tranotra Leads - Automated Customer Discovery & Outreach Pipeline

![Status](https://img.shields.io/badge/status-Phase%201%20MVP-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.0-green)

Automated customer discovery and outreach pipeline for Tranotra plasticizer suppliers. Searches for potential customers using Gemini AI, gathers contact information, scores leads, and generates personalized outreach emails.

## Features (Phase 1 - MVP)

- 🔍 **Company Discovery** — Search for companies by country & keyword via Gemini API
- 💾 **Database Storage** — Store results in local SQLite database
- 🎯 **Lead Scoring** — Simplified 4-factor prospect scoring model (1-9 scale)
- 📊 **Web Dashboard** — View and manage discovered leads
- 📤 **CSV Export** — Export leads for further processing

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Flask | 2.3.0 |
| **ORM** | SQLAlchemy | 2.0.0 |
| **Database** | SQLite | 3.x |
| **AI/LLM** | Gemini API | 2.5-flash |
| **Testing** | pytest | 7.4.0 |
| **Code Quality** | black, isort, mypy | Latest |
| **Python** | 3.8+ | - |

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Poetry (dependency manager)
- Gemini API key (get from [Google AI Studio](https://makersuite.google.com/))

### Installation

```bash
# 1. Clone the repository
cd tranotra-leads

# 2. Install dependencies with Poetry
poetry install

# 3. Create .env file from template
cp .env.example .env

# 4. Add your GEMINI_API_KEY to .env
# Edit .env and set: GEMINI_API_KEY=your-key-here
```

### Running the Application

```bash
# Start the Flask development server
poetry run flask run
# Or using make:
make run

# Access the application at http://localhost:5000
```

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest
# Or using make:
make test

# Run specific test file
poetry run pytest tests/test_main.py -v

# Generate coverage report
poetry run pytest --cov=src/tranotra --cov-report=html
```

### Code Quality Checks

```bash
# Format code with black
poetry run black src/ tests/

# Sort imports with isort
poetry run isort src/ tests/

# Type checking with mypy
poetry run mypy src/

# All checks together
make lint
make format
```

## Project Structure

```
tranotra-leads/
├── src/tranotra/              # Main application package
│   ├── main.py                # Flask app factory
│   ├── config.py              # Configuration management
│   ├── routes.py              # Flask routes (Blueprint)
│   ├── db.py                  # Database models (Story 1.2)
│   ├── gemini_client.py       # Gemini API wrapper (Story 1.3)
│   ├── parser.py              # Data parsing (Story 1.5)
│   ├── core/                  # Business logic layer
│   ├── infrastructure/        # External integrations
│   ├── presentation/          # Web interface
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
│   ├── conftest.py            # Shared fixtures
│   └── fixtures/              # Test data
├── templates/                 # HTML templates
├── static/                    # CSS/JS assets
├── db/                        # SQLite databases
├── logs/                      # Application logs
├── pyproject.toml             # Poetry configuration
└── README.md                  # This file
```

## Development Roadmap

### Phase 1 (MVP) ✅ In Progress
- [x] Story 1.1: Flask Application Initialization (THIS STORY)
- [ ] Story 1.2: SQLite Database Design
- [ ] Story 1.3: Gemini API Integration
- [ ] Story 1.4: Web Search Form & Format Validation
- [ ] Story 1.5: Data Parsing & Normalization
- [ ] Story 2.1-2.5: Results Display & Export
- [ ] Story 3.1-3.4: Analytics Dashboard
- [ ] Story 4.1-4.2: Error Handling & Optimization

### Phase 2+ (Future)
- Async pipeline with queueing
- Circuit breaker pattern for APIs
- Full 16-point scoring model
- Real-time dashboard refresh
- Batch job scheduling (APScheduler)
- Multi-user support
- Email campaign tracking

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and set the following:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | development | Flask environment (development/testing/production) |
| `FLASK_DEBUG` | No | False | Enable Flask debug mode |
| `FLASK_HOST` | No | 0.0.0.0 | Flask server host |
| `FLASK_PORT` | No | 5000 | Flask server port |
| `DATABASE_URL` | No | sqlite:///./data/tranotra_leads.db | Database connection URL |
| `GEMINI_API_KEY` | **Yes** | (none) | Google Gemini API key |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Database Configuration

SQLite is stored locally at `./data/tranotra_leads.db` by default. No external database required.

## API Endpoints (Phase 1)

### Health Check
```
GET /
Response: {"status": "healthy", "version": "1.0"}
```

### Search API (Phase 1.4+)
```
POST /api/search/
Request: {"country": "Vietnam", "keyword": "PVC manufacturer"}
Response: {"success": true, "data": {...}, "error": null}
```

## Testing Strategy

- **Unit Tests** — Test individual functions in isolation
- **Integration Tests** — Test component interactions
- **Coverage Target** — 80%+ code coverage
- **Fixtures** — Shared test data and mocks (see `tests/conftest.py`)

## Known Limitations (Phase 1)

1. **No async processing** — API calls are synchronous
2. **No job scheduling** — Manual execution only
3. **Simplified scoring** — 4-factor model (expands to 16-point in Phase 2)
4. **No encryption** — Local SQLite, user responsible for data security
5. **Single user** — Not designed for multi-user access

## Contributing

See `DEVELOPMENT.md` for setup and development guidelines.

## License

MIT License — See LICENSE file

## Author

Ailong — 2026

## Support

For issues, questions, or feedback:
1. Check existing documentation in `docs/`
2. Review test files for usage examples
3. Check architecture decisions in `_bmad-output/planning-artifacts/architecture/`

---

**Status:** Phase 1 MVP - Story 1.1 Complete ✅
