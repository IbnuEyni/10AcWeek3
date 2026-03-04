#!/usr/bin/env python3
"""
Simple Demo: Show What We've Built
Tests with a simple digital PDF to demonstrate all features
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter


def main():
    print("=" * 70)
    print("🎯 DOCUMENT INTELLIGENCE REFINERY - DEMO")
    print("=" * 70)
    print("\nThis demo shows what we've implemented so far (Stages 1-2)")
    print()
    
    # Use test PDF
    pdf_path = "tests/data/test.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Creating test PDF...")
        Path("tests/data").mkdir(parents=True, exist_ok=True)
        # Create minimal PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "Test Document - Financial Report")
        c.drawString(100, 700, "Q1 2024 Results")
        c.drawString(100, 650, "Revenue: $1.2M")
        c.drawString(100, 600, "Profit: $200K")
        c.save()
        print(f"✅ Created: {pdf_path}\n")
    
    # STAGE 1: TRIAGE
    print("=" * 70)
    print("STAGE 1: DOCUMENT TRIAGE")
    print("=" * 70)
    
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    print(f"\n✅ Document Classified:")
    print(f"   Document ID: {profile.doc_id}")
    print(f"   Origin: {profile.origin_type}")
    print(f"   Layout: {profile.layout_complexity}")
    print(f"   Domain: {profile.domain_hint}")
    print(f"   Pages: {profile.total_pages}")
    print(f"   Strategy: {profile.estimated_extraction_cost}")
    
    # Check artifacts
    profile_file = Path(f".refinery/profiles/{profile.doc_id}.json")
    if profile_file.exists():
        print(f"\n📁 Saved: {profile_file}")
    
    # STAGE 2: EXTRACTION
    print("\n" + "=" * 70)
    print("STAGE 2: STRUCTURE EXTRACTION")
    print("=" * 70)
    
    router = ExtractionRouter()
    extracted = router.extract(pdf_path, profile)
    
    print(f"\n✅ Extraction Complete:")
    print(f"   Strategy: {extracted.extraction_strategy}")
    print(f"   Confidence: {extracted.confidence_score:.2f}")
    print(f"   Text Blocks: {len(extracted.text_blocks)}")
    print(f"   Tables: {len(extracted.tables)}")
    print(f"   Figures: {len(extracted.figures)}")
    
    # Show text blocks
    if extracted.text_blocks:
        print(f"\n📝 Text Blocks:")
        for i, block in enumerate(extracted.text_blocks[:3]):
            print(f"   Block {i+1}: {block.content[:60]}...")
    
    # Check ledger
    ledger = Path(".refinery/extraction_ledger.jsonl")
    if ledger.exists():
        print(f"\n📁 Saved: {ledger}")
    
    # WHAT YOU GET
    print("\n" + "=" * 70)
    print("📦 WHAT YOU GET FROM CURRENT IMPLEMENTATION")
    print("=" * 70)
    
    print("""
1. DOCUMENT PROFILE (.refinery/profiles/)
   • Classification (digital/scanned, layout type, domain)
   • Strategy recommendation
   • Cost estimate
   
2. EXTRACTED CONTENT
   • Text blocks with bounding boxes
   • Tables with structure preserved
   • Figures with metadata
   
3. EXTRACTION LEDGER (.refinery/extraction_ledger.jsonl)
   • Strategy used
   • Confidence score
   • Processing time
   • Cost estimate
   
4. FIGURES (.refinery/figures/)
   • All images extracted and saved
   • Metadata (dimensions, format)
   • Captions bound to figures
   
5. ENHANCED FEATURES
   ✅ Multi-strategy extraction (fast/layout/vision)
   ✅ Confidence-based escalation
   ✅ Enhanced table extraction
   ✅ Figure-caption binding
   ✅ Multi-column layout detection
   ✅ Handwriting OCR support
   ✅ Cost tracking
   ✅ Complete audit trail
""")
    
    print("=" * 70)
    print("⏳ NOT YET IMPLEMENTED (Stages 3-5)")
    print("=" * 70)
    
    print("""
• Stage 3: Semantic Chunking
  - Break into RAG-ready chunks
  - Preserve logical relationships
  - Add metadata and context
  
• Stage 4: PageIndex Builder
  - Create navigation tree
  - Generate section summaries
  - Extract key entities
  
• Stage 5: Query Interface
  - Answer questions
  - Provide provenance
  - Verify claims
""")
    
    print("=" * 70)
    print("✨ Demo Complete!")
    print("=" * 70)
    
    print(f"\n💡 To see real outputs, check:")
    print(f"   • .refinery/profiles/{profile.doc_id}.json")
    print(f"   • .refinery/extraction_ledger.jsonl")
    print(f"   • .refinery/figures/ (if document has images)")


if __name__ == "__main__":
    main()
