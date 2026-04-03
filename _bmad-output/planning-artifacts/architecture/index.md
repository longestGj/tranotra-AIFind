---
title: "Architecture Documentation Index"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
user: "Ailong"
---

# Architecture Documentation Index

**Tranotra Leads: Automated Customer Discovery & Outreach Pipeline**

This directory contains the complete architecture specification for the Tranotra Leads project, split into focused documents for easier navigation and maintenance.

---

## 📚 Documentation Structure

### 1. **[requirements.md](requirements.md)** — Requirements & Constraints
- Functional requirements overview (10 modules across 5 stages)
- Non-functional requirements (local execution, persistence, API resilience)
- Technical constraints and dependencies
- Scale and complexity assessment

**Use this when:** Understanding what the system must do and how it must behave

---

### 2. **[decisions-core.md](decisions-core.md)** — Core Architectural Decisions
- LinkedIn deduplication strategy
- Prospect scoring model
- Gemini response validation
- Database transaction strategy
- Data encryption approach
- API key management
- Rate limit handling

**Use this when:** Making decisions about data handling, API interaction, and error strategies

---

### 3. **[decisions-api.md](decisions-api.md)** — API & Communication Decisions
- Pipeline stage communication pattern
- API client error handling approach
- REST API endpoint design
- External API integration points (Gemini, Apollo, Hunter, Aliyun)

**Use this when:** Building API clients, designing stage communication, or implementing REST endpoints

---

### 4. **[decisions-frontend.md](decisions-frontend.md)** — Frontend Architecture Decisions
- Dashboard technology stack (Bootstrap + Vanilla JavaScript)
- Dashboard views and interaction patterns
- Real-time data refresh strategy

**Use this when:** Building web dashboard, designing UI components, or implementing user-facing features

---

### 5. **[decisions-infrastructure.md](decisions-infrastructure.md)** — Infrastructure & Deployment Decisions
- Logging and error tracking setup
- Local scheduling and batch execution
- Monitoring and health checks
- Summary reporting

**Use this when:** Setting up deployment pipeline, implementing logging, or defining batch operations

---

### 6. **[project-structure.md](project-structure.md)** — Technology Stack & Project Structure
- Technology domain analysis
- Flask Clean Architecture pattern rationale
- Complete project directory structure
- Implementation roadmap (M0-M9)
- Layer-by-layer architectural decisions

**Use this when:** Setting up the project, understanding folder organization, or adding new modules

---

### 7. **[patterns.md](patterns.md)** — Implementation Patterns & Consistency Rules
- Database column naming convention
- API response envelope format
- Error response structure
- Timestamp format (ISO 8601)
- Function naming conventions
- Pipeline stage result format
- Error handling patterns
- API client exception hierarchy

**Use this when:** Writing code, ensuring consistency, or reviewing pull requests

---

### 8. **[risk-mitigation.md](risk-mitigation.md)** — Risk Mitigation Strategy
- Phase 1 (MVP) lean approach
- Known vulnerabilities and mitigations
- Phase 2+ resilience roadmap
- Risk assessment and handling

**Use this when:** Planning error handling, designing resilience features, or assessing risks

---

## 🎯 Quick Navigation by Role

### For Developers
1. Start with **[project-structure.md](project-structure.md)** to understand the folder layout
2. Read **[patterns.md](patterns.md)** to follow consistency rules
3. Refer to **[decisions-core.md](decisions-core.md)** for data handling logic
4. Check **[decisions-api.md](decisions-api.md)** for API implementation
5. Use **[decisions-infrastructure.md](decisions-infrastructure.md)** for logging and deployment

### For Architects
1. Start with **[requirements.md](requirements.md)** for system scope
2. Review **[decisions-core.md](decisions-core.md)** through **[decisions-infrastructure.md](decisions-infrastructure.md)** for architectural choices
3. Check **[risk-mitigation.md](risk-mitigation.md)** for resilience approach
4. Use **[project-structure.md](project-structure.md)** for implementation patterns

### For Project Managers
1. Read **[requirements.md](requirements.md)** for scope and dependencies
2. Check **[project-structure.md](project-structure.md)** implementation roadmap (M0-M9)
3. Review **[risk-mitigation.md](risk-mitigation.md)** for known risks
4. Refer to **[decisions-infrastructure.md](decisions-infrastructure.md)** for monitoring/reporting

---

## 🔑 Key Architectural Decisions at a Glance

| Decision | Choice | File |
|----------|--------|------|
| **Data Model** | 3-table schema with status tracking | [decisions-core.md](decisions-core.md) |
| **API Pattern** | REST CRUD with simple filtering | [decisions-api.md](decisions-api.md) |
| **Pipeline Coordination** | Database-mediated async (status-tracked) | [decisions-api.md](decisions-api.md) |
| **Error Handling** | Record-level resilience (fail-soft) | [decisions-core.md](decisions-core.md) |
| **Frontend** | Bootstrap 5 + Vanilla JavaScript | [decisions-frontend.md](decisions-frontend.md) |
| **Logging** | File-based structured JSON | [decisions-infrastructure.md](decisions-infrastructure.md) |
| **Scoring Model** | Simplified 4-factor (1-9 scale) | [decisions-core.md](decisions-core.md) |
| **Rate Limiting** | Automatic detection + exponential backoff | [decisions-core.md](decisions-core.md) |

---

## 📋 Architectural Principles

1. **Clean Architecture (Onion Pattern)** — Core business logic independent of frameworks
2. **Fail-Soft Record Processing** — Batch continues on individual record failures
3. **Database-Mediated Coordination** — Pipeline stages communicate through status fields
4. **Lenient Parsing** — Accept incomplete/malformed data; log for debugging
5. **Explicit Error Semantics** — Specific exceptions per API for fine-grained control
6. **Simple for Phase 1** — Defer complexity (async, queuing, caching) to Phase 2+

---

## 🔄 Phase Strategy

### Phase 1 (MVP)
- ✅ Core discovery + web dashboard
- ✅ Basic error handling + retry logic
- ✅ Simple scoring model
- ✅ Manual execution (no scheduler)
- ✅ Synchronous API calls

### Phase 2+
- ⏳ Async pipeline with queueing
- ⏳ Circuit breaker + graceful degradation
- ⏳ Full 16-point scoring model
- ⏳ Batch checkpointing + resume
- ⏳ Real-time dashboard refresh
- ⏳ Built-in scheduler (APScheduler)

---

## 📊 Document Statistics

| Document | Size | Sections | Purpose |
|----------|------|----------|---------|
| **requirements.md** | 2.5 KB | 3 | Functional/non-functional requirements, constraints |
| **decisions-core.md** | 3.2 KB | 7 | Core data & API decisions |
| **decisions-api.md** | 2.8 KB | 3 | Pipeline communication & REST endpoints |
| **decisions-frontend.md** | 1.6 KB | 3 | Dashboard & UI decisions |
| **decisions-infrastructure.md** | 2.1 KB | 3 | Logging, scheduling, monitoring |
| **project-structure.md** | 4.5 KB | 4 | Project layout & implementation roadmap |
| **patterns.md** | 4.8 KB | 8 | Consistency rules & implementation patterns |
| **risk-mitigation.md** | 2.2 KB | 2 | Risk assessment & resilience roadmap |
| **index.md (this file)** | 2.1 KB | - | Navigation & overview |

**Total:** ~25.8 KB (original architecture.md was ~40 KB)

---

## 🔗 Related Documents

- `_bmad-output/planning-artifacts/epics/` — Story and task breakdowns
- `_bmad-output/planning-artifacts/implementation-readiness-report-20260403.md` — Readiness assessment
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Development tracking
- `01docs/03tranotra_leads_PRD.md` — Complete product requirements

---

## ❓ Questions & Clarifications

**Is this document finalized?**
Yes, Phase 1 architecture is finalized and ready for implementation. Phase 2+ decisions will be revisited after MVP validation.

**Can I modify these decisions?**
These are documented decisions, not immutable rules. If implementation discovers a better approach, discuss with team and update the relevant document.

**Where do I propose new patterns?**
Add new patterns to [patterns.md](patterns.md) with rationale and examples. Update index.md if creating new sections.

**Which decisions can Phase 2 change?**
Defer decisions marked **(Phase 2+)** in each document. Core decisions (1-4) are stable for Phase 1.

---

**Last Updated:** 2026-04-03  
**Status:** ✅ Ready for Development  
**Next:** Start implementation with [project-structure.md](project-structure.md)
