---
title: "Integration Test Refactoring Plan"
created_date: "2026-04-05"
status: "ACTION_PLAN"
priority: "CRITICAL"
---

# 集成测试重构方案

## 🎯 核心洞察

**当前状态：** 集成测试写得像单元测试（充满 Mock）  
**问题：** Mock 掉了所有外部依赖 → 等于没有测试集成  
**结果：** 代码改变后，这些测试可能仍然通过，但实际功能已破裂  

**正确的集成测试应该：**
- ✅ 使用**真实数据库**（测试 SQLite）
- ✅ 使用**真实 Gemini API**（或测试环境的 API 端点）
- ✅ 验证**端到端数据流**（API 调用 → 解析 → 存储 → 查询）
- ✅ **不使用 Mock**（Mock 属于单元测试）

---

## 🚨 P0 问题重新评估

### **移除不相关的批评**

❌ **不需要修复：**
1. 多线程并发测试（项目不需要）
2. 线程安全的列表操作（不是问题）
3. 100+ 并发测试（scale 超出范围）

✅ **需要修复的真实 P0 问题：**

| # | 问题 | 当前状态 | 修复方法 |
|---|------|--------|---------|
| 1 | **所有测试都用 Mock** | ❌ 严重 | 移除 @patch，使用真实 API 和数据库 |
| 2 | **分页参数无边界检查** | ❌ 严重 | 添加 `page=0, -1, 999999` 等边界测试 |
| 3 | **CSV 导出无内容验证** | ❌ 严重 | 验证实际导出数据，不仅仅结构 |
| 4 | **数据库状态污染** | ❌ 严重 | 使用事务隔离或清理每个测试的数据 |
| 5 | **响应结构验证过浅** | ⚠️ 中等 | 添加必需字段检查和类型验证 |

---

## 📋 真实集成测试设计

### **改造策略**

```
当前（错误）:
test_epic_1_2_integration.py
├── @patch Gemini API
├── @patch Flask client
├── @patch database
└── 结果: 单元测试，不是集成测试 ❌

正确的应该是:
tests/integration/
├── conftest.py (真实数据库 fixture)
├── test_gemini_api_integration.py (真实 API，真实数据库)
├── test_api_endpoints_integration.py (真实 Flask，真实数据库)
└── test_csv_export_integration.py (完整流程验证) ✅
```

---

## 🔧 修复计划（按优先级）

### **Phase 1: 设置真实集成测试环境 (1 小时)**

#### 1.1 创建测试专用配置

文件: `tests/integration/conftest.py`

```python
import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture(scope='session')
def test_db_path():
    """专用于测试的数据库文件"""
    temp_dir = tempfile.gettempdir()
    db_path = Path(temp_dir) / "test_tranotra.db"
    yield str(db_path)
    # 测试完成后清理
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope='function')
def test_db_session(test_db_path):
    """为每个测试创建独立的数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(f"sqlite:///{test_db_path}")
    
    # 创建所有表
    from tranotra.core.models import Base
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # 清理：回滚并关闭
    session.rollback()
    session.close()

@pytest.fixture(scope='function')
def test_app(test_db_session):
    """为每个测试创建独立的 Flask 应用实例"""
    from tranotra.main import create_app
    
    app = create_app(config='testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{test_db_session.get_bind().url.database}"
    
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def test_gemini_api_key():
    """从环境变量读取真实（或测试）API 密钥"""
    key = os.getenv('GEMINI_API_KEY_TEST', os.getenv('GEMINI_API_KEY'))
    if not key:
        pytest.skip("GEMINI_API_KEY not configured for integration testing")
    return key
```

#### 1.2 配置环境变量

文件: `.env.test.local` (添加到 .gitignore)

```bash
FLASK_ENV=testing
FLASK_PORT=5000
FLASK_HOST=localhost
DATABASE_URL=sqlite:///test_tranotra.db
GEMINI_API_KEY_TEST=sk_test_your_api_key_here  # 测试环境密钥
LOG_LEVEL=DEBUG
```

---

### **Phase 2: 重写 P0 集成测试 (2 小时)**

移除所有 @patch，改为真实操作。

#### 2.1 测试真实 API 调用 + 数据库存储

文件: `tests/integration/test_gemini_api_integration.py` (新文件)

```python
"""真实 Gemini API 集成测试 - 不使用 Mock"""

import pytest
import json
from pathlib import Path

class TestGeminiAPIRealIntegration:
    """P0-1: 真实 Gemini API 调用和数据存储"""
    
    def test_p0_1_gemini_api_call_and_store(self, test_gemini_api_key, test_db_session):
        """验证：调用真实 Gemini API → 解析 → 存储到数据库"""
        # 使用真实 API（不是 Mock）
        from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
        from tranotra.parser import parse_gemini_response
        from tranotra.db import insert_company
        
        # 初始化真实 Gemini 客户端
        initialize_gemini(test_gemini_api_key)
        
        # 调用真实 API（可能失败，但会真实地失败）
        try:
            raw_response = call_gemini_grounding_search(
                country="Vietnam",
                query="PVC manufacturer",
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            pytest.skip(f"Gemini API unavailable: {e}")
        
        # 验证：响应是有效 JSON
        assert raw_response, "API returned empty response"
        parsed = parse_gemini_response(raw_response)
        assert parsed is not None, "Failed to parse response"
        assert isinstance(parsed, (dict, list)), f"Unexpected type: {type(parsed)}"
        
        # 提取公司列表
        if isinstance(parsed, dict) and 'companies' in parsed:
            companies = parsed['companies']
        else:
            companies = parsed if isinstance(parsed, list) else []
        
        # 验证：至少返回 1 个公司
        assert len(companies) > 0, "API returned no companies"
        
        # 验证：每个公司都有必需字段
        required_fields = ['name', 'country']
        for company_data in companies:
            for field in required_fields:
                assert field in company_data, f"Missing field: {field}"
        
        # 存储到数据库（真实存储）
        stored_ids = []
        for company_data in companies[:5]:  # 只存前 5 个以避免超时
            try:
                company_id = insert_company(company_data, test_db_session)
                stored_ids.append(company_id)
            except Exception as e:
                pytest.fail(f"Failed to store company: {e}")
        
        # 验证：数据已存储到数据库
        assert len(stored_ids) > 0, "No companies were stored"
        
        from tranotra.core.models import Company
        company = test_db_session.query(Company).filter_by(id=stored_ids[0]).first()
        assert company is not None, "Company not found in database"
        assert company.country == "Vietnam", f"Wrong country: {company.country}"
```

#### 2.2 测试 API 端点分页

文件: `tests/integration/test_api_endpoints_integration.py`

```python
"""真实 API 端点集成测试"""

import pytest

class TestAPIEndpointsRealIntegration:
    """P0-4: 真实 API 分页"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_db_session):
        """为每个测试创建真实数据"""
        from tranotra.core.models import Company
        
        companies = [
            Company(name=f"Company {i}", country="Vietnam", city=f"City {i}", employees="100-500")
            for i in range(50)
        ]
        test_db_session.add_all(companies)
        test_db_session.commit()
        yield
        # 清理：自动回滚
    
    def test_p0_4_pagination_valid_params(self, test_app, test_db_session):
        """验证：有效的分页参数返回正确结果"""
        response = test_app.get('/api/search/results?page=1&per_page=20')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data is not None, "Response JSON is null"
        assert 'success' in data, "Missing 'success' field"
        assert data['success'] is True
        assert 'companies' in data
        assert len(data['companies']) <= 20
        assert data['current_page'] == 1
        assert data['per_page'] == 20
    
    def test_p0_4_pagination_boundary_page_zero(self, test_app):
        """验证：page=0 返回 400 错误"""
        response = test_app.get('/api/search/results?page=0&per_page=20')
        
        # 应该拒绝无效参数
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
    
    def test_p0_4_pagination_boundary_negative_page(self, test_app):
        """验证：page=-1 返回 400 错误"""
        response = test_app.get('/api/search/results?page=-1&per_page=20')
        
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
    
    def test_p0_4_pagination_boundary_per_page_zero(self, test_app):
        """验证：per_page=0 返回 400 错误"""
        response = test_app.get('/api/search/results?page=1&per_page=0')
        
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
    
    def test_p0_4_pagination_boundary_extreme_per_page(self, test_app):
        """验证：per_page=1000000 被限制"""
        response = test_app.get('/api/search/results?page=1&per_page=1000000')
        
        # 应该被限制或返回错误
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.get_json()
            # 如果返回 200，per_page 应该被限制
            assert data['per_page'] <= 1000, f"per_page not limited: {data['per_page']}"
```

#### 2.3 测试 CSV 导出内容

文件: `tests/integration/test_csv_export_integration.py`

```python
"""真实 CSV 导出集成测试"""

import pytest
import csv
import io

class TestCSVExportRealIntegration:
    """P1-6: 真实 CSV 导出验证"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_db_session):
        """创建测试数据"""
        from tranotra.core.models import Company
        
        companies = [
            Company(
                name="Vietnam PVC Co",
                country="Vietnam",
                city="Ho Chi Minh",
                employees="500-2000",
                prospect_score=8,
                main_products="PVC cable",
                website="https://example.com"
            ),
            Company(
                name="Thai Textile Ltd",
                country="Thailand",
                city="Bangkok",
                employees="1000-5000",
                prospect_score=7,
                main_products="Textile export",
                website="https://example2.com"
            )
        ]
        test_db_session.add_all(companies)
        test_db_session.commit()
        yield
    
    def test_p1_6_csv_export_has_real_data(self, test_app, test_db_session):
        """验证：CSV 导出包含真实的公司数据"""
        response = test_app.post('/api/export/csv', json={
            'country': 'Vietnam',
            'query': 'PVC',
            'scope': 'all'
        })
        
        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)
        
        # 解析 CSV
        lines = csv_data.split('\r\n')
        assert len(lines) > 1, "CSV should have header + data rows"
        
        # 读取 CSV 内容
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(csv_reader)
        
        # 验证：至少有 1 行数据
        assert len(rows) > 0, "CSV should contain company data"
        
        # 验证：包含预期的公司
        company_names = [row.get('name') for row in rows]
        assert "Vietnam PVC Co" in company_names, "Expected company not in CSV"
        
        # 验证：数据完整性
        first_company = rows[0]
        assert first_company.get('name'), "Company name is empty"
        assert first_company.get('country') == "Vietnam", "Wrong country"
        assert first_company.get('prospect_score') == "8", "Wrong prospect score"
    
    def test_p1_6_csv_export_structure_and_encoding(self, test_app):
        """验证：CSV 结构正确和编码"""
        response = test_app.post('/api/export/csv', json={'scope': 'all'})
        
        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)
        
        # 验证：不为空
        assert csv_data and len(csv_data) > 0, "CSV is empty"
        
        # 验证：可以正确解析为 CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
            assert len(rows) >= 0, "CSV parsing failed"
        except csv.Error as e:
            pytest.fail(f"Invalid CSV format: {e}")
        
        # 验证：UTF-8 编码正确
        assert isinstance(csv_data, str), "CSV should be text, not bytes"
```

---

### **Phase 3: 移除错误的 Mock 测试 (1 小时)**

#### 3.1 识别需要移除/改写的测试

```python
# 这些应该改为真实集成测试或删除（因为重复）：

❌ 删除或改写：
- test_p0_1_gemini_api_successful_call (只用 Mock)
- test_p0_2_gemini_api_timeout_and_retry (只测 Mock 的重试)
- test_p0_3_data_parsing_and_sqlite_storage (用 Mock 的 insert_company)
- test_p0_4_results_api_pagination (可以保留，但移除 Mock)
- test_p1_1_empty_results_handling (可以保留)
- test_p1_3_large_dataset_pagination (移除 Mock)
- test_p1_4_concurrent_searches (不需要，项目无并发)
- test_p1_6_large_csv_export_performance (改为真实 CSV)
- test_p1_7_request_timeout_shows_retry (只用 Mock)
- test_p1_8_api_response_envelope_format (可以保留)

✅ 保留：
- test_p1_2_missing_api_key_error (验证错误处理)
- test_api_key_not_logged_in_plain_text (安全验证)
```

#### 3.2 新的测试文件结构

```
tests/
├── unit/
│   ├── test_config.py ✅ (已有，单元测试，使用 Mock)
│   ├── test_gemini_client.py ✅ (已有，单元测试，使用 Mock)
│   └── ... 其他单元测试
│
├── integration/
│   ├── conftest.py ✅ (新建，真实数据库 fixture)
│   ├── test_gemini_api_integration.py ✅ (新建，真实 API + DB)
│   ├── test_api_endpoints_integration.py ✅ (新建，真实 Flask + DB)
│   ├── test_csv_export_integration.py ✅ (新建，真实导出)
│   └── test_epic_1_2_integration.py ⚠️ (改写或删除)
│
└── e2e/
    └── test_epic_1_2_e2e.py (Selenium，用户交互)
```

---

## 📊 修复后的测试策略

| 层级 | 目的 | 使用 Mock | 覆盖范围 | 执行时间 |
|------|------|---------|---------|---------|
| **单元测试** | 单个函数逻辑 | ✅ 是 | 函数级别 | 快（ms） |
| **集成测试** | 模块/子系统协作 | ❌ 否 | API+DB+Parser | 中等（s） |
| **E2E 测试** | 用户端到端流程 | ❌ 否 | UI+API+DB | 慢（min） |

---

## 🚀 执行步骤

### **第 1 步：设置真实测试环境（30 分钟）**
```bash
# 1. 创建测试配置
cp .env.example .env.test.local
# 编辑 .env.test.local，添加 GEMINI_API_KEY_TEST

# 2. 创建 conftest.py
# 实现真实数据库 fixture

# 3. 验证环境
pytest tests/integration/ --collect-only
```

### **第 2 步：编写真实集成测试（1 小时）**
```bash
# 4. 创建新的集成测试文件
touch tests/integration/test_gemini_api_integration.py
touch tests/integration/test_api_endpoints_integration.py
touch tests/integration/test_csv_export_integration.py

# 5. 实现真实测试（不使用 @patch）
pytest tests/integration/test_gemini_api_integration.py -v
```

### **第 3 步：验证和清理（30 分钟）**
```bash
# 6. 运行所有集成测试
pytest tests/integration/ -v

# 7. 删除或改写旧的 Mock 测试
rm tests/integration/test_epic_1_2_integration.py
# 或改写为真实测试

# 8. 最终验证
pytest tests/unit/ tests/integration/ tests/e2e/ -v
```

---

## ✅ 完成标准

集成测试重构完成时：

- [ ] 所有集成测试**不使用 @patch**
- [ ] 使用**真实数据库**（SQLite）
- [ ] 使用**真实 Gemini API**（或测试环境密钥）
- [ ] 验证**完整数据流**（API → 解析 → DB → 查询）
- [ ] 测试**边界情况**（page=0, -1, empty results 等）
- [ ] **CSV 导出验证内容**，不仅仅结构
- [ ] **数据库隔离**（每个测试独立）
- [ ] **错误处理**（无 API 密钥、网络错误等）

---

## 📋 检查清单

集成测试通过时：

- [ ] `pytest tests/integration/ -v` 所有通过
- [ ] 覆盖所有 P0/P1 场景
- [ ] 无虚假阳性（Mock 隐蔽的问题）
- [ ] 无虚假阴性（真实 API 返回意外格式）
- [ ] 可以在没有 Mock 的情况下验证整个流程

---

**预计工作量:** 3-4 小时  
**难度:** 中等  
**收益:** 真实的集成测试 vs 虚假的单元测试
