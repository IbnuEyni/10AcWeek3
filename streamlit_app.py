"""Document Intelligence Refinery - Interactive Demo

Showcases the 4-stage pipeline with detailed visualizations:
1. Triage: Document profiling and strategy selection
2. Extraction: Multi-strategy extraction with confidence scores
3. PageIndex: Hierarchical navigation tree
4. Query: Natural language queries with provenance

Usage:
    uv pip install streamlit pymupdf pillow
    streamlit run streamlit_app.py
"""

import json
import io
from pathlib import Path
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent
from src.agents.pageindex_builder import PageIndexBuilder
from src.agents.query_agent import QueryAgent

REFINERY_DIR = Path(".refinery")
REFINERY_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_pdf(uploaded_file) -> str:
    tmp_dir = REFINERY_DIR / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    file_path = tmp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)


def render_pdf_page(pdf_path: str, page_num: int) -> Image.Image:
    """Render a PDF page as an image"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def show_stage1_triage(pdf_path: str):
    """Stage 1: Document Triage"""
    st.header("🔍 Stage 1: Document Triage")
    st.markdown("Analyzing document characteristics to select optimal extraction strategy...")
    
    with st.spinner("Profiling document..."):
        triage = TriageAgent()
        profile = triage.profile_document(pdf_path)
        st.session_state.profile = profile
    
    st.success("✅ Triage Complete")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Document Profile")
        st.json({
            "doc_id": profile.doc_id,
            "filename": profile.filename,
            "total_pages": profile.total_pages,
            "origin_type": profile.origin_type.value if hasattr(profile.origin_type, 'value') else profile.origin_type,
            "layout_complexity": profile.layout_complexity.value if hasattr(profile.layout_complexity, 'value') else profile.layout_complexity,
            "character_density": round(profile.character_density, 4),
            "image_ratio": round(profile.image_ratio, 4),
            "table_count": profile.table_count,
        })
    
    with col2:
        st.subheader("🎯 Strategy Selection")
        st.info(f"**Selected Strategy:** {profile.estimated_extraction_cost.value if hasattr(profile.estimated_extraction_cost, 'value') else profile.estimated_extraction_cost}")
        
        st.markdown("**Decision Rationale:**")
        if "native" in str(profile.origin_type).lower():
            st.write("✓ Native digital PDF detected (high character density)")
            st.write("✓ Using **Layout-Aware** extraction (Docling FAST mode)")
        elif "scanned" in str(profile.origin_type).lower():
            st.write("✓ Scanned document detected (low character density)")
            st.write("✓ Using **Vision-Augmented** extraction (Gemini + OCR)")
        
        if profile.table_count > 0:
            st.write(f"✓ {profile.table_count} tables detected - preserving structure")


def show_stage2_extraction(pdf_path: str, profile):
    """Stage 2: Multi-Strategy Extraction"""
    st.header("⚙️ Stage 2: Extraction")
    st.markdown("Extracting structured content with confidence-gated escalation...")
    
    with st.spinner("Running extraction..."):
        router = ExtractionRouter()
        extracted_doc = router.extract(pdf_path, profile)
        st.session_state.extracted_doc = extracted_doc
    
    st.success("✅ Extraction Complete")
    
    # Show extraction ledger
    ledger_path = REFINERY_DIR / "extraction_ledger.jsonl"
    if ledger_path.exists():
        with open(ledger_path) as f:
            lines = f.readlines()
            if lines:
                ledger_entry = json.loads(lines[-1])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Confidence Score", f"{ledger_entry.get('confidence_score', 0):.2f}")
                with col2:
                    st.metric("Processing Time", f"{ledger_entry.get('processing_time_ms', 0):.0f}ms")
                with col3:
                    st.metric("Cost Estimate", f"${ledger_entry.get('cost_estimate', 0):.3f}")
                
                with st.expander("📊 View Full Extraction Ledger Entry"):
                    st.json(ledger_entry)
    
    # Show extraction results side-by-side with PDF
    st.subheader("📄 Extraction Results")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Original Document (Page 1)**")
        try:
            img = render_pdf_page(pdf_path, 0)
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render PDF: {e}")
    
    with col2:
        st.markdown("**Extracted Content**")
        st.write(f"📝 Text Blocks: {len(extracted_doc.text_blocks)}")
        st.write(f"📊 Tables: {len(extracted_doc.tables)}")
        st.write(f"🖼️ Figures: {len(extracted_doc.figures)}")
        
        if extracted_doc.tables:
            st.markdown("**Sample Table (Structured JSON)**")
            table = extracted_doc.tables[0]
            st.json({
                "headers": table.headers,
                "rows": table.rows[:3],  # First 3 rows
                "bbox": {
                    "page": table.bbox.page,
                    "x0": table.bbox.x0,
                    "y0": table.bbox.y0,
                    "x1": table.bbox.x1,
                    "y1": table.bbox.y1,
                }
            })
        
        if extracted_doc.text_blocks:
            with st.expander("View Text Blocks"):
                for i, block in enumerate(extracted_doc.text_blocks[:5]):
                    st.text(f"Block {i+1} (Page {block.bbox.page}): {block.content[:200]}...")


def show_stage3_pageindex(extracted_doc, pdf_path: str):
    """Stage 3: PageIndex Builder"""
    st.header("🗂️ Stage 3: PageIndex Navigation")
    st.markdown("Building hierarchical navigation structure...")
    
    with st.spinner("Building PageIndex..."):
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, pdf_path)
        
        indexer = PageIndexBuilder()
        pageindex_path = REFINERY_DIR / "pageindex" / f"{extracted_doc.doc_id}_pageindex.json"
        page_index = indexer.build_index(extracted_doc, ldus, output_path=str(pageindex_path))
        
        st.session_state.page_index = page_index
        st.session_state.ldus = ldus
    
    st.success("✅ PageIndex Built")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📊 Index Statistics")
        st.metric("Total Pages", page_index.total_pages)
        st.metric("Root Sections", len(page_index.root_sections))
        st.metric("Total LDUs", len(ldus))
    
    with col2:
        st.subheader("🌲 Section Hierarchy")
        
        def render_section_tree(section, level=0):
            indent = "  " * level
            st.markdown(f"{indent}📁 **{section.title}** (Pages {section.page_start}-{section.page_end})")
            st.caption(f"{indent}   LDUs: {len(section.ldu_ids)} | Types: {', '.join(section.data_types_present)}")
            
            for child in section.children:
                render_section_tree(child, level + 1)
        
        for section in page_index.root_sections[:3]:  # Show first 3 sections
            render_section_tree(section)
        
        if len(page_index.root_sections) > 3:
            st.caption(f"... and {len(page_index.root_sections) - 3} more sections")
    
    # Interactive navigation
    st.subheader("🔍 Navigate PageIndex")
    page_num = st.number_input("Jump to page:", min_value=1, max_value=page_index.total_pages, value=1)
    
    if st.button("Find Section"):
        section = indexer.find_section_by_page(page_index, page_num - 1)
        if section:
            st.success(f"📍 Found: **{section.title}** (Pages {section.page_start}-{section.page_end})")
            st.write(f"Summary: {section.summary}")
            st.write(f"Data types: {', '.join(section.data_types_present)}")
        else:
            st.warning("No section found for this page")


def show_stage4_query(page_index, pdf_path: str):
    """Stage 4: Query with Provenance"""
    st.header("💬 Stage 4: Query Interface")
    st.markdown("Ask natural language questions with full provenance tracking...")
    
    if "query_agent" not in st.session_state:
        st.session_state.query_agent = QueryAgent()
    
    query_agent = st.session_state.query_agent
    
    # Sample queries
    st.subheader("💡 Sample Queries")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What is the total revenue?"):
            st.session_state.query_text = "What is the total revenue?"
    with col2:
        if st.button("List all tables"):
            st.session_state.query_text = "List all tables in the document"
    with col3:
        if st.button("Summarize key findings"):
            st.session_state.query_text = "Summarize the key findings"
    
    query_text = st.text_input("Or enter your own question:", value=st.session_state.get("query_text", ""))
    
    if st.button("🔍 Run Query", type="primary"):
        if not query_text:
            st.warning("Please enter a question")
        else:
            with st.spinner("Processing query..."):
                try:
                    result = query_agent.query(query_text, doc_id=page_index.doc_id)
                    
                    st.success("✅ Query Complete")
                    
                    # Show answer
                    st.subheader("📝 Answer")
                    st.markdown(f"**{result.answer}**")
                    
                    # Show provenance
                    st.subheader("📍 Provenance Chain")
                    
                    for i, citation in enumerate(result.citations):
                        with st.expander(f"Citation {i+1}: Page {citation.page_number}"):
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.markdown("**Citation Details**")
                                st.write(f"Document: {citation.document_name}")
                                st.write(f"Page: {citation.page_number}")
                                st.write(f"Bounding Box: ({citation.bbox.x0:.0f}, {citation.bbox.y0:.0f}) → ({citation.bbox.x1:.0f}, {citation.bbox.y1:.0f})")
                                st.write(f"Content Hash: {citation.content_hash[:16]}...")
                                st.markdown("**Excerpt:**")
                                st.info(citation.excerpt)
                            
                            with col2:
                                st.markdown("**Source Page**")
                                try:
                                    img = render_pdf_page(pdf_path, citation.page_number)
                                    st.image(img, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Could not render page: {e}")
                    
                except Exception as e:
                    st.error(f"Query failed: {e}")


def main():
    st.set_page_config(page_title="Document Intelligence Refinery", layout="wide", page_icon="📄")
    
    st.title("📄 Document Intelligence Refinery")
    st.markdown("**Enterprise-grade agentic pipeline for unstructured document extraction**")
    
    # Sidebar
    with st.sidebar:
        st.header("Pipeline Stages")
        st.markdown("""
        1. 🔍 **Triage** - Document profiling
        2. ⚙️ **Extraction** - Multi-strategy extraction
        3. 🗂️ **PageIndex** - Hierarchical navigation
        4. 💬 **Query** - Provenance-aware Q&A
        """)
        
        st.markdown("---")
        st.markdown("**Upload a PDF to begin**")
    
    uploaded_file = st.file_uploader("📤 Drop your document here", type=["pdf"])
    
    if not uploaded_file:
        st.info("👆 Upload a PDF document to start the demo")
        return
    
    pdf_path = save_uploaded_pdf(uploaded_file)
    
    # Stage 1: Triage
    if "profile" not in st.session_state:
        show_stage1_triage(pdf_path)
    else:
        with st.expander("🔍 Stage 1: Triage (Complete)", expanded=False):
            st.json({"doc_id": st.session_state.profile.doc_id, "strategy": str(st.session_state.profile.estimated_extraction_cost)})
    
    if "profile" not in st.session_state:
        return
    
    st.markdown("---")
    
    # Stage 2: Extraction
    if "extracted_doc" not in st.session_state:
        show_stage2_extraction(pdf_path, st.session_state.profile)
    else:
        with st.expander("⚙️ Stage 2: Extraction (Complete)", expanded=False):
            st.write(f"Extracted {len(st.session_state.extracted_doc.text_blocks)} text blocks, {len(st.session_state.extracted_doc.tables)} tables")
    
    if "extracted_doc" not in st.session_state:
        return
    
    st.markdown("---")
    
    # Stage 3: PageIndex
    if "page_index" not in st.session_state:
        show_stage3_pageindex(st.session_state.extracted_doc, pdf_path)
    else:
        with st.expander("🗂️ Stage 3: PageIndex (Complete)", expanded=False):
            st.write(f"Built index with {len(st.session_state.page_index.root_sections)} sections")
    
    if "page_index" not in st.session_state:
        return
    
    st.markdown("---")
    
    # Stage 4: Query
    show_stage4_query(st.session_state.page_index, pdf_path)


if __name__ == "__main__":
    main()
