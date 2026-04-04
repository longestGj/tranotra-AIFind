# Story 2-3: 实现表格视图展示与排序

**Story ID:** 2.3  
**Epic:** 2 - 结果展示与快速操作  
**Status:** 进行中  
**开始日期:** 2026-04-04

---

## User Story

As a user,  
I want to see search results in a table view with sorting options,  
So that I can analyze and compare companies efficiently.

---

## Acceptance Criteria

### AC1: 表格结构与列配置
**Given** the results page is loaded  
**When** I switch to table view  
**Then** the data is displayed as a sortable table with columns (left to right):

```
| # | Company Name | Country | Score | Priority | Email | LinkedIn | Website |
```

**Table headers are clickable** for sorting  
**All cells are properly aligned and readable**

---

### AC2: 排序功能
**Given** user views the table  
**When** I click on a column header  
**Then**:
- Sort direction toggles: ascending ↑ / descending ↓
- Arrow indicator (↑ or ↓) shows current sort column and direction
- Default sort: Score descending (highest first)
- Clicking same header again reverses sort direction
- Sort preference stored in localStorage for this session
- If sorting takes > 1s, show loading indicator: "排序中..."

---

### AC3: 行交互与链接
**Given** table rows are displayed  
**When** I interact with rows  
**Then**:
- Row hover effect: light background highlight, cursor pointer
- Striped rows: alternating light/dark backgrounds
- Email/LinkedIn/Website cells are **clickable links** (open in new tab)
- Company names truncated with "..." if too long (max 30 chars)
- Full name visible on hover (title attribute or tooltip)

---

### AC4: 响应式布局
**Given** user views table on different screen sizes  
**When** I resize browser or view on different devices  
**Then**:
- **Desktop (≥1024px):** All columns visible
- **Tablet (768-1023px):** Hide Website column
- **Mobile (<768px):** Show only Name, Score, Priority, Email columns
- **Very small screens:** Horizontal scroll enabled if needed
- **All views:** Fully functional, no data loss

---

### AC5: 分页与导航
**Given** results have > 20 records  
**When** I view the table  
**Then**:
- Show 20 rows per page
- Pagination controls at bottom:
  ```
  < Previous | 1 | 2 | 3 | ... | Next >
  ```
- Display: "显示 1-20 / 47 条记录" (dynamic based on data)
- Jump to page: input field "跳转到第 [ ] 页"
- Previous/Next buttons are disabled at first/last page

---

### AC6: 行选中与详情
**Given** table rows are visible  
**When** I click any row  
**Then**:
- Row is highlighted with light border
- **Double-click row:** (optional in Phase 1) would open card detail modal
- Single click: just highlight, prepare for potential bulk actions

---

### AC7: 性能要求
**Given** table data is being rendered  
**When** I load 20 rows  
**Then**:
- Table renders within **500ms**
- If sorting takes > 1s, show loading indicator "排序中..."
- Return results from cache if available (from Story 2-1)

---

### AC8: 移动体验
**Given** user is on mobile device  
**When** I view table  
**Then**:
- Display note: "此视图在手机上显示可能不清晰，推荐使用卡片视图"
- But table is **fully functional** on mobile
- User can choose either view (卡片视图 | 表格视图)

---

## Technical Specification

### Files to Create/Modify

**New Files:**
- None (reuse existing JS/CSS structure from Story 2-2)

**Modified Files:**
- `templates/results.html` — Add table view container
- `static/js/results.js` — Add table rendering + sorting logic
- `static/css/results.css` — Add table styles + responsive design

---

## Implementation Checklist

### Phase 1: HTML Structure
- [ ] Add table view container to results.html
- [ ] Create table element with thead (headers), tbody (data rows)
- [ ] Make column headers clickable (`<th data-sort-column="name">`)
- [ ] Add pagination controls below table

### Phase 2: Sorting Logic
- [ ] Add `sortCompanies(column, direction)` function to results.js
- [ ] Toggle sort direction on header click
- [ ] Display sort indicator (↑ / ↓) on current column
- [ ] Store sort preference in localStorage
- [ ] Handle loading state ("排序中...")

### Phase 3: Row Rendering & Interaction
- [ ] Render table rows from company data
- [ ] Implement hover effects (row highlighting)
- [ ] Make Email/LinkedIn/Website clickable (open in new tab)
- [ ] Truncate company names (max 30 chars, show full on hover)
- [ ] Implement row selection (highlight on click)

### Phase 4: Responsive Design
- [ ] Add CSS media queries for tablet (768px)
- [ ] Add CSS media queries for mobile (<768px)
- [ ] Hide/show columns based on screen size
- [ ] Test horizontal scroll on mobile

### Phase 5: Pagination
- [ ] Implement "显示 X-Y / Z 条记录" counter
- [ ] Add Previous/Next buttons
- [ ] Add page number links
- [ ] Add "跳转到第 [ ] 页" input field
- [ ] Handle pagination state changes

### Phase 6: Testing & Polish
- [ ] Test sorting on all columns
- [ ] Test responsive behavior on 3 screen sizes
- [ ] Verify link clicks open correctly
- [ ] Performance test: 20 rows render < 500ms
- [ ] Test localStorage persistence
- [ ] Mobile accessibility check

---

## Expected Result

After completion, users should be able to:

```
1. See search results in table format (Story 2-1 → 2-3)
2. Click column headers to sort:
   - Score (highest first by default)
   - Company Name (A-Z or Z-A)
   - Country
   - Priority
3. Click Email/LinkedIn/Website to open in new tab
4. Navigate pages (< Previous | 1 | 2 | 3 | Next >)
5. On mobile, see compact view (Name, Score, Priority, Email only)
6. See "排序中..." when sorting takes > 1s
7. Sort preferences persist across page reloads
```

---

## Success Metrics

- ✅ Table renders in < 500ms for 20 rows
- ✅ All 7 columns display correctly on desktop
- ✅ Sorting toggles ascending/descending
- ✅ Responsive layout works on desktop/tablet/mobile
- ✅ Pagination navigation works (Previous/Next/Jump)
- ✅ Email/LinkedIn/Website links open in new tab
- ✅ Sort preference persists in localStorage
- ✅ Mobile note displayed on small screens
- ✅ All links XSS-safe (escaped HTML)

---

## Related Stories

**Previous:** Story 2-1 (Results Page API) ✅  
**Previous:** Story 2-2 (Card View Display) ✅  
**Next:** Story 2-4 (View Switching) — Depends on this  
**Next:** Story 2-5 (CSV Export) — Can work in parallel

---

**Created:** 2026-04-04  
**Status:** Ready for Implementation
