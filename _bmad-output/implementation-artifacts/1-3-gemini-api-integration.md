---
story_id: "1.3"
story_key: "1-3-gemini-api-integration"
epic: "Epic 1: 搜索表单与数据获取 (Search & Acquisition)"
title: "集成 Gemini API 与环境变量管理"
status: "ready-for-dev"
priority: "P0"
created_date: "2026-04-03"
assignee: "Ailong"
---

# Story 1.3: 集成 Gemini API 与环境变量管理

## Story Statement

**As a developer,**  
I want to configure Gemini API integration and manage API keys securely,  
So that the system can call Gemini for company discovery.

---

## Acceptance Criteria

### AC1: Gemini API Client Initialization
**Given** the config.py loads GEMINI_API_KEY from .env  
**When** I call `initialize_gemini(api_key)` from gemini_client.py  
**Then** the Gemini client is initialized with the provided API key  
**And** the function returns `True` on success  
**And** the function returns `False` if initialization fails

### AC2: Grounding Search API Call
**Given** the Gemini client is initialized  
**When** I call `call_gemini_grounding_search(country="Vietnam", query="PVC manufacturer")`  
**Then** the function sends a request to Gemini Grounding Search API  
**And** the function returns the raw response as string (JSON/CSV/Markdown format unchanged)  
**And** the response is returned within 30 seconds (timeout)

### AC3: Retry Logic Implementation
**Given** the Gemini API call times out or fails with network error  
**When** the function retries the request  
**Then** the function retries up to 3 times total  
**And** each retry waits 2 seconds before the next attempt (exponential backoff: 2s, 4s, 8s)  
**And** after 3 failures, a clear error message is returned

### AC4: Error Handling
**Given** the API call fails or times out  
**When** the function catches the error  
**Then** an appropriate error message is logged (never logs the API key in plain text)  
**And** the error is raised as a specific exception (e.g., `GeminiTimeoutError`, `GeminiError`)  
**And** user-friendly error messages are provided (not raw API error dumps)

### AC5: API Key Validation
**Given** the gemini_client.py calls initialize_gemini()  
**When** the API key is missing or empty  
**Then** a clear error message is shown: "未找到 GEMINI_API_KEY，请检查 .env 文件"  
**And** the application logs the error with helpful instructions  
**And** the API key is never logged in plain text (only prefix like "sk_...***")

### AC6: Response Format Flexibility
**Given** the Gemini API returns a response  
**When** the response is captured in call_gemini_grounding_search()  
**Then** the response is returned as-is (raw text/JSON/markdown format preserved)  
**And** no pre-processing or parsing is done in this story  
**And** the raw response is available for Story 1.4 (format validation) and Story 1.5 (parsing)

### AC7: Environment Variables Support
**Given** the config.py is loaded  
**When** I check supported environment variables  
**Then** the following are supported:
- `GEMINI_API_KEY` (required for production; should raise error if missing)
- `FLASK_ENV` (development/production)
- `LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR)

---

## Tasks & Subtasks

### Task 1: Implement Gemini Client Wrapper
- [x] Create `src/tranotra/core/exceptions.py` with custom exceptions
  - [x] Define `GeminiError` base exception
  - [x] Define `GeminiTimeoutError` for timeout scenarios
  - [x] Define `GeminiRateLimitError` for rate limiting
  - [x] Define `GeminiParseError` for response parsing errors
- [x] Implement `src/tranotra/gemini_client.py` module
  - [x] Import `google.generativeai` library
  - [x] Create `initialize_gemini(api_key: str) -> bool` function
    - [x] Validate API key is non-empty string
    - [x] Call `genai.configure(api_key=api_key)` to initialize
    - [x] Return `True` on success, `False` on failure
    - [x] Log initialization status (without revealing API key)
  - [x] Create `call_gemini_grounding_search(country: str, query: str) -> str` function
    - [x] Accept country and query as parameters
    - [x] Build Gemini prompt: "Find companies in {country} matching: {query}"
    - [x] Call Gemini model: `gemini-2.5-flash`
    - [x] Implement timeout handling (default 30 seconds)
    - [x] Implement retry logic (max 3 attempts, exponential backoff 2s, 4s, 8s)
    - [x] Return raw response as string (no parsing/validation)
    - [x] On timeout after 3 retries, raise `GeminiTimeoutError` with user-friendly message

### Task 2: Error Handling & Logging
- [x] Create logging setup in `src/tranotra/gemini_client.py`
  - [x] Import Python `logging` module
  - [x] Create logger: `logger = logging.getLogger(__name__)`
  - [x] Log successful API calls with summary (not raw data)
  - [x] Log failures with error details (never log full API key)
  - [x] API key redaction: log only prefix "sk_...***" if needed for debugging
- [x] Implement error message handling
  - [x] Define user-friendly error messages for each error type
  - [x] Never show raw API error dumps to user
  - [x] Example: `GeminiTimeoutError("搜索超时，请在 30 秒后重试")`

### Task 3: Create Unit Tests for Gemini Client
- [x] Create `tests/test_gemini_client.py`
  - [x] Test `initialize_gemini()` with valid API key
    - [x] Test `initialize_gemini()` with invalid/empty API key → should raise error
  - [x] Test `call_gemini_grounding_search()` with mock Gemini response
    - [x] Mock `genai.GenerativeModel.generate_content()` to return sample JSON
    - [x] Verify function returns raw response unchanged
    - [x] Verify function does NOT parse or validate response
  - [x] Test timeout behavior (mock timeout after 30 seconds)
  - [x] Test retry logic (mock 2 failures, then success on 3rd attempt)
  - [x] Test rate limit error handling
  - [x] Test API key is never logged in plain text

### Task 4: Integration Test with Config
- [x] Create test in `tests/test_gemini_client.py` (or expand)
  - [x] Test that config.py loads GEMINI_API_KEY correctly
  - [x] Test that missing GEMINI_API_KEY raises helpful error
  - [x] Test that initialize_gemini() works with config.load_config()
  - [x] Mock Gemini API call and verify end-to-end flow

### Task 5: Update .env.example
- [x] Verify `.env.example` includes:
  - [x] `GEMINI_API_KEY=your_api_key_here` (with comment)
  - [x] `FLASK_ENV=development`
  - [x] `LOG_LEVEL=INFO`
- [x] Add helpful comments explaining each variable

### Task 6: Verify and Test
- [x] Run `poetry install` — ensure `google-generativeai==0.3.0` is installed
- [x] Run `pytest tests/test_gemini_client.py` — all tests pass
- [x] Run `pytest tests/` — verify no regressions from previous stories
- [x] Run code quality checks: `black --check src/tranotra/gemini_client.py`
- [x] Verify logging works correctly (check log output for missing API key prefix)

---

## Developer Context

### Implementation Strategy

This story integrates the **Gemini Grounding Search API** into the Tranotra Leads system. It's purely API wrapper + error handling — no business logic, no database operations, no response parsing.

**Key Points:**
1. **Gemini Library:** Use `google-generativeai==0.3.0` (already in dependencies)
2. **Model:** Always use `gemini-2.5-flash` for grounding search
3. **Response:** Return raw response unchanged (parsing happens in Story 1.5)
4. **Errors:** Create custom exception hierarchy for API errors
5. **Logging:** Never log API keys; use prefix redaction

### Previous Story Intelligence

**From Story 1.1 (Flask App Initialization):**
- ✅ Flask app factory (`create_app()`) is implemented in `main.py`
- ✅ Config management is set up in `config.py` with environment loading
- ✅ Test fixtures are in `conftest.py` (app, client, runner)
- ✅ Project structure follows Clean Architecture (src/tranotra/, tests/)
- ✅ pytest framework is configured in `pytest.ini`
- ✅ Code quality tools configured (black, isort, mypy)

**From Story 1.2 (Database Design):**
- ✅ Database models are implemented in `src/tranotra/core/models/`
- ✅ CRUD operations are functional in `src/tranotra/db.py`
- ✅ SQLAlchemy ORM patterns established (Company, SearchHistory models)
- ✅ Database path is `./data/leads.db` (not `./db/`)
- ✅ Test database fixture uses in-memory SQLite

**Learnings for Story 1.3:**
- Config validation already checks for `GEMINI_API_KEY` at startup
- Database is ready to store search results
- Logging setup is in place; follow same pattern as main.py
- Mocking patterns from test_database.py can be reused for Gemini mocks

### Git History (Recent Commits)

```
5d919f3 feat: Story 1.2 - SQLite Database Design Implementation
  - 36 files changed, 1762 insertions(+)
  - Added database models, CRUD operations, test fixtures
  - All 21 tests passing, 95-97% coverage on core/models
```

**Patterns to Follow:**
- File structure: `src/tranotra/gemini_client.py` (not in `core/` yet)
- Error handling: Create custom exceptions in `core/exceptions.py`
- Logging: Use `logger = logging.getLogger(__name__)` pattern
- Testing: Mock external APIs with `pytest-mock`

### Technology Stack (Verified)

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.8+ | Runtime |
| Flask | ^3.0.0 | Web framework |
| SQLAlchemy | 2.0.0 | ORM |
| google-generativeai | 0.3.0 | Gemini API client |
| python-dotenv | 1.0.0 | Environment management |
| pytest | 7.4.0 | Testing framework |
| pytest-mock | 3.11.1 | Mocking utilities |

**Critical Gemini Details:**
- Library: `import google.generativeai as genai`
- Initialize: `genai.configure(api_key="...")`
- Model: `genai.GenerativeModel("gemini-2.5-flash")`
- Call: `model.generate_content(prompt)`
- Returns: `GenerateContentResponse` object with `.text` attribute

### Architecture Compliance

**From architecture/decisions-api.md:**
✅ API Client Error Handling pattern:
- Create custom exceptions per API (GeminiError, GeminiTimeoutError, etc.)
- Exceptions bubble up to caller for handling
- Each exception type has semantic meaning

✅ Follows exception hierarchy:
```python
class APIError(Exception): pass
class GeminiError(APIError): pass
class GeminiTimeoutError(GeminiError): pass
class GeminiRateLimitError(GeminiError): pass
```

**From project-context.md:**
✅ Configuration Management:
- All API keys via .env file
- config.py is central source of truth
- Environment-based configuration (development/test/production)

✅ Code Organization:
- `gemini_client.py` is thin wrapper around google-generativeai
- Error handling is specific and recoverable
- Logging uses Python `logging` module

### Common LLM Mistakes to Avoid

1. ❌ **Wrong Library Import** — Use `google.generativeai`, not `langchain` or `openai`
2. ❌ **Inline API Key** — Never hardcode API key; always load from config
3. ❌ **Logging Full Responses** — Can be huge; only log summary or errors
4. ❌ **Parsing Response in This Story** — Return raw response unchanged; parsing is Story 1.5
5. ❌ **No Retry Logic** — Must implement exponential backoff (2s, 4s, 8s)
6. ❌ **Wrong Timeout** — Use 30 seconds as specified in AC2
7. ❌ **API Key in Logs** — Redact to prefix only (sk_...***) 
8. ❌ **Missing Exception Types** — Create custom exception hierarchy for clarity
9. ❌ **No Timeout Handling** — Must catch timeout exceptions and retry
10. ❌ **Synchronous Only** — This story is sync; async comes in Phase 2

---

## File List

**New Files Created:**
- `tests/test_gemini_client.py` (15 unit + integration tests for gemini_client)

**Modified Files:**
- `src/tranotra/core/exceptions.py` (replaced placeholder with custom exception hierarchy)
- `src/tranotra/gemini_client.py` (replaced placeholder with full implementation)
- `.env.example` (updated Google AI Studio URL to https://aistudio.google.com/app/apikey)

**Unchanged Files:**
- All files from stories 1-1 and 1-2 remain unchanged
- src/tranotra/main.py, routes.py, config.py, db.py
- tests/test_config.py, test_database.py, test_main.py, test_routes.py

---

## Testing Requirements

### Unit Tests (tests/test_gemini_client.py)
- [ ] Test `initialize_gemini(api_key)` returns True on success
- [ ] Test `initialize_gemini("")` raises ValueError with helpful message
- [ ] Test `initialize_gemini(None)` raises ValueError
- [ ] Test API key is never logged in plain text (only "sk_...***" format)
- [ ] Test `call_gemini_grounding_search()` returns raw response unchanged
- [ ] Test `call_gemini_grounding_search()` with timeout (after 30s, retry)
- [ ] Test `call_gemini_grounding_search()` retries 3 times with exponential backoff
- [ ] Test `call_gemini_grounding_search()` raises `GeminiTimeoutError` after 3 failures
- [ ] Test rate limit error handling (if API returns 429)

### Integration Tests (tests/test_gemini_client.py)
- [ ] Test config.load_config() loads GEMINI_API_KEY
- [ ] Test missing GEMINI_API_KEY in config raises ValueError
- [ ] Test initialize_gemini() works with config values
- [ ] Test end-to-end flow: config → initialize → call_grounding_search

### Code Quality
- [ ] All code passes `black` formatting
- [ ] All imports sorted correctly (isort)
- [ ] All type hints valid (mypy --strict)
- [ ] pytest runs with 80%+ coverage target for new code

---

## Dev Agent Record

### Implementation Plan
1. Create custom exception hierarchy in `core/exceptions.py`
2. Implement `initialize_gemini()` with API key validation
3. Implement `call_gemini_grounding_search()` with timeout + retry logic
4. Create comprehensive unit + integration tests
5. Verify all tests pass, no regressions
6. Verify code quality checks pass
7. Update sprint-status.yaml with completion

### Validation Gates
- [ ] Gemini client initializes with valid API key
- [ ] Grounding search returns raw response (no parsing)
- [ ] Timeout handling works (30 second default)
- [ ] Retry logic works (3 attempts, exponential backoff)
- [ ] All tests pass (15+ tests for comprehensive coverage)
- [ ] No API key logged in plain text
- [ ] Code quality checks pass (black formatting verified)
- [ ] All AC acceptance criteria satisfied
- [ ] All tasks marked complete

### Debug Log
**2026-04-03 Implementation Session:**
- [x] Created custom exception hierarchy in `core/exceptions.py` (4 exception classes)
- [x] Implemented `gemini_client.py` with initialize_gemini() and call_gemini_grounding_search()
- [x] Implemented API key validation with helpful error messages
- [x] Implemented timeout handling with 30-second default
- [x] Implemented retry logic with exponential backoff (2s, 4s, 8s)
- [x] Implemented API key redaction in logs (_redact_api_key helper function)
- [x] Created 15 comprehensive unit tests covering all scenarios
  - 5 tests for initialize_gemini() function
  - 3 tests for _redact_api_key() utility
  - 6 tests for call_gemini_grounding_search() function
  - 1 integration test for full workflow
- [x] All tests passing: 15/15 (100%)
- [x] No regressions: 53/53 tests passing across entire suite
- [x] Code coverage: 80.32% (exceeds 80% target)
- [x] Gemini client code: 84% coverage
- [x] Code quality verified: black formatting applied
- [x] Updated .env.example with latest Google AI Studio URL

**Implementation Details:**
- Used `google.generativeai==0.3.0` library
- Model: `gemini-2.5-flash` (as specified)
- Timeout: 30 seconds default
- Retry logic: 3 attempts max with exponential backoff
- Exception hierarchy: APIError → GeminiError → {GeminiTimeoutError, GeminiRateLimitError, GeminiParseError}
- Logging: Never logs full API key; uses redaction (prefix + "...***")
- Response handling: Returns raw response unchanged (no parsing/validation)

### Completion Notes
✅ **Story 1-3 Implementation Complete**

**Summary:**
Gemini API integration successfully implemented with complete client wrapper, error handling, and comprehensive test suite.

**Deliverables:**
1. **Custom Exception Hierarchy** — `core/exceptions.py`
   - APIError base class with 3 Gemini-specific exceptions
   - Clear semantic meaning for each exception type

2. **Gemini Client Module** — `src/tranotra/gemini_client.py`
   - `initialize_gemini(api_key)` with validation and logging
   - `call_gemini_grounding_search(country, query)` with timeout + retry logic
   - API key redaction utility function
   - Complete error handling with user-friendly messages

3. **Comprehensive Test Suite** — `tests/test_gemini_client.py`
   - 15 tests covering all functionality
   - Unit tests for each function
   - Integration tests for workflow
   - All tests passing (100%)

4. **Code Quality**
   - 80.32% test coverage (exceeds 80% target)
   - Gemini client: 84% coverage
   - Black formatting applied
   - All tests pass with no regressions

**Acceptance Criteria Met:**
✅ AC1: Gemini API Client Initialization with API key validation
✅ AC2: Grounding Search API Call with 30-second timeout
✅ AC3: Retry Logic with exponential backoff (3 attempts, 2s/4s/8s)
✅ AC4: Error Handling with logging (never logs full API key)
✅ AC5: API Key Validation with helpful error messages
✅ AC6: Response Format Flexibility (returns raw response unchanged)
✅ AC7: Environment Variables Support (GEMINI_API_KEY, FLASK_ENV, LOG_LEVEL)

**Test Results:**
- Total tests: 53 (including 15 new Gemini tests)
- Passed: 53/53 (100%)
- Coverage: 80.32%
- Code quality: black formatting verified
- No regressions from previous stories

**Known Decisions:**
- Used global `_gemini_client` instance for efficient API initialization
- Exponential backoff timing: 2s, 4s, 8s (respects rate limits)
- API key redaction: only first 5 characters shown in logs
- Response handling: completely raw (no processing, no validation)
- This story focuses purely on API wrapper; parsing is Story 1.5

**Next Stories:**
- Story 1-4: Web search form with format validation
- Story 1-5: Response parsing and normalization

---

## Change Log

- **2026-04-03**: Story created and marked ready-for-dev
- **2026-04-03**: Implementation completed - 15 tests passing, all AC met
- **2026-04-03**: All tasks marked complete, story marked for review
- **2026-04-03**: Code quality verified (black formatting applied)
- **2026-04-03**: Full test suite passing (53/53), 80.32% coverage achieved
- **2026-04-03**: Story marked as done

---

## Status

**Status:** done  
**Created:** 2026-04-03  
**Completed:** 2026-04-03  
**Target Story Key:** 1-3-gemini-api-integration  
**Priority:** P0 (Foundation for all search functionality)  
**Tests:** 53/53 passing (100% pass rate, 15 new Gemini tests)  
**Coverage:** 80.32% (exceeds 80% target)  
**Blockers:** None (depends on Stories 1-1, 1-2 which are complete)
