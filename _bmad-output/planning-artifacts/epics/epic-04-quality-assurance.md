---
epic: 4
epicTitle: "系统可迭代性与质量保证 (Reliability, Performance & Quality)"
storyCount: 2
frCoverage: ""
nfrCoverage: "NFR1, NFR2, NFR3, NFR5, NFR7, NFR8"
uxdrCoverage: ""
createdDate: "2026-04-03"
dependsOn: "All epics (cross-cutting)"
priority: "P1-P2"
---

# Epic 4: 系统可迭代性与质量保证 (Reliability, Performance & Quality)

**Epic 目标:** 系统具有完善的错误处理、性能优化、容错能力，支持持续迭代优化

**用户成果:** 系统在各种失败场景下能优雅降级，提供清晰的错误提示和自动恢复机制

**覆盖需求:**
- Non-Functional: NFR1, NFR2, NFR3, NFR5, NFR7, NFR8

**开发优先级:** P1 (Essential for production readiness)

**类型:** 横切关注点（Cross-cutting concern）
- 应在所有 Epic 中并行实施
- 不阻塞其他 Epic，但增强系统健壮性

---

## Story 4.1: 完善错误处理与网络容错机制

**Story ID:** 4.1

**User Story:**

As a system,
I want to handle errors gracefully and recover from failures automatically,
So that users experience a reliable, fault-tolerant service.

**Acceptance Criteria:**

**Given** the system encounters various failure scenarios  
**When** errors occur  
**Then** the system responds appropriately:

### NFR1: 数据库初始化时自动创建所需表

**Scenario: Database not initialized**
```
Given: First run of the application
When: app starts
Then:
  - Check if database file exists at ./data/leads.db
  - If not: automatically create it
  - If exists: verify all required tables (companies, search_history)
  - If tables missing: create them
  - Log: "Database initialized successfully" or "Database verified"
  - Application continues normally
```

### NFR2: Gemini 格式验证失败时提示用户

**Scenario: Gemini returns unexpected format**
```
Given: Gemini API returns invalid/unexpected format
When: Parser attempts to validate response
Then:
  - Detect format is invalid (not JSON/CSV/Markdown table)
  - Log error: "Invalid Gemini response format: {sample of response}"
  - Show user-friendly message: "搜索失败：格式错误，请稍后重试"
  - Provide retry button: [重试]
  - Allow user to try again with same search
```

### NFR3: 解析失败字段用"N/A"填充，不中断流程

**Scenario: Missing or malformed fields in search results**
```
Given: Gemini response has missing or invalid fields
When: Parser processes each record
Then:
  - For optional fields: fill with "N/A" if missing
  - For numeric fields (score, year): validate type
    - If invalid: set to default value (0 for score, NULL for year)
    - Log warning: "Invalid field value: score='abc', using default"
  - Continue processing next record
  - User sees partial success: "处理 15 条结果，成功 12 条，失败 3 条"
  - Failed records are logged for debugging (never shown to user as failure)
```

### NFR5: 网络中断时自动重连 3 次

**Scenario: Network connection lost during API call**
```
Given: API call to Gemini fails due to network error
When: Request times out or connection error occurs
Then:
  - Automatically retry with exponential backoff:
    - Attempt 1: immediate retry
    - Attempt 2: wait 2 seconds, then retry
    - Attempt 3: wait 4 seconds, then retry
  - After 3 attempts, if still failing:
    - Show user message: "网络连接异常，已尝试 3 次重连，请检查网络"
    - Provide manual retry button
  - Log all retry attempts for debugging
  - No automatic retry > 3 times (avoid spam)
```

### NFR7: 搜索返回 0 结果时提示用户

**Scenario: Gemini search returns no companies**
```
Given: User performs search (e.g., "Vietnam + obscure keywords")
When: Gemini returns 0 results
Then:
  - Show friendly message: "本次未找到，建议修改搜索词"
  - Suggest alternatives:
    - "尝试使用更通用的关键词（如: manufacturer, supplier）"
    - "尝试其他国家的相同关键词"
    - "查看搜索历史，找高效的搜索词"
  - Provide "返回搜索" button to modify and retry
  - Do NOT treat as error (0 results is valid outcome)
```

### NFR8: 本地 Python 运行，无需云端定时任务

**Scenario: System deployment and operation**
```
Given: User downloads and runs application locally
When: User runs: python main.py
Then:
  - Application starts on localhost:5000
  - All operations execute locally (no remote dependency)
  - No scheduled background tasks (all user-triggered)
  - Database stored locally in ./data/leads.db
  - All API calls made by local Python process (no cloud relay)
  - User can run application offline (except Gemini/Apollo/Hunter calls)
  - Log to console and ./logs/app.log
```

### Error Logging & Debugging

**All errors should be logged with context:**
```
Format: [TIMESTAMP] [LEVEL] [MODULE] [MESSAGE]
Example: [2026-04-03 12:00:00] [ERROR] [gemini_client] API request failed: timeout after 30s (attempt 2/3)

Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
Location: ./logs/app.log (rotated daily, keep 7 days)
```

**User-Facing Error Messages:**
- Always friendly and actionable
- Suggest next steps (retry, modify search, check network, etc.)
- Never show stack traces or technical jargon
- Include support info if critical: "如需帮助，请查看 README.md"

### Graceful Degradation

```
Scenario: Database query slow (> 3s)
  - Return cached results from previous search
  - Show message: "数据加载中（显示缓存结果）"
  
Scenario: Export takes > 2s
  - Show progress: "正在导出... 34%"
  - Allow cancel operation
  
Scenario: Page load slow
  - Show skeleton placeholders
  - Progressive loading of data
```

**Coverage:**
- NFR1 (自动初始化)
- NFR2 (格式验证)
- NFR3 (失败填充)
- NFR5 (网络重连)
- NFR7 (结果提示)
- NFR8 (本地运行)

---

## Story 4.2: 性能优化、缓存管理与系统监控

**Story ID:** 4.2

**User Story:**

As a developer,
I want to optimize system performance and monitor application health,
So that the system scales well and issues can be quickly detected.

**Acceptance Criteria:**

### Performance Optimization

**Gemini API Rate Limiting:**
```
Given: Multiple rapid searches from same user
When: User performs search
Then:
  - Enforce 2-second delay between searches (NFR6)
  - Show countdown: "准备搜索 (2秒延迟)"
  - Queue searches if multiple rapid requests
  - Rate limit: max 30 searches/hour per session
  - Log rate limit enforcement
```

**Database Query Optimization:**
```
Given: search_history or companies table grows large
When: User performs queries (results page, dashboard, export)
Then:
  - Indexes created on frequently queried columns:
    - companies: (linkedin_normalized, country, created_at)
    - search_history: (country, created_at, avg_score)
  - Paginated queries: fetch 20-50 records at a time
  - Query timeout: 5 seconds (soft limit, 10s hard limit)
  - If query > 3s: return cached results
  - Log slow queries (> 1s) for optimization
```

**Frontend Performance:**
```
Given: Results page with 100+ cards
When: Page loads
Then:
  - Lazy load images (if any)
  - Lazy load table rows (infinite scroll or pagination)
  - CSS and JS minified
  - CSS inlined for above-the-fold content
  - Initial page load: < 2 seconds
  - Interactive: < 3 seconds
  - Measure with Chrome DevTools Lighthouse
```

### Caching Strategy

**Search Results Cache:**
```
Implementation:
  - Use in-memory cache (e.g., functools.lru_cache or simple dict)
  - Key: {country, query}
  - TTL: 5 minutes (refresh on new search)
  - Size: max 50 cache entries (LRU eviction)

Behavior:
  - Cache hit: return immediately (< 100ms)
  - Cache miss: fetch from DB (< 1s), then cache
  - Manual clear: "Clear Cache" button in admin view (not user-facing in Phase 1)
```

**Search History Cache:**
```
Implementation:
  - Cache last 7 days of search_history (typically 50-100 records)
  - Refresh every 1 hour or on new search
  - Store in memory

Behavior:
  - Queries for 7-day analytics use cached data
  - If fresh data needed: "Refresh Now" button
  - Cache invalidation on new search
```

### System Monitoring & Logs

**Application Logging:**
```
Log Location: ./logs/app.log (UTF-8, rotated daily)
Retention: Keep 7 days of logs
Format: JSON for structured logging
```

**Log Levels:**
```
DEBUG: Development info (config loaded, database initialized)
INFO: User actions (search performed, results exported, view switched)
WARNING: Minor issues (slow query, duplicate company, invalid field)
ERROR: Recoverable failures (Gemini format error, network retry, cache miss)
CRITICAL: Unrecoverable failures (database corruption, critical API error)
```

**Key Events to Log:**
```
- Application startup/shutdown
- Database operations (init, insert, query)
- API calls (Gemini request/response, duration, status)
- User actions (search, export, view switch, pagination)
- Errors and retries (with context)
- Performance metrics (query duration, cache hits, API latency)
```

**Example Log Entry:**
```json
{
  "timestamp": "2026-04-03T12:00:00.123Z",
  "level": "INFO",
  "module": "routes",
  "event": "search_completed",
  "country": "Vietnam",
  "query": "PVC manufacturer",
  "new_count": 15,
  "duplicate_count": 3,
  "duration_ms": 8234,
  "cached": false
}
```

**Performance Metrics:**
```
Track and log:
  - Average API response time (Gemini): target < 8s
  - Database query time: target < 1s
  - Page load time: target < 2s
  - Cache hit rate: target > 80% for dashboard
  
Review periodically (weekly):
  - Identify slow queries
  - Monitor cache effectiveness
  - Detect API rate limit issues
```

### Health Checks

**Startup Health Check:**
```
When: Application starts
Then:
  - Verify database connectivity: ✓
  - Verify Gemini API key configured: ✓
  - Create log directory if missing: ✓
  - Verify ./data directory writable: ✓
  - If any check fails: log ERROR and exit with clear message
```

**Runtime Health Check (optional, Phase 2+):**
```
GET /health endpoint returns:
{
  "status": "healthy",
  "database": "ok",
  "timestamp": "2026-04-03T12:00:00Z"
}
```

### Testing & Validation

**Manual Testing Checklist:**
- [ ] Search with no network: verify retry logic works
- [ ] Kill database connection mid-query: verify error handling
- [ ] Return 0 results from Gemini: verify user message
- [ ] Export 500 companies: verify performance
- [ ] Perform 50 searches: verify rate limiting
- [ ] Review logs: verify all events logged appropriately

**Automated Testing (Phase 2+):**
- Unit tests for error handlers
- Integration tests for API error scenarios
- Load testing for performance baseline

**Coverage:**
- NFR4 (超时缓存) — implied in cache strategy
- NFR6 (限流) — enforced in rate limiting
- Performance optimization across the board

---

## Epic 4 Summary

**Stories Created:** 2  
**Estimated Effort:** 4-6 dev days  
**Priority:** P1 (Cross-cutting, essential for production)

**Key Deliverables:**
- ✅ Comprehensive error handling for all failure scenarios
- ✅ Network retry logic (3 attempts with exponential backoff)
- ✅ Graceful degradation and user-friendly error messages
- ✅ Performance optimization (caching, indexing, pagination)
- ✅ Structured logging for debugging and monitoring
- ✅ Rate limiting and API quota management

**Characteristics:**
- **Cross-cutting:** Applies to all other epics
- **Parallel Implementation:** Can be done alongside Epics 1-3
- **Iterative Improvement:** Can be enhanced in later phases

**Testing Strategy:**
- Manual testing of error scenarios
- Performance benchmarking (load testing in Phase 2)
- Log review and analysis (weekly in production)

**Next Step:** No dependencies. Can be implemented in parallel with other epics.

---

**Document Created:** 2026-04-03
