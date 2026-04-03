---
title: "Risk Mitigation Strategy"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Risk Mitigation Strategy

---

## Phase 1 (MVP) — Lean Approach

### What We DO Implement

✅ **Basic Retry Logic**
- Exponential backoff: 1s → 2s → 4s on transient errors
- Max 3 retries per request
- Covers network timeouts, temporary API failures

✅ **Synchronous, Blocking API Calls**
- Simple to implement; deterministic flow
- Single-threaded; no concurrency complexity
- Sufficient for initial batches (100-500 companies)

✅ **Comprehensive Error Logging**
- All errors logged with full context
- Raw API responses saved for debugging
- Batch summary shows success/failure breakdown

✅ **Documented Rate Limit Constraints**
- Publish quota limits per API
- User must monitor; app warns on low quota
- Re-run incomplete batches after quota resets

✅ **SQLite Transaction Atomicity**
- Each record wrapped in transaction
- Failed inserts rolled back automatically
- Data integrity maintained despite partial failures

### What We DON'T Implement

❌ **Circuit Breaker Pattern**
→ Deferred to Phase 2 (adds complexity)

❌ **Persistent Job Queueing**
→ Deferred to Phase 2 (requires Redis or DB queue table)

❌ **Async API Calls**
→ Deferred to Phase 2 (single-threaded sufficient for Phase 1)

❌ **Graceful Degradation**
→ Deferred to Phase 2 (skip stage if API unavailable)

❌ **Batch Checkpointing**
→ Deferred to Phase 2 (idempotent re-run from start is OK)

---

## Known Vulnerabilities (Phase 1)

### 1. Rate Limit Cascade

**Problem:** User runs large batch; Apollo quota exhausted mid-operation.

**Phase 1 Mitigation:**
- Log quota at batch start/end
- Warn user when approaching limit (< 10% remaining)
- User manually stops batch, waits for reset, reruns

**Phase 2+ Fix:**
- Quota tracking + automatic backoff
- Queueing system for pending requests
- Automatic retry after reset

**Impact:** Medium — Affects large batches (1000+ companies); small batches OK

---

### 2. API Dependency Chain Failure

**Problem:** Apollo timeout blocks entire pipeline; no fallback.

**Phase 1 Mitigation:**
- Error logged; user notified
- Mark records as `contacts_failed`
- User reruns `--stage contacts` after API recovery

**Phase 2+ Fix:**
- Circuit breaker pattern
- Skip contacts stage; proceed to scoring if unavailable
- Automatic retry after cooldown period

**Impact:** Medium — Blocks email generation; user can skip to dashboard

---

### 3. Batch Operation Loss

**Problem:** System crashes mid-batch; no checkpoint recovery.

**Phase 1 Mitigation:**
- Idempotent re-run from beginning (safe due to LinkedIn dedup)
- Discovered companies won't be duplicated on retry
- Failed records marked with `_failed` status

**Phase 2+ Fix:**
- Checkpoint after every 50 records
- Resume from checkpoint on restart
- No re-processing of successful records

**Impact:** Low-Medium — User can retry safely; minimal re-processing

---

### 4. CLI ↔ Web Dashboard Desync

**Problem:** User runs batch via CLI while web dashboard active; conflicting writes.

**Phase 1 Mitigation:**
- SQLite atomic writes handle most cases
- Single-user scenario; rare in practice
- Document warning in README

**Phase 2+ Fix:**
- Pessimistic locking (operation_locks table)
- Prevent concurrent writes
- Queue conflicts for sequential execution

**Impact:** Low — Rare in single-user scenario; data integrity maintained

---

### 5. Performance Degradation

**Problem:** Batch slows down as database grows (no indexes).

**Phase 1 Mitigation:**
- No query optimization in Phase 1 MVP
- Acceptable for first 1000 companies
- Document performance expectations

**Phase 2+ Fix:**
- Add indexes on frequently queried columns
- Pagination for large result sets
- Query optimization + benchmarking

**Impact:** Low-Medium — Affects after scale-up (1000+)

---

### 6. Missing or Malformed Gemini Responses

**Problem:** Gemini returns unexpected format; parser fails.

**Phase 1 Mitigation:**
- Lenient parsing (try JSON → CSV → Markdown)
- Allow "N/A" fields; don't reject record
- Log malformed responses for debugging
- Batch continues with partial data

**Phase 2+ Fix:**
- Schema validation + type checking
- Retry with different prompt if format incorrect
- Human review queue for edge cases

**Impact:** Low — Rare in practice; data quality acceptable with "N/A"

---

## Phase 2+ Resilience Roadmap

```
Phase 2 (Enhanced Reliability):
├── Async API calls (concurrent processing)
├── Persistent job queueing (Redis or file-based)
├── Circuit breaker registry (per-API failure tracking)
├── Batch checkpointing + resume capability
├── Rate limit monitoring + alerting
└── Graceful degradation strategies

Phase 3+ (Enterprise):
├── Multi-user support (user authentication + isolation)
├── Data encryption (at-rest + in-transit)
├── Audit logging (compliance + debugging)
├── Automated testing (E2E + load testing)
├── Built-in scheduler (APScheduler)
└── Real-time dashboard (WebSocket updates)
```

---

## Risk Acceptance Criteria

| Risk | Phase 1 | Phase 2+ | Acceptance |
|------|---------|----------|-----------|
| Rate Limit Cascade | User monitors | Auto backoff + queue | ✅ Acceptable |
| API Chain Failure | Manual retry | Circuit breaker | ✅ Acceptable |
| Batch Operation Loss | Re-run from start | Checkpointing | ✅ Acceptable |
| CLI ↔ Web Desync | Rare; atomic writes | Locking | ✅ Acceptable |
| Performance | 1000 limit | Optimized | ✅ Acceptable |
| Malformed Data | Lenient parsing | Validation | ✅ Acceptable |

---

## Testing Strategy for Resilience

### Unit Tests

```python
# tests/unit/test_error_handling.py
def test_gemini_rate_limit_retry():
    """Verify retry logic on 429 response"""
    pass

def test_record_level_failure():
    """Verify batch continues on individual record failure"""
    pass

def test_lenient_parsing():
    """Verify partial data accepted (missing fields = N/A)"""
    pass
```

### Integration Tests

```python
# tests/integration/test_pipeline_resilience.py
def test_pipeline_with_api_failures():
    """Full pipeline with mock API returning errors"""
    pass

def test_batch_completion_summary():
    """Verify summary counts successes + failures"""
    pass

def test_idempotent_rerun():
    """Verify deduplication prevents duplicate processing"""
    pass
```

### Manual Testing

- [ ] Simulate network timeout (mock API hangs)
- [ ] Simulate rate limit error (mock API returns 429)
- [ ] Simulate malformed response (invalid JSON)
- [ ] Kill process mid-batch; verify rerun safe
- [ ] Run two CLI commands simultaneously; check for conflicts

---

## Operational Guidelines

### For Users

1. **Monitor Batch Progress**
   - Watch console output during batch
   - Check `logs/pipeline.log` for errors
   - Note quota remaining in summary

2. **Handle Failures**
   - If batch fails, check logs
   - Fix any data issues (if applicable)
   - Rerun `--run discover` or `--retry-failed`
   - Idempotent; safe to retry

3. **Plan for Scale**
   - Start with small batches (100 companies)
   - Monitor performance (batch time)
   - Document quota usage per API
   - Plan Phase 2 for large-scale runs (1000+)

### For Developers

1. **Error Handling**
   - Catch errors at record level; log + continue
   - Don't silently fail; always log + user-facing message
   - Include context (company name, error type, remedy)

2. **Testing**
   - All external APIs mocked (no real API calls in tests)
   - Test both success + failure paths
   - Verify batch continues on failures

3. **Logging**
   - Use structured JSON logging
   - Include context fields for debugging
   - Log rate limit state at batch start/end

---

## Monitoring Checklist

### Before Release

- [ ] All external APIs mocked in test suite
- [ ] Error logging comprehensive (all paths tested)
- [ ] Batch summary accurate (counts + status)
- [ ] SQLite transaction handling verified
- [ ] Rate limit detection working
- [ ] Idempotent rerun tested

### After Release

- [ ] Monitor batch logs (check error patterns)
- [ ] Track user feedback (frequent failures?)
- [ ] Performance metrics (batch time, company count)
- [ ] Quota usage per API (plan for Phase 2)

---

**Summary:** Phase 1 accepts known risks in favor of simplicity + speed. Phase 2+ adds resilience as needed based on user feedback and scale requirements.

---

**End of Architecture Documentation**

For questions or updates, see [index.md](index.md) or contact the development team.
