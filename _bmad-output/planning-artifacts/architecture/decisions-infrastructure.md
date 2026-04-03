---
title: "Infrastructure & Deployment Decisions"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Infrastructure & Deployment Decisions

---

## Decision 14: Logging & Error Tracking

**Choice:** File-based structured JSON logging  
**Priority:** IMPORTANT — debugging + ops visibility

### Configuration

```python
# infrastructure/logger.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logger():
    """Setup structured JSON logging"""
    logger = logging.getLogger('tranotra')
    
    # File handler with JSON formatter
    handler = logging.FileHandler('./logs/pipeline.log')
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(log_level)
    
    return logger

logger = setup_logger()
```

### Log Format

```json
{
  "timestamp": "2026-04-03T15:30:00.123Z",
  "level": "INFO",
  "logger": "gemini_client",
  "message": "Gemini search completed",
  "context": {
    "country": "Vietnam",
    "query": "PVC manufacturer",
    "result_count": 15,
    "duration_ms": 8234
  }
}
```

### Log Levels

- **DEBUG** — Development info (config loaded, DB initialized)
- **INFO** — User actions (search performed, batch completed)
- **WARNING** — Minor issues (slow query, approaching rate limit)
- **ERROR** — Recoverable failures (API error, parse error, retry)
- **CRITICAL** — Unrecoverable failures (database corruption, API key missing)

### Rationale

- **Machine-Parseable:** JSON format easy for log analysis tools
- **Structured Context:** Additional fields (country, duration, etc.) for debugging
- **Scalable:** Ready for Phase 2 log aggregation (ELK, Splunk, etc.)
- **One Dependency:** python-json-logger (lightweight)

### Affects

- **File Location:** `./logs/pipeline.log` (gitignore'd)
- **Rotation:** Manual (user responsibility in Phase 1; auto-rotation Phase 2)
- **Retention:** 7 days (user responsibility)

---

## Decision 15: Local Scheduling & Batch Execution

**Choice:** Manual execution via CLI (no built-in scheduler)  
**Priority:** IMPORTANT — simplicity vs. automation

### Usage

```bash
# Discover companies
python main.py --run discover --market Vietnam --query "PVC manufacturer"

# Profile discovered companies
python main.py --run profile

# Find contacts
python main.py --run contacts

# Full pipeline
python main.py --run all

# Email review
python main.py --review

# Send approved emails
python main.py --send

# Retry failed records
python main.py --retry-failed --stage profile
```

### Implementation

```python
# src/tranotra/cli.py
import click

@click.group()
def cli():
    """Tranotra Leads CLI"""
    pass

@cli.command()
@click.option('--market', default='Vietnam')
@click.option('--query', required=True)
def discover(market, query):
    """Discover companies via Gemini"""
    from pipeline import discover_stage
    discover_stage.process(market, query)

@cli.command()
def profile():
    """Profile discovered companies"""
    from pipeline import profile_stage
    profile_stage.process()

@cli.command()
def review():
    """Review pending emails"""
    from pipeline import review_stage
    review_stage.process()

if __name__ == '__main__':
    cli()
```

### Rationale

- **Simplest Implementation:** User runs when they want; no scheduler complexity
- **Full Control:** User decides batch size, timing, markets
- **Phase 1 Sufficient:** Good for MVP validation
- **Phase 2+:** Can add APScheduler for scheduled runs

### Optional Enhancement (User-Initiated)

User can set up OS-level scheduler:

```bash
# macOS/Linux: crontab
0 9 * * * cd ~/tranotra-leads && python main.py --run all >> logs/cron.log 2>&1

# Windows: Task Scheduler
# Create task: "Run Tranotra" → C:\Python\python.exe main.py --run all
```

---

## Decision 16: Monitoring & Health Checks

**Choice:** Summary report + exit codes  
**Priority:** IMPORTANT — user visibility + scripting

### Batch Summary Output

```
═══════════════════════════════════════════════════════════
  BATCH SUMMARY — 2026-04-03 15:30:00
═══════════════════════════════════════════════════════════

discover:   487 companies discovered (0 errors)
profile:    423 completed, 3 failed (profile_failed status)
contacts:   180 found, 243 no results, 64 errors → retry queue
score:      612 scored; 401 HIGH, 154 MEDIUM, 57 LOW
draft:      401 emails generated (pending review)
review:     0 approved, 401 pending
send:       0 emails sent

Overall Status: PARTIAL_FAILURE
  → Some stages had errors; check logs/pipeline.log:123
  → 64 records in contacts_failed status; rerun --stage contacts after fix

Elapsed: 4m 23s
```

### Exit Codes

```
0  — Full success (all stages completed without errors)
1  — Partial success (some records failed; batch continued)
2  — Failure (critical error; batch stopped early)
```

### Implementation

```python
# main.py
def main():
    try:
        result = run_pipeline()
        print_summary(result)
        
        if result['failed_count'] == 0:
            sys.exit(0)  # Full success
        elif result['total_count'] > 0:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Total failure
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"FATAL ERROR: {e}")
        sys.exit(2)

def print_summary(result):
    print(f"\\n{'═' * 60}")
    print(f"  BATCH SUMMARY — {datetime.now().isoformat()}")
    print(f"{'═' * 60}\\n")
    
    for stage, stats in result['stages'].items():
        print(f"{stage:15} {stats['successful']:6} successful, {stats['failed']:4} failed")
    
    print(f"\\nElapsed: {result['duration_seconds']}s")
    print(f"Status: {result['overall_status']}")
```

### Rationale

- **Clear Visibility:** User sees what happened at a glance
- **Script-Friendly:** Exit codes enable shell scripting (`if [ $? -eq 0 ]; then`)
- **Logging:** Details in logs for debugging; summary for user comfort
- **Phase 1 OK:** No complex monitoring; Phase 2 can add dashboards

### Affects

- **Error Handling:** All stages contribute to summary statistics
- **Logging:** Final log entry includes summary as JSON
- **CI/CD:** Exit codes enable GitHub Actions workflows

---

**Next:** Read [project-structure.md](project-structure.md) for technology stack and project organization.
