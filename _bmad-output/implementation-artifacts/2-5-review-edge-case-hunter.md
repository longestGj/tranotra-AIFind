# Edge Case Hunter Review - Story 2-5 CSV Export
**Role:** Integration reviewer (diff + project context)  
**Perspective:** Edge cases, integration issues, and context-specific problems

## Project Context Analysis

**Existing Patterns Validated:**
- ✅ `currentState.companies` array exists and contains 23 fields per company (verified in results.js)
- ✅ `currentState.page` and `currentState.perPage` tracked properly (20 items per page)
- ✅ `showToast()` system already exists and working (established in Story 2-2)
- ✅ Bootstrap 5 CSS framework available for button styling
- ✅ Escape key handling pattern matches Story 2-4 keyboard navigation

## Edge Cases & Integration Issues

### [HIGH] Dialog Created Multiple Times Without Cleanup
- **Issue:** User rapidly clicking export button creates multiple overlays
- **Evidence:** `showExportDialog()` checks `document.getElementById('export-overlay')` and removes existing, BUT if user clicks button twice quickly, second call runs before first removal completes
- **Scenario:** User clicks export, dialog appears, user clicks export again while dialog still animating → two overlays created
- **Fix:** Add state flag to prevent duplicate dialog creation, OR debounce button clicks

### [HIGH] Pagination State Change During Export
- **Issue:** User switches page or sorts table while export dialog open
- **Evidence:** If user changes `currentState.page` during export, `performExport()` still has reference to old `companies` array BUT uses `currentState.page` in `generateCSV()`
- **Scenario:** 
  1. User clicks export, dialog shows "Export 15 items on page 1"
  2. User clicks page 2 while dialog open
  3. User confirms export
  4. Export uses page 1 data but might reference wrong page context
- **Severity:** HIGH
- **Fix:** Capture `currentState.page` at dialog creation time, not export time

### [MEDIUM] currentState.perPage Not Guaranteed
- **Issue:** `perPage` could theoretically change between dialog open and export
- **Evidence:** If pagination logic in later features changes `perPage`, export calculation breaks
- **Severity:** MEDIUM
- **Fix:** Capture `currentState.perPage` at dialog creation time

### [MEDIUM] Large Dataset Performance
- **Issue:** No validation that dataset fits in memory before export
- **Evidence:** `generateCSV()` builds entire string in memory with `rows.join('\r\n')`
- **Scenario:** API returns 10,000 companies (unlikely per spec, but possible), browser hangs during string concatenation
- **Severity:** MEDIUM (mitigated by < 5MB spec requirement, but implementation doesn't enforce)
- **Fix:** Add pre-flight check: warn if export > 5000 rows, suggest current page only

### [MEDIUM] URL Parameter Escaping in Filename
- **Issue:** `currentState.country` and `currentState.query` come from URL params, already URL-decoded
- **Evidence:** `generateCSVFilename()` applies regex replacement, but if URL contains special chars before decoding, unknown behavior
- **Scenario:** User searches for "PVC/plastic" → URL param is "PVC%2Fplastic" → `currentState.query` becomes "PVC/plastic" → filename becomes "PVC_plastic" (acceptable, but worth noting)
- **Severity:** LOW (acceptable tradeoff)
- **Note:** Current implementation handles this fine with character replacement

### [LOW] Toast Position Not Verified
- **Issue:** Story spec says "bottom-right corner" but `showToast()` implementation might position differently
- **Evidence:** `showToast()` in results.js doesn't show position in diff, must check CSS
- **Finding:** Toast CSS in results.css not shown in Story 2-5 diff, assumes existing implementation is correct
- **Severity:** LOW (not a Story 2-5 issue, pre-existing)

### [LOW] Mobile Dialog Sizing on Very Small Screens
- **Issue:** Mobile CSS applies `min-width: 90vw` and `max-width: 90vw`
- **Evidence:** `@media (max-width: 768px)` sets both min and max to same value
- **Scenario:** iPhone SE (375px width) → dialog tries to be 90% = 337.5px → readable but cramped
- **Severity:** LOW (acceptable for emergency use)
- **Note:** Could add `overflow-y: auto` and `max-height: 90vh` for very small screens

## Integration Testing Coverage

**Positive:** Implementation uses existing patterns from Story 2-4
- Event handler patterns match keyboard navigation approach
- Button state management mirrors view toggle buttons
- Toast notifications use established system
- localStorage patterns would match if used (though CSV export doesn't use it, correct choice)

**Missing Tests:**
- What if `currentState.companies` is null? (Checked in `handleExportClick()` ✅)
- What if user has no search results? (Handled with toast ✅)
- What if export button disabled but user somehow calls `handleExportClick()` directly? (No protection against direct function call)
- What if CSV generation takes > 2 seconds? (Likely < 100ms in browser, but not timed)

## Cross-File Dependencies

✅ **Verified safe dependencies:**
- `currentState` object structure consistent with Story 2-4
- `showToast()` function available and working
- Button click handlers follow existing onclick pattern
- CSS framework (Bootstrap) classes used correctly

## Browser Compatibility Check

**Blob API support:**
- ✅ Chrome 20+
- ✅ Firefox 13+
- ✅ Safari 6.1+
- ✅ Edge 12+

**URL.createObjectURL() support:**
- ✅ All modern browsers

**String.padStart() support (in generateCSVFilename):**
- ✅ ES2017 feature, supported in all modern browsers
- ⚠️ If IE11 support needed (unlikely for this project), would break
- Note: Project uses ES6+, so this is acceptable

## Memory Leak Verification with Project Context

**Analysis of cleanup:**
1. `showExportDialog()` creates overlay and listeners
2. `overlay.remove()` called on cancel or after export
3. But escape key listener still attached to document — **NOT CLEANED UP**
4. If user exports 10 times, 10 Escape key listeners accumulate
5. Each listener holds reference to `overlay` element in closure, preventing garbage collection

**Impact:** Long-term memory leak in single-page application (SPA)

## Recommendations (Prioritized by Integration Risk)

1. [HIGH] Capture `currentState.page` and `currentState.perPage` at dialog creation time, pass to export function
2. [HIGH] Add debouncing or state flag to prevent duplicate dialogs
3. [MEDIUM] Clean up Escape key listener when overlay removed
4. [MEDIUM] Add file size pre-flight check for large datasets
5. [LOW] Add `max-height: 90vh` to mobile dialog styles
6. [LOW] Consider adding export timestamp/count to success toast for clarity

---

**Overall Assessment:** Integration with existing codebase is sound. Main concerns are edge cases around simultaneous actions (rapid clicking, page changes during dialog) and event listener cleanup. No breaking changes to existing functionality detected.
