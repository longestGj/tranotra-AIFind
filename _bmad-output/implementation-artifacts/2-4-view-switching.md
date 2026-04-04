# Story 2-4: 实现视图切换与视图状态管理

**Story ID:** 2.4  
**Epic:** 2 - 结果展示与快速操作  
**Status:** ready-for-dev  
**Created:** 2026-04-04  
**Estimated Effort:** 1-2 days  
**Priority:** P0-Critical

---

## User Story

As a user,  
I want to toggle between card and table views seamlessly,  
So that I can choose the view that works best for my workflow.

---

## Acceptance Criteria

### AC1: View Toggle Buttons
**Given** the results page is displayed  
**When** I click the view toggle buttons (卡片视图 | 表格视图)  
**Then**:
- Selected button: darker background, bold text
- Unselected button: lighter background, normal text
- View switches immediately to selected view

---

### AC2: View State Persistence
**Given** user selects a view preference  
**When** view changes  
**Then**:
- View state is saved to localStorage with key: `tranotra_leads_view_preference`
- On page reload, the last selected view is automatically restored
- View state survives browser restarts

---

### AC3: View Switch Animation
**Given** user clicks view toggle  
**When** view changes  
**Then**:
- Smooth CSS fade transition (opacity 0.3s)
- OR smooth slide transition from left/right (transform 0.3s)
- Animation completes within 500ms total
- No content flashing or jank during transition

---

### AC4: Card View State Preservation
**Given** user is in card view  
**When** they scroll down and then switch to table view and back  
**Then**:
- Scroll position is remembered
- Returns to the same scroll position when switching back to card view
- localStorage stores: `{ view: 'card', scrollPosition: <number> }`

---

### AC5: Table View State Preservation
**Given** user is in table view  
**When** they change sort column, direction, or page, then switch views and back  
**Then**:
- Sort column is remembered
- Sort direction is remembered
- Current page number is remembered
- Returns to exact table state (sort + page) when switching back
- localStorage stores: `{ view: 'table', sortColumn: 'score', sortDir: 'desc', page: 1 }`

---

### AC6: Loading Indicators
**Given** page is fetching search results  
**When** fetch is in progress  
**Then**:
- Show spinner with "加载中..." text
- Search button (if visible) is disabled during fetch
- Both view toggle buttons remain enabled
- If fetch fails: show "加载失败，请重试" with retry button

---

### AC7: Mobile View Behavior
**Given** user is on mobile device (< 768px)  
**When** they view results  
**Then**:
- Card view is default/recommended view
- Table view is available but displays warning: "此视图在手机上显示可能不清晰，推荐使用卡片视图"
- Both views fully functional and switchable
- Table view responsive layout applies (4 columns on mobile)

---

### AC8: Keyboard Navigation
**Given** user is using keyboard to navigate  
**When** they interact with view toggle  
**Then**:
- Can tab to view toggle buttons
- Can press Enter or Space to activate toggle
- Arrow keys can navigate between cards/table rows (when in respective views)
- Focus indicators are visible

---

## Developer Context

### Architecture Compliance

**Technology Stack (from Decision 11):**
- Framework: Bootstrap 5 + Vanilla JavaScript (ES6+)
- No build step, no bundlers
- Fetch API for network calls
- localStorage for client-side state
- Direct HTML/CSS/JS deployment

**View Management Pattern (from Decision 12):**
- Simple show/hide pattern using CSS display properties
- localStorage for persistence
- Vanilla JS event handlers (no framework required)
- Existing switchView() function already implemented in Story 2-3

### Key Files to Modify

1. **`static/js/results.js`** — View switching & state management logic
2. **`static/css/results.css`** — View transition animations
3. **`templates/results.html`** — Already has view toggle buttons

### Current Implementation Status

**From Story 2-3 Learnings:**
- View toggle buttons already exist: `<button class="view-btn active" data-view="card">`
- switchView() function already implemented: saves to localStorage, toggles button styles
- Both renderCardView() and renderTableView() already exist
- Current state management uses currentState object

**What's Already Working:**
```javascript
// Already implemented in Story 2-3:
function switchView(view) {
    currentState.view = view;
    localStorage.setItem('tranotra_leads_view_preference', view);
    // ... toggle button styles
    // ... re-render view
}
```

**What Story 2-4 Needs to Add:**
1. View transition animations (CSS fade/slide)
2. Scroll position tracking for card view
3. Table view state tracking (sort + page + direction)
4. Keyboard navigation support
5. Mobile-optimized behavior

---

## Implementation Requirements

### 1. View Transition Animation
- Add CSS transitions to view containers
- Fade: opacity 0.3s ease-in-out
- Slide: transform translateX(±100%) 0.3s ease-in-out
- Total animation time: < 500ms
- No blocking during animation

**Files:** `static/css/results.css`

### 2. Scroll Position Management

**For Card View:**
```javascript
// When switching FROM card view:
const scrollPos = document.documentElement.scrollTop || document.body.scrollTop;
localStorage.setItem('tranotra_leads_card_scroll', scrollPos);

// When switching TO card view:
const savedScroll = localStorage.getItem('tranotra_leads_card_scroll');
if (savedScroll) {
    window.scrollTo(0, parseInt(savedScroll, 10));
}
```

**Files:** `static/js/results.js` — in switchView() function

### 3. Table View State Tracking

Table view state already partially tracked in Story 2-3:
- `currentState.sortColumn` — already saved to localStorage
- `currentState.sortDirection` — already saved to localStorage
- `currentState.page` — already tracked

**Story 2-4 Should Enhance:**
```javascript
// Store combined table state when switching FROM table view
function saveTableViewState() {
    localStorage.setItem('tranotra_leads_table_state', JSON.stringify({
        view: 'table',
        sortColumn: currentState.sortColumn,
        sortDir: currentState.sortDirection,
        page: currentState.page
    }));
}

// Restore table state when switching TO table view
function restoreTableViewState() {
    const saved = localStorage.getItem('tranotra_leads_table_state');
    if (saved) {
        try {
            const state = JSON.parse(saved);
            currentState.sortColumn = state.sortColumn;
            currentState.sortDirection = state.sortDir;
            currentState.page = state.page;
        } catch (e) {
            console.warn('Failed to restore table state:', e);
        }
    }
}
```

**Files:** `static/js/results.js`

### 4. Mobile Behavior

**Already Implemented (Story 2-3):**
- Mobile warning on table view: `"此视图在手机上显示可能不清晰，推荐使用卡片视图"`
- Table view responsive columns (4 columns on mobile)

**Story 2-4 Should Add:**
- Detect mobile (< 768px) on page load
- Optionally suggest card view as default
- Maintain full functionality of table view (don't disable it)

**Files:** `static/js/results.js` — in switchView() or initialization

### 5. Keyboard Navigation

**View Toggle Buttons:**
- Already have proper HTML structure
- Should inherit keyboard navigation from DOM structure
- Ensure buttons have aria-labels and role attributes

**Card/Table Navigation:**
```javascript
// Optional: Arrow key navigation within views
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' && currentState.view === 'card') {
        // Scroll to next card or page down
    }
    if (e.key === 'ArrowUp' && currentState.view === 'card') {
        // Scroll to previous card or page up
    }
    // Similar for table: arrow keys navigate rows
});
```

**Files:** `static/js/results.js`

---

## Previous Story Intelligence (From Story 2-3)

### What Story 2-3 Achieved
- ✅ Table view fully implemented with 8 columns
- ✅ Sorting by any column with visual indicators (↑/↓)
- ✅ Pagination with page numbers and jump-to-page
- ✅ Card view already existed from Story 2-2
- ✅ View toggle buttons already exist
- ✅ localStorage persistence for sort preferences already works
- ✅ switchView() function already implemented

### Code Patterns Established

**1. State Management:**
```javascript
let currentState = {
    view: localStorage.getItem('tranotra_leads_view_preference') || 'card',
    sortColumn: 'prospect_score',
    sortDirection: 'desc',
    page: 1,
    // ... other state
};
```

**2. localStorage with Error Handling (from Story 2-3 fixes):**
```javascript
// Story 2-3 added try-catch for localStorage
try {
    localStorage.setItem('tranotra_leads_table_sort', JSON.stringify({...}));
} catch (e) {
    if (e.name === 'QuotaExceededError') {
        console.warn('localStorage quota exceeded');
    }
}
```

**3. View Switching Function (already exists):**
```javascript
function switchView(view) {
    currentState.view = view;
    localStorage.setItem('tranotra_leads_view_preference', view);
    
    // Update button styles
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.view-btn[data-view="${view}"]`).classList.add('active');
    
    // Re-render
    if (view === 'card') {
        renderCardView();
    } else {
        renderTableView();
    }
}
```

### Code Review Fixes Applied (Story 2-3)

**Important for Story 2-4:** Story 2-3 code review fixed several issues:
1. JSON.parse now wrapped in try-catch
2. totalPages validation added
3. URL sanitization enhanced
4. localStorage exception handling
5. Property access validation

**Story 2-4 should apply similar defensive patterns:**
- Wrap localStorage operations in try-catch
- Validate all state data before using
- Use safe defaults if restoration fails

### Testing Approach (from Story 2-3)

Story 2-3 had:
- ✅ 100% acceptance criteria coverage
- ✅ No syntax errors (verified with node -c)
- ✅ Security checks (XSS, URL sanitization)
- ✅ Performance targets met (< 500ms render, < 1s sort)

**Story 2-4 should follow same approach:**
- Verify all AC with manual testing
- Test on desktop, tablet, mobile
- Test keyboard navigation
- Test state persistence across page reloads
- Test localStorage quota edge cases

---

## Security & Accessibility Requirements

### Security
- ✅ Use escapeHtml() for all user-facing data (already in codebase)
- ✅ Validate localStorage data with try-catch before parsing
- ✅ Use safe defaults if localStorage data is invalid
- ✅ No eval() or dynamic code execution

### Accessibility (WCAG 2.1)
- ✅ View toggle buttons must have proper aria-labels
- ✅ Button focus indicators visible
- ✅ Color contrast meets AA standards
- ✅ Keyboard navigation fully supported
- ✅ Screen reader compatible

---

## Performance Requirements

| Metric | Target | Source |
|--------|--------|--------|
| View switch animation | < 500ms | AC3 |
| Page reload restoration | < 200ms | localStorage is instant |
| Button interaction | Immediate | CSS + JS |
| Scroll position restore | < 100ms | scrollTo() is instant |

---

## Files to Modify

| File | Purpose | Estimated Changes |
|------|---------|-------------------|
| `static/js/results.js` | View state management, scroll tracking | +80 lines |
| `static/css/results.css` | View transition animations | +30 lines |
| `templates/results.html` | (No changes - buttons already exist) | 0 lines |

---

## Acceptance Testing Checklist

- [ ] **AC1:** View toggle buttons switch correctly with visual feedback
- [ ] **AC2:** View preference persists across page reload
- [ ] **AC3:** View switch animation is smooth and < 500ms
- [ ] **AC4:** Scroll position saved and restored for card view
- [ ] **AC5:** Table state (sort, direction, page) saved and restored
- [ ] **AC6:** Loading spinner shows during fetch, buttons disabled appropriately
- [ ] **AC7:** Mobile default is card view, table shows warning, both work
- [ ] **AC8:** Tab navigation works, keyboard activation works, arrow keys optional
- [ ] **Security:** All localStorage operations wrapped in try-catch
- [ ] **Performance:** View switching instant, animations < 500ms
- [ ] **Mobile:** Fully responsive and functional on < 768px screens
- [ ] **Keyboard:** Full keyboard navigation works without mouse
- [ ] **Browser:** Works in Chrome, Firefox, Safari, Edge

---

## Known Dependencies

- ✅ Story 2-1: Results Page API — provides data
- ✅ Story 2-2: Card View Display — view already exists
- ✅ Story 2-3: Table View with Sorting — view already exists and fully functional
- ⏳ Story 2-4: This story — enables view switching
- ⏸️ Story 2-5: CSV Export — depends on this story for proper data context

---

## Related Previous Implementations

- **Story 2-2 Card View:** `static/js/results.js` - renderCardView(), createCompanyCard()
- **Story 2-3 Table View:** `static/js/results.js` - renderTableView(), sortTableData(), pagination
- **Story 2-3 Code Review:** All 12 issues fixed, security enhanced

---

## Next Steps After Completion

1. Code review using /bmad-code-review
2. Manual testing across all screen sizes
3. Integration testing with Story 2-5 (CSV export)
4. Ready for merge to master

---

**Status:** ready-for-dev  
**Branch:** feature/story-2-4-view-switching  
**Completion Target:** 2026-04-05

Ultimate BMad Method context engine analysis completed.  
Comprehensive developer guide created with full architectural compliance.

