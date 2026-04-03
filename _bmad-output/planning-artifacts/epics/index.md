---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - "01docs/claude-phase1-design-ceo-reviewed-20260331.md (Phase 1 UX Design, CEO-approved)"
  - "01docs/03tranotra_leads_PRD.md (Full Pipeline PRD, reference for architecture)"
  - "_bmad-output/planning-artifacts/architecture.md (Technology Stack & Architecture)"
phase: "Phase 1 - LinkedIn Search + Web Display"
projectName: "08B2B_AIfind - Tranotra Leads Phase 1"
userName: "Ailong"
extractionDate: "2026-04-03"
epicDesignDate: "2026-04-03"
storyCreationDate: "2026-04-03"
requirementCount: 45
epicCount: 4
storyCount: 16
---

# 08B2B_AIfind - Tranotra Leads Phase 1 - Epics & Stories

**Project:** Tranotra Leads Phase 1 (LinkedIn搜索 + Web展示)  
**Phase:** Phase 1 MVP  
**Status:** All Stories Created - Ready for Sprint Planning  
**Created:** 2026-04-03  
**User:** Ailong

---

## 📋 Overview

This document serves as the index and navigation hub for Phase 1 Epic and Story definitions. All requirements have been extracted, epics designed, and stories created with detailed acceptance criteria.

---

## Requirements Inventory

### Functional Requirements (14)

| FR ID | Requirement | Epic |
|-------|-------------|------|
| FR1 | 用户可通过 Web 表单输入国家和搜索关键词 | Epic 1 |
| FR2 | 系统调用 Gemini Grounding Search API 进行公司搜索 | Epic 1 |
| FR3 | 系统自动解析 Gemini 返回数据（验证格式） | Epic 1 |
| FR4 | 系统自动规范化 LinkedIn URL 进行去重 | Epic 1 |
| FR5 | 系统将搜索结果解析为 16 字段数据并存入 SQLite | Epic 1 |
| FR6 | 系统自动跳过重复的公司（基于 linkedin_normalized） | Epic 1 |
| FR7 | 系统记录搜索历史（国家、关键词、新增数、重复数、平均评分） | Epic 1 |
| FR8 | 系统计算并展示本次搜索的效率指标（去重率、命中率、高分占比） | Epic 3 |
| FR9 | 用户可在卡片视图查看搜索结果（含快捷操作） | Epic 2 |
| FR10 | 用户可在表格视图查看搜索结果（支持排序、导出 CSV） | Epic 2 |
| FR11 | 用户可在视图间切换（卡片 ↔ 表格） | Epic 2 |
| FR12 | 系统展示效率仪表板（7天聚合数据、搜索词排名、历史记录） | Epic 3 |
| FR13 | 用户可导出搜索结果为 CSV | Epic 2 |
| FR14 | 系统记录搜索效率数据（最近 20 条搜索历史） | Epic 3 |

### Non-Functional Requirements (10)

| NFR ID | Requirement | Epic | Priority |
|--------|-------------|------|----------|
| NFR1 | 数据库初始化时自动创建所需表（companies, search_history） | Epic 4 | P0 |
| NFR2 | Gemini 格式验证失败时提示用户"搜索失败：格式错误" | Epic 4 | P0 |
| NFR3 | 解析失败字段用"N/A"填充，不中断流程 | Epic 4 | P1 |
| NFR4 | Web 查询超时 >3s 时返回缓存+分页 | Epic 2 | P1 |
| NFR5 | 网络中断时自动重连 3 次 | Epic 4 | P1 |
| NFR6 | 每次搜索间隔 2 秒，避免 rate limit | Epic 1 | P0 |
| NFR7 | 搜索返回 0 结果时提示用户"本次未找到，建议修改词" | Epic 4 | P1 |
| NFR8 | 本地 Python 运行，无需云端定时任务 | Epic 4 | P0 |
| NFR9 | 使用 Flask 框架，无额外依赖 | Epic 1 | P0 |
| NFR10 | SQLite 本地存储（路径：./data/leads.db） | Epic 1 | P0 |

### UX Design Requirements (15)

| UX-DR ID | Requirement | Epic |
|----------|-------------|------|
| UX-DR1 | 搜索表单页面包含：国家选择器、关键词输入、最近搜索、示例提示 | Epic 1 |
| UX-DR2 | 搜索表单中显示今日统计卡片（搜索次数、新增公司数、去重率） | Epic 1 |
| UX-DR3 | 搜索表单中显示周效率指标（环比上周增长百分比） | Epic 1 |
| UX-DR4 | 搜索表单中显示高分率（Score≥8 的公司占比） | Epic 1 |
| UX-DR5 | 卡片视图展示：公司名、城市、评分/优先级、员工数、产品线等 | Epic 2 |
| UX-DR6 | 卡片视图包含快捷操作按钮（复制邮箱、打开LinkedIn、打开官网等） | Epic 2 |
| UX-DR7 | 表格视图包含列：序号、公司名、评分、优先级、邮箱、LinkedIn、官网 | Epic 2 |
| UX-DR8 | 表格视图支持按评分↓、优先级、公司名排序 | Epic 2 |
| UX-DR9 | 搜索结果页面显示本次搜索统计：新增数、重复数、平均评分 | Epic 2 |
| UX-DR10 | 效率仪表板显示关键指标：总搜索、新增、去重率、平均命中率、高分占比等 | Epic 3 |
| UX-DR11 | 效率仪表板显示搜索词排名表（命中数、重复数、平均评分、效率评价） | Epic 3 |
| UX-DR12 | 效率仪表板显示搜索历史（最近 20 条） | Epic 3 |
| UX-DR13 | 效率仪表板包含建议文案（如："PVC manufacturer 在 ID 的重复率太高，建议跳过"） | Epic 3 |
| UX-DR14 | 导出 CSV 功能包含所有 23 个字段 | Epic 2 |
| UX-DR15 | 加载动画：搜索按钮点击后禁用并显示加载状态 | Epic 2 |

---

## Epic List & Navigation

### Epic 1: 搜索表单与数据获取 (Search & Acquisition)

**状态:** 5 Stories Created ✅

**用户成果:** 用户能够输入国家和关键词，系统自动搜索并将结果持久化到数据库

**覆盖需求:** 
- FR: FR1, FR2, FR3, FR4, FR5, FR6, FR7
- NFR: NFR6, NFR9, NFR10
- UX-DR: UX-DR1, UX-DR2, UX-DR3, UX-DR4

**Stories:**
- Story 1.1: 初始化 Flask 应用与项目结构
- Story 1.2: 设计并初始化 SQLite 数据库（companies、search_history 表）
- Story 1.3: 集成 Gemini API 与环境变量管理
- Story 1.4: 实现 Gemini Grounding Search 调用与格式验证
- Story 1.5: 实现数据解析、规范化与去重逻辑

📄 **详细文档:** [epic-01-search-acquisition.md](epic-01-search-acquisition.md)

---

### Epic 2: 结果展示与快速操作 (Results Display & Interaction)

**状态:** 5 Stories Created ✅

**用户成果:** 用户能够以多种视图查看搜索结果，快速操作（复制、打开链接、导出）

**覆盖需求:**
- FR: FR9, FR10, FR11, FR13
- NFR: NFR4
- UX-DR: UX-DR5, UX-DR6, UX-DR7, UX-DR8, UX-DR9, UX-DR14, UX-DR15

**Stories:**
- Story 2.1: 构建搜索结果页面基础与 API 端点
- Story 2.2: 实现卡片视图展示
- Story 2.3: 实现表格视图展示与排序
- Story 2.4: 实现视图切换与视图状态管理
- Story 2.5: 实现 CSV 导出功能

📄 **详细文档:** [epic-02-results-display.md](epic-02-results-display.md)

---

### Epic 3: 搜索效率分析 (Analytics & Optimization)

**状态:** 4 Stories Created ✅

**用户成果:** 用户能够追踪搜索表现、分析搜索词效率、获得优化建议

**覆盖需求:**
- FR: FR8, FR12, FR14
- UX-DR: UX-DR10, UX-DR11, UX-DR12, UX-DR13

**Stories:**
- Story 3.1: 构建效率仪表板页面与数据聚合 API
- Story 3.2: 实现搜索词效率排名表与智能建议
- Story 3.3: 实现搜索历史表与交互
- Story 3.4: 实现仪表板图表与数据可视化

📄 **详细文档:** [epic-03-analytics-dashboard.md](epic-03-analytics-dashboard.md)

---

### Epic 4: 系统可迭代性与质量保证 (Reliability, Performance & Quality)

**状态:** 2 Stories Created ✅

**用户成果:** 系统具有完善的错误处理、性能优化、容错能力，支持持续迭代优化

**覆盖需求:**
- NFR: NFR1, NFR2, NFR3, NFR5, NFR7, NFR8

**Stories:**
- Story 4.1: 完善错误处理与网络容错机制
- Story 4.2: 性能优化、缓存管理与系统监控

📄 **详细文档:** [epic-04-quality-assurance.md](epic-04-quality-assurance.md)

---

## Summary Statistics

| 指标 | 数值 |
|------|------|
| 功能需求 (FR) | 14 |
| 非功能需求 (NFR) | 10 |
| UX设计需求 (UX-DR) | 15 |
| **总需求数** | **45** |
| **Epic 数量** | **4** |
| **Story 数量** | **16** |
| **验收标准数** | **80+** |

---

## Epic 依赖关系

```
Epic 1: 搜索与获取 ← 基础数据层
  ↓
  ├→ Epic 2: 结果展示（依赖 Epic 1 数据）
  └→ Epic 3: 效率分析（依赖 Epic 1 数据）

Epic 4: 系统质量 ← 横切关注点（贯穿所有 Epic）
```

---

## 需求覆盖完整性

✅ **所有 45 个需求已映射到 Story**

| Epic | FR | NFR | UX-DR | 总计 |
|------|----|----|-------|------|
| Epic 1 | 7 | 3 | 4 | 14 |
| Epic 2 | 4 | 1 | 7 | 12 |
| Epic 3 | 3 | 0 | 4 | 7 |
| Epic 4 | 0 | 6 | 0 | 6 |
| **总计** | **14** | **10** | **15** | **45** |

---

## 后续步骤

- [ ] Sprint Planning: 根据优先级和团队速率排列 Story
- [ ] Story Estimation: 评估每个 Story 的工作量 (points/days)
- [ ] Sprint Assignment: 分配开发 Agent 给具体 Story
- [ ] Testing Strategy: 定义 QA 和验收流程
- [ ] Documentation: 生成 API 文档、部署指南等

---

**文档最后更新:** 2026-04-03
