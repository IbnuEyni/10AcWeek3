#!/usr/bin/env python3
"""
Demo: Test Current Implementation
Shows all outputs from Stages 1-2 that we've built
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter


def main():
    # Test file - use a smaller one
    pdf_path = "data/2013-E.C-Assigned-regular-budget-and-expense.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        print("\nAvailable files in data/:")
        for f in Path("data").glob("*.pdf"):
            print(f"  - {f}")
        return
    
    print("=" * 70)
    print("🧪 TESTING DOCUMENT INTELLIGENCE REFINERY")
    print("=" * 70)
    print(f"\n📄 Processing: {pdf_path}\n")
    
    # ========================================
    # STAGE 1: DOCUMENT TRIAGE
    # ========================================
    print("=" * 70)
    print("STAGE 1: DOCUMENT TRIAGE")
    print("=" * 70)
    
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    print("\n✅ Document Profile Generated:")
    print(f"  • Document ID: {profile.doc_id}")
    print(f"  • Origin Type: {profile.origin_type}")
    print(f"  • Layout Complexity: {profile.layout_complexity}")
    print(f"  • Domain Hint: {profile.domain_hint}")
    print(f"  • Total Pages: {profile.total_pages}")
    print(f"  • Estimated Cost: {profile.estimated_extraction_cost}")
    
    # Check profile artifact
    profile_path = Path(f".refinery/profiles/{profile.doc_id}.json")
    if profile_path.exists():
        print(f"\n📁 Profile saved to: {profile_path}")
        print(f"   Size: {profile_path.stat().st_size} bytes")
    
    # ========================================
    # STAGE 2: STRUCTURE EXTRACTION
    # ========================================
    print("\n" + "=" * 70)
    print("STAGE 2: STRUCTURE EXTRACTION")
    print("=" * 70)
    
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    
    print("\n✅ Extraction Complete:")
    print(f"  • Strategy Used: {extracted_doc.extraction_strategy}")
    print(f"  • Confidence Score: {extracted_doc.confidence_score:.2f}")
    print(f"  • Text Blocks: {len(extracted_doc.text_blocks)}")
    print(f"  • Tables: {len(extracted_doc.tables)}")
    print(f"  • Figures: {len(extracted_doc.figures)}")
    
    # ========================================
    # TEXT BLOCKS SAMPLE
    # ========================================
    if extracted_doc.text_blocks:
        print("\n" + "-" * 70)
        print("📝 TEXT BLOCKS (First 3):")
        print("-" * 70)
        for i, block in enumerate(extracted_doc.text_blocks[:3]):
            preview = block.content[:100].replace('\n', ' ')
            print(f"\n  Block {i+1}:")
            print(f"    Page: {block.bbox.page}")
            print(f"    Position: ({block.bbox.x0:.0f}, {block.bbox.y0:.0f})")
            print(f"    Content: {preview}...")
    
    # ========================================
    # TABLES SAMPLE
    # ========================================
    if extracted_doc.tables:
        print("\n" + "-" * 70)
        print("📊 TABLES (First 2):")
        print("-" * 70)
        for i, table in enumerate(extracted_doc.tables[:2]):
            print(f"\n  Table {i+1} ({table.table_id}):")
            print(f"    Page: {table.bbox.page}")
            print(f"    Headers: {table.headers}")
            print(f"    Rows: {len(table.rows)}")
            if table.rows:
                print(f"    First Row: {table.rows[0]}")
    
    # ========================================
    # FIGURES SAMPLE
    # ========================================
    if extracted_doc.figures:
        print("\n" + "-" * 70)
        print("🖼️  FIGURES:")
        print("-" * 70)
        for i, figure in enumerate(extracted_doc.figures):
            print(f"\n  Figure {i+1} ({figure.figure_id}):")
            print(f"    Page: {figure.page}")
            print(f"    Caption: {figure.caption or 'No caption'}")
            if figure.image_path:
                img_path = Path(figure.image_path)
                if img_path.exists():
                    print(f"    Saved to: {figure.image_path}")
                    print(f"    File size: {img_path.stat().st_size} bytes")
            if figure.metadata:
                print(f"    Metadata: {figure.metadata}")
    
    # ========================================
    # ARTIFACTS GENERATED
    # ========================================
    print("\n" + "=" * 70)
    print("📁 ARTIFACTS GENERATED")
    print("=" * 70)
    
    # Check extraction ledger
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    if ledger_path.exists():
        print(f"\n✅ Extraction Ledger: {ledger_path}")
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            print(f"   Total entries: {len(lines)}")
            if lines:
                last_entry = json.loads(lines[-1])
                print(f"   Last entry:")
                print(f"     - Strategy: {last_entry.get('strategy_used')}")
                print(f"     - Confidence: {last_entry.get('confidence_score')}")
                print(f"     - Cost: ${last_entry.get('cost_estimate'):.4f}")
                print(f"     - Time: {last_entry.get('processing_time_ms'):.0f}ms")
    
    # Check figures directory
    figures_dir = Path(".refinery/figures")
    if figures_dir.exists():
        figure_files = list(figures_dir.glob("*"))
        print(f"\n✅ Figures Directory: {figures_dir}")
        print(f"   Total images: {len(figure_files)}")
        if figure_files:
            print(f"   Files:")
            for fig_file in figure_files[:5]:  # Show first 5
                print(f"     - {fig_file.name} ({fig_file.stat().st_size} bytes)")
            if len(figure_files) > 5:
                print(f"     ... and {len(figure_files) - 5} more")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"""
✅ Stage 1 Complete: Document profiled and classified
✅ Stage 2 Complete: Content extracted with structure preserved

📈 Extraction Results:
  • {len(extracted_doc.text_blocks)} text blocks extracted
  • {len(extracted_doc.tables)} tables extracted
  • {len(extracted_doc.figures)} figures extracted
  • Confidence: {extracted_doc.confidence_score:.2f}

📁 Artifacts Created:
  • Document profile: .refinery/profiles/{profile.doc_id}.json
  • Extraction ledger: .refinery/extraction_ledger.jsonl
  • Figures: .refinery/figures/ ({len(list(figures_dir.glob('*'))) if figures_dir.exists() else 0} images)

🎯 What You Can Do Now:
  1. View document profile in .refinery/profiles/
  2. Check extracted figures in .refinery/figures/
  3. Review extraction log in .refinery/extraction_ledger.jsonl
  4. Access structured data via extracted_doc object

⏳ Next Steps (Not Yet Implemented):
  • Stage 3: Semantic Chunking (break into RAG-ready chunks)
  • Stage 4: PageIndex Builder (create navigation tree)
  • Stage 5: Query Interface (answer questions with proof)
""")
    
    print("=" * 70)
    print("✨ Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
