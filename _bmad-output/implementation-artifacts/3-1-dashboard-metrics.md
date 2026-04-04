# Story 3-1: 构建效率仪表板页面与数据聚合 API

**Story ID:** 3.1  
**Epic:** 3 - 搜索效率分析  
**Status:** ready-for-dev  
**Created:** 2026-04-05  
**Estimated Effort:** 2-3 days  
**Priority:** P1-Important  
**Team:** Developer (dev-story agent)

---

## User Story

As a user,
I want to view an analytics dashboard showing search performance metrics,
So that I can understand how effective my search strategy is.

---

## Acceptance Criteria

### AC1: Dashboard Route & Page Load
**Given** I am logged in and have search history data  
**When** I navigate to `/dashboard`  
**Then**:
- Dashboard page loads successfully (HTTP 200)
- Page title shows: "系统运行效率仪表板 (最近7天)" with selected period
- Time filter dropdown is visible (7天 | 14天 | 30天 | 自定义)
- Dashboard displays in responsive layout

### AC2: API Endpoint - GET /api/analytics/dashboard
**Given** a request to `/api/analytics/dashboard?days=7`  
**When** the endpoint processes the request  
**Then**:
- Response returns HTTP 200 with envelope format:
```json
{
  "success": true,
  "data": {
    "period": "last_7_days",
    "metrics": {
      "total_searches": 47,
      "total_companies": 312,
      "dedup_rate": 18.5,
      "avg_hit_rate": 20.8,
      "high_score_rate": 28.2,
      "day_on_day_growth": 22.1,
      "week_on_week_growth": 18.3
    },
    "timestamp": "2026-04-03T12:00:00Z"
  },
  "error": null
}
```

### AC3: Key Metrics Display
**Given** the dashboard has loaded metrics  
**When** I view the metrics section  
**Then** I see 7 metric cards with:
- **Total Searches (总搜索次数):** Absolute count (47)
- **Total Companies (新增公司总数):** Absolute count (312)
- **Dedup Rate (去重率):** Percentage (18%)
- **Avg Hit Rate (平均命中率):** Decimal (20.8/search)
- **High-Score Rate (高分占比):** Percentage (28%)
- **Day-on-Day Growth:** Percentage with trend arrow (↑22%)
- **Week-on-Week Growth:** Percentage with trend arrow (↑18%)

**Styling Requirements:**
- Each metric is a card with value + trend indicator
- Trend arrows: ↑ for positive, ↓ for negative, — for neutral
- Color coding: Green (positive), Red (negative), Gray (neutral)
- Cards are responsive: 3 columns (desktop) → 2 columns (tablet) → 1 column (mobile)
- Font: metric name (小), value (大), trend (中)

### AC4: Time Period Filter
**Given** the dashboard is displayed  
**When** I click the time period dropdown  
**Then**:
- Dropdown shows options: 7天 | 14天 | 30天 | 自定义
- Default selection is "7天"
- When I select a period, dashboard updates with new metrics
- API call: `/api/analytics/dashboard?days=7|14|30` (or custom range)
- Page title updates: "系统运行效率仪表板 (最近{{days}}天)"

### AC5: API Endpoint Calculation Formulas
**Given** search_history records exist in the database  
**When** the dashboard aggregates metrics  
**Then**:
- **total_searches:** COUNT(DISTINCT search_history.id) in period
- **total_companies:** COUNT(DISTINCT company.id) from search_history in period
- **dedup_rate:** (SUM(duplicate_count) / total_companies) * 100
- **avg_hit_rate:** total_companies / total_searches (result count per search)
- **high_score_rate:** (COUNT(company WHERE prospect_score >= 8) / total_companies) * 100
- **day_on_day_growth:** ((today_companies - yesterday_companies) / yesterday_companies) * 100
- **week_on_week_growth:** ((this_week_companies - last_week_companies) / last_week_companies) * 100

### AC6: No Data Handling
**Given** search_history has no records in the selected period  
**When** the dashboard loads  
**Then**:
- All metrics show "—" (no data)
- Dashboard displays message: "数据不足，请继续搜索"
- Cards are visible but grayed out
- Time filter still works (allows switching periods)

### AC7: Error Handling
**Given** the API call fails or times out  
**When** the dashboard attempts to load  
**Then**:
- Error message displays: "数据加载失败，请刷新页面"
- Retry button is available
- Analytics section is disabled (grayed out)
- Log error with stack trace to browser console

---

## Technical Requirements

### Backend API Requirements

**Endpoint:** `GET /api/analytics/dashboard`

**Query Parameters:**
```
days: int (required) — 7, 14, 30, or custom date range
from_date: string (optional) — ISO 8601 format for custom range
to_date: string (optional) — ISO 8601 format for custom range
```

**Response Format:**
- Status 200 on success
- Status 400 if invalid parameters
- Status 500 if calculation fails
- Always use envelope: { success, data, error }

**Database Tables Required:**
- `company` — Must have: `id`, `prospect_score`, `created_at`
- `search_history` — Must have: `id`, `company_id`, `duplicate_count`, `created_at`

**Performance Requirements:**
- Response time: < 500ms for 7-day aggregation
- Response time: < 2s for 30-day aggregation
- Handle up to 1000+ search_history records efficiently

### Frontend UI Requirements

**Page Route:** `/dashboard`

**Template File:** `templates/dashboard.html`

**JavaScript Requirements:**
- Time period dropdown with event listener
- API call handler (fetch or $.ajax)
- Card rendering logic with responsive grid
- Error handling with retry mechanism
- Trend arrow rendering (↑ / ↓ / —)
- Color coding based on trend direction

**CSS Requirements:**
- Bootstrap 5 or existing styles from results page
- Responsive grid (3 cols desktop, 2 cols tablet, 1 col mobile)
- Card styling: shadow, padding, borders
- Metric value font sizes (large for numbers, small for labels)
- Color palette: Green (#28a745), Red (#dc3545), Gray (#6c757d)

**Assets Required:**
- Metric icon images or emoji (📊, 🎯, etc.) — optional
- Loading spinner during API call
- Toast/alert for error messages

---

## Implementation Steps

### Phase 1: Backend API Development (Day 1-1.5)

1. **Create metrics calculation module**
   - File: `src/tranotra/analytics/metrics.py`
   - Implement aggregation functions:
     - `calculate_total_searches(days)`
     - `calculate_total_companies(days)`
     - `calculate_dedup_rate(days)`
     - `calculate_avg_hit_rate(days, searches_count)`
     - `calculate_high_score_rate(days)`
     - `calculate_day_on_day_growth()`
     - `calculate_week_on_week_growth()`

2. **Create API endpoint**
   - File: `src/tranotra/routes_analytics.py` (new blueprint)
   - Endpoint: `GET /api/analytics/dashboard`
   - Route: `analytics_bp.route('/api/analytics/dashboard', methods=['GET'])`
   - Query param parsing and validation
   - Call metrics functions
   - Return response envelope

3. **Register blueprint in main.py**
   - Import `analytics_bp` from routes_analytics
   - Register with `app.register_blueprint(analytics_bp)`

4. **Database queries**
   - Use SQLAlchemy with optimized queries
   - Use `func.count()`, `func.sum()` for aggregations
   - Filter by created_at date range
   - Handle null values gracefully

### Phase 2: Frontend Development (Day 1.5-2)

1. **Create dashboard template**
   - File: `templates/dashboard.html`
   - Header with title and time filter dropdown
   - Grid container for 7 metric cards
   - Each card: metric_name | value | trend_arrow | growth_%
   - Error message placeholder
   - Loading spinner placeholder

2. **Create dashboard styles**
   - File: `static/css/dashboard.css` (or inline in template)
   - Responsive grid layout
   - Card styling with shadows and padding
   - Color-coded metric cards (green/red/gray)
   - Trend arrow styling

3. **Create dashboard JavaScript**
   - File: `static/js/dashboard.js`
   - `loadDashboard(days)` function
   - Time period dropdown event listener
   - API call handler (fetch API)
   - Error handler with retry
   - Render metrics helper function
   - Format numbers (percentage, decimals, commas)

4. **Add dashboard link to navigation**
   - Update `templates/index.html` or nav template
   - Add "Analytics" or "Dashboard" link to menu
   - Route to `/dashboard`

### Phase 3: Testing (Day 2-2.5)

1. **Unit tests**
   - Test metrics calculation functions with sample data
   - Test edge cases (zero data, single record, large datasets)
   - Test API parameter validation

2. **Integration tests**
   - Test full API endpoint with real database
   - Test with multiple time periods
   - Test error scenarios

3. **UI testing**
   - Test dashboard responsiveness (mobile, tablet, desktop)
   - Test time period filter switching
   - Test error message display
   - Test data formatting (numbers, percentages)

---

## Developer Context & Guardrails

### Architecture Compliance

**API Response Pattern:** Use envelope format from `patterns.md`:
```python
{
  "success": True,
  "data": { ... },
  "error": None
}
```

**Error Handling:** Follow error structure from existing API endpoints:
```python
def handle_error(code, message, status):
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    }, status
```

**Database Naming:** Use `snake_case` for all columns and attributes (see `patterns.md`).

**Imports:** Follow existing pattern from `src/tranotra/db.py`:
- Use `from tranotra.infrastructure.database import get_db`
- Use `from tranotra.core.models import Company, SearchHistory`
- Use SQLAlchemy ORM (not raw SQL)

**Logging:** Use Python logging module:
```python
logger = logging.getLogger(__name__)
logger.info(f"Calculated metrics for {days} days")
```

### Code Structure Rules

**File Locations:**
- Backend: `src/tranotra/` (follow existing module structure)
- Frontend: `static/js/`, `static/css/`, `templates/`
- Tests: `tests/integration/` or `tests/unit/`

**Module Organization:**
- `analytics/` subdirectory not necessary; use routes_analytics.py
- Group related calculations in single module
- Keep calculations separate from route handlers

**Naming Conventions:**
- Routes: snake_case (e.g., `/api/analytics/dashboard`)
- Functions: snake_case (e.g., `calculate_total_searches()`)
- Variables: snake_case (e.g., `total_searches`, `dedup_rate`)
- Classes: PascalCase (e.g., `MetricsCalculator` if created)

### Previous Story Learnings

**From Story 2-5 (CSV Export):**
- Response formatting established ✅ Use existing envelope pattern
- Flask route patterns validated ✅ Follow `search_bp` blueprint pattern
- Responsive design proven ✅ Use Bootstrap 5 grid classes
- Database aggregations working ✅ Use similar query patterns

**Key Insights:**
1. Metrics calculations should be pure functions, not route handlers
2. Template rendering uses Jinja2 with Flask patterns
3. Bootstrap 5 responsive classes are already in project (verified in results page)
4. API envelope pattern is consistent across all endpoints

### Git History Insights

**Recent commits pattern:**
- Story completion: `feat: Story X-Y — feature name`
- Code review fixes: `fix: Apply review patches from Story X.Y`
- Testing: `test: Add integration tests`

**Files created in recent stories:**
- `src/tranotra/routes.py` — Blueprint pattern
- `src/tranotra/db.py` — Database layer
- `templates/index.html` — Flask template

**Architecture decisions:**
- Blueprint pattern for routes (see `routes.py`)
- CRUD operations in `db.py` layer
- Models in `src/tranotra/core/models.py`
- Flask factory pattern in `main.py`

---

## Project Context Reference

**Project:** 08B2B_AIfind - Tranotra Leads  
**User:** Ailong  
**Tech Stack:** Flask 2.3.0, SQLAlchemy 2.0, Bootstrap 5, Python 3.8+

**Database Schema (Relevant):**
- `company` table: id, name, country, prospect_score, created_at, updated_at
- `search_history` table: id, query, country, result_count, duplicate_count, avg_score, created_at, company_id (FK)

**API Patterns (Established):**
- Response envelope: `{ success, data, error }`
- Error codes: NOT_FOUND, VALIDATION_ERROR, RATE_LIMIT_EXCEEDED
- Status codes: 200 (success), 400 (validation), 404 (not found), 500 (server error)

**Frontend Patterns (Established):**
- Bootstrap 5 grid system
- Responsive classes: col-12, col-md-6, col-lg-4
- Color utilities: text-success, text-danger, bg-light
- Jinja2 templating in Flask

**Testing Approach:**
- Unit tests with pytest fixtures
- Integration tests with real database
- E2E tests with Flask test client

---

## Completion Checklist

- [ ] Backend API endpoint created: `GET /api/analytics/dashboard`
- [ ] Metrics calculation functions implemented (7 functions)
- [ ] Database queries optimized and tested
- [ ] Error handling with proper HTTP status codes
- [ ] Dashboard template created: `templates/dashboard.html`
- [ ] Dashboard JavaScript created: `static/js/dashboard.js`
- [ ] Dashboard CSS created or updated: `static/css/dashboard.css`
- [ ] Responsive layout tested (mobile, tablet, desktop)
- [ ] Time period filter implemented and functional
- [ ] No data handling implemented
- [ ] Error handling tested and functional
- [ ] API tests written (unit + integration)
- [ ] UI tests for dashboard responsiveness
- [ ] Dashboard link added to navigation
- [ ] Code review checklist items addressed
- [ ] All acceptance criteria verified

---

## Notes for Developer

**Before starting:**
1. Review `src/tranotra/db.py` to understand database layer pattern
2. Review `src/tranotra/routes.py` to understand blueprint pattern
3. Review `_bmad-output/implementation-artifacts/2-5-csv-export.md` for similar feature pattern
4. Review `_bmad-output/planning-artifacts/architecture/patterns.md` for consistency rules

**Key decisions made in this story:**
- Metrics calculated server-side (not client-side) for accuracy
- Time period filter on dashboard, not in detail pages
- 7 day default (most common analytics period)
- Trend arrows show growth direction (day-on-day, week-on-week)
- High-score threshold: prospect_score >= 8 (based on scoring model)

**Potential blockers:**
- None identified; previous stories (1-1 through 2-5) provide all required foundations

**Test data available:**
- Integration tests already load sample search_history data
- Use test fixtures from `tests/integration/conftest.py`

---

**Status:** ✅ Ready for Development  
**Developer:** Awaiting dev-story agent pickup  
**Created:** 2026-04-05  
**Next Step:** Run `dev-story` agent to begin implementation
