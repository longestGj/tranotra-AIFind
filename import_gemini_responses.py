#!/usr/bin/env python
"""Import all Gemini API responses from JSON files into the database"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tranotra.infrastructure.database import get_db, init_db
from tranotra.db import insert_company
from tranotra.config import load_config


def extract_country_from_filename(filename: str) -> str:
    """Extract country from filename like '20260404_161913_686_Vietnam_pvc_plastic_manufacturer.json'"""
    # Pattern: _Country_rest.json
    match = re.search(r'_([A-Z][a-z]+)_', filename)
    if match:
        return match.group(1)
    return "Unknown"


def import_gemini_responses():
    """Import all Gemini API response files into database"""

    # Initialize database
    try:
        config = load_config()
        database_url = config.get("DATABASE_URL", "sqlite:///./data/tranotra_leads.db")
        init_db(database_url)
    except Exception as e:
        print(f"WARNING: Could not initialize database: {e}")

    responses_dir = Path("data/gemini_responses")

    if not responses_dir.exists():
        print("ERROR: data/gemini_responses directory not found")
        return

    json_files = sorted(responses_dir.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to import\n")

    total_companies = 0
    imported_companies = 0
    skipped = 0
    errors = 0

    for json_file in json_files:
        country = extract_country_from_filename(json_file.name)

        try:
            # Read and parse the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract JSON from ```json ... ``` blocks (may have text before/after)
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if match:
                content = match.group(1).strip()
            else:
                # Try to find JSON array directly (starts with [ and ends with ])
                match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', content)
                if match:
                    content = match.group(0).strip()

            # Parse JSON
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # Try to clean up common JSON errors
                # Remove trailing commas, fix quotes, etc.
                print(f"WARN: {json_file.name} - Attempting to fix JSON errors")
                raise

            # Handle different response formats
            if isinstance(parsed, dict) and 'companies' in parsed:
                companies = parsed['companies']
            elif isinstance(parsed, list):
                companies = parsed
            else:
                print(f"SKIP: {json_file.name} - Unknown format")
                skipped += 1
                continue

            # Import each company
            for company_data in companies:
                try:
                    # Map API response fields to database fields
                    mapped_data = {
                        "name": company_data.get("Company Name (English)"),
                        "country": country,
                        "city": company_data.get("City/Province"),
                        "year_established": company_data.get("Year Established"),
                        "employees": company_data.get("Employees (approximate)"),
                        "estimated_revenue": company_data.get("Estimated Annual Revenue"),
                        "main_products": company_data.get("Main Products"),
                        "export_markets": company_data.get("Export Markets"),
                        "eu_us_jp_export": str(company_data.get("Export to EU/USA/Japan?", "")).lower() == "yes",
                        "raw_materials": company_data.get("Raw Materials"),
                        "recommended_product": company_data.get("Best Plasticizer for them"),
                        "recommendation_reason": company_data.get("Why that plasticizer"),
                        "website": company_data.get("Company Website"),
                        "contact_email": company_data.get("Contact Email"),
                        "linkedin_url": company_data.get("LinkedIn Company Page URL"),
                        "linkedin_normalized": company_data.get("LinkedIn Company Page URL"),
                        "best_contact_title": company_data.get("Best job title to contact"),
                        "prospect_score": company_data.get("Prospect Score"),
                        "source_query": f"import_from_{json_file.stem}",
                        "priority": "HIGH" if company_data.get("Prospect Score", 0) >= 8 else "MEDIUM" if company_data.get("Prospect Score", 0) >= 5 else "LOW",
                    }

                    # Validate required fields
                    if not mapped_data.get("name"):
                        skipped += 1
                        continue

                    # Insert into database
                    company_id = insert_company(mapped_data)
                    imported_companies += 1
                    total_companies += 1

                except Exception as e:
                    errors += 1
                    print(f"  ERROR: Failed to import company: {e}")
                    continue

            print(f"[{json_file.name}] {len(companies)} companies ({country})")

        except json.JSONDecodeError as e:
            errors += 1
            print(f"ERROR: {json_file.name} - Invalid JSON: {e}")
        except Exception as e:
            errors += 1
            print(f"ERROR: {json_file.name} - {e}")

    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  Total files processed: {len(json_files)}")
    print(f"  Companies imported:    {imported_companies}")
    print(f"  Skipped:               {skipped}")
    print(f"  Errors:                {errors}")
    print(f"{'='*60}")

    # Show database stats
    try:
        db = get_db()
        from tranotra.core.models import Company
        total_db = db.query(Company).count()
        print(f"\nDatabase Statistics:")
        print(f"  Total companies in DB: {total_db}")

        # Count by country
        from sqlalchemy import func
        country_stats = db.query(
            Company.country,
            func.count(Company.id).label('count'),
            func.avg(Company.prospect_score).label('avg_score')
        ).group_by(Company.country).all()

        print(f"\n  By Country:")
        for country, count, avg_score in country_stats:
            print(f"    {country}: {count} companies (avg score: {avg_score:.1f})")

    except Exception as e:
        print(f"Warning: Could not fetch database stats: {e}")


if __name__ == "__main__":
    print("Starting import of Gemini API responses...\n")
    import_gemini_responses()
    print("\nImport completed!")
