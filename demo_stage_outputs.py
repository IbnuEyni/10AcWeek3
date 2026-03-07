"""
Demo: Stage-by-Stage Pipeline Outputs
Shows exactly what you get at each stage for a single PDF
"""

import sys
from pathlib import Path
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent
from src.agents.pageindex_builder_ai import PageIndexBuilderAI
from src.agents.query_agent import QueryAgent
from src.logging_config import get_logger

logger = get_logger("demo_outputs")


def print_stage_separator(stage_num: int, stage_name: str):
    """Print visual separator"""
    print("\n" + "="*80)
    print(f"STAGE {stage_num}: {stage_name}")
    print("="*80 + "\n")


def demo_pipeline_outputs(pdf_path: str):
    """Run pipeline and show outputs at each stage"""
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"\n📄 INPUT: {pdf_file.name}")
    print(f"   Path: {pdf_path}")
    
    # ========================================================================
    # STAGE 1: TRIAGE AGENT
    # ========================================================================
    print_stage_separator(1, "TRIAGE AGENT - Document Classification")
    
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    print("OUTPUT: DocumentProfile")
    print(f"├─ doc_id: {profile.doc_id}")
    print(f"├─ filename: {profile.filename}")
    print(f"├─ origin_type: {profile.origin_type}")
    print(f"├─ layout_complexity: {profile.layout_complexity}")
    print(f"├─ domain: {profile.domain}")
    print(f"├─ page_count: {profile.page_count}")
    print(f"├─ confidence_score: {profile.confidence_score:.2f}")
    print(f"├─ recommended_strategy: {profile.recommended_strategy}")
    print(f"└─ estimated_cost: ${profile.estimated_extraction_cost:.4f}")
    
    if hasattr(profile, 'metrics') and profile.metrics:
        print(f"\n   Metrics (Short-Circuit Waterfall):")
        print(f"   ├─ has_fonts: {profile.metrics.get('has_fonts', 'N/A')}")
        print(f"   ├─ image_ratio: {profile.metrics.get('image_ratio', 0):.2%}")
        print(f"   ├─ short_circuit: {profile.metrics.get('short_circuit', 'N/A')}")
        print(f"   └─ processing_time: {profile.metrics.get('processing_time_ms', 0):.1f}ms")
    
    # ========================================================================
    # STAGE 2: EXTRACTION ROUTER
    # ========================================================================
    print_stage_separator(2, "EXTRACTION ROUTER - Multi-Strategy Extraction")
    
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    
    print("OUTPUT: ExtractedDocument")
    print(f"├─ doc_id: {extracted_doc.doc_id}")
    print(f"├─ strategy_used: {extracted_doc.strategy_used}")
    print(f"├─ confidence_score: {extracted_doc.confidence_score:.2f}")
    print(f"├─ text_blocks: {len(extracted_doc.text_blocks)} blocks")
    print(f"├─ tables: {len(extracted_doc.tables)} tables")
    print(f"├─ figures: {len(extracted_doc.figures)} figures")
    print(f"└─ processing_time: {extracted_doc.processing_time_ms:.1f}ms")
    
    # Show sample text blocks
    if extracted_doc.text_blocks:
        print(f"\n   Sample Text Blocks (first 3):")
        for i, block in enumerate(extracted_doc.text_blocks[:3], 1):
            preview = block.content[:80].replace('\n', ' ')
            print(f"   [{i}] Page {block.bbox.page}: \"{preview}...\"")
    
    # Show tables
    if extracted_doc.tables:
        print(f"\n   Tables Found:")
        for i, table in enumerate(extracted_doc.tables, 1):
            print(f"   [{i}] Page {table.bbox.page}: {len(table.rows)} rows × {len(table.rows[0]) if table.rows else 0} cols")
    
    # ========================================================================
    # STAGE 3: CHUNKING AGENT
    # ========================================================================
    print_stage_separator(3, "CHUNKING AGENT - Semantic Chunking")
    
    chunker = ChunkingAgent()
    ldus = chunker.process_document(extracted_doc, pdf_path)
    
    print("OUTPUT: List[LDU] (Logical Document Units)")
    print(f"├─ total_ldus: {len(ldus)}")
    
    # Count by type
    text_ldus = [l for l in ldus if l.chunk_type == 'text']
    table_ldus = [l for l in ldus if l.chunk_type == 'table']
    figure_ldus = [l for l in ldus if l.chunk_type == 'figure']
    
    print(f"├─ text_chunks: {len(text_ldus)}")
    print(f"├─ table_chunks: {len(table_ldus)}")
    print(f"└─ figure_chunks: {len(figure_ldus)}")
    
    # Show sample LDUs
    if ldus:
        print(f"\n   Sample LDUs (first 3):")
        for i, ldu in enumerate(ldus[:3], 1):
            preview = ldu.content[:80].replace('\n', ' ')
            pages = ldu.page_refs if isinstance(ldu.page_refs, list) else [ldu.page_refs]
            print(f"   [{i}] {ldu.chunk_type.upper()} | Pages {pages} | \"{preview}...\"")
    
    # ========================================================================
    # STAGE 4: PAGEINDEX BUILDER
    # ========================================================================
    print_stage_separator(4, "PAGEINDEX BUILDER - Hierarchical Navigation")
    
    indexer = PageIndexBuilderAI()
    page_index = indexer.build_index(extracted_doc, ldus, pdf_path=pdf_path)
    
    print("OUTPUT: PageIndex")
    print(f"├─ doc_id: {page_index.doc_id}")
    print(f"├─ filename: {page_index.filename}")
    print(f"├─ total_pages: {page_index.total_pages}")
    print(f"└─ root_sections: {len(page_index.root_sections)}")
    
    # Show section hierarchy
    def print_section_tree(section, indent=0):
        prefix = "   " + "  " * indent + "├─"
        print(f"{prefix} {section.title} (Level {section.level}, Pages {section.page_start}-{section.page_end})")
        print(f"   {'  ' * indent}   └─ LDUs: {len(section.ldu_ids)}, Types: {section.data_types_present}")
        for child in section.child_sections:
            print_section_tree(child, indent + 1)
    
    if page_index.root_sections:
        print(f"\n   Section Hierarchy:")
        for section in page_index.root_sections:
            print_section_tree(section)
    
    # ========================================================================
    # STAGE 4.5: FACT EXTRACTION (Optional)
    # ========================================================================
    print_stage_separator("4.5", "FACT EXTRACTION - Structured Data Extraction")
    
    try:
        from src.utils.fact_extractor_ai import FactExtractorAI
        
        fact_extractor = FactExtractorAI()
        facts = fact_extractor.extract_facts(extracted_doc, pdf_path)
        
        print("OUTPUT: List[ExtractedFact]")
        print(f"└─ total_facts: {len(facts)}")
        
        if facts:
            print(f"\n   Sample Facts (first 5):")
            for i, fact in enumerate(facts[:5], 1):
                print(f"   [{i}] {fact.key} = {fact.value} {fact.unit or ''}")
                print(f"       Context: {fact.context[:60]}...")
                print(f"       Page: {fact.page_number}")
        else:
            print("   ℹ️  No facts extracted (Gemini API may not be configured)")
    
    except Exception as e:
        print(f"   ⚠️  Fact extraction skipped: {e}")
    
    # ========================================================================
    # STAGE 5: QUERY INTERFACE
    # ========================================================================
    print_stage_separator(5, "QUERY INTERFACE - Natural Language Queries")
    
    query_agent = QueryAgent()
    
    # Example queries
    queries = [
        "What sections are in this document?",
        "Find information about revenue",
        "What is on page 1?"
    ]
    
    print("OUTPUT: ProvenanceChain (for each query)")
    
    for i, query_text in enumerate(queries, 1):
        print(f"\n   Query {i}: \"{query_text}\"")
        
        try:
            result = query_agent.query(query_text, doc_id=profile.doc_id)
            
            print(f"   ├─ answer: {result.answer[:100]}...")
            print(f"   ├─ confidence: {result.confidence:.2f}")
            print(f"   ├─ retrieval_method: {result.retrieval_method}")
            print(f"   └─ citations: {len(result.citations)}")
            
            if result.citations:
                for j, citation in enumerate(result.citations[:2], 1):
                    print(f"       [{j}] {citation.document_name}, Page {citation.page_number}")
                    if citation.excerpt:
                        print(f"           \"{citation.excerpt[:60]}...\"")
        
        except Exception as e:
            print(f"   ⚠️  Query failed: {e}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("PIPELINE SUMMARY")
    print("="*80)
    print(f"✅ Stage 1: Classified as {profile.origin_type} / {profile.layout_complexity}")
    print(f"✅ Stage 2: Extracted {len(extracted_doc.text_blocks)} blocks, {len(extracted_doc.tables)} tables")
    print(f"✅ Stage 3: Created {len(ldus)} LDUs")
    print(f"✅ Stage 4: Built index with {len(page_index.root_sections)} sections")
    print(f"✅ Stage 5: Query interface ready")
    print(f"\n💰 Total Cost: ${profile.estimated_extraction_cost:.4f}")
    print(f"⏱️  Total Time: {extracted_doc.processing_time_ms:.1f}ms")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python demo_stage_outputs.py <path_to_pdf>")
        print("\nExample:")
        print("  python demo_stage_outputs.py data/sample.pdf")
        sys.exit(1)
    
    demo_pipeline_outputs(sys.argv[1])
