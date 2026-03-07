#!/usr/bin/env python3
"""
Quick test of complete 5-stage pipeline
"""

from pathlib import Path
from src.agents import (
    TriageAgent, ExtractionRouter, ChunkingAgent,
    PageIndexBuilder, QueryAgent
)
from src.utils.fact_extractor import FactExtractor

def test_pipeline():
    pdf_path = "data/test_native_digital.pdf"
    
    print("="*70)
    print("5-STAGE PIPELINE TEST")
    print("="*70)
    
    # Stage 1: Triage
    print("\n[Stage 1] Triage...")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    print(f"✓ Profile: {profile.origin_type} | {profile.layout_complexity}")
    
    # Stage 2: Extraction
    print("\n[Stage 2] Extraction...")
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    print(f"✓ Extracted: {len(extracted_doc.text_blocks)} blocks, {len(extracted_doc.tables)} tables")
    
    # Stage 3: Chunking
    print("\n[Stage 3] Chunking...")
    chunker = ChunkingAgent()
    ldus = chunker.process_document(extracted_doc, pdf_path)
    print(f"✓ Created: {len(ldus)} LDUs")
    
    # Stage 4: PageIndex
    print("\n[Stage 4] PageIndex...")
    indexer = PageIndexBuilder()
    page_index = indexer.build_index(
        extracted_doc, 
        ldus, 
        f".refinery/pageindex/{profile.doc_id}_pageindex.json"
    )
    print(f"✓ Built: {len(page_index.root_sections)} sections")
    
    # Extract facts
    print("\n[Stage 4.5] Fact Extraction...")
    fact_extractor = FactExtractor()
    fact_count = fact_extractor.extract_facts(extracted_doc, ldus)
    print(f"✓ Extracted: {fact_count} facts")
    
    # Stage 5: Query
    print("\n[Stage 5] Query Interface...")
    query_agent = QueryAgent()
    
    # Test query
    result = query_agent.query(
        "What are the main sections?",
        doc_id=profile.doc_id,
        method="pageindex"
    )
    
    print(f"✓ Query: {result.query}")
    print(f"  Answer: {result.answer[:100]}...")
    print(f"  Citations: {len(result.citations)}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Method: {result.retrieval_method}")
    
    # Show provenance chain
    if result.citations:
        print("\n[Provenance Chain]")
        for i, citation in enumerate(result.citations[:2], 1):
            print(f"  {i}. {citation.document_name} - Page {citation.page_number}")
            print(f"     Excerpt: {citation.excerpt[:80]}...")
    
    print("\n" + "="*70)
    print("✓ PIPELINE COMPLETE")
    print("="*70)
    
    return profile.doc_id

if __name__ == "__main__":
    doc_id = test_pipeline()
    print(f"\nNow try: python demo_query_interface.py {doc_id}")
