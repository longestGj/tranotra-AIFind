---
title: "Frontend Architecture Decisions"
section: "Architecture"
project: "08B2B_AIfind - Tranotra Leads"
date: "2026-04-03"
---

# Frontend Architecture Decisions

---

## Decision 11: Dashboard Technology Stack

**Choice:** Bootstrap 5 + Vanilla JavaScript  
**Priority:** IMPORTANT — shapes UI implementation

### Stack Components

- **HTML Templates:** Flask Jinja2 (server-side rendering)
- **CSS:** Bootstrap 5 (already in codebase)
- **JavaScript:** Vanilla ES6+ with fetch() API
- **No Build Step:** No npm, webpack, bundlers
- **No Framework:** No React, Vue, Angular

### Rationale

- **Already in Place:** Bootstrap 5 already in `presentation/static/`
- **Simplicity:** No build complexity; deploy HTML/CSS/JS directly
- **Phase 1 Sufficient:** Adequate for dashboard requirements
- **Low Barrier:** Anyone can modify HTML/CSS; no build knowledge needed
- **Phase 2+ Option:** Can migrate to React/Alpine if needed

### Example: Fetch Company Data

```javascript
// presentation/static/js/dashboard.js
async function loadCompanies() {
    const response = await fetch('/api/companies?per_page=20');
    const json = await response.json();
    
    if (json.success) {
        renderCompanies(json.data.companies);
    }
}

function renderCompanies(companies) {
    const container = document.getElementById('companies');
    companies.forEach(company => {
        const card = document.createElement('div');
        card.className = 'company-card';
        card.innerHTML = `
            <h3>${company.name}</h3>
            <p>Score: <span class="score-${company.priority}">${company.prospect_score}</span></p>
            <p>${company.country}</p>
        `;
        container.appendChild(card);
    });
}
```

---

## Decision 12: Dashboard Views & Interaction

**Choice:** View-switch + inline analytics  
**Priority:** IMPORTANT — MVP functionality

### Views

1. **Card View** — Company cards with name, country, score (color-coded), priority badge
2. **Table View** — Sortable columns (name, country, score, priority, email)
3. **Sidebar** — Efficiency metrics (total, avg score, % high-priority)
4. **Filters** — Country dropdown, score range, priority checkboxes
5. **Details Modal** — Click card → expand full info + contacts + emails

### Implementation

```html
<!-- presentation/templates/dashboard.html -->
<button onclick="switchView('card')" class="active">Card View</button>
<button onclick="switchView('table')">Table View</button>

<div id="card-view" style="display: block;">
    <!-- Card view container -->
</div>

<div id="table-view" style="display: none;">
    <!-- Table view container -->
</div>

<script>
function switchView(view) {
    document.getElementById('card-view').style.display = 
        (view === 'card') ? 'block' : 'none';
    document.getElementById('table-view').style.display = 
        (view === 'table') ? 'block' : 'none';
}
</script>
```

### Rationale

- **Rich Visualization:** Multiple views serve different use cases (browsing vs. analyzing)
- **Responsive:** Adapts to desktop/tablet/mobile
- **Efficient:** Same data, different CSS classes; no re-fetching
- **Foundation for Phase 2:** Bulk actions (select multiple, export, reassign)

---

## Decision 13: Real-time Data Refresh

**Choice:** Manual refresh only (user clicks button)  
**Priority:** IMPORTANT — server load + simplicity

### Pattern

```
No polling, no WebSockets
↓
User clicks "Refresh" button → GET /api/companies → update DOM
OR
Page load always fetches fresh data
```

### Implementation

```html
<button onclick="refreshData()" class="btn btn-primary">Refresh</button>

<script>
async function refreshData() {
    const response = await fetch('/api/companies');
    const json = await response.json();
    document.getElementById('companies').innerHTML = ''; // clear
    renderCompanies(json.data.companies); // re-render
}

// On page load
document.addEventListener('DOMContentLoaded', refreshData);
</script>
```

### Rationale

- **No Server Overhead:** No polling drain on resources
- **User Control:** Explicit refresh; user knows data is fresh
- **Simple:** No complex state management
- **Phase 2+:** Can add polling (setInterval every 5s) if needed

### Counterexample

❌ **NOT Real-time updates via WebSocket** (too complex for Phase 1)

---

**Next:** Read [decisions-infrastructure.md](decisions-infrastructure.md) for logging and deployment decisions.
