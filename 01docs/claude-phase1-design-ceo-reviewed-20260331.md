# Design: Tranotra Leads Phase 1 — LinkedIn数据采集 + 去重 + Web展示（CEO Reviewed）

**版本**: v2.0（CEO Review后更新）  
**生成日期**: 2026-03-31  
**项目**: tranotra-leads  
**负责人**: Tranotra Chemical  
**状态**: APPROVED FOR DEVELOPMENT  
**模式**: Startup - HOLD SCOPE（深入审查，无扩展）  
**阶段**: Phase 1 (MVP)

---

## 1. 背景与目标

### 1.1 核心痛点

Tranotra Chemical 是一家增塑剂出口商，目标市场在东南亚（越南、泰国、印尼）和中东（UAE、沙特）。

**定量证据**：
- 当前每天必须手动在LinkedIn搜索，30-45分钟找10个客户
- 成功概率只有10%（需筛选大量不符合的公司）
- 每周花20小时在搜索和记录上
- **目标**：降到5小时/周（75%时间节省）

**定性证据**：
- 这是缓慢行业，找到好客户可长期合作
- 真实痛点：不是"找客户"本身，而是"记录、去重、分析、优化搜索策略"
- 用户已有Gemini和Apollo API账号，对自动化工具认可

### 1.2 产品目标

构建一个本地Python程序，实现：

1. 用Gemini Grounding Search自动发现目标市场的潜在买家
2. 自动解析搜索结果（验证格式）
3. 自动去重（以规范化LinkedIn URL为唯一键）
4. 解析完整16字段数据到SQLite
5. 通过Web界面展示、管理、分析数据
6. 记录搜索历史和系统运行效率指标

### 1.3 核心约束

- **本地运行**，不依赖云端定时任务
- **无Web框架外依赖**（Flask即可）
- **SQLite本地存储**
- **Gemini返回格式待验证**（M1第1天任务）
- **分阶段开发**（Phase 1不涉及官网分析、Apollo集成、邮件发送）

---

## 2. 用户故事

**作为** Tranotra的运营者，  
**我希望** 在Web界面输入"国家 + 搜索词"，系统自动搜索并返回完整的去重公司列表，带评分和联系信息，  
**以便** 我能在10分钟内看到高质量的潜在客户，同时监控搜索策略的效率。

**验收标准**：
- 输入"Vietnam" + "PVC manufacturer"，得到10-20家去重后的公司
- 看到完整信息：公司名、评分、优先级、邮箱、LinkedIn、官网、推荐产品
- 可以在卡片视图和表格视图之间切换
- 看到系统效率指标（去重率、命中率、高分占比）
- 看到搜索历史和哪些搜索词最高效

---

## 3. 核心假设 & 约束（CEO Review后更新）

### 已验证的假设：
1. ✅ Gemini能从搜索结果中提取LinkedIn URL（用户已验证）
2. ⚠️ Gemini返回格式：**待M1验证**（可能Markdown表格/JSON/CSV）
3. ✅ 接受官网缺失（显示"未找到"）
4. ✅ 接受AI推断的不完美性
5. ✅ 去重键：规范化LinkedIn URL（小写+去斜杠+转义）
6. ✅ 分阶段开发（Phase 1包含完整16字段，不只是简化版）

### CEO Review决定：
- **Schema扩展**：从9字段→23字段（完整Gemini返回 + 规范化字段）
- **前端复杂度**：卡片视图+表格视图+效率仪表板+系统指标
- **搜索历史**：保存搜索效率数据，用于优化策略

---

## 4. 系统架构

### 4.1 技术栈

| 组件 | 选择 | 版本 |
|------|------|------|
| 后端框架 | Flask | 2.3.0+ |
| 数据库 | SQLite | 3.x |
| ORM | SQLAlchemy | 2.0.0+ |
| AI能力 | Gemini API | gemini-2.0-flash |
| 前端 | HTML + Bootstrap + Vanilla JS | Bootstrap 5 |
| 部署 | 本地运行 | 用户电脑 python main.py |

### 4.2 数据库设计

**主表：`companies`（23字段）**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK | 自增主键 |
| `name` | TEXT | NOT NULL | 公司名称（英文） |
| `country` | TEXT | NOT NULL | 国家（Vietnam/Thailand等） |
| `city` | TEXT | | 城市/省份 |
| `year_established` | INTEGER | | 成立年份 |
| `employees` | TEXT | | 员工数范围（<100/100-500/500-2000/2000+） |
| `estimated_revenue` | TEXT | | 估计年收入 |
| `main_products` | TEXT | | 主要产品描述 |
| `export_markets` | TEXT | | 出口市场（逗号分隔） |
| `eu_us_jp_export` | BOOLEAN | | 是否出口欧美日 |
| `raw_materials` | TEXT | | 原材料 |
| `recommended_product` | TEXT | | 推荐的Tranotra产品（DOTP/DOP等） |
| `recommendation_reason` | TEXT | | 推荐理由（1句话） |
| `website` | TEXT | | 官网域名 |
| `contact_email` | TEXT | | 联系邮箱 |
| `linkedin_url` | TEXT | | LinkedIn公司页面原始URL |
| `linkedin_normalized` | TEXT | UNIQUE | 规范化后的LinkedIn URL（去重键） |
| `best_contact_title` | TEXT | | 最佳联系职位 |
| `prospect_score` | INTEGER | CHECK(1-10) | 潜在客户评分(1-10) |
| `priority` | TEXT | CHECK(HIGH/MEDIUM/LOW) | 优先级 |
| `source_query` | TEXT | NOT NULL | 本次搜索的国家+关键词 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**辅表：`search_history`（搜索记录+效率指标）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER | PK |
| `country` | TEXT | 搜索的国家 |
| `query` | TEXT | 搜索关键词 |
| `result_count` | INTEGER | Gemini返回的原始公司数 |
| `new_count` | INTEGER | 本次新增（去重后）的公司数 |
| `duplicate_count` | INTEGER | 本次重复的公司数（已存在库中） |
| `avg_score` | FLOAT | 本次新增公司的平均评分 |
| `high_priority_count` | INTEGER | 本次返回的HIGH优先级数 |
| `created_at` | DATETIME | 搜索时间 |

---

## 5. 系统数据流

```
【M1：验证格式】
用户输入: 国家 Vietnam + 关键词 "PVC manufacturer"
                 ↓
        【关键第一步】
        调用 Gemini Grounding Search API
             ↓
        ⚠️ 接收原始数据
        格式：Markdown表格 / JSON / CSV？
             ↓
【M2：解析+去重】
        [格式检测器]
        识别返回格式 (Markdown / JSON / CSV)
             ↓
        [数据提取解析器]
        解析16字段 (name, country, linkedin_url等)
             ↓
        [规范化函数]
        linkedin_url → linkedin_normalized
        (小写 + 去尾部斜杠 + 转义特殊字符)
             ↓
        【去重逻辑】
        FOR EACH 公司:
          IF linkedin_normalized 存在于 companies
            → 记录到 duplicate_count
            → 跳过插入
          ELSE
            → 插入到 companies 表
            → 记录到 new_count
             ↓
【M3：前端渲染】
        [Web API] 查询数据库
          - 本次搜索的所有新增公司（new_count）
          - 计算本次平均评分
          - 计算HIGH优先级比例
             ↓
        [搜索历史写入]
        写入一条 search_history 记录
             ↓
【M4：UI展示】
        [前端渲染]
        - 结果表格（卡片视图 / 表格视图切换）
        - 搜索历史（最近20次）
        - 效率仪表板（7天聚合数据）
```

---

## 6. Web前端详细设计

### 6.1 页面1：搜索表单

```
┌──────────────────────────────────────────────────────┐
│    Tranotra Leads — LinkedIn自动搜索                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  国家:  [Vietnam▼] [Thailand] [Indonesia] [UAE] [SA] │
│                                                      │
│  关键词:  [text input: "PVC manufacturer"]           │
│          [最近搜索 ▼]                                 │
│          💡 示例: cable mfg, synthetic leather...     │
│                                                      │
│          [🔍 搜索按钮]  [清除]                       │
│                                                      │
│  ═════════════════════════════════════════════════   │
│  📊 今日统计:  搜索3次 | 新增47家 | 去重率18%        │
│  📈 本周效率:  ↑ 22% (vs 上周)                       │
│  ⭐ 高分率:   28% (Score≥8)                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**交互说明**：
- 国家支持快速切换（单选）
- 关键词输入框下有"最近搜索"下拉，快速重复搜索
- 示例关键词帮助新用户
- 搜索按钮点击后，禁用按钮并显示加载动画

### 6.2 页面2：搜索结果（双视图）

#### 2A. 卡片视图（推荐首选）

```
本次搜索: Vietnam + "PVC manufacturer"
========================================
新增: 15家 | 重复: 3家 | 平均评分: 8.1

[视图切换] 卡片视图 ✓ | 表格视图
[操作] 导出CSV | 打印 | 刷新

┌─────────────────────────────────────────┐
│ 🏢 CADIVI (Ho Chi Minh City, Vietnam)  │
│ 📊 Score: 10/10 | 优先级: 🔴HIGH        │
│ 👥 员工: 500-2000 | 年收: ~$200M+       │
│ 🏭 产品: 电缆/电线制造                   │
│ 🌍 出口: USA, ASEAN, Australia          │
│ 🎯 推荐: DOTP / TOTM (USA认证电缆)     │
│ 📧 Email: cadivi@cadivi.vn              │
│ 🔗 LinkedIn: linkedin.com/company/...   │
│ 🌐 官网: cadivi.vn                      │
│ 💼 联系: Purchasing Manager             │
│                                         │
│ [复制邮箱] [打开LinkedIn] [打开官网]   │
│ [Draft邮件] [标记已联系] [加备注]      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🏢 VN EcoFloor (Hanoi / Ninh Binh)     │
│ 📊 Score: 10/10 | 优先级: 🔴HIGH        │
│ ...
└─────────────────────────────────────────┘
```

#### 2B. 表格视图

```
[视图切换] 卡片视图 | 表格视图 ✓
[操作] 导出CSV | 刷新
[排序] 按评分↓ | 按优先级 | 按公司名

┌───┬─────────────┬─────┬────────┬──────┬─────────┬──────┐
│ # │ 公司名      │评分 │优先级  │邮箱  │LinkedIn │官网  │
├───┼─────────────┼─────┼────────┼──────┼─────────┼──────┤
│ 1 │ CADIVI      │ 10  │ HIGH   │ ✓    │ ✓       │ ✓    │
│ 2 │ VN EcoFloor │ 10  │ HIGH   │ ✓    │ ✓       │ ✓    │
│ 3 │ Neo Floor   │ 10  │ HIGH   │ ✓    │ ✓       │ ✓    │
│ 4 │ TBS Group   │ 10  │ HIGH   │ ✓    │ ✓       │ ✓    │
│ 5 │ Formosa     │  9  │ HIGH   │ ✓    │ ✓       │ ✓    │
└───┴─────────────┴─────┴────────┴──────┴─────────┴──────┘
```

### 6.3 页面3：效率仪表板 + 搜索历史

```
┌═══════════════════════════════════════════════════════┐
│           🎯 系统运行效率仪表板（最近7天）            │
├═══════════════════════════════════════════════════════┤

📊 关键指标:
┌─────────────────────────────────────────────────────┐
│ 总搜索次数:        47次                             │
│ 新增公司总数:      312家                            │
│ 去重率（重复）:    18% ← 搜索词有重叠，需优化      │
│ 平均命中率:        20.8家/搜索 ← 搜索词质量指标     │
│ 高分公司占比:      28% (312家中89家评分≥8)        │
│ 本日 vs 昨日:      ↑ 22% (搜索频率上升)             │
│ 本周 vs 上周:      ↑ 18% (持续提升)                │
└─────────────────────────────────────────────────────┘

📈 搜索词效率排名（命中率从高到低）:
┌────┬──────────────────┬──────┬──────┬──────┬─────────┐
│排名│ 搜索词           │ 国家 │命中数│重复数│平均评分│
├────┼──────────────────┼──────┼──────┼──────┼─────────┤
│ 1  │ cable mfg        │ VN   │ 28   │ 3    │ 8.2    │ ← 最高效
│ 2  │ synthetic leather│ TH   │ 25   │ 4    │ 7.8    │
│ 3  │ flooring export  │ VN   │ 18   │ 2    │ 7.5    │
│ 4  │ PVC manufacturer │ ID   │ 8    │ 8    │ 6.2    │ ← 最低效
└────┴──────────────────┴──────┴──────┴──────┴─────────┘

🔄 搜索历史明细（最近20次）:
┌──────────┬──────┬──────────────────┬───────┬────────┬────────┐
│ 日期     │ 国家 │ 关键词           │ 新增  │ 重复   │ 评价   │
├──────────┼──────┼──────────────────┼───────┼────────┼────────┤
│2026-03-31│ VN   │ cable mfg        │ 12    │ 3      │ ⭐⭐⭐⭐⭐│
│2026-03-30│ TH   │ synthetic leather│ 8     │ 2      │ ⭐⭐⭐⭐  │
│2026-03-29│ VN   │ PVC manufacturer │ 4     │ 8      │ ⭐⭐    │
│...       │ ...  │ ...              │ ...   │ ...    │ ...   │
└──────────┴──────┴──────────────────┴───────┴────────┴────────┘

💡 建议:
- "PVC manufacturer" 在ID的重复率太高（100%），建议跳过
- "cable mfg" 在VN最高效，可每周重复搜索
```

---

## 7. 错误处理 & 失败场景

| 场景 | 原因 | 处理方式 | 用户看到 | 严重性 |
|------|------|--------|---------|--------|
| Gemini搜索0结果 | 搜索词太具体 | 记录、继续 | "本次未找到，建议修改词" | LOW |
| **Gemini返回格式错误** | API返回非预期格式 | **M1验证失败，无法继续** | "搜索失败：格式错误" | **CRITICAL** |
| 解析失败（字段缺失） | Gemini返回不完整 | 填充"N/A"，继续 | 表格显示"N/A" | MEDIUM |
| LinkedIn URL去重冲突 | 同URL多条记录 | 规范化处理，自动合并 | 无感知，自动处理 | LOW |
| 数据库写入失败 | SQLite锁定/磁盘满 | 重试1次，失败则报错 | "保存失败，请重试" | HIGH |
| Web查询超时(>3s) | 数据库太大/无索引 | 返回缓存+分页 | "加载中...请稍候" | MEDIUM |
| 用户网络中断 | 连接丢失 | 自动重连3次 | "网络连接中断，重试中..." | MEDIUM |

**M1关键验证**：Gemini格式错误是唯一会导致整个系统无法工作的CRITICAL风险。必须在M1第1天验证。

---

## 8. 开发里程碑（更新版）

| 里程碑 | 包含内容 | 时间 | 验收标准 |
|--------|---------|------|---------|
| **M1** | Gemini格式验证 + DB初始化 + Flask框架 + 测试脚本 | 3-4天 | 跑一次搜索，打印原始返回数据，确认格式，成功入库15条记录 |
| **M2** | 格式检测 + 解析器 + 规范化函数 + 去重逻辑 + search_history记录 | 3-4天 | 搜索"Vietnam/PVC"→15家入库，重复率18%正确，search_history记录完整 |
| **M3** | Web前端：搜索表单 + 卡片视图 + 表格视图 + 快捷操作 | 3-4天 | 能在浏览器搜索，两种视图可用，导出CSV工作 |
| **M4** | 效率仪表板 + 系统指标计算 + 完整测试 + 部署文档 | 2-3天 | 仪表板显示7天数据、命中率、去重率、搜索词排名，README完整，用户能独立运行 |

**总计**：2周（每天开发6-8小时）

---

## 9. 不在范围内（Phase 1）

- 官网抓取 & 分析（Phase 2）
- Apollo API集成 & 联系人查找（Phase 2）
- 邮件草稿生成 & 发送（Phase 3）
- 邮件回复追踪（Phase 3+）
- 多用户支持（未定）
- 云端部署（未定）
- 自动邮件跟进（Phase 3+）
- 与CRM集成（未定）

---

## 10. 前置条件 & 依赖

**必须**：
- Gemini API账号 + 有效的API Key
- Python 3.8+
- 50MB磁盘空间（初期）

**可选但推荐**：
- Chrome/Firefox浏览器（Web界面）
- 文本编辑器（查看logs）

---

## 11. 技术细节 & 架构决策

### 11.1 Gemini格式验证（M1关键）

在M1第1天，执行以下测试脚本来确认Gemini返回格式：

```python
# test_gemini_format.py
from google import generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-2.0-flash")

prompt = """
Search for soft PVC product manufacturers in Vietnam 
with 100+ employees that export to EU or USA markets.

Return data with these 16 fields:
1. Company Name
2. City
3. Year Established
... (full list)

Return in STRUCTURED format (CSV or JSON or markdown table).
"""

response = model.generate_content(prompt)
print("=== RAW RESPONSE ===")
print(response.text)
print("=== FORMAT TYPE ===")
# 检查: Markdown表格 / JSON / CSV？
```

基于输出格式，决定M2的解析器实现。

### 11.2 规范化函数（去重）

```python
def normalize_linkedin_url(url: str) -> str:
    """
    规范化LinkedIn URL以便去重
    输入: "https://www.linkedin.com/company/cadivi/"
    输出: "linkedin.com/company/cadivi"
    """
    if not url:
        return ""
    
    url = url.lower().strip()
    # 移除https://和www.
    url = url.replace("https://", "").replace("http://", "")
    url = url.replace("www.", "")
    # 移除尾部斜杠
    url = url.rstrip("/")
    # 标准化特殊字符
    url = url.replace(" ", "-")
    
    return url
```

### 11.3 Web框架最小化

Flask app结构：
```
tranotra-leads/
├── main.py              # Flask应用入口
├── config.py            # 配置（API Key等）
├── db.py                # SQLAlchemy模型+初始化
├── gemini_client.py     # Gemini API调用
├── parser.py            # 数据解析+规范化
├── routes.py            # Flask路由
├── templates/
│   ├── base.html        # 基础模板
│   ├── search.html      # 搜索页面
│   └── results.html     # 结果展示
├── static/
│   ├── style.css        # Bootstrap + 自定义样式
│   └── app.js           # 视图切换、导出CSV等
├── .env                 # 环境变量（不进git）
├── requirements.txt
└── README.md
```

---

## 12. 成功标准 & 交付物

**Phase 1完成后，用户应该能说**：
- "我在Web界面搜索'越南+PVC'，2秒内看到去重的15家公司，完整信息，评分排序"
- "我可以导出结果，也能看到搜索词的效率排名"
- "系统帮我把搜索时间从30分钟降到5分钟"

**交付物**：
1. ✅ tranotra-leads/ 项目目录（完整代码）
2. ✅ README.md（安装+运行说明）
3. ✅ 本地SQLite数据库（初始化脚本）
4. ✅ Web界面（localhost:5000 可访问）
5. ✅ 系统效率仪表板（实时统计）

---

## 13. Phase 2 预告（不在Phase 1范围）

一旦Phase 1稳定运行，Phase 2的目标是：
- 官网自动抓取（BeautifulSoup）
- Gemini分析官网内容（确认产品线、进口需求、规模）
- Apollo API集成（查找联系人和邮箱）
- 邮件草稿自动生成

估计3-4周。

---

## 14. 附录：参考实现细节

### CEO Review 决策摘要

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据库schema | 扩展到23字段（完整16字段+规范化+搜索历史指标） | 用户在Phase 1就能看到完整信息+系统效率 |
| 前端复杂度 | 完整版（卡片+表格+仪表板） | 满足用户"发现系统运行效率高低"的核心需求 |
| 去重策略 | 规范化LinkedIn URL作为UNIQUE键 | 处理URL格式不一致问题 |
| 搜索历史 | 保存搜索效率指标（新增数、去重数、平均评分） | 用户可以优化搜索词策略 |
| 格式验证 | M1第1天优先级最高 | Gemini格式错误是唯一CRITICAL风险 |
| 官网缺失 | 保存所有记录，显示"N/A" | Phase 1的数据库"完整"，不遗漏数据 |
| 前端技术栈 | Flask Jinja2 + Bootstrap + Vanilla JS | 无npm依赖，用户直接python main.py即可运行 |

---

*文档结束*
