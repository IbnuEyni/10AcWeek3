"""Tests for Stage 3: Semantic Chunking"""

import pytest
from src.chunking import SemanticChunker
from src.agents.chunking import ChunkingAgent
from src.models.extracted_document import ExtractedDocument, TextBlock, Table, Figure, BoundingBox
from src.models.document_profile import DocumentProfile, OriginType, LayoutComplexity, DomainHint, ExtractionCost
from src.models.ldu import ChunkType


class TestSemanticChunker:
    """Test semantic chunking logic"""
    
    @pytest.fixture
    def chunker(self):
        return SemanticChunker()
    
    @pytest.fixture
    def sample_doc(self):
        """Create sample extracted document"""
        text_blocks = [
            TextBlock(
                content="This is the first paragraph of text.",
                bbox=BoundingBox(x0=50, y0=100, x1=550, y1=120, page=0),
                reading_order=0
            ),
            TextBlock(
                content="This is the second paragraph with more content.",
                bbox=BoundingBox(x0=50, y0=130, x1=550, y1=150, page=0),
                reading_order=1
            )
        ]
        
        tables = [
            Table(
                headers=["Column1", "Column2"],
                rows=[["Data1", "Data2"], ["Data3", "Data4"]],
                bbox=BoundingBox(x0=50, y0=200, x1=550, y1=300, page=0),
                table_id="table_0"
            )
        ]
        
        figures = [
            Figure(
                figure_id="fig_0",
                bbox=BoundingBox(x0=50, y0=350, x1=550, y1=450, page=0),
                caption="Figure 1: Sample figure",
                page=0
            )
        ]
        
        return ExtractedDocument(
            doc_id="test_doc",
            filename="test.pdf",
            text_blocks=text_blocks,
            tables=tables,
            figures=figures,
            extraction_strategy="fast_text",
            confidence_score=0.85
        )
    
    def test_chunker_initialization(self, chunker):
        """Test chunker initializes with config"""
        assert chunker.max_tokens == 512
        assert chunker.overlap_tokens == 50
        assert len(chunker.rules) == 5
    
    def test_chunk_document_creates_ldus(self, chunker, sample_doc):
        """Test chunking creates LDUs"""
        ldus = chunker.chunk_document(sample_doc, pdf_path=None)
        
        assert len(ldus) > 0
        assert any(ldu.chunk_type == ChunkType.TABLE for ldu in ldus)
        assert any(ldu.chunk_type == ChunkType.FIGURE for ldu in ldus)
        assert any(ldu.chunk_type == ChunkType.TEXT for ldu in ldus)
    
    def test_table_integrity_rule(self, chunker, sample_doc):
        """Test Rule 1: Tables never split"""
        ldus = chunker.chunk_document(sample_doc, pdf_path=None)
        
        table_ldus = [ldu for ldu in ldus if ldu.chunk_type == ChunkType.TABLE]
        assert len(table_ldus) == 1
        assert "Column1" in table_ldus[0].content
        assert "Data1" in table_ldus[0].content
    
    def test_figure_caption_binding(self, chunker, sample_doc):
        """Test Rule 2: Figure-caption binding"""
        ldus = chunker.chunk_document(sample_doc, pdf_path=None)
        
        figure_ldus = [ldu for ldu in ldus if ldu.chunk_type == ChunkType.FIGURE]
        assert len(figure_ldus) == 1
        assert "Figure 1: Sample figure" in figure_ldus[0].content
    
    def test_content_hash_generation(self, chunker, sample_doc):
        """Test content hash is generated"""
        ldus = chunker.chunk_document(sample_doc, pdf_path=None)
        
        for ldu in ldus:
            assert ldu.content_hash is not None
            assert len(ldu.content_hash) == 16
    
    def test_token_estimation(self, chunker):
        """Test token estimation"""
        text = "This is a test sentence with ten words in it."
        tokens = chunker._estimate_tokens(text)
        assert tokens > 0
        assert tokens < 20  # Should be around 10-13 tokens


class TestChunkingAgent:
    """Test chunking agent"""
    
    @pytest.fixture
    def agent(self, tmp_path):
        return ChunkingAgent(output_dir=str(tmp_path / "ldus"))
    
    @pytest.fixture
    def sample_doc(self):
        """Create minimal extracted document"""
        return ExtractedDocument(
            doc_id="test_agent_doc",
            filename="test.pdf",
            text_blocks=[
                TextBlock(
                    content="Test content",
                    bbox=BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0),
                    reading_order=0
                )
            ],
            tables=[],
            figures=[],
            extraction_strategy="fast_text",
            confidence_score=0.85
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initializes"""
        assert agent.chunker is not None
        assert agent.output_dir.exists()
    
    def test_process_document(self, agent, sample_doc):
        """Test agent processes document"""
        ldus = agent.process_document(sample_doc, pdf_path=None)
        
        assert len(ldus) > 0
        assert all(isinstance(ldu.ldu_id, str) for ldu in ldus)
    
    def test_save_and_load_ldus(self, agent, sample_doc):
        """Test saving and loading LDUs"""
        ldus = agent.process_document(sample_doc, pdf_path=None)
        
        # Load back
        loaded_ldus = agent.load_ldus(sample_doc.doc_id)
        
        assert len(loaded_ldus) == len(ldus)
        assert loaded_ldus[0].ldu_id == ldus[0].ldu_id
        assert loaded_ldus[0].content == ldus[0].content
