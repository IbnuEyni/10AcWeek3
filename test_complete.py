#!/usr/bin/env python3
"""
Complete Test: Process PDF with Images
Shows all outputs from the Document Intelligence Refinery
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter


def main():
    # Choose a PDF with images
    pdf_path = "data/2013-E.C-Assigned-regular-budget-and-expense.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        print("\nAvailable PDFs:")
        for f in Path("data").glob("*.pdf"):
            print(f"  - {f}")
        return
    
    print("=" * 80)
    print("🧪 COMPLETE TEST: DOCUMENT INTELLIGENCE REFINERY")
    print("=" * 80)
    print(f"\n📄 Processing: {pdf_path}\n")
    
    # ========================================
    # STAGE 1: TRIAGE
    # ========================================
    print("=" * 80)
    print("STAGE 1: DOCUMENT TRIAGE")
    print("=" * 80)
    
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    print(f"\n✅ Document Profile:")
    print(f"   Document ID: {profile.doc_id}")
    print(f"   Origin: {profile.origin_type}")
    print(f"   Layout: {profile.layout_complexity}")
    print(f"   Domain: {profile.domain_hint}")
    print(f"   Pages: {profile.total_pages}")
    print(f"   Strategy: {profile.estimated_extraction_cost}")
    
    # ========================================
    # STAGE 2: EXTRACTION
    # ========================================
    print("\n" + "=" * 80)
    print("STAGE 2: STRUCTURE EXTRACTION")
    print("=" * 80)
    
    router = ExtractionRouter()
    extracted = router.extract(pdf_path, profile)
    
    print(f"\n✅ Extraction Complete:")
    print(f"   Strategy: {extracted.extraction_strategy}")
    print(f"   Confidence: {extracted.confidence_score:.2f}")
    print(f"   Text Blocks: {len(extracted.text_blocks)}")
    print(f"   Tables: {len(extracted.tables)}")
    print(f"   Figures: {len(extracted.figures)}")
    
    # ========================================
    # OUTPUT 1: TEXT BLOCKS
    # ========================================
    if extracted.text_blocks:
        print("\n" + "=" * 80)
        print("📝 TEXT BLOCKS (First 3)")
        print("=" * 80)
        for i, block in enumerate(extracted.text_blocks[:3]):
            preview = block.content[:80].replace('\n', ' ')
            print(f"\n  Block {i+1}:")
            print(f"    Page: {block.bbox.page}")
            print(f"    Location: ({block.bbox.x0:.0f}, {block.bbox.y0:.0f})")
            print(f"    Content: {preview}...")
    
    # ========================================
    # OUTPUT 2: TABLES
    # ========================================
    if extracted.tables:
        print("\n" + "=" * 80)
        print("📊 TABLES")
        print("=" * 80)
        for i, table in enumerate(extracted.tables):
            print(f"\n  Table {i+1} ({table.table_id}):")
            print(f"    Page: {table.bbox.page}")
            print(f"    Headers: {table.headers}")
            print(f"    Rows: {len(table.rows)}")
            if table.rows:
                print(f"    Sample Row: {table.rows[0]}")
    
    # ========================================
    # OUTPUT 3: FIGURES/IMAGES
    # ========================================
    if extracted.figures:
        print("\n" + "=" * 80)
        print("🖼️  FIGURES/IMAGES")
        print("=" * 80)
        for i, figure in enumerate(extracted.figures):
            print(f"\n  Figure {i+1} ({figure.figure_id}):")
            print(f"    Page: {figure.page}")
            print(f"    Caption: {figure.caption or 'No caption'}")
            if figure.image_path:
                img_path = Path(figure.image_path)
                if img_path.exists():
                    print(f"    Saved: {figure.image_path}")
                    print(f"    Size: {img_path.stat().st_size:,} bytes")
            if figure.metadata:
                print(f"    Dimensions: {figure.metadata.get('width')}x{figure.metadata.get('height')}")
                print(f"    Format: {figure.metadata.get('format')}")
    
    # ========================================
    # OUTPUT 4: DOCUMENT PROFILE (JSON)
    # ========================================
    print("\n" + "=" * 80)
    print("📁 OUTPUT 1: DOCUMENT PROFILE")
    print("=" * 80)
    
    profile_path = Path(f".refinery/profiles/{profile.doc_id}.json")
    if profile_path.exists():
        print(f"\n✅ Saved: {profile_path}")
        with open(profile_path) as f:
            profile_data = json.load(f)
        print(f"\nContent:")
        print(json.dumps(profile_data, indent=2))
    
    # ========================================
    # OUTPUT 5: EXTRACTION LEDGER
    # ========================================
    print("\n" + "=" * 80)
    print("📁 OUTPUT 2: EXTRACTION LEDGER")
    print("=" * 80)
    
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    if ledger_path.exists():
        print(f"\n✅ Saved: {ledger_path}")
        with open(ledger_path) as f:
            lines = f.readlines()
            last_entry = json.loads(lines[-1])
        print(f"\nLast Entry:")
        print(json.dumps(last_entry, indent=2))
    
    # ========================================
    # OUTPUT 6: EXTRACTED FIGURES
    # ========================================
    print("\n" + "=" * 80)
    print("📁 OUTPUT 3: EXTRACTED FIGURES")
    print("=" * 80)
    
    figures_dir = Path(f".refinery/figures/{profile.doc_id}")
    if figures_dir.exists():
        figure_files = list(figures_dir.glob("*"))
        print(f"\n✅ Directory: {figures_dir}")
        print(f"   Total images: {len(figure_files)}")
        if figure_files:
            print(f"\n   Files:")
            for fig_file in figure_files:
                print(f"     - {fig_file.name} ({fig_file.stat().st_size:,} bytes)")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 80)
    print("📊 COMPLETE SUMMARY")
    print("=" * 80)
    
    print(f"""
✅ STAGE 1: Document Triage
   • Classified as: {profile.origin_type}
   • Layout: {profile.layout_complexity}
   • Domain: {profile.domain_hint}
   • Recommended strategy: {profile.estimated_extraction_cost}

✅ STAGE 2: Structure Extraction
   • Strategy used: {extracted.extraction_strategy}
   • Confidence: {extracted.confidence_score:.2f}
   • Text blocks: {len(extracted.text_blocks)}
   • Tables: {len(extracted.tables)}
   • Figures: {len(extracted.figures)}

📁 ARTIFACTS CREATED:
   1. Document Profile: .refinery/profiles/{profile.doc_id}.json
   2. Extraction Ledger: .refinery/extraction_ledger.jsonl
   3. Figures: .refinery/figures/{profile.doc_id}/ ({len(list(figures_dir.glob('*'))) if figures_dir.exists() else 0} images)

🎯 WHAT YOU CAN DO NOW:
   • View profile: cat .refinery/profiles/{profile.doc_id}.json
   • View ledger: tail -1 .refinery/extraction_ledger.jsonl
   • View figures: ls -lh .refinery/figures/{profile.doc_id}/
   • Access data programmatically via extracted object

⏳ NEXT STEPS (Not Yet Implemented):
   • Stage 3: Semantic Chunking (break into RAG-ready chunks)
   • Stage 4: PageIndex Builder (create navigation tree)
   • Stage 5: Query Interface (answer questions with proof)
""")
    
    print("=" * 80)
    print("✨ Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
