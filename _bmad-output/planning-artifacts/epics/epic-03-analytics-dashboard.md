---
epic: 3
epicTitle: "搜索效率分析 (Analytics & Optimization)"
storyCount: 4
frCoverage: "FR8, FR12, FR14"
nfrCoverage: ""
uxdrCoverage: "UX-DR10, UX-DR11, UX-DR12, UX-DR13"
createdDate: "2026-04-03"
dependsOn: "Epic 1, Epic 2"
---

# Epic 3: 搜索效率分析 (Analytics & Optimization)

**Epic 目标:** 用户能够追踪搜索表现、分析搜索词效率、获得优化建议

**用户成果:** 查看仪表板 → 分析7天数据 → 查看搜索词排名 → 获得优化建议

**覆盖需求:**
- Functional: FR8, FR12, FR14
- UX Design: UX-DR10, UX-DR11, UX-DR12, UX-DR13

**开发优先级:** P1 (Nice-to-have, but important for user optimization)

**依赖:** Epic 1 (数据入库), Epic 2 (显示逻辑)

---

## Story 3.1: 构建效率仪表板页面与数据聚合 API

**Story ID:** 3.1

**User Story:**

As a user,
I want to view an analytics dashboard showing search performance metrics,
So that I can understand how effective my search strategy is.

**Acceptance Criteria:**

**Given** the system has accumulated search history data  
**When** I navigate to /dashboard  
**Then** the dashboard displays:

**Key Metrics Section (top):**
```
📊 关键指标 (最近7天)
┌─────────────────────────────────────┐
│ 总搜索次数:        47次             │
│ 新增公司总数:      312家            │
│ 去重率（重复）:    18%              │
│ 平均命中率:        20.8家/搜索      │
│ 高分公司占比:      28% (89家评分≥8) │
│ 本日 vs 昨日:      ↑ 22%            │
│ 本周 vs 上周:      ↑ 18%            │
└─────────────────────────────────────┘
```

**API Endpoint: GET /api/analytics/dashboard?days=7**

Returns:
```json
{
  "success": true,
  "period": "last_7_days",
  "metrics": {
    "total_searches": 47,
    "total_companies": 312,
    "dedup_rate": 18.5,
    "avg_hit_rate": 20.8,
    "high_score_rate": 28.2,
    "day_on_day_growth": 22.1,
    "week_on_week_growth": 18.3
  },
  "timestamp": "2026-04-03T12:00:00"
}
```

**Dashboard Layout:**
- Header: "系统运行效率仪表板 (最近7天)"
- Key metrics cards (7 colored boxes)
- Each metric shows: value + trend arrow (↑/↓) + percentage change
- Color coding: Green (↑positive), Red (↓negative), Gray (neutral)

**Time Filter:**
- Dropdown to select period: 7天 | 14天 | 30天 | 自定义
- Dashboard updates when period changes
- Selected period shown in title

**Responsive:**
- Desktop: 7 metrics in grid (2-3 columns)
- Tablet: metrics stack to 2 columns
- Mobile: single column stack

**Coverage:**
- FR8 (效率指标计算)
- FR12 (仪表板展示)
- UX-DR10 (关键指标展示)

---

## Story 3.2: 实现搜索词效率排名表与智能建议

**Story ID:** 3.2

**User Story:**

As a user,
I want to see which search keywords are most effective,
So that I can focus on high-performing search terms.

**Acceptance Criteria:**

**Given** the dashboard is open  
**When** I scroll to "搜索词效率排名" section  
**Then** I see a ranked table:

**Table Format:**
```
排名 | 搜索词           | 国家 | 命中数 | 重复数 | 平均评分 | 效率
─────┼──────────────────┼──────┼────────┼────────┼─────────┼────────
 1   │ cable mfg        │ VN   │ 28     │ 3      │ 8.2     │ ⭐⭐⭐⭐⭐
 2   │ synthetic leather│ TH   │ 25     │ 4      │ 7.8     │ ⭐⭐⭐⭐
 3   │ flooring export  │ VN   │ 18     │ 2      │ 7.5     │ ⭐⭐⭐
 4   │ PVC manufacturer │ ID   │ 8      │ 8      │ 6.2     │ ⭐⭐
```

**Metrics:**
- 排名: Ranking by hit_count (descending)
- 搜索词 + 国家
- 命中数: result_count from search_history
- 重复数: duplicate_count (lower is better)
- 平均评分: avg_score of results
- 效率: Star rating (1-5 stars)
  - 5 stars: hit_count > 20 AND avg_score >= 8 AND dedup_rate < 20%
  - 4 stars: hit_count > 15 AND avg_score >= 7 AND dedup_rate < 30%
  - 3 stars: hit_count > 10 AND avg_score >= 6
  - 2 stars: hit_count > 5 AND avg_score >= 5
  - 1 star: other

**Smart Suggestions (below table):**
```
💡 建议:
- "PVC manufacturer" 在 ID 的重复率太高（100%），建议跳过
- "cable mfg" 在 VN 最高效，可每周重复搜索
- 尝试新关键词：搪陶、聚酯、增塑剂类似词汇
```

**API Endpoint: GET /api/analytics/search-terms?days=7&limit=10**

Returns:
```json
{
  "success": true,
  "search_terms": [
    {
      "rank": 1,
      "country": "Vietnam",
      "query": "cable mfg",
      "hit_count": 28,
      "duplicate_count": 3,
      "avg_score": 8.2,
      "efficiency_score": 5
    }
  ],
  "suggestions": [...]
}
```

**Coverage:**
- FR8 (效率指标)
- UX-DR11 (搜索词排名)
- UX-DR13 (智能建议)

---

## Story 3.3: 实现搜索历史表与交互

**Story ID:** 3.3

**User Story:**

As a user,
I want to see my recent search history with performance metrics,
So that I can track what I've searched and replicate successful searches.

**Acceptance Criteria:**

**Given** the dashboard is open  
**When** I scroll to "搜索历史明细（最近20次）" section  
**Then** I see a sortable/filterable table:

**Table Format:**
```
日期       │ 国家 │ 关键词           │ 新增 │ 重复 │ 平均评分 │ 评价
───────────┼──────┼──────────────────┼──────┼──────┼─────────┼────────
2026-03-31 │ VN   │ cable mfg        │ 12   │ 3    │ 8.1     │ ⭐⭐⭐⭐⭐
2026-03-30 │ TH   │ synthetic leather│ 8    │ 2    │ 7.9     │ ⭐⭐⭐⭐
2026-03-29 │ VN   │ PVC manufacturer │ 4    │ 8    │ 5.2     │ ⭐⭐
```

**Features:**
- Sort by any column (click header)
- Filter by country (dropdown)
- Filter by date range (date picker: From - To)
- Show 20 results per page
- Pagination: "< 1 | 2 | 3 ... | Next >"

**Quick Actions per row:**
- [🔄 Repeat Search] - button to repeat this exact search
- [📈 View Details] - shows companies from this search in results page

**Hover Effects:**
- Row highlight on hover
- Tooltip on truncated fields (if text too long)

**API Endpoint: GET /api/analytics/search-history?limit=20&offset=0&country=&dateFrom=&dateTo=**

Returns:
```json
{
  "success": true,
  "total": 47,
  "limit": 20,
  "offset": 0,
  "searches": [
    {
      "id": 1,
      "date": "2026-03-31",
      "country": "Vietnam",
      "query": "cable mfg",
      "new_count": 12,
      "duplicate_count": 3,
      "avg_score": 8.1,
      "efficiency_rating": 5
    }
  ]
}
```

**Coverage:**
- FR14 (搜索历史记录)
- UX-DR12 (历史表展示)

---

## Story 3.4: 实现仪表板图表与数据可视化

**Story ID:** 3.4

**User Story:**

As a user,
I want to see visual charts showing trends over time,
So that I can quickly identify patterns in my search activity.

**Acceptance Criteria:**

**Given** the dashboard has 7+ days of search history  
**When** I view the dashboard  
**Then** I see the following charts:

**Chart 1: 搜索次数趋势 (Line Chart)**
- X-axis: Date (last 7 days)
- Y-axis: Number of searches
- Shows daily search count as line graph
- Hover shows exact values

**Chart 2: 新增公司数 vs 重复率 (Bar + Line Combo)**
- X-axis: Date
- Left Y-axis: New companies count (blue bars)
- Right Y-axis: Dedup rate % (red line)
- Shows trend of new acquisitions vs efficiency

**Chart 3: 平均评分分布 (Pie Chart)**
- Segments: HIGH (score 8-10), MEDIUM (6-7), LOW (<6)
- Shows percentage of companies in each category
- Colors: Green, Yellow, Red
- Legend with counts: "HIGH: 89家 | MEDIUM: 156家 | LOW: 67家"

**Chart Implementation:**
- Use simple Chart.js or similar library
- Responsive: adapts to screen size
- Hover tooltips on data points
- Click legend to toggle data series on/off

**No Data Handling:**
- If < 7 days of data: show message "数据不足，请继续搜索"
- Show placeholder charts with empty state

**Coverage:**
- FR12 (仪表板展示)
- UX-DR10 (关键指标可视化)

---

## Epic 3 Summary

**Stories Created:** 4  
**Estimated Effort:** 6-8 dev days  
**Priority:** P1 (Important for user optimization)

**Key Deliverables:**
- ✅ Analytics dashboard with key metrics
- ✅ Search term efficiency ranking with suggestions
- ✅ Search history table with filtering & sorting
- ✅ Visual charts and trend analysis

**Dependencies:**
- Depends on Epic 1 (search_history data)
- Depends on Epic 2 (UI patterns)

**Next Step:** Epic 4 (system quality) is independent

---

**Document Created:** 2026-04-03
