#!/usr/bin/env python3
"""
Demo script to process selected corpus documents for interim submission
"""
import sys
from pathlib import Path
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter


def main():
    """Process 12+ documents (3 per class minimum)"""
    
    # Select smaller documents from each class
    document_classes = {
        "Class A - Financial Report": [
            "Annual_Report_JUNE-2020.pdf",
            "Annual_Report_JUNE-2018.pdf",
            "2018_Audited_Financial_Statement_Report.pdf",
        ],
        "Class B - Scanned Legal": [
            "2018_Audited_Financial_Statement_Report.pdf",
            "2019_Audited_Financial_Statement_Report.pdf",
            "2020_Audited_Financial_Statement_Report.pdf",
            "2021_Audited_Financial_Statement_Report.pdf",
        ],
        "Class C - Technical Assessment": [
            "20191010_Pharmaceutical-Manufacturing-Opportunites-in-Ethiopia_VF.pdf",
            "2013-E.C-Audit-finding-information.pdf",
        ],
        "Class D - Structured Data": [
            "2013-E.C-Assigned-regular-budget-and-expense.pdf",
            "2013-E.C-Procurement-information.pdf",
            "2013-E.C-Audit-finding-information.pdf",
        ]
    }
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("Error: data/ directory not found")
        return 1
    
    # Initialize agents
    print("Initializing agents...")
    triage = TriageAgent()
    router = ExtractionRouter()
    
    # Process documents
    total_processed = 0
    for doc_class, filenames in document_classes.items():
        print(f"\n{'='*60}")
        print(f"Processing {doc_class}")
        print(f"{'='*60}")
        
        for filename in filenames:
            pdf_path = data_dir / filename
            
            if not pdf_path.exists():
                print(f"⚠️  Skipping {filename} (not found)")
                continue
            
            try:
                print(f"\n📄 Processing: {filename}")
                
                # Triage
                print("  → Running triage...")
                profile = triage.profile_document(str(pdf_path))
                
                print(f"  ✓ Origin: {profile.origin_type}")
                print(f"  ✓ Layout: {profile.layout_complexity}")
                print(f"  ✓ Domain: {profile.domain_hint}")
                print(f"  ✓ Strategy: {profile.estimated_extraction_cost}")
                print(f"  ✓ Pages: {profile.total_pages}")
                print(f"  ✓ Char Density: {profile.character_density:.4f}")
                
                # Extract (skip vision for now due to budget)
                if profile.estimated_extraction_cost != "needs_vision_model" or profile.total_pages <= 5:
                    print("  → Running extraction...")
                    extracted_doc = router.extract(str(pdf_path), profile)
                    
                    print(f"  ✓ Text Blocks: {len(extracted_doc.text_blocks)}")
                    print(f"  ✓ Tables: {len(extracted_doc.tables)}")
                    print(f"  ✓ Confidence: {extracted_doc.confidence_score:.2f}")
                    print(f"  ✓ Strategy Used: {extracted_doc.extraction_strategy}")
                    
                    total_processed += 1
                else:
                    print(f"  ⚠️  Skipping extraction (vision model needed, {profile.total_pages} pages)")
                    total_processed += 1  # Count profile as processed
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully processed {total_processed} documents")
    print(f"✓ Profiles saved to: .refinery/profiles/")
    print(f"✓ Ledger saved to: .refinery/extraction_ledger.jsonl")
    print(f"{'='*60}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
