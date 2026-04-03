---
title: "Implementation Patterns & Consistency Rules"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Implementation Patterns & Consistency Rules

All agents MUST follow these standards to ensure consistency across modules.

---

## Pattern 1: Database Column Naming Convention

**Rule:** Use `snake_case` for all database columns and Python attributes.

```python
# ✅ CORRECT
company_name = Column(String)
estimated_revenue = Column(String)
year_established = Column(Integer)
linkedin_normalized = Column(String, unique=True)
prospect_score = Column(Integer)
eu_us_jp_export = Column(Boolean)
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, onupdate=datetime.utcnow)

# ❌ WRONG
companyName = Column(String)  # camelCase
company_Name = Column(String)  # mixed
EstimatedRevenue = Column(String)  # PascalCase
```

**Enforcement:** Code review + SQLAlchemy validation.

---

## Pattern 2: API Response Envelope Format

**Rule:** All API responses use envelope format: `success`, `data`, `error`.

```json
// ✅ SUCCESS
{
  "success": true,
  "data": { "id": 1, "name": "CADIVI", "country": "Vietnam" },
  "error": null
}

// ✅ ERROR
{
  "success": false,
  "data": null,
  "error": {
    "code": "COMPANY_NOT_FOUND",
    "message": "Company with ID 999 not found",
    "status": 404,
    "timestamp": "2026-04-03T15:30:00Z"
  }
}
```

**Implementation:**

```python
def list_companies():
    companies = db.session.query(Company).all()
    return {
        "success": True,
        "data": {"companies": [c.to_dict() for c in companies]},
        "error": None
    }
```

---

## Pattern 3: Error Response Structure

**Rule:** Error responses include code, message, status, timestamp, details.

```python
def handle_error(error_code: str, message: str, status: int, details: dict = None):
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
    }, status
```

**Common Codes:**
- `NOT_FOUND` — Resource not found (404)
- `VALIDATION_ERROR` — Input validation failed (400)
- `RATE_LIMIT_EXCEEDED` — API rate limit hit (429)
- `INTERNAL_ERROR` — Server error (500)

---

## Pattern 4: Timestamp Format (ISO 8601)

**Rule:** All timestamps in ISO 8601 format with timezone.

```python
# ✅ CORRECT
"2026-04-03T15:30:00.123Z"  # With milliseconds
"2026-04-03T15:30:00Z"      # Without milliseconds

# ❌ WRONG
"04/03/2026 15:30"          # Non-ISO format
"2026-04-03 15:30:00"       # No timezone
```

**Implementation:**

```python
from datetime import datetime

def get_timestamp():
    return datetime.utcnow().isoformat() + 'Z'
    # OR: datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
```

---

## Pattern 5: Function Naming (Verb-Subject)

**Rule:** Function names use verb-subject pattern in snake_case.

```python
# ✅ CORRECT (Verb-Subject)
def parse_gemini_response(text: str) -> dict:
    pass

def normalize_linkedin_url(url: str) -> str:
    pass

def calculate_prospect_score(company: Company) -> int:
    pass

def insert_company(data: dict) -> int:
    pass

# ❌ WRONG
def gemini_response_parser(text):  # Subject-Verb
    pass

def linkedin_url_normalizer(url):  # Subject-Verb
    pass

def score(company):  # Too vague
    pass
```

---

## Pattern 6: Pipeline Stage Result Format

**Rule:** Each stage returns `StageResult` with counts + status.

```python
class StageResult:
    """Result from a pipeline stage"""
    successful_count: int
    failed_count: int
    skipped_count: int
    errors: List[str]
    duration_seconds: float

# Usage in pipeline stages
def discover(market: str, query: str) -> StageResult:
    result = StageResult(
        successful_count=487,
        failed_count=0,
        skipped_count=3,  # already exist
        errors=[],
        duration_seconds=8.5
    )
    return result
```

---

## Pattern 7: Error Handling in Stages (Log + Continue)

**Rule:** Stages catch errors at record level; log + continue batch.

```python
def process_batch(companies: List[dict]):
    """Fail-soft: continue on individual failures"""
    results = {"successful": 0, "failed": 0}
    
    for company_data in companies:
        try:
            # Process company
            insert_company(company_data)
            results["successful"] += 1
        except Exception as e:
            results["failed"] += 1
            logger.error(
                "Failed to process company",
                extra={
                    "company_name": company_data.get("name"),
                    "error": str(e),
                    "stacktrace": traceback.format_exc()
                }
            )
    
    return results
```

---

## Pattern 8: API Client Exception Hierarchy

**Rule:** Each API has specific exceptions; stage decides recovery.

```python
# infrastructure/gemini_client.py
class GeminiError(Exception):
    pass

class GeminiRateLimitError(GeminiError):
    pass

class GeminiParseError(GeminiError):
    pass

class GeminiTimeoutError(GeminiError):
    pass

# Usage in stage
def discover():
    try:
        response = gemini_client.search(query)
    except GeminiRateLimitError:
        logger.warning("Gemini rate limited; mark for retry")
        company.status = 'discovery_rate_limited'
    except GeminiParseError:
        logger.error("Gemini parse error; skip")
        company.status = 'discovery_parse_failed'
    except GeminiTimeoutError:
        logger.error("Gemini timeout; skip")
        company.status = 'discovery_timeout'
```

---

## Pattern 9: Logging Context & Fields

**Rule:** All logs include context fields for debugging.

```python
logger.error(
    "API request failed",
    extra={
        "api": "gemini",
        "method": "search",
        "status_code": 500,
        "duration_ms": 5000,
        "company_name": "CADIVI",
        "country": "Vietnam",
        "error": "timeout",
        "stacktrace": "..."
    }
)

# Outputs JSON:
# {
#   "timestamp": "2026-04-03T15:30:00Z",
#   "level": "ERROR",
#   "logger": "gemini_client",
#   "message": "API request failed",
#   "api": "gemini",
#   "method": "search",
#   ...
# }
```

---

## Pattern 10: Type Hints in Python Code

**Rule:** Use type hints for function signatures.

```python
# ✅ CORRECT
def parse_gemini_response(text: str) -> Dict[str, Any]:
    pass

def insert_company(data: Company) -> int:
    pass

def calculate_score(company: Company, weights: Dict[str, float]) -> int:
    pass

# ❌ WRONG
def parse_response(text):  # No type hints
    pass
```

**Tools:**
- `mypy` for type checking
- IDE integration for autocomplete

---

## Enforcement Guidelines

1. **Code Review** — All PRs reviewed for pattern compliance
2. **Pre-Commit Hooks** — Run `black`, `isort`, `mypy` before commit
3. **CI/CD** — GitHub Actions fail on type errors + linting issues
4. **Documentation** — Update CLAUDE.md if patterns change

---

**Next:** Read [risk-mitigation.md](risk-mitigation.md) for resilience strategy and known vulnerabilities.
