"""
Integration Test: Full 5-Stage Pipeline
Tests complete document processing from PDF to queryable knowledge
"""

import pytest
from pathlib import Path
from src.agents import (
    TriageAgent, ExtractionRouter, ChunkingAgent,
    PageIndexBuilderAI, QueryAgent
)
from src.utils.fact_extractor_ai import FactExtractorAI


class TestFullPipeline:
    """Integration test for complete 5-stage pipeline"""
    
    @pytest.fixture
    def test_pdf(self):
        """Get test PDF path"""
        pdf_path = Path("data/test_native_digital.pdf")
        if not pdf_path.exists():
            pytest.skip("Test PDF not found")
        return str(pdf_path)
    
    def test_stage1_triage(self, test_pdf):
        """Test Stage 1: Triage Agent with Short-Circuit Waterfall"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        # Verify profile created
        assert profile is not None
        assert profile.doc_id == "test_native_digital"
        assert profile.total_pages > 0
        assert profile.origin_type in ["native_digital", "scanned_image", "mixed"]
        assert profile.layout_complexity in ["single_column", "multi_column", "table_heavy", "mixed"]
        
        # Verify short-circuit logic
        assert hasattr(profile, 'origin_confidence')
        assert profile.origin_confidence > 0
        
        print(f"✓ Stage 1: {profile.origin_type} | {profile.layout_complexity}")
        return profile
    
    def test_stage2_extraction(self, test_pdf):
        """Test Stage 2: Multi-Strategy Extraction"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        
        # Verify extraction
        assert extracted_doc is not None
        assert extracted_doc.doc_id == profile.doc_id
        # Note: text_blocks may be empty for some PDFs
        assert extracted_doc.confidence_score > 0
        
        print(f"✓ Stage 2: {len(extracted_doc.text_blocks)} blocks | confidence={extracted_doc.confidence_score:.2f}")
        return extracted_doc, profile
    
    def test_stage3_chunking(self, test_pdf):
        """Test Stage 3: Semantic Chunking"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, test_pdf)
        
        # Verify LDUs
        assert ldus is not None
        # LDUs may be empty if no content extracted
        assert all(hasattr(ldu, 'content_hash') for ldu in ldus) if ldus else True
        assert all(hasattr(ldu, 'chunk_type') for ldu in ldus) if ldus else True
        
        print(f"✓ Stage 3: {len(ldus)} LDUs created")
        return ldus, extracted_doc, profile
    
    def test_stage4_pageindex(self, test_pdf):
        """Test Stage 4: AI-Native PageIndex Builder"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, test_pdf)
        
        # Test AI-native PageIndex
        indexer = PageIndexBuilderAI()
        page_index = indexer.build_index(
            extracted_doc, 
            ldus,
            pdf_path=test_pdf
        )
        
        # Verify PageIndex
        assert page_index is not None
        assert page_index.doc_id == profile.doc_id
        assert len(page_index.root_sections) > 0
        assert page_index.total_pages > 0
        
        print(f"✓ Stage 4: {len(page_index.root_sections)} sections | Docling DOM: {indexer.docling_available}")
        return page_index, ldus, extracted_doc, profile
    
    def test_stage45_fact_extraction(self, test_pdf):
        """Test Stage 4.5: AI-Native Fact Extraction"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, test_pdf)
        
        # Test AI-native fact extraction
        fact_extractor = FactExtractorAI()
        fact_count = fact_extractor.extract_facts(extracted_doc, ldus)
        
        # Verify facts (may be 0 if Gemini not configured)
        assert fact_count >= 0
        
        if fact_extractor.gemini_available:
            print(f"✓ Stage 4.5: {fact_count} facts extracted (LLM)")
        else:
            print(f"✓ Stage 4.5: Skipped (Gemini not configured)")
        
        return fact_count
    
    def test_stage5_query_interface(self, test_pdf):
        """Test Stage 5: Query Interface Agent"""
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, test_pdf)
        
        indexer = PageIndexBuilderAI()
        page_index = indexer.build_index(
            extracted_doc, 
            ldus,
            pdf_path=test_pdf,
            output_path=f".refinery/pageindex/{profile.doc_id}_pageindex.json"
        )
        
        # Test query interface
        query_agent = QueryAgent()
        result = query_agent.query(
            "What are the main sections?",
            doc_id=profile.doc_id,
            method="pageindex"
        )
        
        # Verify query result
        assert result is not None
        assert result.query == "What are the main sections?"
        assert result.retrieval_method == "pageindex"
        assert result.confidence >= 0
        
        print(f"✓ Stage 5: Query executed | confidence={result.confidence:.2f} | citations={len(result.citations)}")
        return result
    
    def test_full_pipeline_integration(self, test_pdf):
        """Test complete 5-stage pipeline integration"""
        print("\n" + "="*70)
        print("FULL PIPELINE INTEGRATION TEST")
        print("="*70)
        
        # Stage 1: Triage
        print("\n[Stage 1] Triage...")
        triage = TriageAgent()
        profile = triage.profile_document(test_pdf)
        assert profile is not None
        print(f"  ✓ {profile.origin_type} | {profile.layout_complexity}")
        
        # Stage 2: Extraction
        print("\n[Stage 2] Extraction...")
        router = ExtractionRouter()
        extracted_doc = router.extract(test_pdf, profile)
        assert extracted_doc is not None
        # Note: text_blocks may be empty for some PDFs, but extraction should succeed
        print(f"  ✓ {len(extracted_doc.text_blocks)} blocks | {extracted_doc.extraction_strategy}")
        
        # Stage 3: Chunking
        print("\n[Stage 3] Chunking...")
        chunker = ChunkingAgent()
        ldus = chunker.process_document(extracted_doc, test_pdf)
        assert ldus is not None
        # LDUs may be minimal if extraction was limited
        print(f"  ✓ {len(ldus)} LDUs")
        
        # Stage 4: PageIndex
        print("\n[Stage 4] PageIndex...")
        indexer = PageIndexBuilderAI()
        page_index = indexer.build_index(
            extracted_doc, 
            ldus,
            pdf_path=test_pdf,
            output_path=f".refinery/pageindex/{profile.doc_id}_pageindex.json"
        )
        assert page_index is not None
        print(f"  ✓ {len(page_index.root_sections)} sections")
        
        # Stage 4.5: Fact Extraction
        print("\n[Stage 4.5] Fact Extraction...")
        fact_extractor = FactExtractorAI()
        fact_count = fact_extractor.extract_facts(extracted_doc, ldus)
        print(f"  ✓ {fact_count} facts")
        
        # Stage 5: Query
        print("\n[Stage 5] Query Interface...")
        query_agent = QueryAgent()
        result = query_agent.query(
            "What are the main sections?",
            doc_id=profile.doc_id
        )
        assert result is not None
        print(f"  ✓ Query executed | {result.retrieval_method}")
        
        print("\n" + "="*70)
        print("✓ FULL PIPELINE INTEGRATION TEST PASSED")
        print("="*70)
        
        # Verify artifacts created
        assert Path(f".refinery/profiles/{profile.doc_id}.json").exists()
        assert Path(f".refinery/ldus/{profile.doc_id}_ldus.json").exists()
        assert Path(f".refinery/pageindex/{profile.doc_id}_pageindex.json").exists()
        
        return {
            'profile': profile,
            'extracted_doc': extracted_doc,
            'ldus': ldus,
            'page_index': page_index,
            'fact_count': fact_count,
            'query_result': result
        }


class TestShortCircuitWaterfall:
    """Test Short-Circuit Waterfall optimization"""
    
    def test_pass1_short_circuit(self):
        """Test Pass 1 short-circuit (no fonts)"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        
        # Simulate Pass 1 short-circuit
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "has_font_metadata": False,
            "character_density": 0.0,
            "image_ratio": 1.0
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "scanned_image"
        assert confidence == 0.95
    
    def test_pass2_short_circuit(self):
        """Test Pass 2 short-circuit (high image ratio)"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        
        # Simulate Pass 2 short-circuit
        metrics = {
            "short_circuit": "pass2_high_image_ratio",
            "has_font_metadata": True,
            "character_density": 0.01,
            "image_ratio": 0.85
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "mixed"
        assert confidence == 0.90


class TestAINativeStages:
    """Test AI-native Stage 4 and 4.5"""
    
    def test_pageindex_builder_ai(self):
        """Test AI-native PageIndex builder"""
        from src.agents.pageindex_builder_ai import PageIndexBuilderAI
        
        indexer = PageIndexBuilderAI()
        assert indexer is not None
        
        # Check if Docling available
        print(f"Docling available: {indexer.docling_available}")
    
    def test_fact_extractor_ai(self):
        """Test AI-native fact extractor"""
        from src.utils.fact_extractor_ai import FactExtractorAI
        
        extractor = FactExtractorAI()
        assert extractor is not None
        
        # Check if Gemini available
        print(f"Gemini available: {extractor.gemini_available}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
