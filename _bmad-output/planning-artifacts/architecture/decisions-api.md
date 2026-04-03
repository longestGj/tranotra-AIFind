---
title: "API & Communication Decisions"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# API & Communication Decisions

These decisions shape how stages communicate, how APIs are consumed, and how REST endpoints are designed.

---

## Decision 8: Pipeline Stage Communication

**Choice:** Database-mediated async (status-tracked records)  
**Priority:** CRITICAL — blocks implementation

### Pattern

Each company record has a `status` field tracking workflow:

```
discovered → profiled → contacts_found → scored → drafted → reviewed → sent
     ↓          ↓            ↓             ↓         ↓         ↓        ↓
(discover.py) (profile.py) (contacts.py) (score.py) (draft.py) (review.py) (send.py)

Alternative endpoints:
  _failed suffix: e.g., profile_failed, contacts_failed, scored_failed
  → Marks records needing retry or manual intervention
```

### Implementation

```python
# core/models/company.py
class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    # ... (16 data fields)
    
    # Status workflow
    status = Column(
        String,
        default='discovered',
        index=True  # for filtering
    )
    # Legal values:
    # discovered, profiled, profile_failed
    # contacts_found, contacts_failed, no_contacts_found
    # scored, scored_failed
    # drafted, draft_failed
    # reviewed, reviewed_rejected
    # sent, send_failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Each stage reads + writes status
# discover.py:
# INSERT company SET status='discovered'

# profile.py:
# SELECT * FROM companies WHERE status='discovered'
# UPDATE company SET status='profiled' WHERE id=?

# contacts.py:
# SELECT * FROM companies WHERE status='profiled'
# UPDATE company SET status='contacts_found' WHERE id=?
# OR UPDATE company SET status='contacts_failed' WHERE id=?
```

### Rationale

- **Independent Retries:** Can re-run single stage (`--run profile`) without re-running discovery
- **Resilient:** Failed records marked; can fix data + retry
- **Foundation for Async:** In Phase 2, can have multiple workers process same status
- **Database Coordination:** No inter-process messaging needed; SQL is the communication

### Affects

- **CLI:** `python main.py --run discover`, `--run profile`, `--run all`, `--retry-failed`
- **Web Dashboard:** Filter companies by status (discovery_failed, contacts_found, etc.)
- **Logging:** Track status transitions (company X: discovered → profiled → scored)

---

## Decision 9: API Client Error Handling

**Choice:** Exceptions bubble up (specific exceptions per API)  
**Priority:** IMPORTANT — shapes recovery logic

### Exception Hierarchy

```python
# infrastructure/exceptions.py
class APIError(Exception):
    """Base exception for all API errors"""
    pass

class GeminiError(APIError):
    pass

class GeminiRateLimitError(GeminiError):
    pass

class GeminiParseError(GeminiError):
    pass

class GeminiTimeoutError(GeminiError):
    pass

class ApolloError(APIError):
    pass

class ApolloNotFoundError(ApolloError):
    pass

class ApolloQuotaExceededError(ApolloError):
    pass

class HunterError(APIError):
    pass

class HunterInvalidEmailError(HunterError):
    pass

class AliyunError(APIError):
    pass

class AliyunSendFailedError(AliyunError):
    pass
```

### Stage-Level Handling

```python
# pipeline/contacts.py
def process_company(company: Company):
    """Find contacts for company; handle API errors gracefully"""
    try:
        contacts = apollo_client.search_people(company.domain)
        company.status = 'contacts_found'
        
    except ApolloNotFoundError:
        # No contacts available for this company
        logger.info(f"No contacts found for {company.name}")
        company.status = 'no_contacts_found'
        
    except ApolloQuotaExceededError:
        # Quota exhausted; mark for later retry
        logger.warning(f"Apollo quota exceeded for {company.name}")
        company.status = 'contacts_quota_exceeded'
        
    except ApolloError as e:
        # Other Apollo errors
        logger.error(f"Apollo API error for {company.name}: {e}")
        company.status = 'contacts_failed'
```

### Rationale

- **Fine-Grained Control:** Different errors handled differently (quota vs. not-found)
- **Explicit Semantics:** Exception type tells you exactly what went wrong
- **Per-API Decisions:** Each API has own exception hierarchy
- **Fail-Soft Batches:** Stage catches exceptions, records status, continues

---

## Decision 10: REST API Endpoint Design

**Choice:** Simple CRUD REST (standard conventions, basic filtering)  
**Priority:** IMPORTANT — shapes dashboard + integrations

### Endpoints

```
GET  /api/companies              # List all companies (paginated)
GET  /api/companies?country=VN   # Filter by country
GET  /api/companies?priority=HIGH # Filter by priority
GET  /api/companies?status=contacted # Filter by status
GET  /api/companies/<id>         # Single company detail (with related data)
GET  /api/companies/<id>/contacts # Contacts for company
GET  /api/emails?status=pending   # Pending emails for review
POST /api/emails/<id>/approve    # Approve email
POST /api/emails/<id>/reject     # Reject email (mark as reviewed_rejected)
```

### Response Format

```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "id": 1,
        "name": "CADIVI",
        "country": "Vietnam",
        "status": "profiled",
        "prospect_score": 9,
        "priority": "HIGH"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 487
    }
  },
  "error": null
}
```

### Implementation

```python
# presentation/blueprints/api.py
from flask import Blueprint, request, jsonify

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/companies', methods=['GET'])
def list_companies():
    """List companies with optional filtering"""
    country = request.args.get('country')
    priority = request.args.get('priority')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = db.session.query(Company)
    
    if country:
        query = query.filter_by(country=country)
    if priority:
        query = query.filter_by(priority=priority)
    if status:
        query = query.filter_by(status=status)
    
    total = query.count()
    companies = query.paginate(page=page, per_page=per_page).items
    
    return jsonify({
        'success': True,
        'data': {
            'companies': [c.to_dict() for c in companies],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total
            }
        },
        'error': None
    })

@api_bp.route('/companies/<int:company_id>', methods=['GET'])
def get_company(company_id):
    """Get single company with related data"""
    company = db.session.query(Company).get(company_id)
    if not company:
        return jsonify({
            'success': False,
            'data': None,
            'error': {
                'code': 'NOT_FOUND',
                'message': f'Company {company_id} not found',
                'status': 404
            }
        }), 404
    
    contacts = db.session.query(Contact).filter_by(company_id=company_id).all()
    
    return jsonify({
        'success': True,
        'data': {
            **company.to_dict(),
            'contacts': [c.to_dict() for c in contacts]
        },
        'error': None
    })
```

### Rationale

- **Standard REST:** Familiar patterns for web developers
- **Simple Filtering:** No complex query language; URL params sufficient for Phase 1
- **N+1 Acceptable:** Multiple requests per page load OK for small datasets
- **Pagination:** Handle large result sets (487+ companies)
- **Envelope Format:** Consistent success/error structure (defined in patterns.md)

---

**Next:** Read [decisions-frontend.md](decisions-frontend.md) for dashboard and UI decisions.
