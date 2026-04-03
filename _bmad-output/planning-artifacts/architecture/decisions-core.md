---
title: "Core Architectural Decisions"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Core Architectural Decisions

These decisions are stable for Phase 1 and shape the core data handling, API interaction, and error strategies.

---

## Decision 1: LinkedIn Deduplication Strategy

**Choice:** Simple URL normalization  
**Priority:** CRITICAL — blocks implementation

### Implementation

```python
# examples/linkedin_normalization.py
def normalize_linkedin_url(url: str) -> str:
    """
    Normalize LinkedIn URL to consistent format for deduplication.
    
    Examples:
      https://linkedin.com/company/Tranotra-Chemical/ 
      → linkedin.com/company/tranotra-chemical
      
      https://www.linkedin.com/company/CADIVI
      → linkedin.com/company/cadivi
    """
    # 1. Lowercase
    url = url.lower()
    
    # 2. Remove protocol (https:// or http://)
    url = url.replace('https://', '').replace('http://', '')
    
    # 3. Remove www. prefix
    url = url.replace('www.', '')
    
    # 4. Remove trailing slashes
    url = url.rstrip('/')
    
    # 5. Replace spaces with hyphens
    url = url.replace(' ', '-')
    
    return url
```

### Rationale

- **Speed:** Single regex + string operations; no external calls
- **Sufficient:** Company duplicate rates low in target markets (Vietnam, Thailand, etc.)
- **Idempotent:** Safe to re-run deduplication without side effects

### Affects

- **Database:** `companies.linkedin_normalized` is UNIQUE constraint
- **Pipeline:** `discover.py` sets normalized URL at insertion
- **Deduplication:** Check before insert; skip if `linkedin_normalized` exists

### Counterexample

❌ **NOT Complex LinkedIn API matching** (would require API calls, more fragile)

---

## Decision 2: Prospect Scoring Model

**Choice:** Simplified 4-factor model (1-9 scale)  
**Priority:** IMPORTANT — shapes data flow

### Scoring Rubric

```
Total Score = Size_Score + PVC_Score + Export_Score + Email_Score

Size_Score (1-3 points):
  - 1 pt: < 50 employees
  - 2 pts: 50-500 employees  
  - 3 pts: > 500 employees

PVC_Score (1-3 points):
  - 1 pt: Mentions PVC tangentially
  - 2 pts: PVC is secondary product
  - 3 pts: PVC is primary focus

Export_Score (2 points):
  - 0 pts: No export markets
  - 2 pts: Exports to EU, US, or Japan

Email_Score (1 point):
  - 0 pts: No email available
  - 1 pt: Email available

Final Score: 1-9 scale
  HIGH: 8-9
  MEDIUM: 6-7
  LOW: 1-5

MIN_SCORE_TO_CONTACT = 6 (proceed to contact finding)
```

### Rationale

- **MVP Simplicity:** Validates scoring approach before full 16-point model
- **Fast Iteration:** Easy to adjust thresholds based on user feedback
- **Clear Decision Trees:** `if score < 6: skip_contact_finding()`
- **Phase 2+:** Can expand to 16-point model with more factors (revenue, growth, etc.)

### Implementation

```python
# core/services/scoring.py
def calculate_prospect_score(company: Company) -> int:
    """Calculate prospect score (1-9)"""
    score = 0
    
    # Size (1-3)
    employees = int(company.employees.split('-')[0]) if company.employees else 0
    if employees >= 500:
        score += 3
    elif employees >= 50:
        score += 2
    else:
        score += 1
    
    # PVC focus (1-3)
    pvc_relevance = measure_pvc_focus(company.main_products)
    score += pvc_relevance  # 1-3
    
    # Export (2 pts)
    if company.eu_us_jp_export:
        score += 2
    
    # Email (1 pt)
    if company.contact_email:
        score += 1
    
    # Clamp to 1-9
    return max(1, min(9, score))

def prioritize(score: int) -> str:
    if score >= 8: return "HIGH"
    elif score >= 6: return "MEDIUM"
    else: return "LOW"
```

### Affects

- **Contacts Stage:** Skip if score < 6
- **Email Draft Stage:** Personalization tone based on priority
- **Dashboard:** Color-coded badges (HIGH=green, MEDIUM=yellow, LOW=gray)
- **CSV Export:** Include score + priority in output

---

## Decision 3: Gemini Response Validation

**Choice:** Lenient parsing with fail-soft handling  
**Priority:** IMPORTANT — prevents pipeline failure

### Strategy

```
Try JSON parsing → Try CSV parsing → Try Markdown table parsing
  ↓ (any succeeds)
Extract 16 fields from response
  ↓ (missing fields filled with "N/A")
Return records + count of successful + count of failed
  ↓ (batch continues even if some records malformed)
Log malformed records to logs/raw_responses/ for debugging
```

### Error Handling

```python
# infrastructure/gemini_client.py
def parse_gemini_response(response_text: str) -> tuple[List[dict], List[str]]:
    """Parse Gemini response (flexible format)
    
    Returns:
      - List of parsed company records (may have "N/A" fields)
      - List of error messages for malformed records
    """
    records = []
    errors = []
    
    # Try JSON first
    try:
        data = json.loads(response_text)
        records = extract_companies_from_json(data)
        return records, []
    except json.JSONDecodeError:
        pass
    
    # Try CSV
    try:
        records = parse_csv_response(response_text)
        return records, []
    except Exception:
        pass
    
    # Try Markdown table
    try:
        records = parse_markdown_table(response_text)
        return records, []
    except Exception:
        errors.append(f"Could not parse response format")
    
    return records, errors

def extract_companies_from_json(data: dict) -> List[dict]:
    """Extract 16 company fields from JSON"""
    companies = []
    for item in data.get('companies', []):
        company = {
            'name': item.get('name', 'N/A'),
            'country': item.get('country', 'N/A'),
            'city': item.get('city', 'N/A'),
            # ... (14 more fields, all with 'N/A' default)
        }
        companies.append(company)
    return companies
```

### Rationale

- **Robustness:** API response format sometimes varies; accept all formats
- **Complete Data:** "N/A" fields acceptable; better than rejecting entire batch
- **Debugging:** Log raw responses for later analysis
- **Phase 1 OK:** Good enough for MVP; Phase 2 can add schema validation

### Affects

- **Discovery:** `discover.py` handles parsing errors gracefully
- **Logging:** Raw malformed responses logged to `logs/raw_responses/{timestamp}.txt`
- **User Feedback:** "Processed 50 records, 48 successful, 2 malformed (see logs)"

### Counterexample

❌ **NOT Strict schema validation** (would fail batch on single malformed record)

---

## Decision 4: Database Transaction Strategy

**Choice:** Record-level resilience (fail-soft per record)  
**Priority:** CRITICAL — shapes error recovery

### Pattern

```
For each company in batch:
  try:
    Validate fields
    Insert or update company
    Mark status = discovered
  except Exception as e:
    Log error with context (company name, error details)
    Mark status = discovery_failed
    Continue with next company
```

### Implementation

```python
# pipeline/discover.py
def process_batch(companies: List[dict]):
    """Process batch of companies, continue on individual failures"""
    successful = 0
    failed = 0
    
    session = get_db_session()
    
    for company_data in companies:
        try:
            # Validate + normalize
            company_data['linkedin_normalized'] = normalize_url(company_data['linkedin_url'])
            
            # Check for duplicate
            existing = session.query(Company).filter_by(
                linkedin_normalized=company_data['linkedin_normalized']
            ).first()
            
            if existing:
                logger.info(f"Skipping duplicate: {company_data['name']}")
                continue
            
            # Insert
            company = Company(**company_data)
            company.status = 'discovered'
            session.add(company)
            session.commit()
            successful += 1
            
        except Exception as e:
            session.rollback()
            failed += 1
            logger.error(
                f"Failed to insert company",
                extra={
                    'company_name': company_data.get('name'),
                    'error': str(e),
                    'stacktrace': traceback.format_exc()
                }
            )
    
    # Summary
    logger.info(f"Batch complete: {successful} inserted, {failed} failed")
    return {"successful": successful, "failed": failed}
```

### Rationale

- **Maximum Throughput:** Batch continues despite individual failures
- **Data Quality:** Failed records don't corrupt database (transaction rollback)
- **Visibility:** All errors logged for debugging + user reporting
- **Phase 1 OK:** Orphaned records acceptable; Phase 2 adds checkpoint/resume

### Affects

- **All Pipeline Stages:** Follow same fail-soft pattern
- **Status Tracking:** `status` field marks workflow state (discovered, profiled, contacts_found, etc.)
- **Logging:** Comprehensive error context in `logs/pipeline.log`
- **User Summary:** "Processed 100, successful 97, failed 3 (see logs/pipeline.log:123)"

### Retry Strategy

```
On failure (status = discovery_failed):
  User can manually fix data + rerun stage
  OR user can use --retry-failed flag to auto-retry failed records
  (Phase 2: automatic retry on transient errors)
```

---

## Decision 5: Data Encryption

**Choice:** No encryption (plaintext SQLite)  
**Priority:** IMPORTANT — security stance

### Assumption

- **Local Machine:** User runs pipeline on their own computer
- **User Controls Access:** Physical device security sufficient
- **Single User:** Not multi-user or shared environment
- **Non-Regulated Data:** Not health/payment/highly sensitive

### Rationale

- **Simplicity:** Encryption adds complexity + performance overhead
- **Phase 1 OK:** User can add encryption externally if needed (disk encryption, etc.)
- **Phase 2+:** Revisit if multi-user or remote access added

### Affects

- **Database:** No encryption layer in SQLite
- **API Keys:** Stored in plaintext `.env` (user responsible for security)
- **Backups:** User backups local `.db` file (consider encryption at rest)

---

## Decision 6: API Key Management

**Choice:** Separate environment files by context  
**Priority:** IMPORTANT — security + testing

### File Structure

```
.env.local           # User's real API keys (gitignore'd)
.env.test            # Pytest fixtures with dummy keys (checked in)
.env.example         # Template for users to copy
.env.development     # (optional) dev machine keys
```

### Configuration Loading

```python
# config.py
import os
from pathlib import Path

def load_config():
    """Load config from appropriate .env file"""
    
    # In pytest: load .env.test
    if 'pytest' in sys.modules:
        env_file = Path('.env.test')
    # In development: load .env.local or .env.development
    else:
        env_file = Path('.env.local') or Path('.env.development')
    
    if not env_file.exists():
        raise ValueError(f"Missing {env_file}. Copy from .env.example")
    
    load_dotenv(env_file)
    
    return {
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'APOLLO_API_KEY': os.getenv('APOLLO_API_KEY'),
        'HUNTER_API_KEY': os.getenv('HUNTER_API_KEY'),
        'ALIYUN_ACCESS_KEY_ID': os.getenv('ALIYUN_ACCESS_KEY_ID'),
        'ALIYUN_SECRET': os.getenv('ALIYUN_SECRET'),
        'ALIYUN_FROM_EMAIL': os.getenv('ALIYUN_FROM_EMAIL'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }
```

### Keys Managed

- `GOOGLE_API_KEY` — Gemini API key
- `APOLLO_API_KEY` — Apollo.io person search
- `HUNTER_API_KEY` — Hunter.io email verification
- `ALIYUN_ACCESS_KEY_ID` + `ALIYUN_SECRET` — Aliyun DirectMail
- `ALIYUN_FROM_EMAIL` — Sender email address for DirectMail
- `LOG_LEVEL` — Logging verbosity (DEBUG, INFO, WARNING, ERROR)

### Rationale

- **Clear Separation:** Real keys not in test suite
- **Security:** `.env.local` gitignore'd; prevents key leaks
- **Template:** `.env.example` helps new users onboard
- **Flexible:** Different keys per environment if needed

### Affects

- **.gitignore:** Include `.env.local`, `logs/`, `db/`
- **Tests:** `conftest.py` uses dummy keys from `.env.test`
- **CI/CD:** GitHub Actions loads from secrets, not .env files

---

## Decision 7: Rate Limit Handling (Phase 1)

**Choice:** Automatic detection + exponential backoff  
**Priority:** IMPORTANT — API resilience

### Strategy

```
1. Parse rate limit headers from API response (X-RateLimit-*)
2. Track quota remaining during batch
3. On approaching limit (< 10% remaining): pause + warn user
4. On 429 error: retry with exponential backoff
   - Attempt 1: retry immediately
   - Attempt 2: wait 2s, then retry
   - Attempt 3: wait 4s, then retry
   - After 3 attempts: fail + mark record status = quota_exceeded
5. Log quota state at batch start/end
```

### Implementation

```python
# infrastructure/api_client_base.py
class APIClientBase:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.quota_remaining = None
        self.quota_limit = None
    
    def request_with_retry(self, url: str, max_retries: int = 3) -> dict:
        """Make request with exponential backoff on rate limit"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self._auth_header())
                
                # Parse rate limit headers
                if 'X-RateLimit-Remaining' in response.headers:
                    self.quota_remaining = int(response.headers['X-RateLimit-Remaining'])
                    self.quota_limit = int(response.headers['X-RateLimit-Limit'])
                
                # Check for rate limit error
                if response.status_code == 429:
                    wait_time = (2 ** attempt)  # 1s, 2s, 4s
                    logger.warning(f"Rate limited. Waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                # Check approaching limit
                if self.quota_remaining < (0.1 * self.quota_limit):
                    logger.warning(f"Quota low: {self.quota_remaining}/{self.quota_limit}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                logger.error(f"API request failed: {e} (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise
                continue
        
        raise APIError(f"Failed after {max_retries} retries")
```

### Quota Tracking

```python
# Batch start
logger.info(f"Batch start. Quota remaining: {client.quota_remaining}/{client.quota_limit}")

# Batch end
logger.info(f"Batch end. Quota remaining: {client.quota_remaining}/{client.quota_limit}")
```

### Rationale

- **Smart Behavior:** Detects + adapts to rate limits without external config
- **Phase 1 Sufficient:** Good for MVP; Phase 2 can add persistent queueing
- **User Visibility:** Logs quota state so user can plan batches

### Counterexample

❌ **NOT Persistent queue** (complex; defer to Phase 2)

---

**Next:** Read [decisions-api.md](decisions-api.md) for pipeline communication and API design decisions.
