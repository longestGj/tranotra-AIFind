# Story 2-5 Code Review Triage
**Review Layers Completed:** Blind Hunter ✅ | Edge Case Hunter ✅ | Acceptance Auditor ✅  
**Date:** 2026-04-04

---

## Normalized & Deduplicated Findings

### [1] Escape Key Listener Memory Leak
**Source:** blind + edge  
**Severity:** HIGH  
**Classification:** PATCH  
**Location:** `static/js/results.js`, `showExportDialog()` function, lines ~1290-1300

**Detail:**
Escape key listener is added to document when dialog opens but never removed when dialog closes (via cancel, confirm, or clicking overlay). This causes event listener accumulation on repeated exports:
- User exports → dialog created → listener added
- User cancels → overlay removed BUT listener still attached
- User exports again → 2nd listener added
- After 10 exports → 10 listeners accumulate

Blind Hunter flagged this as memory leak (listeners hold closure references, prevent garbage collection). Edge Case Hunter verified this happens on repeated exports in single-page app.

**Evidence:**
```javascript
// Line ~1293: Listener added
const handleEscape = (e) => {
    if (e.key === 'Escape') {
        overlay.remove();
        document.removeEventListener('keydown', handleEscape);  // Only removes on Escape press
    }
};
document.addEventListener('keydown', handleEscape);

// Cancel button removes overlay but doesn't remove listener:
cancelBtn.addEventListener('click', () => {
    overlay.remove();  // No removeEventListener() call
});
```

**Fix:** Remove listener when overlay is removed in any path (cancel, confirm, click outside).

---

### [2] XSS Vulnerability: Dynamic HTML in Template Literal
**Source:** blind  
**Severity:** CRITICAL  
**Classification:** PATCH  
**Location:** `static/js/results.js`, `showExportDialog()` function, line ~1250

**Detail:**
Dialog HTML uses template literals to inject `currentPageCount` and `totalCount` into HTML string passed to `insertAdjacentHTML()`. While these values come from Math calculations (safe in this case), the pattern is dangerous:

```javascript
const dialogHTML = `
    <span>导出当前页 (${currentPageCount}条)</span>
    <span>导出所有 (${totalCount}条)</span>
    <p>确定要导出${totalCount}条记录到CSV吗?</p>
`;
document.body.insertAdjacentHTML('beforeend', dialogHTML);
```

If `currentPageCount` or `totalCount` could come from user input (they don't, but pattern is wrong), this is XSS.

**Fix:** Use safe DOM methods instead of HTML strings:
- Create elements with `document.createElement()`
- Use `textContent` instead of `innerHTML`
- OR sanitize values before interpolation

**Why this matters:** Establishes unsafe pattern in codebase that could be copied to other features.

---

### [3] Pagination State Race Condition During Export
**Source:** edge  
**Severity:** HIGH  
**Classification:** PATCH  
**Location:** `static/js/results.js`, `showExportDialog()` and `performExport()` functions

**Detail:**
Dialog created at time T shows "Export 15 items on page 1", but if user changes page or sorting before confirming, the export uses the NEW page/sort state:

**Scenario:**
1. User on page 1, 15 items, clicks export
2. Dialog shows "导出当前页 (15条)"
3. User clicks page 2 (while dialog open)
4. `currentState.page` now = 2
5. User clicks confirm
6. `performExport()` receives old `companies` array but uses NEW `currentState.page` value
7. Export calculation: `const start = (2 - 1) * 20 = 20` — exports wrong data

**Evidence:**
```javascript
// Line ~1255: currentPageCount calculated from current state
const currentPageStart = (currentState.page - 1) * currentState.perPage;  // Uses current value

// Later in performExport():
const start = (currentState.page - 1) * currentState.perPage;  // Uses DIFFERENT current value
```

**Fix:** Capture `currentState.page` and `currentState.perPage` at dialog creation time, pass as parameters.

---

### [4] Multiple Dialogs Can Be Created Simultaneously
**Source:** edge  
**Severity:** HIGH  
**Classification:** PATCH  
**Location:** `static/js/results.js`, `showExportDialog()` function, line ~1267

**Detail:**
Rapid button clicks create multiple overlay divs before first one is removed:

```javascript
// Checks for existing, but race condition exists:
const existing = document.getElementById('export-overlay');
if (existing) existing.remove();  // Removes synchronously
document.body.insertAdjacentHTML('beforeend', dialogHTML);  // Adds immediately
```

If user clicks button twice rapidly (within milliseconds), second click happens before first overlay animation/removal completes.

**Scenario:**
1. User double-clicks export button
2. First dialog created
3. Second click runs before first removal completes
4. Check finds overlay and removes it
5. BUT first overlay's event listeners (cancel button, etc.) still live
6. Second overlay created with its own listeners
7. Now two sets of overlays/listeners exist

**Fix:** Add state flag to prevent dialog creation while one exists:
```javascript
if (currentState._exportDialogOpen) return;
currentState._exportDialogOpen = true;
// ... create dialog
// ... when closed, set to false
```

---

### [5] No Input Validation on Form Element Selection
**Source:** blind  
**Severity:** MEDIUM  
**Classification:** DISMISS  
**Location:** `static/js/results.js`, line ~1285

**Detail:**
```javascript
const scope = form.querySelector('input[name="scope"]:checked').value;
```

Assumes radio button is always checked. While the HTML includes `checked` attribute on first option, defensive programming would validate.

**Why DISMISS:** HTML guarantees one radio button is always selected (they're in same group). Defensive check would be noise. Risk level is negligible.

---

### [6] Uncaught Promise Rejection Possible
**Source:** blind  
**Severity:** MEDIUM  
**Classification:** DISMISS  
**Location:** `static/js/results.js`, line ~1286

**Detail:**
`await performExport(companies, scope);` is called without `.catch()` handler. However, `performExport()` is async and wraps everything in try/catch, making this actually safe.

**Why DISMISS:** The try/catch inside the async function handles all exceptions. Pattern is safe even without explicit .catch(). The warning about "unhandled promise rejection" is overly cautious here.

---

### [7] Filename Collision Risk (Seconds-Only Timestamp)
**Source:** blind  
**Severity:** LOW  
**Classification:** DEFER  
**Location:** `static/js/results.js`, `generateCSVFilename()` function, line ~1329

**Detail:**
Timestamp format `YYYYMMDD_HHMMSS` only includes seconds, not milliseconds. Two exports within same second could theoretically have identical filenames and overwrite in Downloads folder.

**Why DEFER:** This is an edge case in an edge case. Spec doesn't require millisecond precision. Browser typically appends ` (1)` or ` (2)` to duplicate filenames. Not a blocker for Story 2-5.

---

### [8] No Null Check on Export Button Element
**Source:** blind  
**Severity:** LOW  
**Classification:** DISMISS  
**Location:** `static/js/results.js`, `performExport()` function, line ~1301

**Detail:**
```javascript
const exportBtn = document.getElementById('export-csv-btn');
// No check if exportBtn === null
```

**Why DISMISS:** Button is defined in HTML template and always exists on results page. Defensive null checks on DOM elements that are guaranteed to exist add noise. Acceptable pattern in this codebase.

---

### [9] Large Dataset Performance Not Validated
**Source:** edge  
**Severity:** MEDIUM  
**Classification:** PATCH  
**Location:** `static/js/results.js`, `generateCSV()` function, line ~1305

**Detail:**
No pre-flight check that dataset fits in memory. If API returns 10,000+ companies (unlikely per spec, but possible), browser string concatenation could hang:

```javascript
const rows = [headers.map(...).join(',')];
dataToExport.forEach(company => {
    const row = headers.map(...).join(',');
    rows.push(row);  // Array could have 10k+ elements
});
const csv = BOM + rows.join('\r\n');  // Joins could be slow
```

**Fix:** Add pre-flight check: warn user if > 5000 rows, recommend current page only.

---

### [10] Mobile Dialog Styling Edge Case
**Source:** edge  
**Severity:** LOW  
**Classification:** DEFER  
**Location:** `static/css/results.css`, lines ~1151-1153

**Detail:**
Mobile dialog uses `min-width: 90vw` and `max-width: 90vw` — both set to same value. On very small screens (320px), dialog becomes 288px, which is narrow but usable.

Could add `max-height: 90vh` and `overflow-y: auto` for screens smaller than iPad.

**Why DEFER:** Works as-is. Enhancement for future mobile improvements, not a blocker.

---

### [11] Button Disabled State vs Toast Message
**Source:** auditor  
**Severity:** LOW  
**Classification:** DECISION_NEEDED  
**Location:** `static/js/results.js`, `handleExportClick()` function

**Spec Requirement:** "Button is disabled when no results (grayed out)"  
**Implementation:** Button always enabled, shows toast "没有数据可导出"

**Detail:**
AC1 specification explicitly asks for disabled button state when no data. Implementation instead handles it with a toast message, which is arguably better UX (user sees feedback) but deviates from spec.

**Decision:** 
- A: Implement `disabled` attribute per spec?
- B: Update spec to match UX decision?
- C: Accept as acceptable deviation?

**Recommendation:** Accept (C) — Toast UX is superior to disabled button. Minor spec deviation acceptable.

---

### [12] AC9: Retry Button Location Deviation
**Source:** auditor  
**Severity:** LOW  
**Classification:** DECISION_NEEDED  
**Location:** `static/js/results.js`, `performExport()` error handling

**Spec Requirement:** "Retry button available in message"  
**Implementation:** Toast shows error, button re-enabled, user re-clicks export to retry

**Detail:**
Spec implies inline retry button in error message. Implementation relies on button state change. Both achieve retry capability but with different UX.

**Decision:**
- A: Add inline retry button to error toast?
- B: Accept current approach as acceptable alternative?

**Recommendation:** Accept (B) — Standard web pattern. Minor spec deviation acceptable.

---

## Triage Summary

| ID | Category | Count | Fixability |
|----|----------|-------|-----------|
| Patch | Fixable without human input | 4 | High |
| Decision Needed | Requires user choice | 2 | N/A |
| Defer | Pre-existing or out-of-scope | 2 | N/A |
| Dismiss | False positive or noise | 3 | N/A |
| **Total** | | **11** | |

---

## Critical Path Issues

**MUST FIX (Blocking approval):**
1. [CRITICAL] XSS pattern in HTML injection — establish safe pattern
2. [HIGH] Escape listener memory leak — cleanup on all paths
3. [HIGH] Pagination race condition — capture state at dialog time
4. [HIGH] Multiple dialogs creation race — add state flag

**Should Fix (Strongly recommended):**
5. [MEDIUM] Large dataset performance check — warn on > 5000 rows

**Nice to Have (Optional):**
6. [LOW] Filename timestamp collision — add milliseconds
7. [LOW] Mobile dialog scrolling — add overflow handling

---

## Verdict

**Review Status:** ⚠️ CONDITIONAL APPROVAL  
**Blockers:** 4 HIGH/CRITICAL issues prevent merge without fixes  
**Recommendations:** 1 MEDIUM issue should be addressed  
**Minor Deviations:** 2 LOW issues (AC1, AC9) are acceptable

**Next Step:** Present findings and implement patches.
