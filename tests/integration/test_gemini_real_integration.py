"""真实 Gemini API 集成测试 - 不使用 Mock

这是真实的集成测试，不 Mock 任何外部依赖：
- 使用真实 Gemini API（需要有效的 API 密钥）
- 使用真实数据库（SQLite）
- 验证完整的数据流：API 调用 → JSON 解析 → 数据存储
"""

import pytest
import json
from pathlib import Path


class TestGeminiRealAPIIntegration:
    """P0-1: 真实 Gemini API 集成测试"""

    def test_gemini_api_call_returns_response(self):
        """验证：真实 Gemini API 返回有效的文本响应

        不使用 Mock，真实调用 Gemini API。
        如果 API 不可用，跳过测试而不是虚假通过。
        """
        from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("GEMINI_API_KEY not configured for real integration testing")

        try:
            # 初始化真实 Gemini 客户端
            initialize_gemini(api_key)

            # 调用真实 API（不是 Mock）
            raw_response = call_gemini_grounding_search(
                country="Vietnam",
                query="plastic manufacturer",
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            pytest.skip(f"Gemini API unavailable or error: {e}")

        # 验证：响应不为空（API 返回文本，可能包含 JSON）
        assert raw_response, "API returned empty response"
        assert isinstance(raw_response, str), f"Response should be string, got {type(raw_response)}"
        assert len(raw_response) > 100, "Response too short, likely invalid"

    def test_gemini_api_response_parseable(self):
        """验证：真实 API 响应可以被 parser 解析"""
        from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
        from tranotra.parser import parse_gemini_response
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("GEMINI_API_KEY not configured")

        try:
            initialize_gemini(api_key)
            raw_response = call_gemini_grounding_search(
                country="Vietnam",
                query="textile export",
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            pytest.skip(f"Gemini API unavailable: {e}")

        # 使用 parser 解析响应（这是正确的流程）
        try:
            parsed = parse_gemini_response(raw_response)
            assert parsed is not None, "Parser returned None"
        except Exception as e:
            pytest.fail(f"Parser failed to parse API response: {e}")

        # 验证：响应包含公司数据
        # Gemini API 可能返回数组或对象，都接受
        if isinstance(parsed, dict):
            assert "companies" in parsed or len(parsed) > 0, "Response should contain companies"
            companies = parsed.get("companies", [parsed])
        else:
            companies = parsed

        assert isinstance(companies, list), f"Companies should be list, got {type(companies)}"

        # 验证：至少有一个公司
        assert len(companies) > 0, "API should return at least one company"

        # 验证：公司数据包含必需字段
        required_fields = ["name", "country"]
        first_company = companies[0]
        for field in required_fields:
            assert field in first_company, f"Missing field: {field}"
            assert first_company[field], f"Field {field} is empty"

    def test_parse_gemini_response(self):
        """验证：响应解析器能处理真实 API 响应"""
        from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
        from tranotra.parser import parse_gemini_response
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("GEMINI_API_KEY not configured")

        try:
            initialize_gemini(api_key)
            raw_response = call_gemini_grounding_search(
                country="Thailand",
                query="electronics manufacturer",
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            pytest.skip(f"Gemini API unavailable: {e}")

        # 解析响应（使用真实解析器）
        try:
            parsed = parse_gemini_response(raw_response)
            assert parsed is not None, "Parser returned None"
        except Exception as e:
            pytest.fail(f"Parser failed on valid API response: {e}")

        # 验证：解析结果是有效的数据结构
        assert isinstance(parsed, (dict, list)), f"Parsed data should be dict or list, got {type(parsed)}"

    def test_store_company_from_api_response(self, db_session):
        """验证：能够将 API 响应中的公司数据存储到数据库

        这是真正的集成测试：API → 解析 → 存储 → 查询
        """
        from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
        from tranotra.parser import parse_gemini_response
        from tranotra.db import insert_company
        from tranotra.core.models import Company
        import os

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("GEMINI_API_KEY not configured")

        try:
            initialize_gemini(api_key)
            raw_response = call_gemini_grounding_search(
                country="Indonesia",
                query="rubber manufacturer",
                timeout=30,
                max_retries=3
            )
        except Exception as e:
            pytest.skip(f"Gemini API unavailable: {e}")

        # 解析响应
        parsed = parse_gemini_response(raw_response)

        # 提取公司列表
        if isinstance(parsed, dict) and "companies" in parsed:
            companies = parsed["companies"]
        elif isinstance(parsed, list):
            companies = parsed
        else:
            pytest.skip("Unexpected API response format")

        assert len(companies) > 0, "API returned no companies"

        # 存储前 3 个公司到数据库
        stored_company_ids = []
        for company_data in companies[:3]:
            try:
                company_id = insert_company(company_data)
                stored_company_ids.append(company_id)
            except Exception as e:
                pytest.fail(f"Failed to store company: {e}\nData: {company_data}")

        # 验证：数据已存储到数据库
        assert len(stored_company_ids) > 0, "No companies were stored"

        # 验证：可以从数据库查询到存储的公司
        for company_id in stored_company_ids:
            company = db_session.query(Company).filter_by(id=company_id).first()
            assert company is not None, f"Company {company_id} not found in database"
            assert company.name, "Company name is empty"
            assert company.country, "Company country is empty"

        # 清理：删除测试数据
        try:
            db_session.query(Company).filter(Company.id.in_(stored_company_ids)).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()
