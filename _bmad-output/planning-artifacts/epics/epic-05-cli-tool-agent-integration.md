---
title: "Epic 5: CLI Tool for Agent Integration"
created_date: "2026-04-05"
status: "SPECIFICATION"
version: "1.0"
---

# 🖥️ Epic 5: CLI Tool for Agent Integration

## 📌 Epic 概述

**Epic ID:** 5  
**Epic Name:** CLI Tool for Agent Integration  
**Priority:** P1 - Important  
**Status:** Planning  
**Owner:** TBD  

**目标：** 构建命令行工具，供 AI Agent 调用完成自然语言驱动的公司数据搜索、导入和查询工作流

---

## 🎯 Epic 目标

### 主要目标
1. ✅ 提供 4 个独立的 CLI 命令供 Agent 调用
2. ✅ 支持完整的工作流：搜索 → 导入 → 查询 → 批量操作
3. ✅ 自动保存搜索结果到 `data/gemini_responses/`
4. ✅ 提供结构化 JSON 输出供 Agent 解析
5. ✅ 支持错误处理和重试机制

### 业务价值
- 🤖 **Agent 驱动工作流** - Agent 接收自然语言 → 调用 CLI → 返回结果
- 🔄 **流程自动化** - 批量搜索导入一条命令完成
- 📊 **数据可追溯** - 所有搜索结果自动保存，便于审计和重复使用
- 🧪 **可测试性** - CLI 命令易于测试和集成

---

## 📋 Epic 范围

### 包含的工作
- ✅ 4 个 CLI 命令实现
- ✅ JSON/CSV/Markdown 输出格式
- ✅ 配置文件（YAML）支持
- ✅ 错误处理和 Exit Code
- ✅ 单元测试和集成测试
- ✅ 文档和示例

### 不包含的工作（后续 Epic）
- ❌ 并发搜索优化（Phase 2）
- ❌ 缓存机制（Phase 2）
- ❌ 增量导入（Phase 3）
- ❌ Web UI 集成（独立 Epic）

---

## 👥 Epic 包含的 Story

### Story 5-1: Implement CLI search command
**标题：** CLI Search Command - Gemini API Integration  
**优先级：** P0 - Critical  
**描述：** 实现 `tranotra search` 命令，调用 Gemini API，自动保存结果到文件，同时输出到 stdout

**主要工作：**
- 构建 CLI 框架（Click/Typer）
- 集成 Gemini API 调用
- 自动生成文件名保存搜索结果
- JSON/CSV 输出支持
- Agent 友好的错误处理

**成功标准：**
- [ ] 命令可执行：`tranotra search --country Vietnam --query "PVC manufacturer"`
- [ ] 结果自动保存到 `data/gemini_responses/`
- [ ] 文件名符合规则：`{YYYYMMDD}_{HHMMSS}_{count}_{COUNTRY}_{keyword}.json`
- [ ] stdout 输出完整 JSON
- [ ] metadata 字段包含 saved_file 路径
- [ ] 支持 --output-dir 指定自定义目录
- [ ] 所有参数验证和错误处理完整
- [ ] 单元测试覆盖 > 80%

**依赖：** 无（基础功能）  
**预计工时：** 2-3 天

---

### Story 5-2: Implement CLI import command
**标题：** CLI Import Command - Data Loading with Duplicate Handling  
**优先级：** P0 - Critical  
**描述：** 实现 `tranotra import` 命令，从 JSON/CSV 文件导入数据到数据库，处理重复和验证

**主要工作：**
- 解析 JSON/CSV 输入文件
- 数据验证和转换
- 重复检测（基于 linkedin_normalized）
- 冲突处理策略（skip/update/error）
- 事务管理和错误恢复
- Dry-run 支持（预览不执行）

**成功标准：**
- [ ] 命令可执行：`tranotra import --file results.json`
- [ ] 支持 JSON 和 CSV 输入
- [ ] 数据验证完整（必需字段、数据类型）
- [ ] 重复检测基于 linkedin_normalized
- [ ] 支持 3 种冲突策略：skip, update, error
- [ ] --dry-run 能预览导入结果（不写数据库）
- [ ] 输出统计：导入数、跳过数、错误数
- [ ] 错误回滚和事务管理
- [ ] 单元测试覆盖 > 80%

**依赖：** Story 5-1（搜索结果作为输入）  
**预计工时：** 2-3 天

---

### Story 5-3: Implement CLI query command
**标题：** CLI Query Command - Database Search and Filtering  
**优先级：** P0 - Critical  
**描述：** 实现 `tranotra query` 命令，从数据库查询公司数据，支持多维过滤和排序

**主要工作：**
- 数据库查询构建
- 多维度过滤（国家、关键词、前景分数、优先级）
- 排序和分页支持
- JSON/CSV/Markdown 输出
- 查询性能优化

**成功标准：**
- [ ] 命令可执行：`tranotra query --country Vietnam --prospect-score-min 8`
- [ ] 支持所有过滤参数：country, query, prospect_score, priority
- [ ] 支持排序：字段选择、ASC/DESC
- [ ] 支持分页：limit, offset
- [ ] 支持多种输出格式：JSON, CSV, Markdown
- [ ] 查询响应时间 < 500ms（100+ 记录）
- [ ] 返回结果包含分页元数据：total, current_page, per_page
- [ ] 空结果处理正确
- [ ] 单元测试覆盖 > 80%

**依赖：** Story 5-2（导入数据后才能查询）  
**预计工时：** 2 天

---

### Story 5-4: Implement CLI batch command & Integration Testing
**标题：** CLI Batch Command - Complete Workflow & Testing  
**优先级：** P1 - Important  
**描述：** 实现 `tranotra batch` 命令执行完整的搜索+导入流程，并完成全套测试

**主要工作：**
- YAML 配置文件解析
- 批量搜索和导入编排
- 中间结果保存
- 完整工作流日志
- 单元测试（4 个命令各自独立）
- 集成测试（命令间协作）
- E2E 测试（Agent 模拟调用）
- CLI 文档和 --help 支持

**成功标准：**
- [ ] 命令可执行：`tranotra batch --action search-and-import --config config.yaml`
- [ ] YAML 配置文件支持完整格式
- [ ] 支持 --dry-run 预览
- [ ] 输出包含详细的搜索和导入统计
- [ ] 所有搜索结果自动保存
- [ ] 错误处理和日志完整
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试覆盖主要工作流
- [ ] E2E 测试验证 Agent 集成
- [ ] --help 文档清晰准确

**依赖：** Story 5-1, 5-2, 5-3（所有独立命令）  
**预计工时：** 3-4 天

---

## 📊 Epic 统计

| 项目 | 数值 |
|------|------|
| **Total Stories** | 4 |
| **Total Tasks** | ~20-25 |
| **Estimated Effort** | 9-13 days |
| **Team Size** | 1-2 developers |
| **Dependencies** | Epic 1-2 (已完成) |
| **Risk Level** | Low (well-scoped) |

---

## 🔄 依赖和前置条件

### 前置要求
- ✅ Epic 1-2 已完成（搜索和导入逻辑已有）
- ✅ 测试框架已搭建（pytest）
- ✅ 数据库模型已定义

### 关键依赖
```
Story 5-1 (search)
    ↓
Story 5-2 (import) ← 依赖 5-1 输出
    ↓
Story 5-3 (query) ← 依赖 5-2 导入的数据
    ↓
Story 5-4 (batch + tests) ← 依赖 5-1, 5-2, 5-3 全部完成
```

---

## 📅 实现计划

### Phase 1: Core Commands (Week 1-2)
- Story 5-1: search command (2-3 days)
- Story 5-2: import command (2-3 days)
- Story 5-3: query command (2 days)

### Phase 2: Batch & Testing (Week 2-3)
- Story 5-4: batch command (2 days)
- Story 5-4: comprehensive testing (1-2 days)
- Story 5-4: documentation (1 day)

---

## ✅ 成功标准（Epic 级别）

1. **功能完整性**
   - ✅ 4 个命令全部可用
   - ✅ 所有参数和选项都能工作
   - ✅ JSON 输出格式符合规范

2. **质量标准**
   - ✅ 代码覆盖率 > 80%
   - ✅ 所有测试通过（单元 + 集成 + E2E）
   - ✅ 无 critical bugs

3. **Agent 集成**
   - ✅ Agent 能成功调用所有命令
   - ✅ 能解析 JSON 输出
   - ✅ 能处理错误响应

4. **文档完善**
   - ✅ CLI help 文档完整
   - ✅ 使用示例清晰
   - ✅ 配置文件示例可用

---

## ♻️ 代码复用策略

### 架构设计：薄 CLI 层 + 复用业务逻辑层

```
CLI 工具层（新增，薄层）
    ↓ 调用
业务逻辑层（现有代码，复用）
    ├── gemini_client.py
    │   ├── call_gemini_grounding_search() → 调用 Gemini API
    │   └── save_raw_response() → 自动保存结果到 data/gemini_responses/
    ├── parser.py
    │   └── CompanyParser.parse_response() → 解析 JSON/CSV/Markdown
    └── db.py
        ├── insert_company() → 导入数据到数据库
        └── get_companies_paginated() → 查询数据（支持过滤）
```

### 复用现有代码的具体方式

#### **Story 5-1: search 命令复用**
```python
from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search, get_last_saved_response_path
from tranotra.parser import CompanyParser

@cli.command()
def search(country: str, query: str, limit: int, output_format: str, output_dir: str):
    # 1. 直接调用现有的 Gemini API
    response = call_gemini_grounding_search(country, query)
    
    # 2. gemini_client.py 已自动保存原始响应到 data/gemini_responses/
    saved_file = get_last_saved_response_path()
    
    # 3. 用现有的 Parser 解析结果
    parser = CompanyParser()
    companies = parser.parse_response(response, format="JSON")
    
    # 4. 输出 JSON（含 saved_file 元数据）
    print(json.dumps({...}))
```

#### **Story 5-2: import 命令复用**
```python
from tranotra.db import insert_company
from tranotra.parser import CompanyParser

@cli.command()
def import_data(file: str, conflict_strategy: str, dry_run: bool):
    # 1. 读取文件
    with open(file) as f:
        data = json.load(f)
    
    # 2. 用现有的 Parser 解析
    parser = CompanyParser()
    companies = parser.parse_response(json.dumps(data), format="JSON")
    
    # 3. 用现有的 insert_company 导入
    for company in companies:
        try:
            insert_company(company)
        except ValueError as e:
            # 处理重复（基于现有逻辑）
            handle_conflict(company, conflict_strategy)
    
    # 4. 输出统计结果
    print(json.dumps({summary...}))
```

#### **Story 5-3: query 命令复用**
```python
from tranotra.db import get_companies_paginated

@cli.command()
def query(country: str, prospect_score_min: int, priority: str, limit: int, offset: int):
    # 直接调用现有的查询函数
    result = get_companies_paginated(
        country=country,
        prospect_score_min=prospect_score_min,
        priority=priority,
        page=(offset // limit) + 1,
        per_page=limit
    )
    
    # 输出格式化结果
    print(json.dumps({results...}))
```

### 复用的代码清单

| 模块 | 现有函数 | CLI 命令使用 |
|------|---------|-----------|
| **gemini_client.py** | `initialize_gemini()` | search 初始化 |
| | `call_gemini_grounding_search()` | search 调用 API |
| | `save_raw_response()` | search 自动保存 |
| | `get_last_saved_response_path()` | search 获取文件路径 |
| **parser.py** | `CompanyParser.parse_response()` | search/import 解析数据 |
| **db.py** | `insert_company()` | import 导入数据 |
| | `get_companies_paginated()` | query 查询数据 |
| | `get_today_statistics()` | batch 统计信息 |

### 优势

1. **避免代码重复** - 一行代码，两处使用（API + CLI）
2. **维护性强** - 修改业务逻辑无需改 CLI 层
3. **Bug 减少** - 复用已测试的代码（> 80% 覆盖率）
4. **开发快速** - CLI 层只负责参数解析和输出格式化
5. **一致性** - API 和 CLI 使用相同的业务逻辑，行为完全一致

### CLI 层职责（薄层）

- ✅ 参数解析和验证（Typer 框架）
- ✅ 调用业务逻辑层函数
- ✅ 结果格式化（JSON/CSV/Markdown）
- ✅ 错误处理和 Exit Code
- ✅ 日志输出（stderr）

---

## 🚀 关键设计决策

### 1. CLI 框架选择
- **方案：** Typer（基于 Click，更现代）
- **原因：** 类型提示支持、自动文档生成、Agent 友好

### 2. 输出格式
- **默认：** JSON（便于 Agent 解析）
- **可选：** CSV, Markdown（便于人工查看）

### 3. 文件保存策略
- **自动保存：** 搜索结果总是保存到 `data/gemini_responses/`
- **自定义目录：** 可通过 --output-dir 指定
- **文件命名：** 自动生成（包含时间戳、国家、关键词、结果数）

### 4. 错误处理
- **Exit Code 约定：**
  - 0: 成功
  - 1: 参数错误
  - 2: API/网络错误
  - 3: 验证错误
  - 4: 数据库错误

---

## 📚 参考文档

- 📄 **CLI 命令规范：** `4-cli-command-specification.md`
  - 完整的命令参数定义
  - 输出格式 JSON Schema
  - 使用示例和 Agent 集成示例

- 📄 **Epic 1-2 实现报告：** 
  - 搜索逻辑实现参考
  - 数据导入逻辑参考
  - 错误处理模式参考

---

## 🎓 技术栈

| 组件 | 选择 | 版本 |
|------|------|------|
| CLI Framework | Typer | Latest |
| Config Parser | PyYAML | 6.0+ |
| Testing | pytest | 7.4+ |
| Code Style | Black + isort | Latest |
| Type Hints | Python 3.8+ | - |

---

## 📌 备注

- CLI 优先于 Web UI（用户需求）
- API 和 Web UI 保留（并行维护）
- 设计充分考虑 Agent 集成需求
- 所有搜索结果自动持久化（审计和重用）

---

**Epic 状态：** 待批准  
**下一步：** 创建 4 个 Story 的详细规范文档

