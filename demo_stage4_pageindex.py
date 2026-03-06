#!/usr/bin/env python3
"""
Stage 4 Demo: PageIndex Builder
Demonstrates hierarchical navigation structure creation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def demo_pageindex():
    """Demo PageIndex building"""
    from src.agents.triage import TriageAgent
    from src.agents.extractor import ExtractionRouter
    from src.chunking import SemanticChunker
    from src.agents.pageindex_builder import PageIndexBuilder
    
    print("\n" + "="*70)
    print("STAGE 4: PageIndex Builder Demo")
    print("="*70)
    
    # Use a test document
    data_dir = Path("data")
    pdf_file = data_dir / "CBE Annual Report 2012-13.pdf"
    
    if not pdf_file.exists():
        print(f"❌ Test file not found: {pdf_file}")
        return False
    
    print(f"\n📄 Processing: {pdf_file.name}\n")
    
    # Stage 1-3: Get extracted doc and LDUs
    print("⏳ Running Stages 1-3 (Triage → Extraction → Chunking)...")
    
    triage = TriageAgent()
    router = ExtractionRouter()
    chunker = SemanticChunker()
    
    profile = triage.profile_document(str(pdf_file))
    print(f"  ✓ Triage: {profile.origin_type}, {profile.layout_complexity}")
    
    extracted_doc = router.extract(str(pdf_file), profile)
    print(f"  ✓ Extraction: {len(extracted_doc.text_blocks)} blocks, {len(extracted_doc.tables)} tables")
    
    ldus = chunker.chunk_document(extracted_doc)
    print(f"  ✓ Chunking: {len(ldus)} LDUs created")
    
    # Stage 4: Build PageIndex
    print("\n🗂️  STAGE 4: Building PageIndex...")
    print("-"*70)
    
    builder = PageIndexBuilder()
    
    output_path = f".refinery/pageindex/{profile.doc_id}_index.json"
    page_index = builder.build_index(extracted_doc, ldus, output_path)
    
    print(f"\n✓ PageIndex built successfully!")
    print(f"  • Total Pages: {page_index.total_pages}")
    print(f"  • Root Sections: {len(page_index.root_sections)}")
    
    # Display section hierarchy
    print(f"\n📑 Section Hierarchy:")
    print("-"*70)
    
    def print_section(section, indent=0):
        """Recursively print section hierarchy"""
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        print(f"{prefix}{section.title}")
        print(f"{'  ' * (indent + 1)}Pages: {section.page_start}-{section.page_end} | "
              f"LDUs: {len(section.ldu_ids)} | "
              f"Level: {section.level}")
        
        if section.data_types_present:
            print(f"{'  ' * (indent + 1)}Contains: {', '.join(section.data_types_present)}")
        
        if section.summary:
            summary = section.summary[:100] + "..." if len(section.summary) > 100 else section.summary
            print(f"{'  ' * (indent + 1)}Summary: {summary}")
        
        print()
        
        for child in section.child_sections:
            print_section(child, indent + 1)
    
    for section in page_index.root_sections[:5]:  # Show first 5 sections
        print_section(section)
    
    # Test navigation
    print("\n🔍 Navigation Tests:")
    print("-"*70)
    
    # Test 1: Find section by page
    test_page = 5
    section = page_index.find_section_by_page(test_page)
    if section:
        print(f"✓ Page {test_page} is in section: '{section.title}'")
        print(f"  Section spans pages {section.page_start}-{section.page_end}")
    else:
        print(f"✗ No section found for page {test_page}")
    
    # Test 2: Search by keyword
    print(f"\n✓ Searching for 'financial'...")
    results = page_index.find_section_by_query("financial")
    if results:
        print(f"  Found {len(results)} matching sections:")
        for r in results[:3]:
            print(f"    - {r.title} (pages {r.page_start}-{r.page_end})")
    else:
        print("  No matching sections found")
    
    # Summary
    print("\n" + "="*70)
    print("📊 PageIndex Summary")
    print("="*70)
    
    total_sections = len(page_index.root_sections)
    
    def count_all_sections(sections):
        count = len(sections)
        for section in sections:
            count += count_all_sections(section.child_sections)
        return count
    
    all_sections = count_all_sections(page_index.root_sections)
    
    print(f"\n✓ Total Sections: {all_sections}")
    print(f"✓ Root Sections: {total_sections}")
    print(f"✓ Total Pages: {page_index.total_pages}")
    print(f"✓ Output: {output_path}")
    
    print("\n🎯 Use Cases:")
    print("  • Spatial search: Find content by page number")
    print("  • Semantic search: Find sections by keyword")
    print("  • Navigation: Browse document hierarchy")
    print("  • Context: Get section context for LDUs")
    
    print("\n🎉 Stage 4 completed successfully!")
    
    return True


if __name__ == "__main__":
    try:
        success = demo_pageindex()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
