---
title: "CLI Tool Command Specification for Agent Integration"
created_date: "2026-04-05"
version: "1.0"
status: "SPECIFICATION"
---

# 🖥️ CLI 工具命令规范

## 📌 概述

**目标：** 提供命令行工具供 AI Agent 调用，完成从搜索到入库的完整流程

**设计原则：**
- ✅ 独立命令（单一职责）
- ✅ 结构化输出（JSON 为主）
- ✅ Agent 友好（易于解析）
- ✅ 错误处理清晰（exit code + 错误信息）
- ✅ 幂等操作（可重复调用）

**使用场景：** Agent 接收自然语言 → 调用 CLI 命令 → 解析结果 → 返回给用户

---

## 🎯 4 个独立命令

### 1️⃣ `tranotra search` - 搜索公司数据

**用途：** 调用 Gemini API 搜索公司，返回原始数据

**⚡ 关键特性：**
- 🔍 调用 Gemini API 执行搜索
- 💾 **自动保存搜索结果到文件**（默认：`data/gemini_responses/`）
- 📺 **同时输出完整结果到 stdout**（Agent 可立即读取）
- 📄 支持 JSON、CSV、Markdown 多种格式
- ⏱️ 文件名自动生成（包含时间戳、国家、关键词、结果数量）

**命令：**
```bash
tranotra search \
  --country COUNTRY \
  --query QUERY \
  [--limit LIMIT] \
  [--output-format FORMAT] \
  [--output-dir DIR]
```

**参数：**

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--country` | string | ✓ | 国家名称 | Vietnam, Thailand, Indonesia |
| `--query` | string | ✓ | 搜索关键词 | "PVC manufacturer", "cable export" |
| `--limit` | int | ✗ | 返回结果数量（默认 50） | 20, 100 |
| `--output-format` | enum | ✗ | 输出格式（默认 json） | json, csv, markdown |
| `--output-dir` | string | ✗ | 保存文件的目录（默认：data/gemini_responses） | ./results, /tmp/data |

**输出行为：** 
- ✅ **总是保存到文件**：自动生成文件名（时间戳 + 国家 + 关键词），保存到 `--output-dir` 指定的目录
- ✅ **同时输出到 stdout**：完整的 JSON/CSV 数据输出到终端，Agent 可立即读取
- 📂 **默认保存位置**：`data/gemini_responses/` （相对于项目根目录）

**文件命名规则：**
```
{YYYYMMDD}_{HHMMSS}_{count}_{COUNTRY}_{keyword}.json

示例：
20260405_103000_25_Vietnam_PVC_manufacturer.json
20260405_103015_18_Thailand_textile_export.json
```

**输出格式（JSON）：**

```json
{
  "success": true,
  "command": "search",
  "timestamp": "2026-04-05T10:30:00Z",
  "query": {
    "country": "Vietnam",
    "keywords": "PVC manufacturer",
    "limit": 50
  },
  "results": {
    "total": 25,
    "companies": [
      {
        "name": "Vietnam PVC Co Ltd",
        "country": "Vietnam",
        "city": "Ho Chi Minh",
        "year_established": 2010,
        "employees": "100-500",
        "estimated_revenue": "$5M-10M",
        "main_products": "PVC plastic sheets",
        "export_markets": "USA, Singapore, Japan",
        "eu_us_jp_export": true,
        "raw_materials": "Vinyl chloride monomer",
        "recommended_product": "DOTP",
        "recommendation_reason": "Perfect fit for their production scale",
        "website": "www.vietnampvc.com",
        "contact_email": "sales@vietnampvc.com",
        "linkedin_url": "linkedin.com/company/vietnam-pvc",
        "best_contact_title": "Purchasing Manager",
        "prospect_score": 8
      }
    ]
  },
  "metadata": {
    "api_provider": "gemini",
    "execution_time_seconds": 3.5,
    "cached": false,
    "saved_file": "data/gemini_responses/20260405_103000_25_Vietnam_PVC_manufacturer.json",
    "saved_format": "json"
  }
}
```

**错误响应：**

```json
{
  "success": false,
  "command": "search",
  "error": "API_ERROR",
  "message": "Gemini API rate limit exceeded",
  "timestamp": "2026-04-05T10:30:00Z"
}
```

**Exit Code：**
- `0` - 成功
- `1` - 参数错误或其他错误
- `2` - API 错误（可重试）
- `3` - 网络错误（可重试）

**使用示例：**

```bash
# 搜索越南 PVC 制造商
# 结果自动保存到 data/gemini_responses/，同时输出到 stdout
tranotra search --country Vietnam --query "PVC manufacturer" --limit 50

# 搜索并保存到自定义目录
tranotra search \
  --country Thailand \
  --query "textile export" \
  --output-dir ./my_results \
  --output-format json
# 文件保存：./my_results/20260405_103015_18_Thailand_textile_export.json
# 内容同时输出到 stdout

# Agent 调用示例（Python）
result = subprocess.run([
    'tranotra', 'search',
    '--country', 'Vietnam',
    '--query', 'PVC manufacturer',
    '--output-format', 'json'
], capture_output=True, text=True)

if result.returncode == 0:
    data = json.loads(result.stdout)
    saved_file = data['metadata']['saved_file']
    print(f"Found {data['results']['total']} companies")
    print(f"Saved to: {saved_file}")  # 文件已自动保存
    
    # 如果需要查看保存的文件
    with open(saved_file, 'r') as f:
        saved_data = json.load(f)
```

---

### 2️⃣ `tranotra import` - 导入数据到数据库

**用途：** 从 JSON/CSV 文件导入公司数据到数据库，处理重复和验证

**命令：**
```bash
tranotra import \
  --file FILE \
  [--dry-run] \
  [--skip-validation] \
  [--conflict-strategy STRATEGY]
```

**参数：**

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--file` | string | ✓ | 输入文件路径（JSON 或 CSV） | results.json, data.csv |
| `--dry-run` | flag | ✗ | 预览导入（不实际写入数据库） | 无值 |
| `--skip-validation` | flag | ✗ | 跳过数据验证（谨慎使用） | 无值 |
| `--conflict-strategy` | enum | ✗ | 重复处理策略（默认 skip） | skip, update, error |

**冲突处理策略：**
- `skip` - 跳过重复的公司（基于 linkedin_normalized）
- `update` - 用新数据更新已存在的公司
- `error` - 遇到重复时返回错误并停止

**输出格式（JSON）：**

```json
{
  "success": true,
  "command": "import",
  "timestamp": "2026-04-05T10:30:00Z",
  "file": "results.json",
  "dry_run": false,
  "summary": {
    "total_records": 25,
    "imported": 23,
    "skipped": 2,
    "errors": 0,
    "updated": 0
  },
  "details": {
    "imported_ids": [1, 2, 3, 4, 5],
    "skipped_reasons": [
      {
        "row": 10,
        "company": "Duplicate PVC Ltd",
        "reason": "Duplicate linkedin_url (linkedin.com/company/dup-pvc)"
      },
      {
        "row": 15,
        "company": "Invalid Co",
        "reason": "Missing required field: name"
      }
    ],
    "validation_errors": []
  },
  "metadata": {
    "execution_time_seconds": 2.3,
    "database": "sqlite:///./data/tranotra_leads.db"
  }
}
```

**错误响应：**

```json
{
  "success": false,
  "command": "import",
  "error": "VALIDATION_ERROR",
  "message": "Failed to import: 5 records with validation errors",
  "timestamp": "2026-04-05T10:30:00Z",
  "details": {
    "errors": [
      {
        "row": 3,
        "reason": "Invalid prospect_score: 15 (must be 1-10)"
      }
    ]
  }
}
```

**Exit Code：**
- `0` - 完全成功
- `1` - 部分失败（有导入但有错误）
- `2` - 完全失败
- `3` - 验证错误

**使用示例：**

```bash
# 导入数据
tranotra import --file results.json

# 预览导入（不写数据库）
tranotra import --file results.json --dry-run

# 更新重复的公司
tranotra import --file results.json --conflict-strategy update

# Agent 调用示例（Python）
result = subprocess.run([
    'tranotra', 'import',
    '--file', 'results.json',
    '--conflict-strategy', 'skip'
], capture_output=True, text=True)

if result.returncode == 0:
    data = json.loads(result.stdout)
    print(f"Imported {data['summary']['imported']} companies")
    print(f"Skipped {data['summary']['skipped']} duplicates")
```

---

### 3️⃣ `tranotra query` - 查询数据库中的公司

**用途：** 从数据库查询公司数据，支持过滤和排序

**命令：**
```bash
tranotra query \
  [--country COUNTRY] \
  [--query SEARCH] \
  [--prospect-score-min SCORE] \
  [--prospect-score-max SCORE] \
  [--priority PRIORITY] \
  [--limit LIMIT] \
  [--offset OFFSET] \
  [--sort FIELD] \
  [--order ASC|DESC] \
  [--output-format FORMAT] \
  [--output-file FILE]
```

**参数：**

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--country` | string | ✗ | 国家过滤 | Vietnam, Thailand |
| `--query` | string | ✗ | 源查询关键词过滤 | "PVC manufacturer" |
| `--prospect-score-min` | int | ✗ | 最低前景分数 | 7 |
| `--prospect-score-max` | int | ✗ | 最高前景分数 | 10 |
| `--priority` | enum | ✗ | 优先级过滤 | HIGH, MEDIUM, LOW |
| `--limit` | int | ✗ | 返回数量（默认 20） | 50, 100 |
| `--offset` | int | ✗ | 分页偏移量 | 0, 20, 40 |
| `--sort` | string | ✗ | 排序字段（默认 prospect_score） | prospect_score, name, country |
| `--order` | enum | ✗ | 排序顺序（默认 DESC） | ASC, DESC |
| `--output-format` | enum | ✗ | 输出格式（默认 json） | json, csv, markdown |
| `--output-file` | string | ✗ | 保存到文件 | companies.json |

**输出格式（JSON）：**

```json
{
  "success": true,
  "command": "query",
  "timestamp": "2026-04-05T10:30:00Z",
  "filters": {
    "country": "Vietnam",
    "prospect_score_min": 7,
    "priority": "HIGH"
  },
  "results": {
    "total": 12,
    "returned": 10,
    "page": 1,
    "per_page": 10,
    "companies": [
      {
        "id": 1,
        "name": "Vietnam PVC Co Ltd",
        "country": "Vietnam",
        "city": "Ho Chi Minh",
        "prospect_score": 9,
        "priority": "HIGH",
        "main_products": "PVC plastic sheets",
        "export_markets": "USA, Singapore",
        "contact_email": "sales@vietnampvc.com"
      }
    ]
  },
  "metadata": {
    "execution_time_ms": 45,
    "database_records": 127
  }
}
```

**错误响应：**

```json
{
  "success": false,
  "command": "query",
  "error": "NO_RESULTS",
  "message": "No companies found matching criteria",
  "timestamp": "2026-04-05T10:30:00Z"
}
```

**Exit Code：**
- `0` - 有结果或无结果但成功
- `1` - 查询错误
- `2` - 数据库错误

**使用示例：**

```bash
# 查询越南高优先级公司
tranotra query --country Vietnam --priority HIGH --limit 50

# 查询前景分数 ≥ 8 的公司，按分数降序
tranotra query \
  --prospect-score-min 8 \
  --sort prospect_score \
  --order DESC \
  --limit 20

# 分页查询
tranotra query --limit 10 --offset 0  # 第 1 页
tranotra query --limit 10 --offset 10 # 第 2 页

# Agent 调用示例（Python）
result = subprocess.run([
    'tranotra', 'query',
    '--country', 'Vietnam',
    '--prospect-score-min', '8',
    '--output-format', 'json'
], capture_output=True, text=True)

if result.returncode == 0:
    data = json.loads(result.stdout)
    for company in data['results']['companies']:
        print(f"{company['name']}: {company['prospect_score']}/10")
```

---

### 4️⃣ `tranotra batch` - 批量操作（搜索+导入）

**用途：** 执行完整的搜索和导入流程，一条命令完成

**命令：**
```bash
tranotra batch \
  --action ACTION \
  --config CONFIG_FILE \
  [--dry-run] \
  [--output-file FILE]
```

**参数：**

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--action` | enum | ✓ | 批量操作类型 | search-and-import, import-only |
| `--config` | string | ✓ | 配置文件路径（YAML） | batch-config.yaml |
| `--dry-run` | flag | ✗ | 预览执行 | 无值 |
| `--output-file` | string | ✗ | 保存操作日志 | batch-results.json |

**配置文件格式（batch-config.yaml）：**

```yaml
# 批量搜索和导入配置
batch:
  name: "Vietnam PVC Manufacturers"
  description: "搜索并导入越南 PVC 制造商"
  
  searches:
    - country: "Vietnam"
      queries:
        - "PVC manufacturer"
        - "plastic film production"
        - "flexible hose export"
      limit: 50
    
    - country: "Thailand"
      queries:
        - "cable manufacturer"
        - "synthetic leather"
      limit: 50

  import:
    conflict_strategy: "skip"  # skip, update, error
    skip_validation: false
    
  options:
    parallel_searches: false  # 并发搜索（未来支持）
    save_intermediate: true   # 保存搜索结果到文件（总是开启，保存到 data/gemini_responses）
    search_results_dir: "data/gemini_responses"  # 搜索结果保存目录
```

**输出格式（JSON）：**

```json
{
  "success": true,
  "command": "batch",
  "timestamp": "2026-04-05T10:30:00Z",
  "action": "search-and-import",
  "config": "batch-config.yaml",
  "summary": {
    "searches_total": 5,
    "searches_successful": 5,
    "companies_found": 120,
    "companies_imported": 115,
    "companies_skipped": 5,
    "companies_errors": 0
  },
  "details": {
    "searches": [
      {
        "country": "Vietnam",
        "query": "PVC manufacturer",
        "found": 25,
        "imported": 23,
        "skipped": 2,
        "status": "success",
        "saved_file": "data/gemini_responses/20260405_103000_25_Vietnam_PVC_manufacturer.json"
      },
      {
        "country": "Vietnam",
        "query": "plastic film production",
        "found": 18,
        "imported": 18,
        "skipped": 0,
        "status": "success",
        "saved_file": "data/gemini_responses/20260405_103012_18_Vietnam_plastic_film_production.json"
      }
    ]
  },
  "metadata": {
    "total_execution_time_seconds": 45,
    "api_calls": 5,
    "database_writes": 115,
    "search_results_dir": "data/gemini_responses"
  }
}
```

**使用示例：**

```bash
# 执行批量操作
tranotra batch --action search-and-import --config batch-config.yaml

# 预览（不实际导入）
tranotra batch --action search-and-import --config batch-config.yaml --dry-run

# Agent 调用示例（Python）
result = subprocess.run([
    'tranotra', 'batch',
    '--action', 'search-and-import',
    '--config', 'batch-config.yaml'
], capture_output=True, text=True)

if result.returncode == 0:
    data = json.loads(result.stdout)
    print(f"导入 {data['summary']['companies_imported']} 家公司")
    print(f"跳过 {data['summary']['companies_skipped']} 个重复")
```

---

## 🔄 Agent 工作流示例

### 场景 1：搜索→导入→查询

```
用户输入：
"帮我搜索越南的 PVC 制造商，导入数据库，然后显示前景分数最高的 5 家公司"

Agent 执行步骤：
1. 调用 search:
   tranotra search --country Vietnam --query "PVC manufacturer" --limit 50
   → 返回 25 家公司

2. 调用 import:
   tranotra import --file search_results.json --conflict-strategy skip
   → 导入 23 家（跳过 2 个重复）

3. 调用 query:
   tranotra query --country Vietnam --sort prospect_score --order DESC --limit 5
   → 返回前 5 家公司

4. 返回给用户：格式化结果
```

### 场景 2：批量导入多个国家

```
用户输入：
"批量导入越南、泰国、印尼的制造商数据"

Agent 执行步骤：
1. 创建 batch-config.yaml
2. 调用 batch:
   tranotra batch --action search-and-import --config batch-config.yaml
   → 自动搜索 3 个国家、导入所有公司
```

---

## ⚙️ 技术实现细节

### 使用的库
- **Click** 或 **Typer** - CLI 框架
- **json** - JSON 输出
- **csv** - CSV 支持
- **pyyaml** - 配置文件支持
- **logging** - 日志记录

### 错误处理
```python
Exit Code 约定：
0 - 完全成功
1 - 参数错误或一般错误
2 - API/网络错误（可重试）
3 - 业务逻辑错误（验证、重复等）
4 - 数据库错误
```

### 日志输出（stderr）
- `INFO` - 操作进度（搜索中、导入中）
- `WARNING` - 跳过项目、轻微错误
- `ERROR` - 严重错误
- `DEBUG` - 详细调试信息（可选）

---

## 📦 输出文件格式

### JSON Schema
```json
{
  "success": boolean,
  "command": string,
  "timestamp": ISO 8601,
  "error": string (optional),
  "message": string (optional),
  "results": object,
  "summary": object,
  "metadata": object
}
```

### CSV 格式
- 表头行
- 数据行（一公司一行）
- 编码：UTF-8

### Markdown 格式（可选）
```markdown
# 查询结果

总共：12 家公司
返回：10 家

| 公司名 | 国家 | 前景分数 | 优先级 |
|-------|------|--------|-------|
| ... | ... | ... | ... |
```

---

## 🧪 测试场景

### 单元测试
- ✓ 参数验证
- ✓ 输出格式正确
- ✓ 错误处理

### 集成测试
- ✓ search + import 完整流程
- ✓ query 结果准确性
- ✓ batch 多步操作

### E2E 测试（Agent 模拟）
- ✓ Agent 调用 CLI
- ✓ 解析 JSON 输出
- ✓ 处理错误响应

---

## 📋 实现检查清单

- [ ] 命令框架搭建（Click/Typer）
- [ ] `search` 命令实现
- [ ] `import` 命令实现
- [ ] `query` 命令实现
- [ ] `batch` 命令实现
- [ ] JSON 输出序列化
- [ ] 错误处理和 Exit Code
- [ ] CSV/Markdown 输出支持
- [ ] 配置文件解析（YAML）
- [ ] 单元测试
- [ ] 集成测试
- [ ] Agent 集成测试
- [ ] 文档编写（--help）

---

## 🎯 优先级

**Phase 1（MVP）：**
1. `search` 命令（基础搜索）
2. `import` 命令（基础导入）
3. `query` 命令（基础查询）
4. JSON 输出

**Phase 2（增强）：**
1. `batch` 命令
2. CSV 输出
3. 配置文件支持
4. 并发搜索（可选）

**Phase 3（优化）：**
1. 性能优化
2. 缓存机制
3. 增量导入
4. 日志系统

---

**状态：** 规范完成，准备实现

**下一步：** 创建开发故事，开始实现 Phase 1
