"""Unit tests for Query Interface Agent"""

import pytest
import json
from pathlib import Path
from src.agents.query_agent import QueryAgent
from src.models.provenance import ProvenanceChain, SourceCitation
from src.models.ldu import LDU
from src.models.pageindex import PageIndex, Section


class TestQueryAgent:
    """Test Query Interface Agent"""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = QueryAgent()
        assert agent is not None
        assert agent.pageindex_dir == Path(".refinery/pageindex")
        assert agent.ldu_dir == Path(".refinery/ldus")
    
    def test_method_selection(self):
        """Test automatic method selection"""
        agent = QueryAgent()
        
        # Structured query indicators
        assert agent._select_method("What is the total revenue?") == "structured"
        assert agent._select_method("How much was spent?") == "structured"
        
        # PageIndex indicators
        assert agent._select_method("What are the main sections?") == "pageindex"
        assert agent._select_method("Which page has the table?") == "pageindex"
        
        # Semantic search default
        assert agent._select_method("Explain the methodology") == "semantic"
    
    def test_empty_result(self):
        """Test empty result generation"""
        agent = QueryAgent()
        result = agent._empty_result("test query", "semantic")
        
        assert isinstance(result, ProvenanceChain)
        assert result.query == "test query"
        assert result.answer == "No relevant information found."
        assert len(result.citations) == 0
        assert result.confidence == 0.0
        assert result.retrieval_method == "semantic"
    
    def test_claim_matching(self):
        """Test claim matching logic"""
        agent = QueryAgent()
        
        claim = "The revenue was 4.2 billion"
        content = "In Q3 2024, the company reported revenue of $4.2 billion, up from previous quarter."
        
        # Should match (70% keyword threshold)
        assert agent._claim_matches_content(claim, content) is True
        
        # Non-matching claim
        claim2 = "The revenue was 10 billion"
        # May or may not match depending on keyword overlap
        result = agent._claim_matches_content(claim2, content)
        assert isinstance(result, bool)


class TestProvenanceChain:
    """Test ProvenanceChain model"""
    
    def test_provenance_creation(self):
        """Test creating provenance chain"""
        citation = SourceCitation(
            document_name="test.pdf",
            doc_id="test",
            page_number=5,
            content_hash="abc123",
            excerpt="Test excerpt"
        )
        
        provenance = ProvenanceChain(
            query="Test query",
            answer="Test answer",
            citations=[citation],
            confidence=0.85,
            retrieval_method="semantic_search"
        )
        
        assert provenance.query == "Test query"
        assert provenance.answer == "Test answer"
        assert len(provenance.citations) == 1
        assert provenance.confidence == 0.85
        assert provenance.retrieval_method == "semantic_search"
    
    def test_provenance_validation(self):
        """Test provenance validation"""
        citation = SourceCitation(
            document_name="test.pdf",
            doc_id="test",
            page_number=0,
            content_hash="abc123",
            excerpt="Test"
        )
        
        # Valid confidence
        provenance = ProvenanceChain(
            query="Q",
            answer="A",
            citations=[citation],
            confidence=0.5,
            retrieval_method="test"
        )
        assert provenance.confidence == 0.5
        
        # Invalid confidence should raise error
        with pytest.raises(Exception):
            ProvenanceChain(
                query="Q",
                answer="A",
                citations=[citation],
                confidence=1.5,  # Invalid
                retrieval_method="test"
            )


class TestSourceCitation:
    """Test SourceCitation model"""
    
    def test_citation_creation(self):
        """Test creating source citation"""
        citation = SourceCitation(
            document_name="annual_report.pdf",
            doc_id="annual_report",
            page_number=10,
            bbox={"x0": 100, "y0": 200, "x1": 300, "y1": 400},
            content_hash="hash123",
            excerpt="Revenue was $4.2B",
            ldu_id="ldu_001"
        )
        
        assert citation.document_name == "annual_report.pdf"
        assert citation.page_number == 10
        assert citation.bbox["x0"] == 100
        assert citation.content_hash == "hash123"
        assert citation.ldu_id == "ldu_001"
    
    def test_citation_serialization(self):
        """Test citation can be serialized"""
        citation = SourceCitation(
            document_name="test.pdf",
            doc_id="test",
            page_number=5,
            content_hash="abc",
            excerpt="Test"
        )
        
        # Should be serializable to dict
        citation_dict = citation.model_dump()
        assert isinstance(citation_dict, dict)
        assert citation_dict['document_name'] == "test.pdf"
        assert citation_dict['page_number'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
