---
story_id: "1.4"
story_key: "1-4-gemini-grounding-search"
epic: "Epic 1: 搜索表单与数据获取 (Search & Acquisition)"
title: "实现 Gemini Grounding Search 调用与格式验证"
status: "review"
priority: "P0"
created_date: "2026-04-04"
assignee: "Ailong"
---

# Story 1.4: 实现 Gemini Grounding Search 调用与格式验证

## Story Statement

**As a user,**  
I want to search for companies by entering country and keyword,  
So that I can discover potential customers automatically.

---

## Acceptance Criteria

### AC1: Search Form Display on Home Page
**Given** the Flask application is running  
**When** I navigate to the home page (/)  
**Then** I see a search form with:
- Country dropdown selector with options: Vietnam, Thailand, Indonesia, UAE, Saudi Arabia
- Keyword text input field with placeholder "例如: cable mfg, synthetic leather, flooring export"
- Search button labeled "🔍 搜索"
- Example text below the form

### AC2: Search Request Submission
**Given** the search form is displayed  
**When** I select "Vietnam" and enter "PVC manufacturer", then click "搜索"  
**Then** the search button becomes disabled
**And** the button shows loading text "搜索中..."
**And** a spinner is displayed

### AC3: Rate Limit Compliance (2-Second Delay)
**Given** the user submits a search request  
**When** the system processes the request  
**Then** a 2-second delay is enforced before calling Gemini API
**And** the user sees countdown text: "准备搜索 (2秒延迟)" → "准备搜索 (1秒延迟)" → "准备搜索中..."
**And** the search button remains disabled during countdown

### AC4: Gemini Grounding Search API Call
**Given** the 2-second delay has elapsed  
**When** the system calls Gemini Grounding Search API  
**Then** the request includes:
- Country: "Vietnam"
- Query: "PVC manufacturer"
- Timeout: 30 seconds
**And** the function returns the raw response from Story 1.3's `call_gemini_grounding_search()`
**And** no response parsing or validation happens in this story

### AC5: Format Detection (JSON / Markdown / CSV)
**Given** the Gemini API returns a response  
**When** the response is received  
**Then** the system detects the response format:
- JSON format: detect `{` at start or `[` for arrays
- Markdown table format: detect `|` table delimiters and `---` separators
- CSV format: detect comma/tab-separated values with header row
**And** the detected format is logged for debugging: `"Response format detected: JSON"`

### AC6: Valid Format Handling
**Given** the response format is detected as valid (JSON / Markdown / CSV)  
**When** validation completes  
**Then** a success message is shown: "搜索成功，正在处理结果..."
**And** the raw response is stored temporarily for Story 1.5
**And** the system transitions to parsing (Story 1.5) automatically
**And** the search form is reset for the next search

### AC7: Invalid Format Handling
**Given** the response format is not recognized or unparseable  
**When** format validation fails  
**Then** a user-friendly error message is shown: "搜索失败：格式错误，请稍后重试"
**And** the raw response is logged for debugging (without exposing to user)
**And** the search button is re-enabled
**And** the user can retry the search

### AC8: Timeout Handling
**Given** the Gemini API call takes longer than 30 seconds  
**When** the timeout is reached  
**Then** an error message is shown: "搜索超时，请重试"
**And** the search button is re-enabled
**And** the user can retry the search

### AC9: Search Statistics Display
**Given** the home page is loaded  
**When** I view the page  
**Then** I see search statistics from the search_history table:
- 📊 今日统计: 搜索 X 次 | 新增 Y 家 | 去重率 Z%
**And** statistics are calculated from today's searches only

### AC10: API Key Validation
**Given** the search form is submitted  
**When** the system calls `initialize_gemini()` from Story 1.3  
**Then** if GEMINI_API_KEY is missing or invalid, a helpful error message is shown
**And** the search button is re-enabled for retry

---

## Tasks & Subtasks

### Task 1: Implement Search Form HTML Template
- [x] Create/update `templates/index.html` with:
  - [ ] Form with country dropdown, keyword input, search button
  - [ ] Loading spinner (hidden by default, shown during request)
  - [ ] Countdown text for 2-second delay (hidden by default)
  - [ ] Error message container (hidden by default)
  - [ ] Success message container (hidden by default)
  - [ ] Search statistics section (populated from database)
- [x] CSS styling for form, spinner, and messages
- [x] Example text with industry keywords

### Task 2: Implement Flask Route for Search Endpoint
- [x] Create/update `GET /` route to display home page with search form
  - [ ] Query search_history table for today's statistics
  - [ ] Calculate: total searches, new companies count, dedup rate
  - [ ] Render template with statistics
- [x] Create `POST /api/search` route to handle search requests:
  - [ ] Extract `country` and `keyword` from form data
  - [ ] Validate inputs (non-empty country, non-empty keyword)
  - [ ] Return JSON response with `status`, `message`

### Task 3: Implement Frontend JavaScript for UX
- [x] Create `static/js/search.js`:
  - [ ] On form submit, prevent default, extract country + keyword
  - [ ] Disable search button and show "搜索中..." text
  - [ ] Start 2-second countdown timer with "准备搜索 (2s)" → "准备搜索 (1s)" → "准备搜索中..."
  - [ ] After countdown, call `POST /api/search` with AJAX
  - [ ] On success, show "搜索成功，正在处理结果..." message
  - [ ] On error, show error message and re-enable button
  - [ ] On timeout (> 30s), show "搜索超时，请重试" and re-enable button

### Task 4: Implement Format Detection Logic
- [x] Create function `detect_response_format(response: str) -> str` in `routes.py`:
  - [ ] Check if response starts with `{` or `[` → return "JSON"
  - [ ] Check if response contains `|` and `---` patterns → return "Markdown"
  - [ ] Check if response contains comma/tab-separated values → return "CSV"
  - [ ] If no format detected → return "UNKNOWN"
- [x] Log detected format: `logger.info(f"Response format detected: {format}")`

### Task 5: Implement Search API Handler
- [x] Create route handler `/api/search` that:
  - [ ] Calls `initialize_gemini(api_key)` with API key from config
  - [ ] Handles missing/invalid API key → return 500 error with helpful message
  - [ ] Calls `call_gemini_grounding_search(country, keyword)` from Story 1.3
  - [ ] Handles timeout (> 30s) → return error with "搜索超时，请重试"
  - [ ] Receives raw response from Gemini (already done in Story 1.3)
  - [ ] Calls `detect_response_format(response)` to validate format
  - [ ] If format valid → return JSON: `{"status": "success", "format": "JSON", "message": "搜索成功，正在处理结果..."}`
  - [ ] If format invalid → return JSON: `{"status": "error", "message": "搜索失败：格式错误，请稍后重试"}`
  - [ ] If timeout → return JSON: `{"status": "timeout", "message": "搜索超时，请重试"}`
  - [ ] Log all actions with context (country, keyword, format, errors)

### Task 6: Implement Search Statistics Calculation
- [x] Create function `get_today_statistics()` in `db.py`:
  - [ ] Query `search_history` table for searches created today (CURRENT_DATE)
  - [ ] Calculate:
    - [ ] `total_searches` = COUNT(*) for today's searches
    - [ ] `total_new_companies` = SUM(new_count) for today's searches
    - [ ] `total_duplicates` = SUM(duplicate_count) for today's searches
    - [ ] `dedup_rate` = (total_duplicates / (total_new_companies + total_duplicates)) * 100
  - [ ] Return dict: `{"searches": X, "new_companies": Y, "dedup_rate": Z}`
- [x] Update `GET /` route to call this function and pass to template

### Task 7: Create Comprehensive Tests
- [x] Create `tests/test_search_form.py`:
  - [ ] Test home page loads successfully (GET /)
  - [ ] Test search statistics are calculated correctly from search_history table
  - [ ] Test search statistics display "0" when no searches today
- [x] Create `tests/test_search_api.py`:
  - [ ] Test `POST /api/search` with valid country and keyword
  - [ ] Test format detection for JSON responses
  - [ ] Test format detection for Markdown responses
  - [ ] Test format detection for CSV responses
  - [ ] Test format detection for invalid/unknown formats
  - [ ] Test missing country field → return 400 error
  - [ ] Test missing keyword field → return 400 error
  - [ ] Test API key missing → return 500 error with helpful message
  - [ ] Test timeout scenario (mock Gemini API to timeout)
  - [ ] Test Gemini API error → return 500 with user-friendly message
- [x] Create `tests/test_format_detection.py`:
  - [ ] Test JSON format detection with various JSON structures
  - [ ] Test Markdown table format detection
  - [ ] Test CSV format detection
  - [ ] Test edge cases (whitespace, malformed data, empty responses)
- [x] Create `tests/test_statistics.py`:
  - [ ] Test `get_today_statistics()` with sample search_history data
  - [ ] Test dedup rate calculation accuracy
  - [ ] Test statistics with no data
- [x] All tests should mock Gemini API and database calls as needed

### Task 8: Integration Testing
- [x] Test end-to-end flow: form submit → rate limit delay → API call → format detection → success response
- [x] Test error scenarios: invalid input, API key missing, timeout, format error
- [x] Test with real database (using test database fixture)

### Task 9: Code Quality & Verification
- [x] Run `pytest tests/test_search_form.py tests/test_search_api.py tests/test_format_detection.py tests/test_statistics.py` — all tests pass
- [x] Run `pytest tests/` — verify no regressions from previous stories
- [x] Run code quality checks: `black --check src/tranotra/routes.py` and `black --check static/js/search.js`
- [x] Verify logging outputs (no sensitive data logged)
- [x] Verify statistics calculation accuracy with sample data

---

## Developer Context

### Implementation Strategy

This story bridges the backend API (Story 1.3) with the frontend UX and format validation. Key points:

1. **Frontend Form:** Simple HTML form with jQuery/vanilla JS for UX
2. **Rate Limiting:** 2-second delay enforced via frontend countdown + backend can add delay if needed
3. **Format Detection:** Simple string matching (not full parsing) — parsing happens in Story 1.5
4. **Error Handling:** User-friendly messages, graceful degradation
5. **Statistics:** Query search_history table for aggregates

### Architecture Compliance

**From decisions-api.md:**
✅ Pipeline Stage Communication (status field approach)
✅ API Error Handling (exceptions bubble up from Story 1.3)

**From project-context.md:**
✅ Technology Stack: Flask 2.3.0, SQLAlchemy 2.0.0, google-generativeai 0.3.0
✅ Database: SQLite at `./data/leads.db` (confirmed from Story 1.2)
✅ Testing: pytest 7.4.0 with fixtures from conftest.py
✅ Configuration: Environment variables via .env and config.py

### Previous Story Intelligence

**From Story 1.3 (Gemini API Integration):**
- ✅ `initialize_gemini(api_key: str) -> bool` is implemented and tested
- ✅ `call_gemini_grounding_search(country: str, query: str) -> str` returns raw response
- ✅ Timeout handling: 30-second default already implemented
- ✅ Retry logic: 3 attempts with exponential backoff (2s, 4s, 8s)
- ✅ Custom exceptions: GeminiError, GeminiTimeoutError, GeminiRateLimitError
- ✅ Logging pattern: never log API keys in plain text

**From Story 1.2 (Database Design):**
- ✅ `search_history` table exists with fields: country, query, result_count, new_count, duplicate_count, avg_score, high_priority_count, created_at
- ✅ `get_search_history(limit: int = 20) -> list` function available in db.py
- ✅ CRUD functions follow pattern: function returns data or None on error

**From Story 1.1 (Flask Setup):**
- ✅ Flask app factory: `create_app()` in main.py
- ✅ Routes defined in routes.py
- ✅ Template directory: `templates/`
- ✅ Static assets directory: `static/`
- ✅ Config loading via config.py

### File Structure

**New Files to Create:**
- `templates/index.html` (or update if exists)
- `static/js/search.js` (new JavaScript for frontend UX)
- `tests/test_search_form.py` (tests for home page route)
- `tests/test_search_api.py` (tests for search API endpoint)
- `tests/test_format_detection.py` (tests for format detection logic)
- `tests/test_statistics.py` (tests for statistics calculation)

**Modified Files:**
- `src/tranotra/routes.py` (add GET / and POST /api/search routes)
- `src/tranotra/db.py` (add get_today_statistics() function)

**Unchanged Files:**
- All files from stories 1-1, 1-2, 1-3 remain unchanged
- src/tranotra/main.py, config.py, gemini_client.py
- tests/test_config.py, test_database.py, test_gemini_client.py, test_main.py

### Technology Stack (Verified)

| Technology | Version | Purpose | Verified |
|---|---|---|---|
| Flask | 2.3.0 | Web framework, routing | ✅ Story 1.1 |
| SQLAlchemy | 2.0.0 | ORM, database queries | ✅ Story 1.2 |
| google-generativeai | 0.3.0 | Gemini API client | ✅ Story 1.3 |
| pytest | 7.4.0 | Testing framework | ✅ All stories |
| Jinja2 | (Flask dep) | Template rendering | ✅ Flask |

**Frontend (Optional):**
- Vanilla JavaScript (no jQuery required)
- HTML5 form elements
- CSS for styling

### Git History Intelligence

**Recent commits (from Story 1.3):**
```
e89782a Merge pull request #2 from longestGj/feature/story-1-3-gemini-api-integration
3753122 Mark story 1-3 complete with all code review patches applied
291fffe Fix critical issues in Gemini API integration and test mocking
```

**Patterns to follow:**
- File structure: `src/tranotra/` for source, `tests/` for tests
- Logging: use `logger = logging.getLogger(__name__)` pattern
- Testing: mock external APIs with `pytest-mock`
- Git commits: feature branch per story, merge to master after code review

### Common Mistakes to Avoid

1. ❌ **Frontend sends Gemini API key** — Never expose API key to frontend! Always call backend route
2. ❌ **Parsing in this story** — Only detect format, don't parse. Parsing is Story 1.5
3. ❌ **No rate limiting** — Must enforce 2-second delay before API call
4. ❌ **Ignoring timeout** — Story 1.3 handles timeout, but story 1.4 must handle error response
5. ❌ **Format detection too strict** — Be lenient; simple pattern matching is OK
6. ❌ **No error logging** — Log all API calls, errors, timeouts for debugging
7. ❌ **User sees raw error** — Always wrap errors in user-friendly messages
8. ❌ **Form not disabled** — Button must be disabled during request to prevent double-submit
9. ❌ **No statistics on home page** — Must query search_history for today's aggregates
10. ❌ **Missing test coverage** — Aim for 80%+ coverage on new routes and functions

### Example Implementation Sketch (Not Required)

```python
# routes.py
@app.route('/', methods=['GET'])
def home():
    stats = db.get_today_statistics()  # {"searches": 5, "new_companies": 42, "dedup_rate": 15.2}
    return render_template('index.html', stats=stats)

@app.route('/api/search', methods=['POST'])
def search():
    country = request.form.get('country', '').strip()
    keyword = request.form.get('keyword', '').strip()
    
    if not country or not keyword:
        return jsonify({"status": "error", "message": "国家和关键词不能为空"}), 400
    
    try:
        # Call Story 1.3
        if not initialize_gemini(api_key):
            return jsonify({"status": "error", "message": "API密钥配置错误"}), 500
        
        response = call_gemini_grounding_search(country, keyword)
        
        # Detect format
        fmt = detect_response_format(response)
        if fmt == "UNKNOWN":
            return jsonify({"status": "error", "message": "搜索失败：格式错误，请稍后重试"}), 400
        
        logger.info(f"Search successful: country={country}, format={fmt}")
        return jsonify({"status": "success", "format": fmt, "message": "搜索成功，正在处理结果..."})
    
    except GeminiTimeoutError:
        return jsonify({"status": "timeout", "message": "搜索超时，请重试"}), 500
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"status": "error", "message": "搜索失败，请稍后重试"}), 500
```

```html
<!-- templates/index.html -->
<form id="searchForm">
  <select name="country" required>
    <option value="">请选择国家</option>
    <option value="Vietnam">Vietnam</option>
    <option value="Thailand">Thailand</option>
    <!-- ... -->
  </select>
  
  <input type="text" name="keyword" placeholder="例如: cable mfg, synthetic leather, flooring export" required>
  
  <button type="submit" id="searchBtn">🔍 搜索</button>
  
  <div id="countdown" style="display: none;">准备搜索 (2秒延迟)</div>
  <div id="loading" style="display: none;">
    <span class="spinner"></span> 搜索中...
  </div>
  <div id="errorMsg" style="display: none;"></div>
  <div id="successMsg" style="display: none;"></div>
</form>

<div class="stats">
  📊 今日统计: 搜索 {{ stats.searches }} 次 | 新增 {{ stats.new_companies }} 家 | 去重率 {{ stats.dedup_rate|round(1) }}%
</div>

<script src="/static/js/search.js"></script>
```

---

## Testing Requirements

### Unit Tests

**test_search_form.py:**
- [x] `test_home_page_loads` — GET / returns 200 and contains search form
- [x] `test_home_page_shows_statistics` — GET / includes today's search statistics
- [x] `test_statistics_zero_when_no_searches` — Statistics show 0 when search_history is empty

**test_search_api.py:**
- [x] `test_search_api_with_valid_data` — POST /api/search with valid country and keyword returns success
- [x] `test_search_api_missing_country` — POST /api/search without country returns 400
- [x] `test_search_api_missing_keyword` — POST /api/search without keyword returns 400
- [x] `test_search_api_missing_api_key` — Gemini initialization fails returns 500 with helpful message
- [x] `test_search_api_timeout` — Timeout from Story 1.3 returns error with "搜索超时，请重试"
- [x] `test_search_api_format_detection_json` — Response format detected as JSON returns success
- [x] `test_search_api_format_detection_invalid` — Invalid format returns error with "搜索失败：格式错误，请稍后重试"

**test_format_detection.py:**
- [x] `test_detect_json_format` — Detects `{...}` or `[...]` as JSON
- [x] `test_detect_markdown_format` — Detects `|...|` and `---` as Markdown
- [x] `test_detect_csv_format` — Detects comma/tab-separated values as CSV
- [x] `test_detect_unknown_format` — Unknown format returns "UNKNOWN"
- [x] `test_format_detection_with_whitespace` — Handles leading/trailing whitespace

**test_statistics.py:**
- [x] `test_get_today_statistics_empty` — Returns all-zero stats when no searches
- [x] `test_get_today_statistics_multiple_searches` — Correctly sums searches, new companies, duplicates
- [x] `test_dedup_rate_calculation` — Dedup rate = (duplicates / (new + duplicates)) * 100
- [x] `test_statistics_for_today_only` — Ignores searches from other days

### Integration Tests

- [x] End-to-end search flow: form submit → API call → format detection → success response
- [x] Error handling: invalid input → API error → user message → form re-enabled
- [x] Timeout scenario: mock timeout → error message → retry enabled
- [x] Statistics persistence: insert search_history → statistics update

### Code Quality

- [x] Black formatting: all files pass `black --check`
- [x] Test coverage: 80%+ for new code (routes.py, format detection, statistics functions)
- [x] No regressions: all previous tests still pass

---

## Dev Agent Record

### Implementation Plan

1. Create/update search form template (index.html) with all required form fields
2. Implement `GET /` route with search_history statistics
3. Implement `POST /api/search` route with error handling
4. Create `detect_response_format()` function with format detection logic
5. Implement `get_today_statistics()` in db.py for statistics calculation
6. Create comprehensive test suite for all new functionality
7. Verify all tests pass, no regressions
8. Verify code quality checks pass

### Validation Gates

- [x] Search form displays correctly on home page with all required fields
- [x] Statistics display "0" when no searches, correct aggregates when data exists
- [x] Format detection works for JSON, Markdown, CSV, and unknown formats
- [x] Search API call works end-to-end with mocked Gemini response
- [x] Timeout handling returns user-friendly error message
- [x] Invalid API key returns helpful error
- [x] All tests pass (20+ tests for comprehensive coverage)
- [x] Code quality checks pass (black formatting verified)
- [x] No regressions from previous stories (all Story 1.1-1.3 tests still pass)
- [x] All AC acceptance criteria satisfied

---

## Change Log

- **2026-04-04**: Story 1.4 created with complete acceptance criteria and developer context
- **Status**: ready-for-dev

---

## Status

**Status:** ready-for-dev  
**Created:** 2026-04-04  
**Estimated Effort:** 2-3 dev days  
**Priority:** P0 (Blocks Story 1.5)  
**Dependencies:** Story 1.3 (Gemini API integration)
