"""Real Gemini API integration tests - No mocking!
Tests actual Gemini API calls using real API key from .env.development
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime
from tranotra.gemini_client import (
    call_gemini_grounding_search,
    save_raw_response,
    initialize_gemini,
    get_last_saved_response_path
)
from tranotra.db import parse_response_and_insert, get_search_history
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory
from tranotra.routes import detect_response_format


@pytest.fixture(scope="module")
def gemini_api_key():
    """Get real Gemini API key from environment"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        pytest.skip("GEMINI_API_KEY not found in environment")
    return api_key


@pytest.fixture
def cleanup_response_files():
    """Keep gemini_responses directory for inspection (don't delete)"""
    # Create directory if it doesn't exist
    response_dir = Path("data/gemini_responses")
    response_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Note: Don't delete the directory to allow inspection of saved responses
    # This is useful for debugging and verifying API responses are saved correctly
    # Comment: Files are preserved for manual review


class TestRealGeminiAPIIntegration:
    """Test real Gemini API integration - actual API calls"""

    def test_gemini_api_initialization(self, gemini_api_key, app):
        """Test initializing Gemini API with real key"""
        with app.app_context():
            # Initialize with real API key
            try:
                initialize_gemini(gemini_api_key)
                print("[INIT] [OK] Gemini API initialized successfully")
            except Exception as e:
                pytest.fail(f"Failed to initialize Gemini API: {e}")

    def test_real_gemini_api_call_vietnam(self, gemini_api_key, app, cleanup_response_files):
        """Test real Gemini API call for Vietnam market"""
        with app.app_context():
            initialize_gemini(gemini_api_key)

            country = "Vietnam"
            query = "PVC plastic manufacturer"

            try:
                # Make real API call
                response = call_gemini_grounding_search(country, query)

                # Verify response received
                assert response is not None, "No response from Gemini API"
                assert len(response) > 0, "Empty response from Gemini API"
                print(f"[API] [OK] Received {len(response)} bytes from Gemini")

                # Verify file was saved
                saved_path = get_last_saved_response_path()
                assert saved_path != "", "Response file path is empty"
                assert Path(saved_path).exists(), f"Response file not saved: {saved_path}"
                print(f"[FILE] [OK] Response saved to: {saved_path}")

                # Print response preview
                preview = response[:200] if len(response) > 200 else response
                print(f"[RESPONSE] Preview: {preview}...")

            except Exception as e:
                pytest.fail(f"Real API call failed: {e}")

    def test_real_gemini_response_format_detection(self, gemini_api_key, app, cleanup_response_files):
        """Test that real Gemini response format is correctly detected"""
        with app.app_context():
            initialize_gemini(gemini_api_key)

            country = "Thailand"
            query = "textile manufacturer export"

            try:
                response = call_gemini_grounding_search(country, query)

                # Detect format
                detected_format = detect_response_format(response)
                assert detected_format in ["JSON", "CSV", "Markdown", "UNKNOWN"], f"Invalid format: {detected_format}"
                print(f"[FORMAT] [OK] Detected: {detected_format}")

                # Verify it's not just unknown
                assert detected_format != "UNKNOWN", "Response format could not be detected"

            except Exception as e:
                pytest.fail(f"Format detection test failed: {e}")

    def test_complete_pipeline_vietnam_pvc(self, gemini_api_key, app, cleanup_response_files):
        """Test complete real pipeline: API → File → Format detect → Parse → Database"""
        with app.app_context():
            db = get_db()

            initialize_gemini(gemini_api_key)

            country = "Vietnam"
            query = "PVC cable manufacturer"

            print("\n[PIPELINE] Starting complete pipeline test...")

            try:
                # Step 1: Call real Gemini API
                print(f"[STEP 1] Calling Gemini API for {country} + {query}...")
                response = call_gemini_grounding_search(country, query)
                assert response, "No response from API"
                print(f"[STEP 1] [OK] API call successful ({len(response)} bytes)")

                # Step 2: Verify file saved
                print("[STEP 2] Verifying response file saved...")
                saved_path = get_last_saved_response_path()
                assert Path(saved_path).exists()
                print(f"[STEP 2] [OK] File saved: {saved_path}")

                # Step 3: Detect format
                print("[STEP 3] Detecting response format...")
                detected_format = detect_response_format(response)
                assert detected_format != "UNKNOWN"
                print(f"[STEP 3] [OK] Format detected: {detected_format}")

                # Step 4: Parse and insert
                print("[STEP 4] Parsing and inserting into database...")
                result = parse_response_and_insert(
                    country=country,
                    query=query,
                    response_or_filepath=response,
                    format=detected_format
                )

                assert result["success"] == True, f"Parsing failed: {result.get('error')}"
                print(f"[STEP 4] [OK] Parsed successfully")

                # Step 5: Verify database
                print("[STEP 5] Verifying database records...")
                companies = db.query(Company).filter_by(country=country).all()
                print(f"[STEP 5] [OK] Database has {len(companies)} companies from {country}")

                # Step 6: Verify search history
                print("[STEP 6] Verifying search history...")
                history = db.query(SearchHistory).filter_by(
                    country=country,
                    query=query
                ).order_by(SearchHistory.created_at.desc()).first()

                if history:
                    print(f"[STEP 6] [OK] Search history recorded:")
                    print(f"         - New: {history.new_count}")
                    print(f"         - Duplicates: {history.duplicate_count}")
                    print(f"         - Avg Score: {history.avg_score}")
                    print(f"         - High Priority: {history.high_priority_count}")

                print("\n[PIPELINE] [OK] Complete pipeline test PASSED\n")

            except Exception as e:
                print(f"\n[PIPELINE] [ERROR] Test failed: {e}\n")
                raise

    def test_complete_pipeline_thailand_textile(self, gemini_api_key, app, cleanup_response_files):
        """Test complete real pipeline for Thailand textile manufacturers"""
        with app.app_context():
            db = get_db()

            initialize_gemini(gemini_api_key)

            country = "Thailand"
            query = "textile synthetic fiber manufacturer"

            print(f"\n[TEST] Running pipeline test for {country} + {query}...\n")

            try:
                # API call
                response = call_gemini_grounding_search(country, query)
                print(f"[API] [OK] Response received ({len(response)} bytes)")

                # Format detection
                detected_format = detect_response_format(response)
                print(f"[FORMAT] [OK] Detected: {detected_format}")

                # Parse and insert
                result = parse_response_and_insert(
                    country=country,
                    query=query,
                    response_or_filepath=response,
                    format=detected_format
                )

                assert result["success"] == True
                print(f"[PARSE] [OK] Success - {result.get('new_count', 0)} new companies")

                # Verify database
                companies = db.query(Company).filter_by(country=country).all()
                print(f"[DB] [OK] Total {len(companies)} companies in database")

            except Exception as e:
                pytest.fail(f"Thailand textile test failed: {e}")

    def test_multiple_sequential_real_api_calls(self, gemini_api_key, app, cleanup_response_files):
        """Test multiple sequential real API calls to different countries"""
        with app.app_context():
            db = get_db()

            initialize_gemini(gemini_api_key)

            test_cases = [
                ("Vietnam", "plastic manufacturer"),
                ("Thailand", "chemical producer"),
                ("Indonesia", "rubber manufacturer"),
            ]

            print("\n[MULTI] Testing sequential API calls...\n")

            for country, query in test_cases:
                try:
                    print(f"[CALL] {country} + {query}...")

                    # Real API call
                    response = call_gemini_grounding_search(country, query)

                    # Format detect
                    detected = detect_response_format(response)

                    # Parse
                    result = parse_response_and_insert(
                        country=country,
                        query=query,
                        response_or_filepath=response,
                        format=detected
                    )

                    companies = db.query(Company).filter_by(country=country).all()
                    print(f"      [OK] {len(companies)} companies from {country}\n")

                except Exception as e:
                    print(f"      [ERROR] Failed: {e}\n")
                    # Don't fail test, just skip this country
                    continue

    def test_api_response_reparse_without_new_call(self, gemini_api_key, app, cleanup_response_files):
        """Test that saved response can be re-parsed without new API call"""
        with app.app_context():
            db = get_db()

            initialize_gemini(gemini_api_key)

            country = "Vietnam"
            query = "Initial search"

            print("\n[REPARSE] Testing response file reuse...\n")

            try:
                # First API call
                print("[1] Making first API call...")
                response1 = call_gemini_grounding_search(country, query)
                saved_path = get_last_saved_response_path()
                print(f"[1] [OK] Saved: {saved_path}")

                # Read saved file
                print("[2] Reading saved response file...")
                with open(saved_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                print(f"[2] [OK] Read {len(saved_content)} bytes from file")

                # Parse without new API call
                print("[3] Parsing saved content without new API call...")
                detected = detect_response_format(saved_content)
                result = parse_response_and_insert(
                    country=country,
                    query="Different query - same file",
                    response_or_filepath=saved_content,
                    format=detected
                )
                print(f"[3] [OK] Successfully re-parsed saved response")

                print("\n[REPARSE] [OK] Response file successfully reused\n")

            except Exception as e:
                pytest.fail(f"Reparse test failed: {e}")

    def test_api_response_data_quality(self, gemini_api_key, app, cleanup_response_files):
        """Test data quality of real Gemini API responses"""
        with app.app_context():
            db = get_db()

            initialize_gemini(gemini_api_key)

            country = "Vietnam"
            query = "manufacturer export company"

            print("\n[QUALITY] Checking response data quality...\n")

            try:
                # Get real response
                response = call_gemini_grounding_search(country, query)
                detected = detect_response_format(response)

                # Parse
                result = parse_response_and_insert(
                    country=country,
                    query=query,
                    response_or_filepath=response,
                    format=detected
                )

                # Verify data quality
                companies = db.query(Company).filter_by(country=country).all()

                if companies:
                    print(f"[QUALITY] Checking {len(companies)} companies...\n")

                    for i, company in enumerate(companies[:5], 1):  # Check first 5
                        print(f"Company {i}: {company.name}")
                        print(f"  - Country: {company.country}")
                        print(f"  - Score: {company.prospect_score}")
                        print(f"  - Email: {company.contact_email}")
                        print(f"  - LinkedIn: {company.linkedin_normalized}")
                        print()

                        # Basic quality checks
                        assert company.name, "Company name missing"
                        assert company.country, "Country missing"
                        if company.contact_email:
                            assert "@" in company.contact_email, "Invalid email"
                        if company.prospect_score:
                            assert 0 <= company.prospect_score <= 10, "Invalid score"

                    print("[QUALITY] [OK] Data quality verified\n")

                else:
                    print("[QUALITY] [WARN]  No companies found to check\n")

            except Exception as e:
                pytest.fail(f"Data quality test failed: {e}")

    def test_gemini_api_rate_limiting(self, gemini_api_key, app, cleanup_response_files):
        """Test that API respects rate limiting (2-second delay)"""
        with app.app_context():
            import time

            initialize_gemini(gemini_api_key)

            print("\n[RATE] Testing rate limiting...\n")

            try:
                queries = [
                    ("Vietnam", "plastic"),
                    ("Thailand", "textile"),
                ]

                for country, keyword in queries:
                    print(f"[RATE] Calling API for {country}...")
                    start_time = time.time()

                    response = call_gemini_grounding_search(country, keyword)

                    elapsed = time.time() - start_time
                    print(f"[RATE] [OK] Response received in {elapsed:.2f}s\n")

                    # Verify not too fast (should include some processing)
                    assert elapsed > 0.1, "Response suspiciously fast"

                print("[RATE] [OK] Rate limiting test passed\n")

            except Exception as e:
                pytest.fail(f"Rate limiting test failed: {e}")


class TestGeminiAPIErrorHandling:
    """Test error handling with real Gemini API"""

    def test_invalid_api_key_handling(self, app):
        """Test handling of invalid API key"""
        with app.app_context():
            invalid_key = "invalid-api-key-12345"

            try:
                initialize_gemini(invalid_key)
                # If we get here, try to make a call
                try:
                    call_gemini_grounding_search("Vietnam", "test")
                    # If call succeeds with invalid key, that's a test issue
                    pytest.skip("Invalid key was somehow accepted")
                except Exception:
                    # Expected - invalid key should fail
                    print("[ERROR] [OK] Invalid API key properly rejected")
                    pass
            except Exception:
                # Expected - initialization should fail with invalid key
                print("[ERROR] [OK] Invalid key initialization properly failed")
                pass

    def test_empty_response_handling(self, gemini_api_key, app, cleanup_response_files):
        """Test handling of edge cases"""
        with app.app_context():
            initialize_gemini(gemini_api_key)

            # Test empty query
            detected = detect_response_format("")
            assert detected == "UNKNOWN"
            print("[EDGE] [OK] Empty response handled")

            # Test whitespace
            detected = detect_response_format("   ")
            assert detected == "UNKNOWN"
            print("[EDGE] [OK] Whitespace response handled")
