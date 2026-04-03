---
epic: 2
epicTitle: "结果展示与快速操作 (Results Display & Interaction)"
storyCount: 5
frCoverage: "FR9, FR10, FR11, FR13"
nfrCoverage: "NFR4"
uxdrCoverage: "UX-DR5, UX-DR6, UX-DR7, UX-DR8, UX-DR9, UX-DR14, UX-DR15"
createdDate: "2026-04-03"
dependsOn: "Epic 1"
---

# Epic 2: 结果展示与快速操作 (Results Display & Interaction)

**Epic 目标:** 用户能够以多种视图查看搜索结果，快速操作（复制、打开链接、导出）

**用户成果:** 搜索完成 → 查看结果（卡片/表格） → 快速操作（复制邮箱、打开链接、导出CSV）

**覆盖需求:**
- Functional: FR9, FR10, FR11, FR13
- Non-Functional: NFR4
- UX Design: UX-DR5, UX-DR6, UX-DR7, UX-DR8, UX-DR9, UX-DR14, UX-DR15

**开发优先级:** P0 (Core user-facing feature)

**依赖:** Epic 1 (搜索完成 → 数据入库)

---

## Story 2.1: 构建搜索结果页面基础与 API 端点

**Story ID:** 2.1

**User Story:**

As a developer,
I want to create the results page layout and API endpoint for fetching search results,
So that the frontend can display company data.

**Acceptance Criteria:**

**Given** the database contains company records from a search  
**When** I create a new Flask route: GET /api/search/results  
**Then** the endpoint:
- Accepts query parameters: country (optional), query (optional), page (optional, default 1)
- Returns JSON response with structure:
```json
{
  "success": true,
  "timestamp": "2026-04-03T12:00:00",
  "new_count": 15,
  "duplicate_count": 3,
  "avg_score": 8.2,
  "total_count": 47,
  "current_page": 1,
  "per_page": 20,
  "companies": [
    {
      "id": 1,
      "name": "Company Name",
      "country": "Vietnam",
      "city": "Ho Chi Minh",
      "year_established": 2010,
      "employees": "500-2000",
      "estimated_revenue": "$200M+",
      "main_products": "PVC cable",
      "export_markets": "USA, ASEAN",
      "eu_us_jp_export": true,
      "raw_materials": "PVC resin",
      "recommended_product": "DOTP",
      "recommendation_reason": "Perfect fit",
      "website": "example.com",
      "contact_email": "contact@example.com",
      "linkedin_url": "linkedin.com/company/...",
      "linkedin_normalized": "linkedin.com/company/...",
      "best_contact_title": "Purchasing Manager",
      "prospect_score": 10,
      "priority": "HIGH",
      "source_query": "Vietnam/PVC manufacturer",
      "created_at": "2026-04-03T12:00:00",
      "updated_at": "2026-04-03T12:00:00"
    }
  ]
}
```

**And** when query timeout > 3 seconds:
- Return cached results from previous search (if available)
- Include flag: "cached": true in response
- Show message to user: "数据加载中（显示缓存结果）"

**And** when no results:
- Return empty companies array with success=true
- User sees message: "本次未找到，建议修改搜索词"

**And** the results page (results.html) includes:
- Header showing: "搜索: Vietnam + PVC manufacturer"
- Statistics card showing search metrics
- View toggle buttons: "卡片视图 | 表格视图"
- Loading indicator (shown during initial fetch)
- Results container (placeholder until data loads)

**And** pagination:
- Default: 20 results per page
- Supports "Load More" or page navigation
- Display: "显示 1-20 / 47 条记录"

**Coverage:**
- FR9 (卡片视图基础)
- FR10 (表格视图基础)
- NFR4 (超时缓存)

---

## Story 2.2: 实现卡片视图展示

**Story ID:** 2.2

**User Story:**

As a user,
I want to see search results in a card view with all company details and quick actions,
So that I can quickly scan companies and perform actions.

**Acceptance Criteria:**

**Given** the results page is loaded with search data  
**When** I view search results in card view  
**Then** each company is displayed as a visually appealing card with:

**Header Section:**
- Company name (large, bold, 28px font)
- Location: "城市, 国家" (e.g., "Ho Chi Minh City, Vietnam")

**Score Badge:**
- "Score: 10/10" with color coding:
  - Green if score >= 8 (HIGH)
  - Yellow if score 6-7 (MEDIUM)
  - Red if score < 6 (LOW)
- Priority label: 🔴HIGH / 🟡MEDIUM / ⚫LOW

**Company Details Grid (2 columns):**
- 👥 员工: 500-2000
- 💰 年收: ~$200M+
- 🏭 产品: PVC cable manufacturing
- 🌍 出口: USA, ASEAN, Australia
- 🎯 推荐产品: DOTP / TOTM
- 📝 推荐理由: "Perfect fit for cable applications"

**Contact Information Section:**
- 📧 Email: cadivi@cadivi.vn (appears as clickable link)
- 🔗 LinkedIn: [linkedin.com/company/...]
- 🌐 Website: [cadivi.vn]
- 💼 最佳联系职位: Purchasing Manager

**Quick Action Buttons (below card):**
- [📋 Copy Email] → copies to clipboard, shows "已复制" toast for 2s
- [🔗 Open LinkedIn] → opens LinkedIn URL in new tab
- [🌐 Open Website] → opens website URL in new tab
- [📧 Draft Email] → opens email draft modal (grayed out for Phase 1)
- [✓ Mark as Contacted] → toggles flag, updates UI state
- [📝 Add Note] → opens note input modal (stored locally for now)

**Card Styling:**
- Shadow effect on hover (lift animation)
- Border on focus (for keyboard navigation)
- Responsive padding (20px desktop, 15px tablet, 10px mobile)
- Max-width: 400px per card, flexible grid layout

**Pagination:**
- If > 20 cards, show "加载更多" button at bottom
- Display current count: "显示 15 / 47 个公司"
- Clicking "加载更多" fetches next page

**Mobile Responsiveness:**
- Cards stack in single column on devices < 768px
- Action buttons stay horizontal (scroll if needed)
- Maintain full functionality on mobile

**Coverage:**
- FR9 (卡片视图)
- UX-DR5 (16字段展示)
- UX-DR6 (快捷按钮)

---

## Story 2.3: 实现表格视图展示与排序

**Story ID:** 2.3

**User Story:**

As a user,
I want to see search results in a table view with sorting options,
So that I can analyze and compare companies efficiently.

**Acceptance Criteria:**

**Given** the results page is loaded  
**When** I switch to table view  
**Then** the data is displayed as a sortable table with columns:

**Table Structure (left to right):**
| # | Company Name | Country | Score | Priority | Email | LinkedIn | Website |
|---|---|---|---|---|---|---|---|

**Sorting Functionality:**
- Click on column header to toggle sort (ascending ↑ / descending ↓)
- Default sort: Score descending (highest first)
- Arrow indicator shows current sort column and direction
- Sort preference stored in localStorage for this session
- Clicking same header again reverses sort direction

**Table Features:**
- Row hover effect (light background highlight, cursor pointer)
- Striped rows (alternating light/dark backgrounds)
- Email/LinkedIn/Website cells are clickable links (open in new tab)
- Company names truncated with "..." if too long (max 30 chars), full name on hover

**Responsive Behavior:**
- On desktop: all columns visible
- On tablet (768-1024px): hide Website column
- On mobile (< 768px): show only Name, Score, Priority, Email
- Horizontal scroll on very small screens

**Row Action:**
- Click any row to highlight it (light border)
- Double-click row to open card detail modal (if needed)

**Pagination:**
- Show 20 rows per page
- Pagination controls at bottom: "< 1 | 2 | 3 ... | Next >"
- Display: "显示 1-20 / 47 条记录"
- Jump to page: input field "跳转到第 [  ] 页"

**Performance:**
- Table renders within 500ms for 20 rows
- If sorting takes > 1s, show loading indicator: "排序中..."
- Return results from cache if available

**Coverage:**
- FR10 (表格视图)
- FR11 (视图切换)
- UX-DR7 (表格列配置)
- UX-DR8 (排序功能)

---

## Story 2.4: 实现视图切换与视图状态管理

**Story ID:** 2.4

**User Story:**

As a user,
I want to toggle between card and table views seamlessly,
So that I can choose the view that works best for my workflow.

**Acceptance Criteria:**

**Given** the results page is displayed  
**When** I click the view toggle buttons (卡片视图 | 表格视图)  
**Then** the view switches immediately:
- Selected button: darker background, bold text
- Unselected button: lighter background, normal text
- View state is saved in localStorage with key: `tranotra_leads_view_preference`
- On page reload, the last selected view is restored

**View Switch Animation:**
- Smooth CSS fade transition (opacity 0.3s)
- OR slide transition from left/right (transform 0.3s)
- Complete within 500ms total

**State Persistence:**
- Card view state:
  - Remembers scroll position within card view
  - Restores when switching back
  - Stores: `{ view: 'card', scrollPosition: 1234 }`

- Table view state:
  - Remembers sort column and direction
  - Remembers pagination page number
  - Stores: `{ view: 'table', sortColumn: 'score', sortDir: 'desc', page: 1 }`

**Loading Indicators:**
- While fetching search data: show spinner with "加载中..."
- Search button is disabled during fetch
- If fetch fails: show error message "加载失败，请重试" with retry button

**Mobile Behavior:**
- On mobile (< 768px): Card view is default/recommended
- Display note on table view: "此视图在手机上显示可能不清晰，推荐使用卡片视图"
- Both views fully functional on mobile (user can choose)

**Keyboard Navigation:**
- Tab through view buttons
- Enter/Space to activate toggle
- Arrow keys to navigate between cards/rows

**Coverage:**
- FR11 (视图切换)
- UX-DR15 (加载动画)

---

## Story 2.5: 实现 CSV 导出功能

**Story ID:** 2.5

**User Story:**

As a user,
I want to export search results to a CSV file,
So that I can process the data in Excel or other tools.

**Acceptance Criteria:**

**Given** the results page is displayed  
**When** I click the "导出 CSV" button  
**Then** a CSV file is generated and downloaded with:

**Filename Format:**
`tranotra_leads_{country}_{query}_{timestamp}.csv`

Example: `tranotra_leads_Vietnam_PVC_manufacturer_20260403_120000.csv`

**CSV Structure (23 columns in order):**
```
id,name,country,city,year_established,employees,estimated_revenue,
main_products,export_markets,eu_us_jp_export,raw_materials,
recommended_product,recommendation_reason,website,contact_email,
linkedin_url,linkedin_normalized,best_contact_title,prospect_score,
priority,source_query,created_at,updated_at
```

**CSV Content:**
- Header row with column names (first row)
- Data rows: one company per row
- Strings containing commas enclosed in quotes: `"PVC, cable, components"`
- Empty fields: left completely empty (not "N/A")
- Null values: empty cell
- All timestamps in ISO 8601 format: 2026-04-03T12:00:00
- Boolean values: true/false (lowercase)

**File Properties:**
- Encoding: UTF-8 with BOM (for Excel compatibility)
- Line endings: CRLF (Windows-compatible)
- Generated in < 2 seconds (for up to 500 companies)
- File size: < 5MB

**Export Scope:**
- Default: Export currently displayed data (respecting current filters/sorts)
- Option: "导出所有" to include all (not just current page)
- Confirm dialog: "确定要导出 47 条记录到 CSV 吗?"

**User Feedback:**
- Button shows loading state: "正在导出..." during generation
- After download: toast message "已导出，查看您的下载文件夹"
- If export fails: error message "导出失败，请重试" with retry button

**Browser Compatibility:**
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Uses HTML5 Blob and download API
- File downloads to browser's default Downloads folder

**Coverage:**
- FR13 (CSV导出)
- UX-DR14 (导出功能)

---

## Epic 2 Summary

**Stories Created:** 5  
**Estimated Effort:** 8-10 dev days  
**Priority:** P0 (Core feature)

**Key Deliverables:**
- ✅ Search results page with dual view support
- ✅ Card view with all 23 fields and quick action buttons
- ✅ Table view with sorting and pagination
- ✅ Seamless view switching with state persistence
- ✅ CSV export functionality for data processing

**Dependencies:** 
- Depends on Epic 1 (搜索数据需要先入库)
- Required for Epic 3 (仪表板依赖显示逻辑)

**Next Step:** Epic 3 depends on Epic 2 completion

---

**Document Created:** 2026-04-03
