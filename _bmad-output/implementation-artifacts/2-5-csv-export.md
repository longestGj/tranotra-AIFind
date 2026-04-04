# Story 2-5: 实现 CSV 导出功能

**Story ID:** 2.5  
**Epic:** 2 - 结果展示与快速操作  
**Status:** ready-for-dev  
**Created:** 2026-04-04  
**Estimated Effort:** 1-2 days  
**Priority:** P0-Critical

---

## User Story

As a user,
I want to export search results to a CSV file,
So that I can process the data in Excel or other tools.

---

## Acceptance Criteria

### AC1: CSV Export Button
**Given** the results page is displayed  
**When** I look for export functionality  
**Then**:
- An "导出 CSV" button is visible on the results page
- Button is enabled when results are available
- Button is disabled when no results (grayed out)
- Button location: next to view toggle buttons or in results header

---

### AC2: CSV File Generation
**Given** I click the "导出 CSV" button  
**When** CSV generation completes  
**Then**:
- File is generated with exactly 23 columns in specified order
- Header row contains column names (first row)
- One data row per company
- File encoding: UTF-8 with BOM (Excel-compatible)
- Line endings: CRLF (Windows-compatible)
- File size: < 5MB
- Generation time: < 2 seconds (for up to 500 companies)

---

### AC3: CSV Filename Format
**Given** CSV is generated for search results  
**When** file is created  
**Then**:
- Filename format: `tranotra_leads_{country}_{query}_{timestamp}.csv`
- Example: `tranotra_leads_Vietnam_PVC_manufacturer_20260404_150000.csv`
- Country: from search parameter (or "All" if not specified)
- Query: from search parameter (or "All" if not specified)
- Timestamp: ISO format YYYYMMDD_HHMMSS (local timezone)

---

### AC4: CSV Column Structure
**Given** CSV file is generated  
**When** I open it in Excel  
**Then** columns appear in this exact order (23 total):

```
1. id
2. name
3. country
4. city
5. year_established
6. employees
7. estimated_revenue
8. main_products
9. export_markets
10. eu_us_jp_export
11. raw_materials
12. recommended_product
13. recommendation_reason
14. website
15. contact_email
16. linkedin_url
17. linkedin_normalized
18. best_contact_title
19. prospect_score
20. priority
21. source_query
22. created_at
23. updated_at
```

---

### AC5: CSV Data Formatting
**Given** CSV data is exported  
**When** I inspect values in Excel  
**Then**:
- Strings containing commas are enclosed in double quotes: `"PVC, cable, components"`
- Empty fields: left completely empty (not "N/A" or "null")
- Null values: empty cell
- Timestamps: ISO 8601 format (2026-04-04T15:30:00)
- Booleans: lowercase true/false (not TRUE/FALSE)
- Numbers: no quotes or formatting
- All special characters properly escaped

---

### AC6: Export Scope Options
**Given** I initiate CSV export  
**When** confirmation dialog appears  
**Then**:
- Option 1: "导出当前页 (20条)" — export only visible page
- Option 2: "导出所有 (47条)" — export all results
- Confirm dialog text: "确定要导出 {count} 条记录到 CSV 吗?"
- Cancel button: allows me to cancel operation
- Default: "导出当前页" selected

---

### AC7: Export Loading State
**Given** I click "导出" button  
**When** CSV is being generated  
**Then**:
- Button shows loading state: "正在导出..." (cursor: loading)
- Button is disabled during export (no multiple clicks)
- Loading time is visible: "30%", "60%", "100%" progress (optional)
- If export takes > 5 seconds: show message "正在处理..." to prevent user frustration

---

### AC8: Export Success Feedback
**Given** CSV export completes successfully  
**When** file downloads  
**Then**:
- Toast notification displays: "已导出，查看您的下载文件夹"
- Duration: 3 seconds (auto-dismiss)
- Position: bottom-right corner
- Button returns to normal state: "导出 CSV"
- File downloads to browser's default Downloads folder
- No error messages

---

### AC9: Export Error Handling
**Given** CSV export encounters an error  
**When** generation fails  
**Then**:
- Error message displays: "导出失败，请重试"
- Toast or alert notification (not silent fail)
- Retry button available in message
- Log error to console for debugging
- Button returns to normal state
- User can retry the export

---

## Developer Context

### Technology Stack (from Decision 11)
- **Frontend:** Vanilla JavaScript ES6+, Fetch API
- **Build:** No build step, no bundlers (deploy HTML/CSS/JS directly)
- **Framework:** Bootstrap 5 (already in codebase)
- **Storage:** No server-side storage needed (download only)

### Previous Story Intelligence (from Story 2-4)

**Completed Stories:**
- ✅ Story 2-1: Results Page API (data endpoint works)
- ✅ Story 2-2: Card View Display (all 23 fields available)
- ✅ Story 2-3: Table View Sorting (view data accessible)
- ✅ Story 2-4: View Switching (state management established)

**Current State:**
- `static/js/results.js`: Contains data handling for both views
- `static/css/results.css`: UI styling established
- `templates/results.html`: HTML structure in place
- `currentState` object: Contains companies array with all data
- Button locations: View toggle area (place export button nearby)

**Code Patterns Established:**
```javascript
// Data access pattern (already working):
currentState.companies    // Array of all company objects
currentState.view         // Current view: 'card' or 'table'
currentState.page         // Current page number
currentState.perPage      // Items per page (20)

// localStorage pattern (already used):
localStorage.setItem('key', value)        // Save with error handling
localStorage.getItem('key')               // Retrieve

// Error handling pattern (already established):
try {
    // operation
} catch (e) {
    if (e.name === 'QuotaExceededError') {
        console.warn('operation failed');
    }
}
```

### Key Files to Modify

1. **`static/js/results.js`** — CSV generation and download logic
2. **`static/css/results.css`** — Export button styling, toast styles
3. **`templates/results.html`** — Export button and confirmation dialog HTML

### Current Implementation Status

**What's Already Working:**
- ✅ View toggle buttons exist and work
- ✅ Results data accessible via `currentState.companies`
- ✅ All 23 company fields available from API
- ✅ Button styling framework (Bootstrap 5)
- ✅ Toast notification system (from previous stories)
- ✅ Fetch API for data (already used)

**What Story 2-5 Needs to Add:**
1. "导出 CSV" button in results header
2. CSV generation logic (convert array to CSV string)
3. File download mechanism (Blob + download API)
4. Confirmation dialog (export scope selection)
5. Loading state management
6. Error handling and retry logic
7. Success/error toast notifications

---

## Implementation Requirements

### 1. CSV Generation Function

```javascript
/**
 * Generate CSV string from company data
 * @param {Array} companies - Array of company objects
 * @param {string} exportScope - 'current' or 'all'
 * @returns {string} CSV formatted string with BOM
 */
function generateCSV(companies, exportScope) {
    // Headers (23 columns)
    const headers = [
        'id', 'name', 'country', 'city', 'year_established',
        'employees', 'estimated_revenue', 'main_products',
        'export_markets', 'eu_us_jp_export', 'raw_materials',
        'recommended_product', 'recommendation_reason', 'website',
        'contact_email', 'linkedin_url', 'linkedin_normalized',
        'best_contact_title', 'prospect_score', 'priority',
        'source_query', 'created_at', 'updated_at'
    ];

    // Prepare data based on export scope
    const dataToExport = exportScope === 'all' 
        ? companies 
        : companies.slice(0, currentState.perPage);

    // Build CSV rows
    const rows = [headers.map(escapeCSVField).join(',')];
    
    dataToExport.forEach(company => {
        const row = headers.map(field => {
            const value = company[field];
            return escapeCSVField(value);
        }).join(',');
        rows.push(row);
    });

    // Add UTF-8 BOM for Excel compatibility
    const BOM = '\uFEFF';
    const csv = BOM + rows.join('\r\n');
    
    return csv;
}

/**
 * Escape CSV field values
 * Handle commas, quotes, newlines
 */
function escapeCSVField(value) {
    if (value === null || value === undefined) {
        return '';
    }
    
    const str = String(value);
    
    // Fields with commas, quotes, or newlines need quotes
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
    }
    
    return str;
}
```

### 2. File Download Function

```javascript
/**
 * Trigger file download using Blob and download API
 * @param {string} csvContent - CSV string with BOM
 * @param {string} filename - Desired filename
 */
function downloadCSV(csvContent, filename) {
    // Create Blob with UTF-8 encoding
    const blob = new Blob([csvContent], { 
        type: 'text/csv;charset=utf-8;' 
    });
    
    // Create download link
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    URL.revokeObjectURL(url);
}
```

### 3. Export Button Click Handler

```javascript
/**
 * Handle "导出 CSV" button click
 */
function handleExportClick() {
    if (!currentState.companies || currentState.companies.length === 0) {
        showToast('没有数据可导出', 3000);
        return;
    }

    // Show confirmation dialog
    showExportDialog(currentState.companies);
}

/**
 * Show export scope confirmation dialog
 */
function showExportDialog(companies) {
    const currentPageCount = Math.min(
        currentState.perPage, 
        companies.length - (currentState.page - 1) * currentState.perPage
    );
    const totalCount = companies.length;

    const dialog = `
        <div class="export-dialog-overlay">
            <div class="export-dialog">
                <h3>导出数据</h3>
                <p>请选择导出范围：</p>
                <form id="export-form">
                    <label>
                        <input type="radio" name="scope" value="current" checked>
                        导出当前页 (${currentPageCount}条)
                    </label>
                    <label>
                        <input type="radio" name="scope" value="all">
                        导出所有 (${totalCount}条)
                    </label>
                </form>
                <p style="font-size: 12px; color: #666;">
                    确定要导出${totalCount}条记录到CSV吗?
                </p>
                <div class="dialog-actions">
                    <button class="btn btn-secondary" id="export-cancel">取消</button>
                    <button class="btn btn-primary" id="export-confirm">导出</button>
                </div>
            </div>
        </div>
    `;

    // Insert and setup handlers...
}
```

### 4. Button HTML

```html
<!-- Add to results header, near view toggle buttons -->
<button id="export-csv-btn" class="btn btn-secondary" onclick="handleExportClick()">
    📥 导出 CSV
</button>
```

### 5. CSS Styling

```css
/* Export button */
#export-csv-btn {
    margin-left: 10px;
    white-space: nowrap;
}

#export-csv-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

#export-csv-btn.loading {
    pointer-events: none;
    opacity: 0.6;
}

/* Export dialog */
.export-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.export-dialog {
    background: white;
    border-radius: 8px;
    padding: 30px;
    min-width: 400px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.export-dialog h3 {
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 18px;
}

.export-dialog form label {
    display: block;
    margin: 15px 0;
    cursor: pointer;
}

.export-dialog form input[type="radio"] {
    margin-right: 10px;
}

.dialog-actions {
    margin-top: 30px;
    display: flex;
    gap: 10px;
    justify-content: flex-end;
}
```

---

## Security & Accessibility

### Security
- ✅ CSV escaping prevents injection attacks (quotes, commas escaped)
- ✅ No eval() or dynamic code execution
- ✅ File download via safe Blob API (not script injection)
- ✅ No sensitive data exposed (only search results data)
- ✅ Error messages don't leak system information

### Accessibility
- ✅ Export button keyboard accessible (Tab, Enter)
- ✅ Dialog follows focus management (trap focus in dialog)
- ✅ Clear labeling for export scope options
- ✅ Toast notifications announced to screen readers (role="alert")
- ✅ Color not the only indicator (icon + text)

---

## Performance Requirements

| Metric | Target | Source |
|--------|--------|--------|
| CSV generation | < 2 seconds | AC2 |
| File download | Instant | HTML5 API |
| UI responsiveness | No blocking | No synchronous operations |
| File size | < 5MB | AC2 |
| Button feedback | < 100ms | UX standard |

---

## Testing Checklist

### Functional Testing
- [ ] AC1: Export button visible and enabled when data available
- [ ] AC2: CSV generated in < 2 seconds, correct encoding
- [ ] AC3: Filename follows format with country, query, timestamp
- [ ] AC4: All 23 columns in correct order
- [ ] AC5: Data formatting correct (commas, nulls, dates, booleans)
- [ ] AC6: Export scope dialog works (current/all options)
- [ ] AC7: Loading state displays during export
- [ ] AC8: Success toast shows after download
- [ ] AC9: Error handling and retry works

### Integration Testing
- [ ] Works with Story 2-4 view switching (both card/table)
- [ ] Exports data respecting current sort order
- [ ] Works with all data from Story 2-1 API
- [ ] Handles pagination correctly (current page vs all)

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Testing
- [ ] Button visible and clickable on mobile (< 768px)
- [ ] Dialog displays correctly on small screens
- [ ] Download works on mobile (varies by browser)

---

## Known Dependencies

- ✅ Story 2-1: Results Page API — provides data via `/api/search/results`
- ✅ Story 2-2: Card View Display — 23 fields from company object
- ✅ Story 2-3: Table View Sorting — currentState.companies array
- ✅ Story 2-4: View Switching — state management and button location
- ⏳ Story 2-5: This story — enables CSV export
- ⏸️ Story 2-6+: Future stories can build on export (bulk actions, etc.)

---

## Next Steps After Completion

1. Code review using `/bmad-code-review`
2. Manual testing across all browsers and devices
3. Verify AC1-AC9 all passing
4. Integration testing with Stories 2-1 through 2-4
5. Ready for merge to master
6. Begin Story 2-6 (or complete Epic 2 retrospective)

---

**Status:** ready-for-dev  
**Branch:** (will be feature/story-2-5-csv-export)  
**Completion Target:** 2026-04-05

Ultimate BMad Method context engine analysis completed.
Comprehensive developer guide created with full architectural compliance.
