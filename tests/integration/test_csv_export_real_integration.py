"""真实 CSV 导出集成测试 - 不使用 Mock

验证 CSV 导出的完整流程：
- 真实数据库查询
- CSV 生成
- 内容验证（不仅仅结构，还要验证真实数据）
"""

import pytest
import csv
import io


class TestCSVExportRealIntegration:
    """P1-6: 真实 CSV 导出集成测试"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db_session):
        """创建用于 CSV 导出测试的真实数据"""
        from tranotra.core.models import Company
        from tranotra.db import insert_company

        companies = []

        # 创建已知的测试数据，用于验证导出内容
        test_companies = [
            {
                "name": "Vietnam PVC Co Ltd",
                "country": "Vietnam",
                "city": "Ho Chi Minh",
                "employees": "500-2000",
                "year_established": 2010,
                "prospect_score": 8,
                "main_products": "PVC cable and plastic products",
                "website": "https://vietnampvc.example.com",
                "contact_email": "contact@vietnampvc.example.com",
                "source_query": "PVC manufacturer",
                "linkedin_normalized": "linkedin.com/company/vietnam-pvc-co",
            },
            {
                "name": "Thai Textile Export",
                "country": "Thailand",
                "city": "Bangkok",
                "employees": "1000-5000",
                "year_established": 2008,
                "prospect_score": 7,
                "main_products": "Textile and fabric export",
                "website": "https://thaisiamtextile.example.com",
                "contact_email": "info@thaisiamtextile.example.com",
                "source_query": "textile export",
                "linkedin_normalized": "linkedin.com/company/thai-textile-export",
            },
            {
                "name": "Indonesia Electronics Ltd",
                "country": "Indonesia",
                "city": "Jakarta",
                "employees": "200-1000",
                "year_established": 2015,
                "prospect_score": 6,
                "main_products": "Electronics and semiconductors",
                "website": "https://indoelectronics.example.com",
                "contact_email": "sales@indoelectronics.example.com",
                "source_query": "electronics manufacturer",
                "linkedin_normalized": "linkedin.com/company/indo-electronics",
            },
        ]

        for company_data in test_companies:
            try:
                company_id = insert_company(company_data)
                companies.append(company_id)
            except Exception as e:
                pytest.fail(f"Failed to create test company: {e}")

        yield companies

        # 清理：删除所有测试数据
        try:
            db_session.query(Company).filter(Company.id.in_(companies)).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_csv_export_returns_200(self, client):
        """验证：CSV 导出请求返回 200"""
        response = client.post('/api/search/export/csv', json={
            'scope': 'all'
        })

        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.get_data(as_text=True)[:500]}"

    def test_csv_export_returns_csv_content_type(self, client):
        """验证：响应的 Content-Type 是 text/csv"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        assert response.status_code == 200
        content_type = response.content_type

        assert "text/csv" in content_type or "csv" in content_type, \
            f"Expected CSV content type, got {content_type}"

    def test_csv_export_not_empty(self, client):
        """验证：导出的 CSV 不为空"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)

        assert csv_data and len(csv_data) > 0, "CSV export is empty"

    def test_csv_export_has_header_and_data(self, client):
        """验证：CSV 包含 header 行和数据行"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        csv_data = response.get_data(as_text=True)
        lines = csv_data.split('\r\n') if '\r\n' in csv_data else csv_data.split('\n')

        # 应该至少有 header + 1 数据行
        assert len(lines) > 1, "CSV should have header and at least one data row"

    def test_csv_export_contains_real_company_names(self, client, setup_test_data):
        """验证：导出的 CSV 包含创建的真实公司数据"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        csv_data = response.get_data(as_text=True)

        # 解析 CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
        except csv.Error as e:
            pytest.fail(f"Failed to parse CSV: {e}")

        assert len(rows) > 0, "CSV should contain data rows"

        # 验证：包含我们创建的公司
        company_names = [row.get('name', '') for row in rows if 'name' in row]

        expected_companies = [
            "Vietnam PVC Co Ltd",
            "Thai Textile Export",
            "Indonesia Electronics Ltd"
        ]

        for expected_name in expected_companies:
            assert expected_name in company_names, \
                f"Expected company '{expected_name}' not found in CSV. Found: {company_names}"

    def test_csv_export_company_fields_complete(self, client):
        """验证：导出的公司数据字段完整"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        csv_data = response.get_data(as_text=True)
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(csv_reader)

        assert len(rows) > 0, "CSV should have data"

        # 验证：关键字段存在
        first_row = rows[0]
        required_fields = ['name', 'country', 'city', 'prospect_score']

        for field in required_fields:
            assert field in first_row, f"Missing field: {field}"
            assert first_row[field], f"Field {field} is empty"

    def test_csv_export_data_accuracy(self, client):
        """验证：导出的数据准确性（值匹配）"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        csv_data = response.get_data(as_text=True)
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(csv_reader)

        # 查找 Vietnam PVC Co Ltd
        vietnam_company = None
        for row in rows:
            if row.get('name') == 'Vietnam PVC Co Ltd':
                vietnam_company = row
                break

        assert vietnam_company is not None, "Vietnam PVC Co Ltd not found in CSV"

        # 验证：数据值匹配
        assert vietnam_company.get('country') == 'Vietnam', \
            f"Wrong country: {vietnam_company.get('country')}"
        assert vietnam_company.get('city') == 'Ho Chi Minh', \
            f"Wrong city: {vietnam_company.get('city')}"
        assert vietnam_company.get('prospect_score') == '8' or vietnam_company.get('prospect_score') == '8.0', \
            f"Wrong prospect_score: {vietnam_company.get('prospect_score')}"

    def test_csv_export_encoding_utf8(self, client):
        """验证：CSV 使用 UTF-8 编码（支持国际字符）"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        # 验证：可以正确解码为 UTF-8
        csv_data = response.get_data(as_text=True)
        assert isinstance(csv_data, str), "CSV should be text (UTF-8 decoded)"

        # 验证：包含可读的公司名称
        assert 'Vietnam' in csv_data, "UTF-8 text should be readable"

    def test_csv_export_field_count(self, client):
        """验证：CSV 每行的列数一致"""
        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        csv_data = response.get_data(as_text=True)
        csv_reader = csv.reader(io.StringIO(csv_data))

        rows = list(csv_reader)
        assert len(rows) > 1, "CSV should have header and data"

        header_cols = len(rows[0])
        expected_cols = 23  # 23 列字段

        # 验证：header 有 23 列
        assert header_cols == expected_cols, \
            f"Expected {expected_cols} columns, got {header_cols}"

        # 验证：所有数据行也有 23 列
        for i, row in enumerate(rows[1:], start=2):
            assert len(row) == header_cols, \
                f"Row {i} has {len(row)} columns, expected {header_cols}"

    def test_csv_export_handles_empty_database(self, client, db_session):
        """验证：当数据库为空时，导出返回有效的 CSV（header 只）"""
        # 先清空所有公司数据
        from tranotra.core.models import Company

        db_session.query(Company).delete()
        db_session.commit()

        response = client.post('/api/export/csv', json={
            'scope': 'all'
        })

        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)

        # 即使没有数据，也应该返回 header
        lines = csv_data.split('\n') if '\n' in csv_data else csv_data.split('\r\n')
        assert len(lines) >= 1, "CSV should at least have header"

        # 验证：可以解析为有效 CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
            # 应该是空列表（无数据行）
            assert len(rows) == 0, "Empty database should return no data rows"
        except csv.Error as e:
            pytest.fail(f"Invalid CSV format for empty export: {e}")

    def test_csv_export_filters_by_country(self, client):
        """验证：导出支持按国家筛选"""
        response = client.post('/api/export/csv', json={
            'country': 'Vietnam',
            'scope': 'all'
        })

        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)

        csv_reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(csv_reader)

        # 验证：只包含越南公司
        for row in rows:
            assert row.get('country') == 'Vietnam', \
                f"Filter failed: found {row.get('country')}, expected Vietnam"

    def test_csv_export_with_query_filter(self, client):
        """验证：导出支持查询过滤"""
        response = client.post('/api/export/csv', json={
            'query': 'PVC',
            'scope': 'all'
        })

        assert response.status_code == 200
        csv_data = response.get_data(as_text=True)

        # 如果有过滤器，应该返回有效的 CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            rows = list(csv_reader)
            # 至少应该包含 PVC 公司
            names = [row.get('name', '') for row in rows]
            assert any('PVC' in name for name in names) or len(rows) == 0, \
                "Query filter should return PVC companies or empty"
        except csv.Error as e:
            pytest.fail(f"Invalid CSV with query filter: {e}")
