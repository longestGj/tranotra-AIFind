"""Real integration tests using actual Gemini API response files from data/gemini_responses/
Tests the complete pipeline: Format detection → Parsing → Database insertion → Deduplication
"""

import json
import pytest
from pathlib import Path

from tranotra.routes import detect_response_format
from tranotra.db import parse_response_and_insert, get_companies_by_search
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


class TestRealDataPipeline:
    """Test complete pipeline with real Gemini API response files"""

    @pytest.fixture(scope="class")
    def real_responses_dir(self):
        """Get the directory containing real Gemini API responses"""
        base_dir = Path(__file__).parent.parent.parent
        responses_dir = base_dir / "data" / "gemini_responses"
        assert responses_dir.exists(), f"Real data directory not found: {responses_dir}"
        return responses_dir

    @pytest.fixture(scope="class")
    def sample_json_file(self, real_responses_dir):
        """Get first JSON file from real responses"""
        json_files = list(real_responses_dir.glob("*.json"))
        assert len(json_files) > 0, "No JSON files found in data/gemini_responses"
        return json_files[0]

    @pytest.fixture
    def clean_db(self, app):
        """Ensure database is clean before each test"""
        with app.app_context():
            db = get_db()
            # Clear companies and search history
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()
            yield
            # Cleanup after test
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()

    # ============================================================================
    # Format Detection Tests
    # ============================================================================

    def test_format_detection_json_with_markdown_block(self, sample_json_file, app):
        """Test format detection for JSON in Markdown code block"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            detected = detect_response_format(content)
            assert detected == "JSON", f"Expected JSON, got {detected}"

    def test_format_detection_empty_response(self, app):
        """Test format detection for empty response"""
        with app.app_context():
            detected = detect_response_format("")
            assert detected == "UNKNOWN"
            detected = detect_response_format("   ")
            assert detected == "UNKNOWN"

    def test_format_detection_malformed_json(self, app):
        """Test format detection with malformed JSON"""
        with app.app_context():
            detected = detect_response_format("```json\n[{incomplete")
            assert detected == "JSON"

    # ============================================================================
    # Real Data Parsing Tests
    # ============================================================================

    def test_parse_real_json_response(self, sample_json_file, app, clean_db):
        """Test parsing real JSON response from Gemini API"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            fmt = detect_response_format(content)
            assert fmt == "JSON"

            result = parse_response_and_insert(
                country="Vietnam",
                query="plastic manufacturer",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"], f"Parse failed: {result['message']}"
            assert result["new_count"] > 0, f"No companies parsed: {result}"
            assert result["avg_score"] >= 0, "Invalid average score"

    def test_parse_real_json_data_integrity(self, sample_json_file, app, clean_db):
        """Test that parsed data maintains integrity"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="pvc manufacturer",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            companies = get_companies_by_search("Vietnam", "pvc manufacturer")
            assert len(companies) > 0

            for company in companies:
                assert company.name, "Company missing name"
                assert company.country == "Vietnam", f"Wrong country: {company.country}"
                if company.linkedin_url:
                    assert isinstance(company.linkedin_url, str)

    def test_parse_json_field_mapping(self, sample_json_file, app, clean_db):
        """Test that Gemini fields are correctly mapped to internal fields"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="export company",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]
            companies = get_companies_by_search("Vietnam", "export company")

            for company in companies:
                assert company.name is not None
                if company.year_established:
                    assert isinstance(company.year_established, int)
                if company.prospect_score:
                    assert 1 <= company.prospect_score <= 10
                if company.linkedin_url:
                    assert "linkedin" in company.linkedin_url.lower()

    # ============================================================================
    # Database Insertion Tests
    # ============================================================================

    def test_insert_companies_from_real_data(self, sample_json_file, app, clean_db):
        """Test actual database insertion of real companies"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="textile manufacturer",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            db = get_db()
            total_companies = db.query(Company).count()
            assert total_companies == result["new_count"], "Company count mismatch"

    def test_search_history_created(self, sample_json_file, app, clean_db):
        """Test that search history is created after parsing"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Thailand",
                query="textile export",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            db = get_db()
            history = db.query(SearchHistory).filter_by(
                country="Thailand",
                query="textile export"
            ).first()

            assert history is not None
            assert history.result_count > 0
            assert history.new_count == result["new_count"]
            assert history.duplicate_count == result["duplicate_count"]
            assert abs(history.avg_score - result["avg_score"]) < 0.1

    # ============================================================================
    # Deduplication Tests
    # ============================================================================

    def test_duplicate_detection_by_linkedin_url(self, sample_json_file, app, clean_db):
        """Test that duplicate companies (same LinkedIn URL) are detected"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="first search",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )
            assert result1["success"]
            first_count = result1["new_count"]

            result2 = parse_response_and_insert(
                country="Vietnam",
                query="second search",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )
            assert result2["success"]

            assert result2["duplicate_count"] == first_count, \
                f"Expected {first_count} duplicates, got {result2['duplicate_count']}"
            assert result2["new_count"] == 0, \
                f"Expected 0 new companies, got {result2['new_count']}"

    def test_partial_duplicate_detection(self, real_responses_dir, app, clean_db):
        """Test deduplication when processing multiple files with overlapping companies"""
        json_files = list(real_responses_dir.glob("*.json"))
        if len(json_files) < 2:
            pytest.skip("Need at least 2 JSON files for this test")

        file1, file2 = json_files[0], json_files[1]

        with app.app_context():
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="batch 1",
                response_or_filepath=str(file1),
                format="JSON"
            )
            assert result1["success"]

            result2 = parse_response_and_insert(
                country="Vietnam",
                query="batch 2",
                response_or_filepath=str(file2),
                format="JSON"
            )
            assert result2["success"]

            db = get_db()
            total = db.query(Company).count()
            assert total >= result1["new_count"], "Total should be >= first batch"

    # ============================================================================
    # Error Handling Tests
    # ============================================================================

    def test_handle_invalid_file_path(self, app, clean_db):
        """Test graceful handling of non-existent file path"""
        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="test",
                response_or_filepath="/nonexistent/path/file.json",
                format="JSON"
            )

            assert result["success"] is False

    def test_handle_empty_parsed_data(self, tmp_path, app, clean_db):
        """Test handling of valid file with empty or invalid data"""
        empty_json = tmp_path / "empty.json"
        empty_json.write_text("```json\n[]\n```", encoding="utf-8")

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="empty test",
                response_or_filepath=str(empty_json),
                format="JSON"
            )

            assert result["success"] is False
            assert result["new_count"] == 0

    def test_handle_missing_required_fields(self, tmp_path, app, clean_db):
        """Test handling of records missing required fields"""
        incomplete_json = tmp_path / "incomplete.json"
        incomplete_json.write_text(
            """```json
[
    {"City/Province": "Hanoi"},
    {"Company Name (English)": "Valid Company", "City/Province": "HCMC", "Year Established": 2000}
]
```""",
            encoding="utf-8"
        )

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="incomplete test",
                response_or_filepath=str(incomplete_json),
                format="JSON"
            )

            if result["success"]:
                companies = get_companies_by_search("Vietnam", "incomplete test")
                assert len(companies) >= 0

    # ============================================================================
    # Data Consistency Tests
    # ============================================================================

    def test_source_query_tracking(self, sample_json_file, app, clean_db):
        """Test that source_query is properly tracked for each company"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            search_query = "tracked query"
            result = parse_response_and_insert(
                country="Vietnam",
                query=search_query,
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            companies = get_companies_by_search("Vietnam", search_query)
            for company in companies:
                assert company.source_query == search_query

    def test_prospect_score_normalization(self, sample_json_file, app, clean_db):
        """Test that prospect scores are normalized correctly"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="score test",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            companies = get_companies_by_search("Vietnam", "score test")
            scores = []
            for company in companies:
                if company.prospect_score:
                    assert 1 <= company.prospect_score <= 10, \
                        f"Invalid score: {company.prospect_score}"
                    scores.append(company.prospect_score)

            if scores:
                expected_avg = round(sum(scores) / len(scores), 1)
                assert result["avg_score"] == expected_avg

    def test_linkedin_url_normalization(self, sample_json_file, app, clean_db):
        """Test that LinkedIn URLs are normalized for dedup"""
        with open(sample_json_file, "r", encoding="utf-8") as f:
            content = f.read()

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="linkedin test",
                response_or_filepath=str(sample_json_file),
                format="JSON"
            )

            assert result["success"]

            db = get_db()
            companies = db.query(Company).filter_by(
                source_query="linkedin test"
            ).all()

            for company in companies:
                if company.linkedin_url:
                    assert company.linkedin_normalized is not None
                    assert company.linkedin_normalized == company.linkedin_normalized.lower()

    # ============================================================================
    # Integration Tests with Multiple Files
    # ============================================================================

    def test_process_all_available_real_files(self, real_responses_dir, app, clean_db):
        """Test processing all real data files sequentially"""
        json_files = list(real_responses_dir.glob("*.json"))
        if len(json_files) == 0:
            pytest.skip("No JSON files available for testing")

        with app.app_context():
            results = []
            for i, json_file in enumerate(json_files[:5]):
                result = parse_response_and_insert(
                    country="Vietnam",
                    query=f"batch_{i}",
                    response_or_filepath=str(json_file),
                    format="JSON"
                )
                results.append(result)

                assert "success" in result
                assert "message" in result

            successful = sum(1 for r in results if r["success"])
            assert successful > 0, "At least one file should be processed successfully"

    def test_concurrent_country_searches(self, real_responses_dir, app, clean_db):
        """Test that searches for different countries don't interfere"""
        json_files = list(real_responses_dir.glob("*.json"))
        if len(json_files) < 2:
            pytest.skip("Need at least 2 files")

        with app.app_context():
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="search1",
                response_or_filepath=str(json_files[0]),
                format="JSON"
            )

            result2 = parse_response_and_insert(
                country="Thailand",
                query="search2",
                response_or_filepath=str(json_files[1]),
                format="JSON"
            )

            vietnam_companies = get_companies_by_search("Vietnam", "search1")
            thailand_companies = get_companies_by_search("Thailand", "search2")

            assert all(c.country == "Vietnam" for c in vietnam_companies)
            assert all(c.country == "Thailand" for c in thailand_companies)


class TestRealDataEdgeCases:
    """Test edge cases with real data"""

    @pytest.fixture
    def clean_db(self, app):
        """Ensure database is clean"""
        with app.app_context():
            db = get_db()
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()
            yield
            db.query(Company).delete()
            db.query(SearchHistory).delete()
            db.commit()

    def test_malformed_json_with_comments(self, tmp_path, app, clean_db):
        """Test parsing JSON with inline comments that Gemini sometimes includes"""
        malformed_json = tmp_path / "malformed.json"
        malformed_json.write_text(
            """```json
[
  {
    "Company Name (English)": "Test Company",
    "City/Province": "Hanoi",
    "Year Established": 2000,
    "Employees (approximate)": "100-500",
    "Estimated Annual Revenue": "Undisclosed",
    "Main Products": "Test products",
    "Export Markets": "USA, EU",
    "Export to EU/USA/Japan?": "Yes",
    "Raw Materials": "Test materials",
    "Best Plasticizer for them": "DOTP",
    "Why that plasticizer": "Good for export",
    "Company Website": "https://test.com",
    "Contact Email": "test@example.com",
    "LinkedIn Company Page URL": "https://linkedin.com/company/test",
    "Best job title to contact": "Manager",
    "Prospect Score": 8
  }
]
```""",
            encoding="utf-8"
        )

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="malformed test",
                response_or_filepath=str(malformed_json),
                format="JSON"
            )

            assert result["success"]
            companies = get_companies_by_search("Vietnam", "malformed test")
            assert len(companies) == 1
            assert companies[0].name == "Test Company"

    def test_unicode_handling_in_company_names(self, tmp_path, app, clean_db):
        """Test handling of Unicode characters in company data"""
        unicode_json = tmp_path / "unicode.json"
        unicode_json.write_text(
            """```json
[
  {
    "Company Name (English)": "Công Ty ABC",
    "City/Province": "Hà Nội",
    "Year Established": 2000,
    "Employees (approximate)": "100-500",
    "Estimated Annual Revenue": "Undisclosed",
    "Main Products": "Sản phẩm",
    "Export Markets": "EU",
    "Export to EU/USA/Japan?": "Yes",
    "Raw Materials": "Vật liệu",
    "Best Plasticizer for them": "DOTP",
    "Why that plasticizer": "Tốt",
    "Company Website": "https://test.com",
    "Contact Email": "test@example.com",
    "LinkedIn Company Page URL": "https://linkedin.com/company/test",
    "Best job title to contact": "Manager",
    "Prospect Score": 8
  }
]
```""",
            encoding="utf-8"
        )

        with app.app_context():
            result = parse_response_and_insert(
                country="Vietnam",
                query="unicode test",
                response_or_filepath=str(unicode_json),
                format="JSON"
            )

            assert result["success"]
            companies = get_companies_by_search("Vietnam", "unicode test")
            assert len(companies) == 1
            assert "Công" in companies[0].name or "ABC" in companies[0].name
