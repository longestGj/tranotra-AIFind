# Blind Hunter Review - Story 2-5 CSV Export
**Role:** Adversarial reviewer (diff only, no spec context)  
**Perspective:** Code quality, security, and robustness

## Findings

### [CRITICAL] XSS Vulnerability in Dialog HTML Construction
- **Issue:** `showExportDialog()` uses template literals to inject dynamic content into HTML string passed to `insertAdjacentHTML()`
- **Evidence:** Line with `${currentPageCount}` and `${totalCount}` directly interpolated into HTML
- **Risk:** If `currentPageCount` or `totalCount` are derived from unsanitized user input, XSS possible
- **Severity:** CRITICAL
- **Status:** Requires context to assess — spec shows these come from pagination math, likely safe, but pattern is dangerous

### [HIGH] Memory Leak: Escape Key Listener Never Removed
- **Issue:** `showExportDialog()` adds keydown listener for Escape key but never removes it after dialog closes
- **Evidence:** Lines create `handleEscape` function and add listener: `document.addEventListener('keydown', handleEscape);` but removal only happens inside the handler after `overlay.remove()`
- **Impact:** If dialog created multiple times, listeners accumulate
- **Fix:** Should remove listener when overlay is removed

### [HIGH] Event Listener Not Removed on Cancel
- **Issue:** Cancel button removes overlay but doesn't clean up the Escape key listener
- **Evidence:** `cancelBtn.addEventListener('click', () => { overlay.remove(); });` — listener added but escape listener not removed
- **Severity:** HIGH
- **Impact:** Accumulated event listeners on document

### [MEDIUM] No Input Validation on Form Element Selection
- **Issue:** `form.querySelector('input[name="scope"]:checked')` assumes element always exists
- **Evidence:** Line: `const scope = form.querySelector('input[name="scope"]:checked').value;`
- **Risk:** If radio button not checked (shouldn't happen due to `checked` attribute, but defensive coding needed)
- **Severity:** MEDIUM

### [MEDIUM] Uncaught Promise Rejection Possible
- **Issue:** `performExport()` is async but called without `.catch()` handler
- **Evidence:** `await performExport(companies, scope);` in confirmBtn click handler — async function with promise, no catch
- **Risk:** If exception thrown, unhandled promise rejection warning
- **Severity:** MEDIUM (low actual risk due to try/catch inside async function, but pattern is unsafe)

### [LOW] CSV Filename Collision Risk
- **Issue:** Timestamp only includes seconds, not milliseconds
- **Evidence:** `generateCSVFilename()` uses only `YYYYMMDD_HHMMSS` format
- **Risk:** Two exports within same second could overwrite in Downloads folder
- **Severity:** LOW (unlikely in practice, but possible)
- **Fix:** Add milliseconds or random suffix

### [LOW] Missing null Check Before Property Access
- **Issue:** `performExport()` accesses `exportBtn` without null check
- **Evidence:** `const exportBtn = document.getElementById('export-csv-btn');` — no validation
- **Risk:** If button doesn't exist (shouldn't happen, but defensive coding)
- **Severity:** LOW

### [LOW] String Replacement in Field Names Could Miss Fields
- **Issue:** CSV filename cleaning uses regex `/[^a-zA-Z0-9_-]/g` which removes ALL non-alphanumeric characters
- **Evidence:** Line: `const cleanCountry = country.replace(/[^a-zA-Z0-9_-]/g, '_');`
- **Risk:** "Hong Kong" becomes "Hong_Kong" (acceptable), but some characters might be needed in query strings
- **Severity:** LOW (by design, acceptable tradeoff)

## Security Analysis

✅ **CSV Escaping:** Proper quote escaping `str.replace(/"/g, '""')` prevents CSV injection  
✅ **No eval() or dynamic code execution**  
✅ **File download via safe Blob API** (not using `eval()` or script tags)  
⚠️ **HTML Injection:** Template literal usage is dangerous pattern, needs context assessment  
✅ **No localStorage used** (appropriate for this feature)  

## Performance Analysis

✅ **O(n) complexity for CSV generation** — linear pass through data  
✅ **Instant generation** — no async delays needed for in-browser processing  
✅ **Blob API efficient** — browser handles download without streaming  
⚠️ **Large datasets:** No size validation before export, could hang browser with 50k+ rows  

## Code Quality

**Positive aspects:**
- Clear function separation of concerns
- Good JSDoc comments
- Readable variable names
- Proper error handling with try/catch

**Issues:**
- Event listener cleanup missing
- Promise handling pattern could be safer
- Could benefit from null checks on DOM queries
- Magic strings in column names (not bad, just observation)

## Recommendations

1. [CRITICAL] Sanitize all dynamic HTML content or use `textContent` where possible
2. [HIGH] Clean up Escape key listener properly when dialog closes
3. [MEDIUM] Add `.catch()` to promise or mark function as properly async-safe
4. [LOW] Add milliseconds to filename timestamp for uniqueness
5. [LOW] Add null check for export button element

---

**Overall Assessment:** Code is functional and follows patterns from existing codebase. Security mostly solid with one dangerous pattern (HTML template injection). Event listener cleanup is primary concern.
