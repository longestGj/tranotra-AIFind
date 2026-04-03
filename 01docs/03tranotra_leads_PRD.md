# PRD: Tranotra Leads — 本地化客户开发自动化流水线

**版本**: v1.0  
**产品**: tranotra-leads  
**负责人**: Tranotra Chemical  
**状态**: 待开发

---

## 1. 背景与目标

### 1.1 业务背景

Tranotra Chemical 是一家专注增塑剂（DOTP、DOP、ATBC、TOTM 等）出口的外贸 SOHO，目标市场为东南亚（越南、泰国、印尼）和中东（UAE、沙特）。

核心痛点：客户开发完全依赖人工，效率极低。需要一套本地化运行的自动化流水线，从"搜索目标公司"到"生成个性化开发信草稿"全流程自动化，人工仅在最后审核环节介入。

### 1.2 产品目标

构建一个本地 Python 程序，实现：

1. 自动发现目标市场的潜在买家公司
2. 自动抓取并分析公司官网，生成公司画像
3. 通过 API 找到对应联系人和邮箱
4. 自动生成个性化英文开发信草稿
5. 人工审核后通过 Aliyun DirectMail 发送
6. 所有数据持久化到本地 SQLite 数据库

### 1.3 核心约束

- 本地运行，不依赖云端定时任务（无 Google Apps Script）
- 人工审核是发送前的必经环节，不支持全自动发送
- 邮件发送使用已有的 Aliyun DirectMail 账号（`info@mail.tranotra.com`）
- 初期不需要 Web UI，CLI 界面即可

---

## 2. 用户故事

**作为** Tranotra 的唯一运营者，  
**我希望** 每周运行一次流水线，自动生成一批高质量的潜在买家名单和开发信草稿，  
**以便** 我只需花 30 分钟做审核和发送，而不是花几小时手动搜索和写信。

---

## 3. 系统架构

### 3.1 项目结构

```
tranotra-leads/
├── config.py              # API keys、目标市场、产品配置
├── db.py                  # SQLite 初始化 + CRUD 操作
├── pipeline/
│   ├── __init__.py
│   ├── discover.py        # 阶段1: Gemini Grounding Search 发现公司
│   ├── profile.py         # 阶段2: 官网抓取 + Gemini 画像分析
│   ├── contacts.py        # 阶段3: Apollo + Hunter.io 找联系人
│   ├── score.py           # 阶段3b: 公司评分与过滤
│   └── draft_email.py     # 阶段4: Gemini 生成开发信草稿
├── outreach/
│   ├── __init__.py
│   ├── review.py          # 阶段5: CLI 审核界面
│   └── send.py            # 阶段5b: Aliyun DirectMail 发送
├── main.py                # 入口：一键运行完整流水线
├── requirements.txt
└── .env                   # 环境变量（不进 git）
```

### 3.2 数据流

```
Gemini Grounding Search
    → 公司名单 (companies 表)
    → 官网抓取 + Gemini 画像分析 (companies 表更新)
    → ImportYeti 验证 (可选，companies 表更新)
    → Apollo API 找联系人 → Hunter.io 验证邮箱 (contacts 表)
    → 评分过滤 (score >= 6 才进入下一阶段)
    → Gemini 生成开发信草稿 (emails 表)
    → CLI 审核 (emails 表状态更新: pending → approved/rejected)
    → Aliyun DirectMail 发送 (emails 表状态更新: approved → sent)
```

---

## 4. 数据库设计

使用 SQLite，文件路径：`./data/leads.db`

### 4.1 `companies` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `name` | TEXT | 公司名称 |
| `website` | TEXT | 官网域名（用于 API 查询） |
| `country` | TEXT | 国家（Vietnam / Thailand / Indonesia / UAE / Saudi Arabia） |
| `source_query` | TEXT | 发现该公司时使用的搜索词 |
| `description` | TEXT | Gemini 返回的公司描述 |
| `product_line` | TEXT | 官网分析得出的产品线 |
| `import_need` | TEXT | 是否有增塑剂进口需求（yes/no/unknown） |
| `recommended_product` | TEXT | 推荐产品（DOTP/DOP/ATBC 等） |
| `recommended_reason` | TEXT | 推荐理由 |
| `score` | INTEGER | Prospect Score 1-10 |
| `priority` | TEXT | A/B/C 优先级 |
| `eu_export_flag` | BOOLEAN | 是否出口欧盟（影响 DOP 限制） |
| `importyeti_verified` | BOOLEAN | 是否通过 ImportYeti 验证 |
| `website_fetched` | BOOLEAN | 官网是否已抓取 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

### 4.2 `contacts` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `company_id` | INTEGER FK | 关联 companies.id |
| `name` | TEXT | 联系人姓名 |
| `title` | TEXT | 职位 |
| `email` | TEXT | 邮箱地址 |
| `email_verified` | BOOLEAN | Hunter.io 是否验证通过 |
| `source` | TEXT | 来源（apollo / hunter） |
| `created_at` | DATETIME | 创建时间 |

### 4.3 `emails` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `company_id` | INTEGER FK | 关联 companies.id |
| `contact_id` | INTEGER FK | 关联 contacts.id |
| `subject` | TEXT | 邮件主题 |
| `body` | TEXT | 邮件正文（草稿） |
| `status` | TEXT | pending / approved / rejected / sent / failed |
| `sent_at` | DATETIME | 发送时间 |
| `created_at` | DATETIME | 创建时间 |

---

## 5. 功能模块详细说明

### 5.1 `config.py` — 配置管理

使用 `python-dotenv` 从 `.env` 文件加载所有敏感配置。

**环境变量（`.env` 文件）：**

```
GEMINI_API_KEY=
APOLLO_API_KEY=
HUNTER_API_KEY=
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_FROM_EMAIL=info@mail.tranotra.com
ADMIN_EMAIL=info@tranotra.com
```

**目标市场配置（硬编码在 `config.py`）：**

```python
TARGET_MARKETS = [
    "Vietnam",
    "Thailand", 
    "Indonesia",
    "UAE",
    "Saudi Arabia",
]

PRODUCT_CONTEXT = """
Tranotra Chemical is a China-based plasticizer supplier.
Products: DOTP (flagship, non-phthalate), DOP, ATBC (food-grade), 
          TOTM (heat-resistant), DOS, TBC, LF-10, PVC paste resin.
Key advantage: DOTP from Blue Sail Chemical, top China producer.
Target buyers: PVC product manufacturers (cables, flooring, artificial leather, 
               medical tubing, food packaging).
Note: DOP has EU REACH restrictions — avoid recommending DOP for EU exporters.
"""

MIN_SCORE_TO_PROCEED = 6  # 低于此分数跳过联系人查找和邮件生成
```

---

### 5.2 `db.py` — 数据库层

初始化 SQLite 数据库，提供 CRUD 函数。

**关键函数：**

- `init_db()` — 创建所有表（如不存在）
- `insert_company(data: dict) -> int` — 插入公司，返回 id；如域名已存在则跳过（`UNIQUE` on `website`）
- `update_company(id: int, data: dict)` — 更新公司字段
- `get_companies_pending_profile() -> list` — 查询 `website_fetched=False` 的公司
- `get_companies_pending_contacts() -> list` — 查询 `score >= MIN_SCORE` 且无联系人的公司
- `get_companies_pending_email() -> list` — 查询有联系人但无草稿邮件的公司
- `insert_contact(data: dict) -> int`
- `insert_email(data: dict) -> int`
- `update_email_status(id: int, status: str)`
- `get_emails_pending_review() -> list` — 查询 `status='pending'` 的邮件，JOIN contacts 和 companies

---

### 5.3 `pipeline/discover.py` — 公司发现

**使用**: Gemini API（`gemini-2.0-flash` 或更新版本），开启 Google Search Grounding。

**搜索逻辑：**

对每个目标市场，依次执行多个搜索查询，覆盖不同买家类型：

```python
SEARCH_QUERIES_TEMPLATE = [
    "{country} PVC manufacturer plasticizer importer",
    "{country} cable wire manufacturer PVC compound",
    "{country} artificial leather PVC flooring manufacturer",
    "{country} medical PVC tubing manufacturer",
    "{country} plastic products factory DOTP DOP",
]
```

**Gemini Prompt（每次查询）：**

```
Search for companies in {country} that manufacture PVC products and likely 
import plasticizers (DOTP, DOP, ATBC) from China.

For each company found, return a JSON array. Each item must have:
- name: company name
- website: company website domain (without https://)
- country: "{country}"
- description: 1-2 sentence description
- product_line: what PVC products they make
- import_need: "yes" / "no" / "unknown"
- eu_export_flag: true if they export to EU/USA (affects plasticizer compliance)
- source_query: "{query}"

Return ONLY valid JSON array, no markdown, no explanation.
```

**输出处理：**
- 解析 JSON，调用 `db.insert_company()` 写入
- 跳过重复域名
- 每次查询间隔 2 秒（避免 rate limit）

---

### 5.4 `pipeline/profile.py` — 公司画像分析

**流程：**

1. 从 DB 取所有 `website_fetched=False` 的公司
2. 用 `requests` + `BeautifulSoup` 抓取官网首页（timeout=10s，User-Agent 伪装浏览器）
3. 提取纯文本内容（去除 script/style 标签），截取前 3000 字符
4. 调用 Gemini API 分析内容，更新公司画像

**Gemini 分析 Prompt：**

```
You are analyzing a company website to assess if they are a good prospect 
for purchasing plasticizers (DOTP, DOP, ATBC, TOTM) from a Chinese supplier.

Company: {company_name}
Country: {country}
Website content:
---
{website_text}
---

Return a JSON object with:
- product_line: what products they make (string)
- import_need: "yes" / "no" / "unknown" — do they likely import plasticizers?
- recommended_product: best plasticizer to pitch (DOTP/DOP/ATBC/TOTM/DOS)
- recommended_reason: 1 sentence why
- eu_export_flag: true/false — do they export to EU or USA?
- score: integer 1-10 (10 = perfect prospect)
  Scoring guide:
  8-10: PVC manufacturer, clear plasticizer need, mid-size company
  5-7:  Possible fit but uncertain product line or scale
  1-4:  Unlikely buyer (trader, wrong industry, too large/small)
- priority: "A" (score 8-10) / "B" (score 6-7) / "C" (score < 6)

Return ONLY valid JSON, no markdown.
```

**错误处理：**
- 官网抓取失败（超时、403、DNS 错误）：`website_fetched=True`，其余字段留空，score 设为 0
- Gemini 解析失败：记录错误日志，跳过该公司

---

### 5.5 `pipeline/contacts.py` — 联系人查找

**使用**: Apollo.io API（主）+ Hunter.io API（邮箱验证）

**流程：**

1. 从 DB 取所有 `score >= MIN_SCORE_TO_PROCEED` 且无联系人的公司
2. 调用 Apollo `/people/search` API，按公司域名搜索

**Apollo API 调用：**

```
POST https://api.apollo.io/v1/mixed_people/search
Headers: x-api-key: {APOLLO_API_KEY}
Body: {
    "q_organization_domains": "{domain}",
    "person_titles": ["purchasing manager", "procurement", "buyer", 
                      "sourcing manager", "supply chain", "import manager"],
    "page": 1,
    "per_page": 3
}
```

取前 3 个联系人结果。

**Hunter.io 邮箱验证：**

对 Apollo 返回的每个邮箱，调用 Hunter.io `/email-verifier` 端点验证。仅保存 `result: "deliverable"` 或 `"risky"` 的邮箱（跳过 `"undeliverable"`）。

**如果 Apollo 无结果：**

调用 Hunter `/domain-search` 查找公司域名下的邮箱，过滤职位关键词（purchasing、procurement、import、sourcing、supply）。

**写入 DB：** 调用 `db.insert_contact()`，记录来源（apollo/hunter）和验证状态。

---

### 5.6 `pipeline/score.py` — 评分与过滤

此模块在 `profile.py` 运行后，提供一个汇总函数，用于打印当前批次的评分分布，并确认哪些公司将进入联系人查找阶段。

**输出示例（CLI）：**

```
=== 本批次评分分布 ===
A 级 (score 8-10): 5 家公司 → 进入联系人查找
B 级 (score 6-7):  8 家公司 → 进入联系人查找
C 级 (score < 6): 12 家公司 → 跳过
共 13 家公司进入下一阶段
```

---

### 5.7 `pipeline/draft_email.py` — 生成开发信草稿

**使用**: Gemini API

**流程：**

1. 从 DB 取所有有联系人但无草稿邮件（`emails` 表无对应记录）的公司
2. 对每个联系人生成一封个性化开发信

**Gemini Prompt：**

```
Write a professional B2B cold outreach email from Tranotra Chemical 
(a China-based plasticizer supplier) to a potential buyer.

Sender context:
- Company: Tranotra Chemical (tranotra.com)
- Products: DOTP (flagship), DOP, ATBC, TOTM, DOS, TBC
- Key pitch: DOTP from Blue Sail Chemical (top China producer), 
             non-phthalate, REACH-compliant
- Sender name: Ai Long

Recipient:
- Name: {contact_name}
- Title: {contact_title}
- Company: {company_name}
- Country: {country}
- Their products: {product_line}
- Recommended product: {recommended_product}
- Reason: {recommended_reason}

Requirements:
- Subject line: specific, not generic
- Length: 120-180 words
- Tone: professional but direct, no fluff
- Mention their specific product line (personalization)
- Highlight the recommended product and ONE key benefit
- End with a clear call-to-action (request a call or ask if they need a quote)
- Do NOT mention Blue Sail Chemical by name
- Do NOT use generic phrases like "I hope this email finds you well"

Return JSON with:
{
  "subject": "...",
  "body": "..."
}
Return ONLY valid JSON, no markdown.
```

**写入 DB：** `db.insert_email()` with `status='pending'`

---

### 5.8 `outreach/review.py` — CLI 审核界面

人工审核所有 `status='pending'` 的草稿邮件。

**交互流程：**

```
============================================================
待审核邮件 [1/8]
============================================================
收件人:  Nguyen Van A <nguyen@example.com.vn>
公司:    ABC Plastics Co., Ltd (Vietnam) | Score: 8 | 优先级: A
产品:    PVC cable compound
推荐:    DOTP

主题: DOTP Supply for Your PVC Cable Compound Production

正文:
Dear Mr. Nguyen,

I noticed that ABC Plastics specializes in PVC cable compounds — 
a segment where DOTP has been rapidly replacing DOP due to stricter 
environmental standards...

[操作] (a)批准发送  (e)编辑  (s)跳过  (r)拒绝  (q)退出
> 
```

**操作说明：**
- `a` — 批准，更新 `status='approved'`
- `e` — 打开编辑模式，允许直接修改 subject 和 body，保存后状态设为 `approved`
- `s` — 跳过（保持 pending，下次继续审核）
- `r` — 拒绝，更新 `status='rejected'`
- `q` — 退出审核

**编辑模式：** 将草稿写入临时文件，调用系统默认编辑器（`$EDITOR`，默认 `nano`），保存后读回。

---

### 5.9 `outreach/send.py` — 邮件发送

**使用**: Aliyun DirectMail API

发送所有 `status='approved'` 的邮件。

**Aliyun DirectMail 调用参数：**

```python
params = {
    "Action": "SingleSendMail",
    "AccountName": ALIYUN_FROM_EMAIL,  # info@mail.tranotra.com
    "AddressType": 1,  # 发信地址类型（1=随机账号）
    "ReplyToAddress": False,
    "ToAddress": contact_email,
    "Subject": email_subject,
    "HtmlBody": email_body_html,  # 将纯文本转为简单 HTML
    "FromAlias": "Ai Long | Tranotra Chemical",
}
```

**鉴权**: 使用 Aliyun SDK (`aliyun-python-sdk-dm`) 或手动签名，读取 `ALIYUN_ACCESS_KEY_ID` 和 `ALIYUN_ACCESS_KEY_SECRET`。

**发送后：** 更新 `emails.status='sent'`，记录 `sent_at` 时间戳。失败时更新 `status='failed'`，记录错误信息到日志。

**发送间隔：** 每封邮件间隔 5 秒，避免触发 spam 检测。

---

### 5.10 `main.py` — 主入口

支持分阶段运行或全流水线运行。

**命令行用法：**

```bash
# 运行完整流水线（发现 → 画像 → 联系人 → 草稿）
python main.py --run all

# 仅运行特定阶段
python main.py --run discover --market Vietnam
python main.py --run profile
python main.py --run contacts
python main.py --run draft

# 审核界面
python main.py --review

# 发送已批准邮件
python main.py --send

# 查看数据库统计
python main.py --stats
```

**`--stats` 输出示例：**

```
=== Tranotra Leads 统计 ===
公司总数:        47
  - 已画像分析:  42
  - 高分(≥6):   21
联系人总数:      18
邮件草稿:        15
  - 待审核:       8
  - 已批准:       4
  - 已发送:       3
  - 已拒绝:       0
```

---

## 6. 错误处理与日志

- 使用 Python 标准库 `logging`，日志写入 `./logs/pipeline.log`
- 每个阶段独立 try/except，单条记录失败不中断批次处理
- 网络请求统一设置 timeout（默认 15s）
- API rate limit 处理：遇到 429 错误，等待 60s 后重试一次

---

## 7. 依赖包

```
# requirements.txt
google-generativeai>=0.8.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
aliyun-python-sdk-dm>=3.0.0
```

Apollo 和 Hunter 通过 REST API 直接调用，无需专用 SDK。

---

## 8. 开发优先级 / 里程碑

| 里程碑 | 包含内容 | 目标 |
|--------|---------|------|
| M1 | `db.py` + `config.py` + `discover.py` + `main.py --stats` | Gemini 能搜出公司名单并存入 DB |
| M2 | `profile.py` | 官网抓取 + 画像分析跑通 |
| M3 | `contacts.py` | Apollo + Hunter 联系人查找跑通 |
| M4 | `draft_email.py` | 开发信草稿生成 |
| M5 | `review.py` + `send.py` | 审核界面 + DirectMail 发送 |

**建议先完成 M1，用 `--stats` 验证数据入库正确后再继续。**

---

## 9. 不在范围内（v1.0）

- Web UI / Dashboard
- 自动跟进邮件（follow-up）
- 邮件回复追踪
- ImportYeti API 集成（可选，预留字段但不实现）
- 多用户支持
- 云端部署

---

## 10. 附录：目标买家画像

| 维度 | 描述 |
|------|------|
| 行业 | PVC 制品制造商（电缆、地板、人造革、医疗管材、食品包装） |
| 规模 | 中小型工厂，月用量 5-50 吨增塑剂 |
| 地区 | 越南 > 泰国 > 印尼 > UAE > 沙特 |
| 当前采购 | 从本地贸易商或中间商采购（价格高，有替换空间） |
| 首单目标 | 5-10 吨 DOTP，100% 预付或 50% 定金 |
| 排除 | 大型跨国企业（已有固定供应商）、纯贸易商、出口欧美但用 DOP 的企业 |

---

*文档结束*
