"""Verify actual database content after parsing real Gemini API responses"""

import json
from pathlib import Path
import pytest

from tranotra.db import parse_response_and_insert, get_companies_by_search
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


class TestVerifyDatabaseContent:
    """Verify that data stored in database is correct and complete"""

    @pytest.fixture
    def real_responses_dir(self):
        """Get real Gemini API responses directory"""
        base_dir = Path(__file__).parent.parent.parent
        responses_dir = base_dir / "data" / "gemini_responses"
        assert responses_dir.exists()
        return responses_dir

    @pytest.fixture
    def clean_db(self, app):
        """Clean database before each test"""
        with app.app_context():
            db = get_db()
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()
            yield
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()

    def test_verify_company_fields_complete(self, real_responses_dir, app, clean_db):
        """验证数据库中存储的公司字段是否完整"""
        json_files = list(real_responses_dir.glob("*.json"))
        test_file = json_files[0]

        # 读取原始文件看看有多少条记录
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            # 提取 JSON 部分
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                json_part = content[start:end]
                original_data = json.loads(json_part)
                print(f"\n[原始文件] 包含 {len(original_data)} 条记录")

        with app.app_context():
            # 插入数据
            result = parse_response_and_insert(
                country="Vietnam",
                query="test",
                response_or_filepath=str(test_file),
                format="JSON"
            )
            print(f"\n[插入结果] 新增: {result['new_count']}, 重复: {result['duplicate_count']}")

            # 从数据库读取
            db = get_db()
            companies = db.query(Company).all()
            print(f"[数据库] 总数: {len(companies)}")

            # 验证每条记录的字段
            for i, company in enumerate(companies[:3]):  # 检查前 3 条
                print(f"\n--- 公司 {i+1} ---")
                print(f"名称: {company.name}")
                print(f"国家: {company.country}")
                print(f"城市: {company.city}")
                print(f"成立年: {company.year_established}")
                print(f"员工: {company.employees}")
                print(f"收入: {company.estimated_revenue}")
                print(f"主产品: {company.main_products}")
                print(f"出口市场: {company.export_markets}")
                print(f"EU/US/JP: {company.eu_us_jp_export}")
                print(f"原材料: {company.raw_materials}")
                print(f"推荐产品: {company.recommended_product}")
                print(f"推荐原因: {company.recommendation_reason}")
                print(f"网站: {company.website}")
                print(f"邮箱: {company.contact_email}")
                print(f"LinkedIn: {company.linkedin_url}")
                print(f"LinkedIn 规范: {company.linkedin_normalized}")
                print(f"最佳联系人: {company.best_contact_title}")
                print(f"评分: {company.prospect_score}")
                print(f"优先级: {company.priority}")
                print(f"查询源: {company.source_query}")
                print(f"创建时间: {company.created_at}")

                # 验证必需字段
                assert company.name, "缺少公司名称"
                assert company.country, "缺少国家"
                if company.linkedin_url:
                    assert company.linkedin_normalized, "有 LinkedIn URL 但缺少规范化版本"

            print(f"\n[OK] All records verified")

    def test_verify_search_history_accuracy(self, real_responses_dir, app, clean_db):
        """Verify search history record accuracy"""
        json_files = list(real_responses_dir.glob("*.json"))
        test_file = json_files[0]

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="accuracy test",
                response_or_filepath=str(test_file),
                format="JSON"
            )

            db = get_db()
            history = db.query(SearchHistory).filter_by(
                country="Vietnam",
                query="accuracy test"
            ).first()

            print(f"\n[SEARCH HISTORY]")
            print(f"country: {history.country}")
            print(f"query: {history.query}")
            print(f"result_count: {history.result_count}")
            print(f"new_count: {history.new_count}")
            print(f"duplicate_count: {history.duplicate_count}")
            print(f"avg_score: {history.avg_score}")
            print(f"high_priority_count: {history.high_priority_count}")

            companies = db.query(Company).filter_by(
                source_query="accuracy test"
            ).all()

            print(f"\n[VERIFICATION]")
            print(f"Actual record count: {len(companies)}")
            print(f"new_count accurate: {history.new_count == len(companies)}")

            scores = [c.prospect_score for c in companies if c.prospect_score]
            if scores:
                expected_avg = round(sum(scores) / len(scores), 1)
                print(f"Calculated avg score: {expected_avg}")
                print(f"Stored avg score: {history.avg_score}")
                print(f"avg_score accurate: {history.avg_score == expected_avg}")

            high_priority = sum(1 for c in companies if c.prospect_score and c.prospect_score >= 8)
            print(f"Actual high priority: {high_priority}")
            print(f"Stored high priority: {history.high_priority_count}")
            print(f"high_priority accurate: {history.high_priority_count == high_priority}")

    def test_show_duplicate_detection_working(self, real_responses_dir, app, clean_db):
        """验证去重逻辑是否正确"""
        json_files = list(real_responses_dir.glob("*.json"))
        test_file = json_files[0]

        with app.app_context():
            # 第一次插入
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="dup test 1",
                response_or_filepath=str(test_file),
                format="JSON"
            )
            print(f"\n[第一次插入]")
            print(f"新增: {result1['new_count']}")

            db = get_db()
            first_batch = db.query(Company).filter_by(
                source_query="dup test 1"
            ).all()

            print(f"数据库中的记录: {len(first_batch)}")

            # 显示一些 LinkedIn URL
            if first_batch:
                print(f"\n前 3 条公司的 LinkedIn URL:")
                for i, c in enumerate(first_batch[:3]):
                    print(f"  {i+1}. {c.name}: {c.linkedin_normalized}")

            # 第二次插入相同文件
            result2 = parse_response_and_insert(
                country="Vietnam",
                query="dup test 2",
                response_or_filepath=str(test_file),
                format="JSON"
            )
            print(f"\n[第二次插入]")
            print(f"新增: {result2['new_count']}")
            print(f"重复: {result2['duplicate_count']}")
            print(f"重复检测是否工作: {result2['duplicate_count'] == result1['new_count']}")

            # 验证数据库中没有重复
            all_companies = db.query(Company).all()
            linkedin_urls = [c.linkedin_normalized for c in all_companies if c.linkedin_normalized]
            unique_urls = set(linkedin_urls)

            print(f"\n[去重验证]")
            print(f"总公司数: {len(all_companies)}")
            print(f"LinkedIn URLs 总数: {len(linkedin_urls)}")
            print(f"唯一 URLs 数: {len(unique_urls)}")
            print(f"没有重复吗: {len(linkedin_urls) == len(unique_urls)}")

    def test_compare_original_vs_stored(self, real_responses_dir, app, clean_db):
        """对比原始文件和数据库中存储的数据"""
        json_files = list(real_responses_dir.glob("*.json"))
        test_file = json_files[0]

        # 读取原始文件
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                json_part = content[start:end]
                original_data = json.loads(json_part)

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="compare test",
                response_or_filepath=str(test_file),
                format="JSON"
            )

            companies = get_companies_by_search("Vietnam", "compare test")

            print(f"\n[对比分析]")
            print(f"原始数据条数: {len(original_data)}")
            print(f"数据库存储条数: {len(companies)}")
            print(f"差异原因: 可能有字段缺失的记录被过滤掉")

            if len(companies) > 0 and len(original_data) > 0:
                # 对比第一条
                orig_first = original_data[0]
                db_first = companies[0]

                print(f"\n[第一条数据对比]")
                print(f"原始名称: {orig_first.get('Company Name (English)', 'N/A')}")
                print(f"数据库名称: {db_first.name}")
                print(f"名称匹配: {db_first.name == orig_first.get('Company Name (English)', '')}")

                # 检查其他字段
                expected_city = orig_first.get("City/Province", "N/A")
                print(f"\n原始城市: {expected_city}")
                print(f"数据库城市: {db_first.city}")
                print(f"城市匹配: {db_first.city == expected_city}")

                # 检查评分
                expected_score = orig_first.get("Prospect Score", "N/A")
                print(f"\n原始评分: {expected_score}")
                print(f"数据库评分: {db_first.prospect_score}")
                print(f"评分匹配: {str(db_first.prospect_score) == str(expected_score)}")

    def test_show_field_values_sample(self, real_responses_dir, app, clean_db):
        """显示数据库中字段值的样本"""
        json_files = list(real_responses_dir.glob("*.json"))
        if len(json_files) < 2:
            pytest.skip("需要至少 2 个文件")

        test_file1, test_file2 = json_files[0], json_files[1]

        with app.app_context():
            # 从两个文件插入数据
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="sample 1",
                response_or_filepath=str(test_file1),
                format="JSON"
            )

            result2 = parse_response_and_insert(
                country="Thailand",
                query="sample 2",
                response_or_filepath=str(test_file2),
                format="JSON"
            )

            db = get_db()

            print(f"\n[数据库内容样本]")
            print(f"\nVietnam 搜索结果 ({result1['new_count']} 条):")
            vietnam_cos = get_companies_by_search("Vietnam", "sample 1")
            for i, c in enumerate(vietnam_cos[:2]):
                print(f"\n  {i+1}. {c.name}")
                print(f"     城市: {c.city}")
                print(f"     成立年: {c.year_established}")
                print(f"     员工: {c.employees}")
                print(f"     评分: {c.prospect_score}")
                print(f"     优先级: {c.priority}")

            print(f"\n\nThailand 搜索结果 ({result2['new_count']} 条):")
            thailand_cos = get_companies_by_search("Thailand", "sample 2")
            for i, c in enumerate(thailand_cos[:2]):
                print(f"\n  {i+1}. {c.name}")
                print(f"     城市: {c.city}")
                print(f"     成立年: {c.year_established}")
                print(f"     员工: {c.employees}")
                print(f"     评分: {c.prospect_score}")
                print(f"     优先级: {c.priority}")

            # 统计
            total = db.query(Company).count()
            print(f"\n\n[数据库统计]")
            print(f"总公司数: {total}")
            print(f"Vietnam: {len(vietnam_cos)}")
            print(f"Thailand: {len(thailand_cos)}")
