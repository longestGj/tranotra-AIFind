---
story_id: "1.5"
story_key: "1-5-data-parsing-normalization"
epic: "Epic 1: 搜索表单与数据获取 (Search & Acquisition)"
title: "实现数据解析、规范化与去重逻辑"
status: "ready-for-dev"
priority: "P0"
created_date: "2026-04-04"
assignee: "Developer Agent"
---

# Story 1.5: 实现数据解析、规范化与去重逻辑

## Story Statement

**As a developer,**  
I want to parse, normalize, and deduplicate search results,  
So that the database contains only clean, unique company records.

---

## Acceptance Criteria

### AC1: Parse All Company Fields from Response
**Given** the Gemini response is received from Story 1.4  
**When** the parser processes each company record  
**Then** it extracts and validates all 16 required fields:
- Company name
- Country
- City
- Year established
- Employees
- Estimated revenue
- Main products
- Export markets
- EU/US/JP export flag
- Raw materials
- Recommended product
- Recommendation reason
- Website
- Contact email
- LinkedIn URL
- Best contact title
- Prospect score
- Priority

### AC2: Handle Missing Fields Gracefully
**Given** a company record has missing fields  
**When** the parser encounters empty/null values  
**Then**:
- Missing required fields (name, country) → skip record, log error
- Missing optional fields → fill with "N/A" or empty string
- Continue processing (do not fail entire batch)
- Log count: "处理 15 条结果，成功 12 条，失败 3 条"

### AC3: Normalize LinkedIn URLs
**Given** raw LinkedIn URLs like "https://www.linkedin.com/company/cadivi/"  
**When** the parser normalizes URLs  
**Then** the output is:
- Lowercase conversion: "https://..." → "https://..."
- Protocol removal: "linkedin.com/company/cadivi"
- www prefix removal: "linkedin.com/company/cadivi"
- Trailing slash removal: "linkedin.com/company/cadivi"
- Space to hyphen: "company name" → "company-name"
- **Final output:** "linkedin.com/company/cadivi"

### AC4: Deduplicate by Normalized LinkedIn URL
**Given** a company with normalized LinkedIn URL  
**When** the deduplication logic checks the database  
**Then**:
- If linkedin_normalized already exists → skip insertion, increment duplicate_count
- If not exists → insert new record, increment new_count
- Log each decision: "跳过重复: {company_name}" or "插入新公司: {company_name}"

### AC5: Validate and Normalize Scores
**Given** company prospect scores from the response  
**When** the parser validates scores  
**Then**:
- Scores must be integers 1-10
- If score < 1 → clamp to 1
- If score > 10 → clamp to 10
- If non-numeric → set to 0 (invalid prospect)
- Calculate avg_score from all **new** companies only

### AC6: Create Search History Record
**Given** parsing completes with new/duplicate counts  
**When** the search history is logged  
**Then** a record is created with:
```python
{
    "country": "Vietnam",              # from request
    "query": "PVC manufacturer",        # from request
    "result_count": 15,                 # total from Gemini
    "new_count": 12,                    # inserted
    "duplicate_count": 3,               # skipped
    "avg_score": 8.1,                   # average of new only
    "high_priority_count": 8,           # score >= 8, new only
    "created_at": datetime.now()
}
```

### AC7: Redirect to Results Page
**Given** parsing completes successfully  
**When** all records are processed  
**Then**:
- Redirect user to results page (Story 2.1 integration point)
- Display success message: "新增: 12 | 重复: 3 | 平均评分: 8.1"
- If processing takes > 3 seconds, show: "正在处理结果，请稍候..."

### AC8: Parse Multiple Response Formats
**Given** the response format is JSON, Markdown table, or CSV  
**When** the parser receives each format  
**Then** it correctly extracts fields:
- **JSON:** Array of objects or array of arrays
- **Markdown:** Pipe-delimited table with header row
- **CSV:** Comma/tab-separated values with header row
- **Partial success:** If one record fails, continue processing others

### AC9: Handle Edge Cases
**Given** various malformed or incomplete data  
**When** parsing is executed  
**Then** the system:
- Skips records with missing required fields (name, country, score)
- Fills optional fields with "N/A"
- Clamps scores to valid range
- Logs all skipped records with reason
- Completes in < 3 seconds for typical responses

### AC10: Maintain Data Consistency
**Given** the entire parse → normalize → deduplicate → insert pipeline  
**When** execution completes  
**Then**:
- Either all new companies are inserted + history created, OR none (transaction semantics)
- If insert fails → rollback + show error message + allow retry
- Database state remains consistent (no partial inserts)
- History record accurately reflects what was inserted

---

## Technical Requirements

### Core Dependencies
- **Framework:** Flask 2.3.0 (already initialized in Story 1.1)
- **Database:** SQLAlchemy 2.0.0 with SQLite (Story 1.2)
- **Data:** Companies and search_history tables (Story 1.2)
- **Input:** `call_gemini_grounding_search()` from Story 1.3 (returns raw response)
- **Format Detection:** `detect_response_format()` from Story 1.4 (validates format)

### Python Module Organization
```
src/tranotra/
├── parser.py              [NEW] Data parsing & normalization logic
├── routes.py              [MODIFY] Add POST /api/parse endpoint
├── db.py                  [MODIFY] Add parse_response_and_insert() function
└── main.py                [MODIFY] Register parse endpoint if needed
```

### Key Functions to Implement

#### parser.py (NEW FILE)
```python
class CompanyParser:
    """Handles parsing, normalization, and validation of company data"""
    
    def __init__(self):
        pass
    
    def parse_response(self, response: str, format: str) -> List[Dict]:
        """Parse raw response into list of company dicts
        
        Args:
            response: Raw string from Gemini API
            format: "JSON", "Markdown", or "CSV"
            
        Returns:
            List of company dicts (may be incomplete/invalid)
            
        Raises:
            ValueError: If format is unsupported or response malformed
        """
        if format == "JSON":
            return self._parse_json(response)
        elif format == "Markdown":
            return self._parse_markdown(response)
        elif format == "CSV":
            return self._parse_csv(response)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _parse_json(self, response: str) -> List[Dict]:
        """Parse JSON array into company records"""
        pass
    
    def _parse_markdown(self, response: str) -> List[Dict]:
        """Parse Markdown table into company records"""
        pass
    
    def _parse_csv(self, response: str) -> List[Dict]:
        """Parse CSV into company records"""
        pass
    
    def normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to canonical form
        
        Example:
            Input: "https://www.linkedin.com/company/cadivi/"
            Output: "linkedin.com/company/cadivi"
        """
        pass
    
    def validate_and_clamp_score(self, score) -> int:
        """Validate prospect score and clamp to 1-10 range
        
        - If < 1 → 1
        - If > 10 → 10
        - If non-numeric → 0
        """
        pass
```

#### db.py (ADD FUNCTION)
```python
def parse_response_and_insert(
    country: str,
    query: str,
    response: str,
    format: str
) -> Dict:
    """Parse Gemini response and insert companies into database
    
    Returns:
        {
            "success": True,
            "new_count": 12,
            "duplicate_count": 3,
            "error_count": 0,
            "avg_score": 8.1,
            "high_priority_count": 8,
            "message": "成功处理 15 条，新增 12 条，重复 3 条"
        }
    """
    pass
```

### Response Format Examples

#### JSON Format
```json
[
  {
    "name": "Cadivi Company Limited",
    "country": "Vietnam",
    "city": "Ho Chi Minh City",
    "year_established": 2005,
    "employees": "100-500",
    "estimated_revenue": "$5M-10M",
    "main_products": "PVC compounds, additives",
    "export_markets": "Thailand, Malaysia, Indonesia",
    "eu_us_jp_export": true,
    "raw_materials": "Petroleum-based",
    "recommended_product": "Masterbatch",
    "recommendation_reason": "High-volume PVC processor",
    "website": "cadivi.vn",
    "contact_email": "contact@cadivi.vn",
    "linkedin_url": "https://www.linkedin.com/company/cadivi/",
    "best_contact_title": "Operations Director",
    "prospect_score": 9,
    "priority": "A"
  },
  ...
]
```

#### Markdown Table Format
```markdown
| Name | Country | City | Employees | Score |
| --- | --- | --- | --- | --- |
| Cadivi Ltd | Vietnam | HCMC | 100-500 | 9 |
| ...
```

#### CSV Format
```csv
name,country,city,employees,prospect_score
Cadivi Ltd,Vietnam,HCMC,100-500,9
```

### Error Handling Strategy

| Scenario | Action | Message |
|----------|--------|---------|
| Unsupported format | Skip, log error | "搜索失败：格式不支持" |
| Malformed JSON | Skip record, continue | "解析失败 [Row 5]: Invalid JSON" |
| Missing required field (name, country) | Skip record, continue | "解析失败 [Row 3]: missing 'name'" |
| Missing optional field | Fill with "N/A", continue | Log at INFO level |
| Invalid score (non-numeric) | Set to 0, continue | "无效评分 [Row 7]: 'abc' → 0" |
| Database insert fails | Rollback, show error | "数据保存失败，请稍后重试" |
| Processing takes > 3s | Show status message | "正在处理结果，请稍候..." |

---

## Architecture Compliance

### From decisions-api.md
✅ Pipeline Stage Communication: Use status object for multi-stage operations
✅ Error Handling: Specific exceptions for validation, database, parsing errors
✅ Partial Success: Allow batch operations to continue on individual record failures

### From decisions-core.md
✅ Data Normalization: URL normalization follows consistent pattern
✅ Deduplication: Use unique constraint (linkedin_normalized) for idempotency
✅ Validation: Clamp scores, fill missing fields, reject invalid required fields

### From project-structure.md
✅ File Location: `src/tranotra/parser.py` (new module for parsing logic)
✅ Naming: Function names in snake_case, classes in PascalCase
✅ Imports: Always import from tranotra package (not src.tranotra)

---

## Implementation Strategy

### Phase 1: Core Parser Implementation (Days 1-2)
1. Create `parser.py` with `CompanyParser` class
2. Implement `parse_response()` with JSON/Markdown/CSV handlers
3. Implement `normalize_linkedin_url()` function
4. Write unit tests for each parser format
5. Test edge cases: empty responses, malformed data, missing fields

### Phase 2: Database Integration (Days 3-4)
1. Add `parse_response_and_insert()` to db.py
2. Implement deduplication logic (check linkedin_normalized)
3. Create search_history record with statistics
4. Handle database transactions for consistency
5. Write integration tests with real database

### Phase 3: API Integration (Days 5)
1. Add POST `/api/parse` endpoint to routes.py
2. Connect Story 1.4 search endpoint to parser
3. Implement redirect to results page (Story 2.1)
4. Add error messages and user feedback
5. End-to-end testing

### Phase 4: Refinement (Days 6-7)
1. Performance optimization (< 3s for 100 records)
2. Comprehensive error handling and logging
3. Code review and quality checks
4. Documentation and knowledge transfer

---

## Previous Story Intelligence

### From Story 1.4 (Gemini Grounding Search)
✅ `detect_response_format()` function is available in routes.py
✅ API endpoint `/api/search` validates format before calling Story 1.5
✅ Gemini returns raw response (JSON, Markdown, or CSV)
✅ Client expects "搜索成功，正在处理结果..." message

### From Story 1.3 (Gemini API Integration)
✅ `call_gemini_grounding_search(country, query)` returns raw string
✅ Response is **NOT** pre-processed or validated
✅ Parsing should happen in Story 1.5 (this story)
✅ Error handling: GeminiTimeoutError, GeminiError exceptions defined

### From Story 1.2 (Database Design)
✅ **companies table:** 23 columns including linkedin_normalized (UNIQUE)
✅ **search_history table:** country, query, result_count, new_count, duplicate_count, avg_score, high_priority_count
✅ CRUD functions: `insert_company()`, `insert_search_history()`
✅ Constraint: prospect_score must be 1-10

### From Story 1.1 (Flask Setup)
✅ Project structure: `src/tranotra/` with __init__.py
✅ Database initialization: `init_db()` creates tables on startup
✅ Config loading: Environment variables via `.env` and `config.py`
✅ Logging: Logger available as `logger = logging.getLogger(__name__)`

---

## Testing Strategy

### Unit Tests (test_parser.py)
```python
class TestCompanyParser:
    def test_parse_json_format()  # Parse JSON array
    def test_parse_markdown_format()  # Parse Markdown table
    def test_parse_csv_format()  # Parse CSV
    def test_normalize_linkedin_url()  # URL normalization
    def test_validate_score_clamping()  # Score validation
    def test_handle_missing_fields()  # Missing field handling
    def test_handle_invalid_data()  # Malformed data

class TestLinkedInNormalization:
    def test_https_protocol_removal()
    def test_www_removal()
    def test_trailing_slash_removal()
    def test_space_to_hyphen_conversion()
    def test_lowercase_conversion()
    def test_edge_cases()
```

### Integration Tests (test_parsing_integration.py)
```python
class TestParsingPipeline:
    def test_parse_and_insert_new_companies()  # New company insertion
    def test_parse_and_skip_duplicates()  # Deduplication
    def test_search_history_creation()  # History logging
    def test_partial_failure_handling()  # Continue on error
    def test_transaction_rollback()  # Consistency
    def test_performance_under_load()  # < 3 seconds for 100 records
```

### End-to-End Tests (test_e2e_parsing.py)
```python
class TestEndToEnd:
    def test_search_to_results_pipeline()  # Full flow
    def test_error_messages_displayed()  # User feedback
    def test_statistics_calculation()  # avg_score, high_priority_count
    def test_redirect_to_results_page()  # Story 2.1 integration
```

---

## Key Implementation Notes

### LinkedIn URL Normalization
The `linkedin_normalized` field is the **deduplication key**. Every company must have:
```python
linkedin_normalized = normalize_linkedin_url(linkedin_url)
```

Examples:
```
"https://www.linkedin.com/company/cadivi/" → "linkedin.com/company/cadivi"
"linkedin.com/company/foo-bar" → "linkedin.com/company/foo-bar"
"www.linkedin.com/company/with spaces/" → "linkedin.com/company/with-spaces"
```

### Score Calculation
```python
# Only for NEW companies (not duplicates)
new_company_scores = [c['prospect_score'] for c in new_companies]
avg_score = sum(new_company_scores) / len(new_company_scores) if new_company_scores else 0
high_priority_count = len([c for c in new_companies if c['prospect_score'] >= 8])
```

### Database Consistency
```python
# Use transaction: either all succeed or all fail
try:
    for company_data in parsed_companies:
        if not db.query(Company).filter_by(
            linkedin_normalized=company_data['linkedin_normalized']
        ).first():
            insert_company(company_data)
            new_count += 1
        else:
            duplicate_count += 1
    
    insert_search_history({
        "country": country,
        "query": query,
        "result_count": len(parsed_companies),
        "new_count": new_count,
        "duplicate_count": duplicate_count,
        "avg_score": avg_score,
        "high_priority_count": high_priority_count
    })
    db.commit()  # Commit after search_history too
except Exception as e:
    db.rollback()
    raise
```

---

## Deliverables Checklist

- [ ] parser.py created with CompanyParser class
- [ ] JSON/Markdown/CSV parsing implemented and tested
- [ ] LinkedIn URL normalization working correctly
- [ ] Score validation and clamping implemented
- [ ] parse_response_and_insert() function in db.py
- [ ] Deduplication logic using linkedin_normalized
- [ ] Search history record creation
- [ ] POST /api/parse endpoint (or modify /api/search)
- [ ] 25+ unit and integration tests (all passing)
- [ ] Performance: parsing < 3 seconds for 100 records
- [ ] Error handling: graceful failure with user messages
- [ ] Code coverage: 80%+ for parser.py and db.py
- [ ] Logging: all operations logged (no sensitive data)
- [ ] Documentation: docstrings for all public functions

---

## Acceptance Definition of Done

✅ All 10 acceptance criteria passed  
✅ All tests passing (25+)  
✅ Code review approved  
✅ Performance validated (< 3s)  
✅ Integration with Story 1.4 complete  
✅ Story 2.1 ready to use parsed results  
✅ Documentation updated  
✅ No regressions from previous stories  

---

**Status:** Ready for Development  
**Created:** 2026-04-04  
**Next Step:** Run `dev-story` to implement Story 1-5

---

## Review Findings

### Decision Needed
✅ **已解决：** AC7 在本故事实现（重定向 + 进度提示）

### Patches (7) ✅ 已修复
- [x] [Review][Patch] AC2 违反：prospect_score 不应为必需字段 [parser.py:17]
- [x] [Review][Patch] AC7 实现：添加重定向到结果页面和进度提示 [routes.py:79-142]
- [x] [Review][Patch] AC10 违反：事务边界不完整，搜索历史失败无法回滚 [db.py:360-383]
- [x] [Review][Patch] 过宽泛的异常捕获（混合 JSON、格式、IO 错误） [parser.py:53-64]
- [x] [Review][Patch] LinkedIn URL 规范化缺少验证（规范化后 URL 可能为空） [parser.py:166-239]
- [x] [Review][Patch] CSV 解析缺少编码处理（BOM、UTF-8） [parser.py:103-130]

### Deferred (3)
- [x] [Review][Defer] 国际化问题：错误消息硬编码中文 [db.py, routes.py] — deferred, pre-existing, 跨项目问题
- [x] [Review][Defer] Markdown 表解析过于简单，不处理多行表头 [parser.py:301-319] — deferred, pre-existing, 非关键路径
- [x] [Review][Defer] 日志级别不一致（缺少 warning 级别） [db.py] — deferred, pre-existing, 代码风格问题
