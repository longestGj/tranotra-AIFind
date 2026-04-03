---
story: 2.1
storyTitle: "构建搜索结果页面基础与 API 端点"
epicNumber: 2
epicTitle: "结果展示与快速操作 (Results Display & Interaction)"
status: review
createdDate: "2026-04-04"
lastUpdated: "2026-04-04"
storyKey: "2-1-results-page-api"
implementation:
  completed: "2026-04-04"
  status: "All Acceptance Criteria satisfied - 16/16 tests passing"
  summary: "Backend API endpoint and caching layer implemented. Frontend HTML/CSS/JS with card and table view templates created. Comprehensive test coverage for pagination, filtering, caching, and edge cases."
---

# Story 2.1: 构建搜索结果页面基础与 API 端点

**Epic:** 2 - 结果展示与快速操作 (Results Display & Interaction)

**Priority:** P0 (Core user-facing feature)

**Depends On:** Epic 1 (Story 1-5 data parsing completed)

---

## User Story

As a developer,  
I want to create the results page layout and API endpoint for fetching search results,  
So that the frontend can display company data.

---

## Acceptance Criteria

### AC 1: API Endpoint - GET /api/search/results

**Given** the database contains company records from a search  
**When** I call GET /api/search/results with query parameters  
**Then** the endpoint returns:

```
GET /api/search/results?country=Vietnam&query=PVC%20manufacturer&page=1
```

**Response (Success):**
```json
{
  "success": true,
  "timestamp": "2026-04-03T12:00:00Z",
  "new_count": 15,
  "duplicate_count": 3,
  "avg_score": 8.2,
  "total_count": 47,
  "current_page": 1,
  "per_page": 20,
  "total_pages": 3,
  "companies": [
    {
      "id": 1,
      "name": "Company Name",
      "country": "Vietnam",
      "city": "Ho Chi Minh",
      "year_established": 2010,
      "employees": "500-2000",
      "estimated_revenue": "$200M+",
      "main_products": "PVC cable",
      "export_markets": "USA, ASEAN",
      "eu_us_jp_export": true,
      "raw_materials": "PVC resin",
      "recommended_product": "DOTP",
      "recommendation_reason": "Perfect fit",
      "website": "example.com",
      "contact_email": "contact@example.com",
      "linkedin_url": "linkedin.com/company/...",
      "linkedin_normalized": "linkedin.com/company/...",
      "best_contact_title": "Purchasing Manager",
      "prospect_score": 10,
      "priority": "HIGH",
      "source_query": "Vietnam/PVC manufacturer",
      "created_at": "2026-04-03T12:00:00Z",
      "updated_at": "2026-04-03T12:00:00Z"
    }
  ]
}
```

### AC 2: Query Parameters & Filtering

**Given** user wants to filter results  
**When** I provide query parameters  
**Then** the endpoint:

- Accepts `country` (optional) - filter by country
- Accepts `query` (optional) - filter by search keyword
- Accepts `page` (optional, default=1) - pagination
- Accepts `per_page` (optional, default=20) - results per page (max 100)
- Returns only records matching country AND query (if provided)

**Edge cases:**
- If `country` and `query` both empty → return all results from any search (paginated)
- If no results match filters → return empty companies array with success=true
- Invalid page number → return page 1
- Invalid per_page → use default 20

### AC 3: Timeout & Caching

**Given** database query takes > 3 seconds  
**When** response is pending  
**Then**:
- Return cached results from previous identical search (if available)
- Include flag: `"cached": true` in response
- Show message to user: "数据加载中（显示缓存结果）"

**Caching logic:**
- Cache key: `{country}#{query}#{page}`
- TTL: 5 minutes
- Max cache size: 50 entries (LRU eviction)

### AC 4: Results Page HTML Structure

**Given** API returns search results  
**When** user loads results page (/results or /search/results)  
**Then** the page displays:

```html
<!DOCTYPE html>
<html>
<head>
  <title>搜索结果 - Tranotra Leads</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
  <div class="container">
    <!-- Header showing search context -->
    <div class="results-header">
      <h1>搜索: Vietnam + PVC manufacturer</h1>
      <button class="back-btn">← 返回搜索</button>
    </div>

    <!-- Statistics Card -->
    <div class="stats-card">
      <div class="stat">
        <label>新增:</label>
        <span class="value">15</span>
      </div>
      <div class="stat">
        <label>重复:</label>
        <span class="value">3</span>
      </div>
      <div class="stat">
        <label>平均评分:</label>
        <span class="value">8.2</span>
      </div>
    </div>

    <!-- View Toggle Buttons -->
    <div class="view-toggle">
      <button class="view-btn active" data-view="card">卡片视图</button>
      <button class="view-btn" data-view="table">表格视图</button>
    </div>

    <!-- Loading Indicator -->
    <div class="loading-indicator" style="display: none;">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Results Container (populated by JavaScript) -->
    <div id="results-container" class="results-container">
      <!-- Card view or table view will be rendered here -->
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <button class="page-btn prev-btn">← 上一页</button>
      <span class="page-info">第 1 页，共 3 页</span>
      <button class="page-btn next-btn">下一页 →</button>
    </div>
  </div>

  <script src="/static/js/results.js"></script>
</body>
</html>
```

### AC 5: Empty Results Handling

**Given** search returns no results  
**When** results page loads  
**Then**:
- Display message: "本次未找到，建议修改搜索词"
- Show suggestions:
  - "尝试使用更通用的关键词"
  - "尝试其他国家"
  - "查看搜索历史找高效的搜索词"
- Provide "返回搜索" button

### AC 6: Performance & Load Time

**Given** results page is loading  
**When** initial page load  
**Then**:
- Page load starts (skeleton placeholders shown)
- API call to /api/search/results
- Parse JSON response
- Render initial 20 results
- Total time: < 2 seconds for common cases (cache hit)
- For first time (DB query): < 8 seconds (acceptable with loading indicator)

---

## Technical Requirements

### Backend (Flask)

**New route in routes.py:**

```python
@app.route('/api/search/results', methods=['GET'])
def get_search_results():
    """
    Fetch paginated search results with optional filtering.
    
    Query Parameters:
    - country: optional string
    - query: optional string
    - page: optional int (default=1)
    - per_page: optional int (default=20, max=100)
    
    Returns:
    - JSON with companies array and metadata
    """
    pass
```

**Key implementation details:**
- Extract query params safely
- Validate pagination (page >= 1, per_page <= 100)
- Query database with filters
- Calculate pagination metadata
- Implement caching layer
- Handle timeouts gracefully

### Frontend (HTML/CSS/JavaScript)

**New files:**
- `templates/results.html` - Results page layout
- `static/js/results.js` - JavaScript for API calls and view switching
- `static/css/results.css` - Styling for results page

**JavaScript responsibilities:**
- Fetch results from API on page load
- Parse response and render companies
- Handle loading states
- Manage pagination (next/prev buttons)
- Store view preference in localStorage
- Error handling and retry logic

### Database

**No schema changes** - uses existing `companies` table from Story 1-2

**Queries needed:**
```python
def get_companies_paginated(
    country: str = None,
    query: str = None,
    page: int = 1,
    per_page: int = 20
) -> dict:
    """
    Returns:
    {
      'total': int,
      'companies': [company_dict, ...],
      'page': int,
      'per_page': int
    }
    """
```

---

## Architecture Compliance

### File Structure (from Story 1-1)

```
tranotra-leads/
├── main.py                    # Flask app (existing)
├── routes.py                  # API routes (ADD: /api/search/results)
├── db.py                      # Database (ADD: get_companies_paginated)
├── templates/
│   ├── index.html             # Home page (existing)
│   └── results.html           # NEW: Results page
├── static/
│   ├── css/
│   │   ├── style.css          # Global styles (existing)
│   │   └── results.css        # NEW: Results styles
│   └── js/
│       ├── common.js          # Common utilities (existing)
│       └── results.js         # NEW: Results page logic
└── data/
    └── leads.db               # SQLite database (existing)
```

### Code Patterns from Previous Stories

**From Story 1-1 (Flask structure):**
- Use Flask blueprints if complex (optional for this simple endpoint)
- Return JSON responses with `jsonify()`
- Error handling with try/except and HTTP status codes

**From Story 1-3 (Gemini API integration):**
- Implement timeout handling (5-second soft limit, 10-second hard limit)
- Use structured logging with context
- Never expose sensitive data in responses

**From Story 1-4 (Search form):**
- Show loading indicators to user
- Implement rate limiting consideration (may reuse delays)
- User-friendly error messages in Chinese

---

## Implementation Checklist

### Backend Implementation

- [ ] Add `get_companies_paginated()` function to `db.py`
  - [ ] Handle optional filters (country, query)
  - [ ] Implement pagination logic
  - [ ] Add indexes on frequently queried columns:
    - `linkedin_normalized`, `country`, `created_at` for companies table
  - [ ] Test with 0, 1, 20, 100 results
  
- [ ] Add `/api/search/results` route to `routes.py`
  - [ ] Parse and validate query parameters
  - [ ] Call `get_companies_paginated()` with filters
  - [ ] Implement caching layer (5-min TTL, max 50 entries)
  - [ ] Handle database timeout (> 3 seconds)
  - [ ] Return JSON with correct structure
  - [ ] Add error handling for malformed requests

- [ ] Implement caching mechanism
  - [ ] Use `functools.lru_cache` or simple dict with TTL
  - [ ] Cache key: `{country}#{query}#{page}`
  - [ ] Invalidate on new search

### Frontend Implementation

- [ ] Create `templates/results.html`
  - [ ] Header with search context
  - [ ] Statistics card (new_count, duplicate_count, avg_score)
  - [ ] View toggle buttons (card/table)
  - [ ] Results container (dynamic)
  - [ ] Pagination controls
  - [ ] Loading indicator

- [ ] Create `static/js/results.js`
  - [ ] Fetch URL parameters (country, query, page)
  - [ ] Call `/api/search/results` API
  - [ ] Parse JSON response
  - [ ] Render results (default: card view, placeholder for table)
  - [ ] Implement pagination (next/prev buttons)
  - [ ] Handle loading states
  - [ ] Implement error display
  - [ ] Store view preference in localStorage

- [ ] Create `static/css/results.css`
  - [ ] Header styling
  - [ ] Statistics card layout
  - [ ] View toggle button styling
  - [ ] Placeholder for results container
  - [ ] Pagination controls styling
  - [ ] Loading indicator animation
  - [ ] Responsive design (mobile-first)

### Testing

- [ ] Test API endpoint with various query combinations
  - [ ] Both filters provided
  - [ ] One filter provided
  - [ ] No filters (all results)
  - [ ] Invalid page number
  - [ ] No results match filter
  
- [ ] Test pagination
  - [ ] Page 1, 2, 3, etc.
  - [ ] Per_page parameter
  - [ ] Total count accuracy
  
- [ ] Test caching
  - [ ] Same query returns cached result
  - [ ] Different query returns fresh result
  - [ ] Cache expires after 5 minutes
  
- [ ] Test error scenarios
  - [ ] Database timeout (> 3s)
  - [ ] Malformed request
  - [ ] Empty results
  
- [ ] Test frontend
  - [ ] Page loads correctly
  - [ ] Results render in card view
  - [ ] Pagination works
  - [ ] Loading indicator shows/hides
  - [ ] Error message displays
  - [ ] Mobile responsive

---

## Previous Story Context (from Epic 1)

### Story 1-4 Learnings

Story 1-4 (Gemini Grounding Search) implements:
- Flask form handling and UX
- API timeout management (30-second deadline)
- Format detection for responses
- User feedback (loading spinner, error messages)
- Rate limiting with 2-second delays

**Relevant for Story 2-1:**
- Use similar loading indicator patterns
- Implement 5-second soft timeout on database (similar to API timeout approach)
- Show user-friendly error messages (Chinese language convention)
- Consider async patterns for slow operations

### Story 1-1 Architecture

Story 1-1 established:
- Project structure with `routes.py`, `db.py`, `templates/`, `static/`
- Flask app initialization in `main.py`
- Use of Jinja2 templates
- Static files served from `/static/`

**Relevant for Story 2-1:**
- Follow same folder structure
- Use Flask's `render_template()` for HTML
- Use Flask's `jsonify()` for JSON responses
- Use blueprints if API grows complex

---

## Technical Decisions

### Why Cache Results (NFR4)?
- Database queries on large result sets (1000+ companies) can be slow
- Most users revisit same searches within a session
- 5-minute TTL balances freshness vs. performance
- LRU eviction prevents unbounded memory growth

### Why Soft Timeout (3 seconds)?
- Story 1-4 uses 30-second timeout (API constraint)
- Database queries on local SQLite typically < 1 second
- 3-second timeout gives room for slow cases without user frustration
- Cached results are better than "forever loading"

### Why Pagination?
- Results can exceed 100+ companies
- Loading all at once impacts performance and UX
- Default 20 per page balances usability with performance
- Users can request more if needed

---

## Estimated Effort

- Backend API implementation: 2-3 hours
- Frontend HTML/CSS/JS: 3-4 hours
- Testing (manual + automated): 2-3 hours
- **Total: 7-10 hours**

---

## Success Criteria

✅ API endpoint returns correct JSON structure  
✅ Pagination works correctly (total_pages calculated)  
✅ Filtering by country/query works  
✅ Caching reduces subsequent requests to < 100ms  
✅ Timeout after 3s shows cached results  
✅ Results page loads and displays data  
✅ Empty results message displays appropriately  
✅ Page responsive on mobile (< 768px)  
✅ All tests pass  

---

## Dependencies & Blockers

**Dependency on Story 1-5 (Data Parsing):**
- Story 2-1 assumes data is already in the database
- Story 1-5 (data parsing from Gemini) must complete first
- Can develop/test with mock data in the meantime

**No blockers identified.**

---

## Notes for Developer

1. **Start with mock data:** Create a script to insert test data into `companies` table for development/testing
2. **Use existing patterns:** Follow `routes.py` patterns from Story 1-1 and 1-3
3. **Performance is key:** This story is the foundation for Views 2-2 to 2-5; optimize now
4. **Test thoroughly:** Pagination bugs will cause cascade failures in later stories
5. **Document API:** Add comments/docstrings for API endpoint (will be referenced in later stories)

---

**Story Status:** ready-for-dev  
**Next Story:** 2-2 (Card View Display) - depends on completion of 2-1
