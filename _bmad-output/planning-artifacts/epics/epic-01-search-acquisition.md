---
epic: 1
epicTitle: "搜索表单与数据获取 (Search & Acquisition)"
storyCount: 5
frCoverage: "FR1, FR2, FR3, FR4, FR5, FR6, FR7"
nfrCoverage: "NFR6, NFR9, NFR10"
uxdrCoverage: "UX-DR1, UX-DR2, UX-DR3, UX-DR4"
createdDate: "2026-04-03"
---

# Epic 1: 搜索表单与数据获取 (Search & Acquisition)

**Epic 目标:** 用户能够输入国家和关键词，系统自动搜索并将结果持久化到数据库

**用户成果:** 从搜索表单输入 → Gemini API 调用 → 保存原始响应到文件 → 从文件读取解析 → 数据规范化、去重 → 数据入库

**覆盖需求:**
- Functional: FR1, FR2, FR3, FR4, FR5, FR6, FR7
- Non-Functional: NFR6, NFR9, NFR10
- UX Design: UX-DR1, UX-DR2, UX-DR3, UX-DR4

**开发优先级:** P0 (基础功能，其他 Epic 依赖)

---

## Story 1.1: 初始化 Flask 应用与项目结构

**Story ID:** 1.1

**User Story:**

As a developer,
I want to set up a Flask application with proper project structure,
So that I can build the search API on a solid foundation.

**Acceptance Criteria:**

**Given** a fresh Python project directory  
**When** I run the setup script  
**Then** the following structure is created:
```
tranotra-leads/
├── main.py                  # Flask app entry point
├── config.py                # configuration & environment variables
├── db.py                    # database layer
├── gemini_client.py         # Gemini API client
├── parser.py                # data parsing & normalization
├── routes.py                # Flask routes
├── templates/               # HTML templates directory
├── static/                  # CSS, JS, images directory
├── requirements.txt         # Python dependencies
├── .env.example             # environment variables template
└── .gitignore               # git ignore rules
```

**And** the Flask app runs successfully on localhost:5000  
**And** all dependencies in requirements.txt are Python 3.8+ compatible  
**And** the following Flask blueprint structure is used:
- main.py creates Flask app
- routes.py defines all API routes
- Static and template directories are properly configured

**Coverage:**
- FR1 (Web 表单基础)
- NFR9 (Flask 框架)

---

## Story 1.2: 设计并初始化 SQLite 数据库（companies、search_history 表）

**Story ID:** 1.2

**User Story:**

As a developer,
I want to create database tables and provide CRUD functions,
So that the system can persist search results and search history.

**Acceptance Criteria:**

**Given** the Flask application is initialized  
**When** I call db.init_db()  
**Then** the following tables are created in ./data/leads.db:

**companies table (23 columns):**
- id (INTEGER PK, auto-increment)
- name (TEXT NOT NULL) — 公司名称
- country (TEXT NOT NULL) — Vietnam/Thailand/Indonesia/UAE/Saudi Arabia
- city (TEXT) — 城市/省份
- year_established (INTEGER) — 成立年份
- employees (TEXT) — 员工数范围
- estimated_revenue (TEXT) — 估计年收入
- main_products (TEXT) — 主要产品描述
- export_markets (TEXT) — 出口市场（逗号分隔）
- eu_us_jp_export (BOOLEAN) — 是否出口欧美日
- raw_materials (TEXT) — 原材料
- recommended_product (TEXT) — 推荐的 Tranotra 产品
- recommendation_reason (TEXT) — 推荐理由
- website (TEXT) — 官网域名
- contact_email (TEXT) — 联系邮箱
- linkedin_url (TEXT) — LinkedIn 原始 URL
- linkedin_normalized (TEXT UNIQUE) — 规范化 LinkedIn URL（去重键）
- best_contact_title (TEXT) — 最佳联系职位
- prospect_score (INTEGER CHECK 1-10) — 潜在客户评分
- priority (TEXT CHECK A/B/C) — 优先级
- source_query (TEXT NOT NULL) — 本次搜索条件
- created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
- updated_at (DATETIME DEFAULT CURRENT_TIMESTAMP)

**search_history table:**
- id (INTEGER PK)
- country (TEXT NOT NULL)
- query (TEXT NOT NULL)
- result_count (INTEGER) — Gemini 返回的原始公司数
- new_count (INTEGER) — 本次新增的公司数
- duplicate_count (INTEGER) — 本次重复的公司数
- avg_score (FLOAT) — 本次新增公司的平均评分
- high_priority_count (INTEGER) — 本次返回的 HIGH 优先级数
- created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)

**And** the following CRUD functions are available in db.py:
```python
def insert_company(data: dict) -> int:
    """Insert company, return company id. Skip if domain exists."""

def update_company(id: int, data: dict) -> bool:
    """Update company fields by id."""

def get_companies_by_score(min_score: int) -> list:
    """Get all companies with score >= min_score."""

def get_companies_by_search(country: str, query: str) -> list:
    """Get companies from a specific search."""

def insert_contact(data: dict) -> int:
    """Insert contact (for Phase 2)."""

def insert_email(data: dict) -> int:
    """Insert email draft (for Phase 2)."""

def insert_search_history(data: dict) -> int:
    """Insert search history record."""

def get_search_history(limit: int = 20) -> list:
    """Get recent search history."""
```

**And** duplicate calls to init_db() do not recreate existing tables  
**And** all datetime fields use CURRENT_TIMESTAMP as default  
**And** the database file is stored in ./data/leads.db (directory created if not exists)

**Coverage:**
- FR5 (16字段数据结构)
- NFR1 (自动初始化)
- NFR10 (SQLite本地存储)

---

## Story 1.3: 集成 Gemini API 与环境变量管理

**Story ID:** 1.3

**User Story:**

As a developer,
I want to configure Gemini API integration and manage API keys securely,
So that the system can call Gemini for company discovery.

**Acceptance Criteria:**

**Given** the Flask application is initialized  
**When** I create a .env file with GEMINI_API_KEY=xxx  
**Then** the config.py loads the environment variables correctly

**And** the following environment variables are supported:
```
GEMINI_API_KEY=your_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True (optional)
```

**And** a .env.example file is provided with template values

**And** gemini_client.py provides these functions:
```python
def initialize_gemini(api_key: str) -> bool:
    """Initialize Gemini client with API key."""

def call_gemini_grounding_search(country: str, query: str) -> str:
    """Call Gemini Grounding Search API.
    Returns raw response (could be JSON/CSV/Markdown).
    Automatically saves raw response to file before returning.
    """

def save_raw_response(country: str, query: str, response_text: str) -> str:
    """Save raw API response to file for debugging and re-parsing.
    Returns file path: data/gemini_responses/{timestamp}_{country}_{query}.json
    """
```

**And** the call_gemini_grounding_search() function includes:
- Timeout handling (default 30s)
- Retry logic (max 3 attempts with 2s exponential backoff on network error)
- Error logging on API failure (but never logs API key)
- User-friendly error messages
- Automatic saving of raw response to file (via save_raw_response())

**And** the save_raw_response() function:
- Creates data/gemini_responses/ directory if not exists
- Saves with filename: {timestamp}_{country}_{query}.json
- Returns file path as string
- Non-critical operation - errors are logged but don't raise exceptions

**And** when GEMINI_API_KEY is missing:
- Show clear error: "未找到 GEMINI_API_KEY，请检查 .env 文件"
- Application exits gracefully with helpful message

**And** the API key is never logged in plain text (only prefix like "sk_...***")

**And** the response from Gemini is returned as-is (raw text/JSON/markdown)
- No pre-processing of response in this story
- Raw response is already saved to file automatically
- Response validation happens in Story 1.4

**Coverage:**
- FR2 (Gemini API 调用)
- NFR9 (无额外依赖)

---

## Story 1.4: 实现 Gemini Grounding Search 调用与格式验证

**Story ID:** 1.4

**User Story:**

As a user,
I want to search for companies by entering country and keyword,
So that I can discover potential customers automatically.

**Acceptance Criteria:**

**Given** the Gemini API is configured  
**When** a user submits a search form with:
- country: "Vietnam"
- keyword: "PVC manufacturer"

**Then** the system displays a search form on the home page with:
```
[国家选择] Vietnam ▼
[关键词] [PVC manufacturer text input]
[搜索按钮] 🔍 搜索
[示例] 例如: cable mfg, synthetic leather, flooring export
```

**And** when user clicks "搜索":
1. The search button is disabled and shows "搜索中..." spinner
2. The system calls Gemini Grounding Search API with the query
3. The system waits for response (timeout 30s)

**And** the response is automatically saved to file:
- File path: data/gemini_responses/{timestamp}_{country}_{query}.json
- This happens automatically in gemini_client.call_gemini_grounding_search()
- This allows developers to re-parse data without re-calling the API
- File is saved regardless of format validity

**And** the system reads the saved file and detects response format:
- Read content from data/gemini_responses/{timestamp}_{country}_{query}.json
- Detect format: JSON / Markdown table / CSV / UNKNOWN
- Log the detected format and file path for debugging

**And** when the response format is valid (can be parsed):
- The file path is passed to Story 1.5 (parsing & normalization)
- Story 1.5 reads file and parses the data
- Show success message: "搜索成功，正在处理结果..."

**And** when the response format is invalid or unparseable:
- Show user-friendly error message: "搜索失败：格式错误，请稍后重试"
- Log the raw response file path for debugging
- Allow user to retry the search
- File is preserved for manual inspection

**And** the search form includes proper UX:
- Loading spinner during API call
- Search button is disabled during request
- If request times out (> 30s): show "搜索超时，请重试"

**And** every search request includes a 2-second delay before executing
- To respect API rate limits (NFR6)
- Show this delay to user with countdown: "准备搜索 (2秒延迟)"

**And** the home page displays search statistics (from previous searches):
- 📊 今日统计: 搜索 X 次 | 新增 Y 家 | 去重率 Z%
- (These values are calculated from search_history table)

**Coverage:**
- FR1 (Web表单)
- FR2 (Gemini API)
- FR3 (格式验证)
- NFR6 (限流)
- UX-DR1, UX-DR2, UX-DR3, UX-DR4

---

## Story 1.5: 实现数据解析、规范化与去重逻辑

**Story ID:** 1.5

**User Story:**

As a developer,
I want to parse, normalize, and deduplicate search results,
So that the database contains only clean, unique company records.

**Acceptance Criteria:**

**Given** the Gemini response has been saved to file: data/gemini_responses/{timestamp}_{country}_{query}.json  
**And** the response format has been detected (JSON / Markdown / CSV)  
**When** the parse_response_and_insert() function reads the file and processes it:

**Then** the function first reads the raw response content from the saved file:
- Open file: data/gemini_responses/{timestamp}_{country}_{query}.json
- Parse content according to detected format (JSON / Markdown / CSV)
- Extract company records from parsed content

**And** for each company record in the parsed response:
1. **Parse all 16 fields:**
   - Company name, country, city, year_established, employees, estimated_revenue
   - main_products, export_markets, eu_us_jp_export, raw_materials
   - recommended_product, recommendation_reason, website, contact_email
   - linkedin_url, best_contact_title, prospect_score, priority

2. **Handle missing fields:**
   - If a field is missing → fill with "N/A" (empty string is OK for optional fields)
   - Continue processing (do not skip the record)

3. **Normalize LinkedIn URL:**
   - Input: "https://www.linkedin.com/company/cadivi/"
   - Steps:
     - Convert to lowercase
     - Remove "https://" and "http://"
     - Remove "www." prefix
     - Remove trailing slashes
     - Replace spaces with hyphens
   - Output: "linkedin.com/company/cadivi"
   - Store in linkedin_normalized field

**And** for deduplication:
1. Check if linkedin_normalized already exists in companies table
2. If exists:
   - Record in duplicate_count
   - Skip insertion (don't create duplicate)
   - Log: "跳过重复: {company_name}"
3. If not exists:
   - Insert new company record into database
   - Record in new_count
   - Log: "插入新公司: {company_name}"

**And** create search_history record with:
```
{
  "country": "Vietnam",           # from user input
  "query": "PVC manufacturer",     # from user input
  "result_count": 15,              # total from Gemini (before dedup)
  "new_count": 12,                 # inserted companies
  "duplicate_count": 3,            # skipped companies
  "avg_score": 8.1,                # average score of new companies only
  "high_priority_count": 8,        # companies with score >= 8 (new only)
  "created_at": "2026-04-03T12:00:00"
}
```

**And** when parsing fails for a single record:
- Log error with details: "解析失败 [Row 5]: missing field 'prospect_score'"
- Skip the invalid record
- Continue with next record (partial success)
- Show message: "处理 15 条结果，成功 12 条，失败 3 条"

**And** validate all company scores:
- Score must be integer 1-10
- If score < 1 → clamp to 1
- If score > 10 → clamp to 10
- If score is non-numeric → set to 0 (invalid prospect)

**And** after parsing completes:
- Redirect user to results page with new search results
- Display statistics: "新增: 12 | 重复: 3 | 平均评分: 8.1"

**And** the entire pipeline (API call + parsing) completes within 30 seconds
- If parsing takes > 3 seconds, show status message: "正在处理结果，请稍候..."

**Coverage:**
- FR3 (格式验证)
- FR4 (URL规范化)
- FR5 (16字段数据)
- FR6 (去重)
- FR7 (记录历史)
- NFR3 (失败填充)
- NFR7 (结果提示)

---

## Epic 1 Summary

**Stories Created:** 5  
**Estimated Effort:** 10-12 dev days  
**Priority:** P0 (Blocks all other epics)

**Key Deliverables:**
- ✅ Flask project structure with proper organization
- ✅ SQLite database with companies & search_history tables
- ✅ Gemini API integration with error handling & retry logic
- ✅ Raw Gemini responses saved to local files (data/gemini_responses/)
- ✅ Web search form with proper UX
- ✅ Data parsing, normalization, and deduplication pipeline (reads from saved files)

**Dependencies:** None (Epic 1 is the foundation)

**Next Step:** Epic 2 depends on Epic 1 completion

---

## Code Review Findings (2026-04-04)

**Status:** RESOLVED ✅

### Decision-Needed (Resolved) ✓
- [x] [Review][Decision → Patch B] **save_raw_response() exception handling** — Resolved: Changed to raise `GeminiError` on write failure instead of returning empty string. [gemini_client.py:90-112]

- [x] [Review][Decision → Patch C] **Success message in response** — Resolved: Added message field to JSON response with "搜索成功，正在处理结果..." text. [routes.py:240-245]

### Patches (All Fixed) ✓

- [x] [Review][Patch] **CRITICAL: Global variable race condition** — FIXED: Added `threading.Lock()` protection around `_last_saved_response_path` reads/writes. [gemini_client.py:32-35, 73-75, 107-108]

- [x] [Review][Patch] **HIGH: Unsafe file path construction** — FIXED: Implemented regex-based sanitization to remove all illegal Windows filename characters. [gemini_client.py:95-99]

- [x] [Review][Patch] **HIGH: File system error recovery unclear** — FIXED: Now raises `GeminiError` on save failure, added file existence verification in routes layer. [gemini_client.py:90-112, routes.py:206-230]

- [x] [Review][Patch] **MEDIUM: Missing file path validation** — FIXED: Added explicit file existence check before parsing. [routes.py:224-230]

- [x] [Review][Patch] **MEDIUM: Error message ambiguity** — FIXED: Distinguished between save failures (500) and format errors (400) with specific error messages. [routes.py:201-230]

- [x] [Review][Patch] **MEDIUM: Backward compatibility logic fragile** — FIXED: Improved heuristic by checking for path indicators (/, \, .json) before attempting file read. [db.py:438-460]

- [x] [Review][Patch] **MEDIUM: Test coverage gaps** — FIXED: Added concurrent thread test, special character sanitization test, file verification test. [tests/unit/test_gemini_client.py:195-234]

### Deferred ✓
(Pre-existing or non-blocking)

- [x] [Review][Defer] **LOW: Documentation-implementation mismatch** — Story spec shows `{timestamp}_{country}_{query}.json` but implementation truncates query and applies additional escaping. Minor discrepancy, update docs in next spec revision. [spec vs. gemini_client.py:81-83]

- [x] [Review][Defer] **LOW: Timestamp precision collision** — File naming uses `strftime("%Y%m%d_%H%M%S")` (second precision). Same query run within same second overwrites previous file. Low probability, can optimize in future PR. [gemini_client.py:81]

---

**Document Created:** 2026-04-03
