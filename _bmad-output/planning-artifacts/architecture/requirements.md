---
title: "Requirements & Constraints"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Requirements & Constraints

---

## Functional Requirements

### 10 Modules Across 5 Stages

1. **Discovery** — Gemini Grounding Search to find companies by market + keywords
2. **Profiling** — Website scraping + Gemini analysis to enrich company data
3. **Contact Finding** — Apollo + Hunter API to find decision-maker emails
4. **Scoring** — 16-point rubric to prioritize prospects
5. **Email Generation** — Gemini template → personalized email drafts
6. **Manual Review** — CLI interface for human approval before send
7. **Email Sending** — Aliyun DirectMail SDK to dispatch emails
8. **Dashboard** — Web UI for analytics + company/contact management
9. **Batch CLI** — Command-line interface for automated pipeline runs
10. **Data Export** — CSV export for external tools (Excel, CRM, etc.)

### Data Model

**3 Core Tables:**

- **companies** (23 fields)
  - ID, name, country, city, year_established, employees
  - estimated_revenue, main_products, export_markets, eu_us_jp_export
  - raw_materials, recommended_product, recommendation_reason
  - website, contact_email, linkedin_url, linkedin_normalized (dedup key)
  - best_contact_title, prospect_score, priority
  - source_query (search context), status (workflow state)
  - created_at, updated_at

- **contacts** (per company, email verification)
  - ID, company_id, name, title, email, phone
  - email_verified, verification_source (apollo/hunter/manual)
  - created_at, updated_at

- **emails** (workflow tracking)
  - ID, contact_id, company_id, subject, body
  - template_used, personalization_tokens
  - status (pending_review → approved → sent → bounced/open)
  - created_at, sent_at, open_count, click_count

### External Integrations

1. **Gemini Grounding Search** — Discovery + analysis + email drafting
2. **Apollo.io** — Find decision-maker contacts (3 result limit per company)
3. **Hunter.io** — Email verification (up to 100/month free)
4. **Aliyun DirectMail** — Email dispatch (bulk sending with tracking)

### Workflow & User Flows

- **Manual execution:** User runs stages via CLI (`python main.py --run discover`, etc.)
- **Human gating:** Emails must be approved before sending (no auto-send in Phase 1)
- **Resumable:** Can re-run any stage on failed records without re-processing successful ones
- **Dual interface:** Both CLI (automation) and web dashboard (analytics/review)

---

## Non-Functional Requirements

### Local Execution
- ✅ No cloud scheduling; user runs pipeline on their local machine
- ✅ No external job queue or message broker required
- ✅ Works offline (except API calls to Gemini/Apollo/Hunter/Aliyun)

### Data Persistence
- ✅ SQLite 3.x local database at `./db/tranotra_leads.db`
- ✅ All pipeline stages produce atomic writes (transactional safety)
- ✅ Data available for export (CSV, JSON) anytime

### API Resilience (Phase 1)

**Phase 1 (MVP):**
- ✅ Basic retry logic with exponential backoff (1s → 2s → 4s)
- ✅ Timeout handling (default 30s per request)
- ✅ Rate limit detection and warning (but no queuing)
- ✅ Synchronous blocking calls (simple, deterministic)

**Known Limitations (Phase 2+):**
- ⏳ Circuit breaker pattern (auto-disable failing APIs)
- ⏳ Persistent queueing (retry on failure)
- ⏳ Async/concurrent API calls
- ⏳ Graceful degradation (skip stage if API unavailable)

### Test Coverage

- ✅ Target: 80%+ code coverage
- ✅ All external APIs mocked in test suite
- ✅ Shared fixtures in `conftest.py`
- ✅ Unit tests for business logic (scoring, parsing, normalization)
- ✅ Integration tests for pipeline stages
- ✅ Database tests (CRUD operations, constraints)

### Format Flexibility

- ✅ Gemini responses may be JSON, CSV, or Markdown
- ✅ Parser auto-detects format
- ✅ Lenient parsing: incomplete/malformed data accepted (log for debugging)
- ✅ Missing fields filled with "N/A" (batch continues)

### Logging & Observability

- ✅ Python `logging` module to `./logs/pipeline.log`
- ✅ Structured JSON log format for machine parsing
- ✅ Configurable via `LOG_LEVEL` environment variable
- ✅ All API calls logged with timestamp + duration + status
- ✅ Errors logged with full context (record data, error details, stack trace)

### Idempotency & Safety

- ✅ Safe to re-run any stage without data corruption
- ✅ Deduplication on LinkedIn URL (normalized key) prevents duplicates
- ✅ Status field tracks which stage each record completed
- ✅ Failed records marked with `_failed` status (e.g., `profile_failed`) for retry

---

## Technical Constraints & Dependencies

### Language & Runtime
- **Python:** 3.8+ required (f-strings, type hints, asyncio-ready)

### Framework & Libraries
- **Framework:** Flask 2.3.0 (web interface)
- **ORM:** SQLAlchemy 2.0.0 (ORM + relationship management)
- **WSGI:** Werkzeug 2.3.0 (included in Flask)
- **CLI:** Click framework (modern, composable commands)
- **Dependency Management:** Poetry (reproducible builds, lock file)

### Database
- **Database:** SQLite 3.x (file-based, no external DB dependency)
- **Transactions:** SQLAlchemy session management
- **Migrations:** Optional (Phase 2+); manual schema updates for Phase 1

### AI/LLM
- **API:** Gemini Grounding Search via `google-generativeai` 0.3.0
- **Model:** Pinned to `gemini-2.5-flash` (confirmed working 2026-03-31)
- **Features:** Google Search Grounding for real-time web data

### External APIs
- **Apollo.io** — Person search API (requires account)
- **Hunter.io** — Email verification (requires account)
- **Aliyun DirectMail** — Email dispatch (requires SDK + account)

### User Prerequisites
- ✅ Already has configured accounts for Gemini, Apollo, Hunter, Aliyun
- ✅ API keys available (stored in `.env` file)
- ✅ Local machine (Windows/Mac/Linux) with Python 3.8+

---

## Scale & Complexity Assessment

### Complexity Level
**Medium-High:**
- Multi-stage pipeline coordination
- Multi-API integration (4 external services)
- Complex scoring logic (16-point rubric with thresholds)
- Dual interface layers (CLI + Flask web)

### Architectural Components
- 10 functional modules
- 4 API client wrappers
- 2 interface layers (CLI + Flask)
- 3 database entities (companies, contacts, emails)
- 3+ pipeline stages (discover, profile, contacts, score, draft, review, send)

### Cross-Cutting Concerns

1. **API Integration Pattern**
   - Consistent retry logic + timeout handling
   - Specific exception types per API
   - Rate limit tracking + warnings
   - All in `infrastructure/api_client_base.py`

2. **Deduplication Logic**
   - LinkedIn URL normalization at insertion
   - Prevents duplicate processing across all stages
   - Core algorithm in `utils/normalizers.py`

3. **Prospect Scoring**
   - Shared rubric used by multiple stages
   - Affects data flow decisions (score < 6 = skip contacts/email)
   - Central logic in `core/services/scoring.py`

4. **Error Recovery**
   - Granular logging (all errors recorded)
   - Batch checkpointing (Phase 2+)
   - User-facing error messages + recovery suggestions

5. **Configuration Management**
   - All API keys, endpoints, search queries, product context
   - Centralized in `config.py` (loaded from `.env`)
   - Different configs per environment (dev, test, prod)

---

## Phase 1 vs. Phase 2+ Scope

### Phase 1 (MVP) — Focused Scope

✅ **Included:**
- Gemini-only discovery (no website scraping)
- Basic web dashboard (card view + table view)
- Manual email review (no auto-send)
- CSV export (read-only)
- Local SQLite (no multi-user)

❌ **Deferred to Phase 2+:**
- Apollo.io + Hunter.io integration (contact finding)
- Website scraping + profile enrichment
- Email generation + personalization
- Aliyun DirectMail sending
- Built-in scheduler
- Async/concurrent processing
- Circuit breaker + graceful degradation

### Rationale for Phase 1 Scope

1. **MVP Validation** — Validate demand with LinkedIn-only search first
2. **Time to Market** — Reduce complexity; ship faster
3. **Cost Control** — Minimize external API costs (Gemini free tier available)
4. **User Feedback** — Gather feedback before building full pipeline

---

## Summary of Constraints

| Category | Constraint | Impact |
|----------|-----------|--------|
| **Execution** | Local-only (no cloud) | Simple deployment; user controls timing |
| **Database** | SQLite (single file) | No multi-user; no distributed transactions |
| **API** | Sync calls (Phase 1) | Blocking I/O; simpler to implement |
| **Error Handling** | Record-level (fail-soft) | Batch continues on failures; orphaned records Phase 2 |
| **Interfaces** | CLI + Flask only | No REST API (Phase 2+); no WebSockets |
| **Scope** | Gemini discovery only | No contact finding Phase 1; no email sending |
| **Test Coverage** | 80%+ target | All APIs mocked; no live API tests Phase 1 |
| **Performance** | Single-threaded | OK for ~1000 companies/batch; async Phase 2 |

---

**Next:** Read [decisions-core.md](decisions-core.md) to understand how these requirements are addressed architecturally.
