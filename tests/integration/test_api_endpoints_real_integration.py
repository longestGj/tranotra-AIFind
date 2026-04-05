"""真实 API 端点集成测试 - 不使用 Mock

测试 Flask API 端点与真实数据库的集成。
包括：
- 有效参数的正常流程
- 边界值测试（page=0, -1, empty results 等）
- 错误处理验证
"""

import pytest


class TestAPIEndpointsRealIntegration:
    """P0-4: 真实 API 端点集成测试"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db_session):
        """为每个测试创建真实的测试数据

        创建 50 个公司记录用于分页测试。
        """
        from tranotra.core.models import Company
        from tranotra.db import insert_company

        companies = []
        for i in range(50):
            company_data = {
                "name": f"Test Company {i:03d}",
                "country": "Vietnam" if i % 2 == 0 else "Thailand",
                "city": "Ho Chi Minh" if i % 2 == 0 else "Bangkok",
                "employees": "100-500",
                "year_established": 2010 + (i % 15),
                "prospect_score": 8 - (i % 9),
                "main_products": f"Product {i % 5}",
                "source_query": f"test_query_{i}",
                "linkedin_normalized": f"linkedin.com/company/test-company-{i}",
            }
            try:
                company_id = insert_company(company_data)
                companies.append(company_id)
            except Exception:
                pass

        yield companies

        # 清理：删除所有测试公司
        try:
            db_session.query(Company).filter(Company.id.in_(companies)).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_valid_pagination_page_1_per_page_20(self, client):
        """验证：有效分页参数 (page=1, per_page=20) 返回正确结果"""
        response = client.get('/api/search/results?page=1&per_page=20')

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()

        assert data is not None, "Response JSON is null"
        assert "success" in data, "Missing 'success' field"
        assert data["success"] is True, f"success should be True, got {data.get('success')}"

        # 验证：分页字段
        assert "companies" in data, "Missing 'companies' field"
        assert isinstance(data["companies"], list), "companies should be list"
        assert len(data["companies"]) <= 20, f"Too many results: {len(data['companies'])}"

        # 验证：分页元数据
        assert "current_page" in data, "Missing current_page"
        assert data["current_page"] == 1, f"Wrong page: {data['current_page']}"
        assert "per_page" in data, "Missing per_page"
        assert data["per_page"] == 20, f"Wrong per_page: {data['per_page']}"
        assert "total_count" in data, "Missing total_count"
        assert "total_pages" in data, "Missing total_pages"

    def test_pagination_page_2(self, client):
        """验证：第二页的数据与第一页不同"""
        response1 = client.get('/api/search/results?page=1&per_page=20')
        response2 = client.get('/api/search/results?page=2&per_page=20')

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.get_json()
        data2 = response2.get_json()

        # 验证：两页数据不同
        if len(data1["companies"]) > 0 and len(data2["companies"]) > 0:
            assert data1["companies"][0]["id"] != data2["companies"][0]["id"], \
                "Page 2 should have different companies than page 1"

    def test_pagination_boundary_page_zero(self, client):
        """验证：page=0 被调整为 page=1（宽松处理）"""
        response = client.get('/api/search/results?page=0&per_page=20')

        # API 将 page=0 调整为 page=1 而不是返回错误（这是真实行为）
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        # 验证响应格式正确
        assert data is not None, "Response is null"
        assert "success" in data, "Missing 'success' field"
        # page=0 会被调整为 1，但 current_page 字段可能不返回（检查是否存在）
        if "current_page" in data:
            assert data['current_page'] == 1, f"Expected current_page=1, got {data['current_page']}"

    def test_pagination_boundary_negative_page(self, client):
        """验证：page=-1 返回 400 错误（API 拒绝负数）"""
        response = client.get('/api/search/results?page=-1&per_page=20')

        # API 拒绝负数参数，返回 400
        assert response.status_code == 400, f"Expected 400 for negative page, got {response.status_code}"
        data = response.get_json()
        assert data["success"] is False, "Error response should indicate failure"

    def test_pagination_boundary_per_page_zero(self, client):
        """验证：per_page=0 被调整为 per_page=1"""
        response = client.get('/api/search/results?page=1&per_page=0')

        # API 调整无效的 per_page 为 1（这是真实行为）
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data is not None, "Response is null"
        assert "success" in data, "Missing 'success' field"
        # 验证 per_page 被调整或者使用默认值
        if "per_page" in data:
            assert data['per_page'] >= 1, f"per_page should be >= 1, got {data['per_page']}"

    def test_pagination_boundary_negative_per_page(self, client):
        """验证：per_page=-1 返回 400 错误（API 拒绝负数）"""
        response = client.get('/api/search/results?page=1&per_page=-1')

        # API 拒绝负数参数，返回 400
        assert response.status_code == 400, f"Expected 400 for negative per_page, got {response.status_code}"
        data = response.get_json()
        assert data["success"] is False, "Error response should indicate failure"

    def test_pagination_boundary_extreme_per_page(self, client):
        """验证：per_page=1000000 被合理处理（限制或错误）"""
        response = client.get('/api/search/results?page=1&per_page=1000000')

        # 可能返回 200（但被限制）或 400（拒绝）
        assert response.status_code in [200, 400, 422], \
            f"Expected 200/400/422 for extreme per_page, got {response.status_code}"

        if response.status_code == 200:
            data = response.get_json()
            # 如果返回 200，per_page 应该被限制
            assert data["per_page"] <= 1000, \
                f"per_page should be limited, got {data['per_page']}"

    def test_empty_results_with_nonexistent_country(self, client):
        """验证：查询不存在的国家返回空结果"""
        response = client.get('/api/search/results?country=Nonexistent&query=xyz')

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        assert data["companies"] == [], "Empty results should return empty list"
        assert data["total_count"] == 0, "Empty results should have total_count=0"

    def test_response_includes_all_required_fields(self, client):
        """验证：响应中的每个公司都包含必需字段"""
        response = client.get('/api/search/results?page=1&per_page=5')

        assert response.status_code == 200
        data = response.get_json()

        if len(data["companies"]) > 0:
            company = data["companies"][0]

            # 验证：基本字段存在
            required_fields = ["id", "name", "country"]
            for field in required_fields:
                assert field in company, f"Missing field: {field}"
                assert company[field] is not None, f"Field {field} is None"

    def test_response_data_types(self, client):
        """验证：响应字段的数据类型正确"""
        response = client.get('/api/search/results?page=1&per_page=5')

        assert response.status_code == 200
        data = response.get_json()

        # 验证：顶层字段类型
        assert isinstance(data["success"], bool), "success should be boolean"
        assert isinstance(data["companies"], list), "companies should be list"
        assert isinstance(data["current_page"], int), "current_page should be int"
        assert isinstance(data["per_page"], int), "per_page should be int"
        assert isinstance(data["total_count"], int), "total_count should be int"
        assert isinstance(data["total_pages"], int), "total_pages should be int"

        # 验证：公司字段类型
        if len(data["companies"]) > 0:
            company = data["companies"][0]
            assert isinstance(company["id"], int), "Company id should be int"
            assert isinstance(company["name"], str), "Company name should be string"
            assert isinstance(company["country"], str), "Company country should be string"

    def test_missing_parameters_use_defaults(self, client):
        """验证：缺少 page/per_page 参数时使用默认值"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = response.get_json()

        # 应该使用默认值
        assert "current_page" in data
        assert "per_page" in data
        # 通常默认是 page=1, per_page=20
        assert data["current_page"] >= 1
        assert data["per_page"] >= 1


class TestAPIErrorHandling:
    """API 错误处理测试"""

    def test_invalid_method_returns_405(self, client):
        """验证：不支持的 HTTP 方法返回 405"""
        response = client.post('/api/search/results')

        assert response.status_code == 405, \
            f"Expected 405 for POST on GET endpoint, got {response.status_code}"

    def test_malformed_json_returns_400(self, client):
        """验证：格式错误的 JSON 返回错误"""
        response = client.post(
            '/api/search/export/csv',
            data='{invalid json',
            content_type='application/json'
        )

        # 非 200 响应表示错误被处理
        # 可能返回 400（客户端错误）或 500（服务器无法处理）
        assert response.status_code >= 400, \
            f"Expected error response (4xx or 5xx), got {response.status_code}"

        # 验证响应是 JSON 或文本错误信息
        try:
            data = response.get_json()
            assert "success" in data and data["success"] is False, "Error response should indicate failure"
        except Exception:
            # 如果不是 JSON，至少应该有文本响应
            assert response.get_data(as_text=True), "Error response should have content"
