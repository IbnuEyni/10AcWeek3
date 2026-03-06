#!/usr/bin/env python3
"""
Full Pipeline Demo - Single Document Through Complete Pipeline
Shows: Triage → Extraction → Chunking
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def demo_full_pipeline():
    """Run complete pipeline on one document"""
    from src.agents.triage import TriageAgent
    from src.agents.extractor import ExtractionRouter
    from src.chunking import SemanticChunker
    
    print("\n" + "="*70)
    print("DOCUMENT INTELLIGENCE REFINERY - FULL PIPELINE DEMO")
    print("="*70)
    
    # Find one document
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return False
    
    # Use specific test file
    pdf_file = data_dir / "CBE Annual Report 2012-13.pdf"
    
    if not pdf_file.exists():
        print(f"❌ Test file not found: {pdf_file}")
        print("Available files:")
        for f in list(data_dir.glob("*.pdf"))[:5]:
            print(f"  - {f.name}")
        return False
    
    print(f"\n📄 Processing: {pdf_file.name}")
    print("="*70)
    
    # Initialize triage
    triage = TriageAgent()
    
    # STAGE 1: TRIAGE
    print("\n🔍 STAGE 1: DOCUMENT TRIAGE")
    print("-"*70)
    
    profile = triage.profile_document(str(pdf_file))
    
    print(f"✓ Document ID: {profile.doc_id}")
    print(f"✓ Origin Type: {profile.origin_type}")
    print(f"✓ Layout Complexity: {profile.layout_complexity}")
    print(f"✓ Domain: {profile.domain_hint}")
    print(f"✓ Total Pages: {profile.total_pages}")
    print(f"✓ Character Density: {profile.character_density:.4f}")
    print(f"✓ Image Ratio: {profile.image_ratio:.2f}")
    print(f"✓ Has Font Metadata: {profile.has_font_metadata}")
    print(f"✓ Estimated Cost: {profile.estimated_extraction_cost}")
    
    # STAGE 2: EXTRACTION
    print("\n📊 STAGE 2: STRUCTURE EXTRACTION")
    print("-"*70)
    
    router = ExtractionRouter()
    
    # Show selected strategy
    strategy = router._select_strategy(profile)
    print(f"✓ Selected Strategy: {strategy.strategy_name}")
    
    # Extract
    print(f"⏳ Extracting (this may take 10-30 seconds)...")
    extracted_doc = router.extract(str(pdf_file), profile)
    
    print(f"\n✓ Extraction Complete!")
    print(f"  • Strategy Used: {extracted_doc.extraction_strategy}")
    print(f"  • Confidence Score: {extracted_doc.confidence_score:.2f}")
    print(f"  • Text Blocks: {len(extracted_doc.text_blocks)}")
    print(f"  • Tables: {len(extracted_doc.tables)}")
    print(f"  • Figures: {len(extracted_doc.figures)}")
    
    if extracted_doc.routing_summary:
        print(f"  • Total Attempts: {extracted_doc.routing_summary.total_attempts}")
        print(f"  • Escalation: {extracted_doc.routing_summary.escalation_triggered}")
        print(f"  • Processing Time: {extracted_doc.routing_summary.processing_time_ms}ms")
        print(f"  • Cost: ${extracted_doc.routing_summary.total_cost:.4f}")
    
    # Show sample content
    if extracted_doc.text_blocks:
        print(f"\n📝 Sample Text Block (first 300 chars):")
        print("-"*70)
        sample = extracted_doc.text_blocks[0].content[:300]
        print(f"{sample}...")
        print(f"\n  • Bounding Box: page={extracted_doc.text_blocks[0].bbox.page}, "
              f"x0={extracted_doc.text_blocks[0].bbox.x0:.1f}, "
              f"y0={extracted_doc.text_blocks[0].bbox.y0:.1f}")
    
    if extracted_doc.tables:
        print(f"\n📋 Sample Table:")
        print("-"*70)
        table = extracted_doc.tables[0]
        print(f"  • Headers: {table.headers[:5]}")
        print(f"  • Rows: {len(table.rows)}")
        if table.rows:
            print(f"  • First Row: {table.rows[0][:5]}")
    
    # STAGE 3: SEMANTIC CHUNKING
    print("\n🧩 STAGE 3: SEMANTIC CHUNKING")
    print("-"*70)
    
    chunker = SemanticChunker()
    
    print(f"⏳ Chunking extracted content...")
    chunks = chunker.chunk_document(extracted_doc)
    
    print(f"\n✓ Chunking Complete!")
    print(f"  • Total Chunks: {len(chunks)}")
    
    # Analyze chunks
    if chunks:
        avg_tokens = sum(c.token_count for c in chunks) / len(chunks)
        print(f"  • Average Tokens per Chunk: {avg_tokens:.0f}")
        
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        print(f"  • Chunk Types:")
        for ctype, count in chunk_types.items():
            print(f"    - {ctype}: {count}")
        
        # Show sample chunks
        print(f"\n📦 Sample Chunks:")
        print("-"*70)
        
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\nChunk {i}:")
            print(f"  • Type: {chunk.chunk_type}")
            print(f"  • Tokens: {chunk.token_count}")
            print(f"  • Content (first 150 chars): {chunk.content[:150]}...")
            if hasattr(chunk, 'metadata') and chunk.metadata:
                print(f"  • Metadata: {list(chunk.metadata.keys())}")
    
    # SUMMARY
    print("\n" + "="*70)
    print("📊 PIPELINE SUMMARY")
    print("="*70)
    
    print(f"\n✅ Successfully processed: {pdf_file.name}")
    print(f"\nStage 1 (Triage):")
    print(f"  • Classified as: {profile.origin_type}")
    print(f"  • Layout: {profile.layout_complexity}")
    
    print(f"\nStage 2 (Extraction):")
    print(f"  • Strategy: {extracted_doc.extraction_strategy}")
    print(f"  • Confidence: {extracted_doc.confidence_score:.2f}")
    print(f"  • Content: {len(extracted_doc.text_blocks)} blocks, {len(extracted_doc.tables)} tables")
    
    print(f"\nStage 3 (Chunking):")
    print(f"  • Chunks created: {len(chunks)}")
    print(f"  • Ready for RAG: ✓")
    
    print("\n🎉 Full pipeline completed successfully!")
    
    return True


if __name__ == "__main__":
    try:
        success = demo_full_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
