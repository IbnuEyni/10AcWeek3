import pytest
from pathlib import Path
from src.agents.triage import TriageAgent
from src.models.document_profile import OriginType, LayoutComplexity, DomainHint


class TestTriageAgent:
    """Unit tests for document classification"""
    
    @pytest.fixture
    def triage_agent(self, tmp_path):
        """Create triage agent with temp output dir"""
        return TriageAgent(output_dir=str(tmp_path / "profiles"))
    
    def test_domain_detection_financial(self, triage_agent):
        """Test financial domain detection"""
        domain = triage_agent._detect_domain("CBE_Annual_Report_2023.pdf")
        assert domain == DomainHint.FINANCIAL
    
    def test_domain_detection_legal(self, triage_agent):
        """Test legal domain detection"""
        domain = triage_agent._detect_domain("legal_contract_agreement.pdf")
        assert domain == DomainHint.LEGAL
    
    def test_domain_detection_technical(self, triage_agent):
        """Test technical domain detection"""
        domain = triage_agent._detect_domain("technical_specification.pdf")
        assert domain == DomainHint.TECHNICAL
    
    def test_extraction_cost_estimation_native(self, triage_agent):
        """Test cost estimation for native digital PDF"""
        cost = triage_agent._estimate_extraction_cost(
            origin_type="native_digital",
            layout_complexity="single_column",
            metrics={"character_density": 0.05}
        )
        assert cost.value == "fast_text_sufficient"
    
    def test_extraction_cost_estimation_scanned(self, triage_agent):
        """Test cost estimation for scanned PDF"""
        cost = triage_agent._estimate_extraction_cost(
            origin_type="scanned_image",
            layout_complexity="single_column",
            metrics={"character_density": 0.001}
        )
        assert cost.value == "needs_vision_model"
    
    def test_extraction_cost_estimation_table_heavy(self, triage_agent):
        """Test cost estimation for table-heavy document"""
        cost = triage_agent._estimate_extraction_cost(
            origin_type="native_digital",
            layout_complexity="table_heavy",
            metrics={"character_density": 0.05}
        )
        assert cost.value == "needs_layout_model"


class TestPDFAnalyzer:
    """Unit tests for PDF analysis utilities"""
    
    def test_origin_type_detection_digital(self):
        """Test detection of native digital PDF"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        metrics = {
            "character_density": 0.05,
            "has_font_metadata": True,
            "image_ratio": 0.2
        }
        
        origin_type, confidence = PDFAnalyzer.detect_origin_type(metrics)
        assert origin_type == "native_digital"
        assert confidence > 0.8
    
    def test_origin_type_detection_scanned(self):
        """Test detection of scanned PDF"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        metrics = {
            "character_density": 0.001,
            "has_font_metadata": False,
            "image_ratio": 0.9
        }
        
        origin_type, confidence = PDFAnalyzer.detect_origin_type(metrics)
        assert origin_type == "scanned_image"
        assert confidence > 0.7
    
    def test_layout_complexity_detection_table_heavy(self):
        """Test detection of table-heavy layout"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        metrics = {"table_count_estimate": 15}
        complexity = PDFAnalyzer.detect_layout_complexity(metrics)
        assert complexity == "table_heavy"
    
    def test_layout_complexity_detection_simple(self):
        """Test detection of simple layout"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        metrics = {"table_count_estimate": 0}
        complexity = PDFAnalyzer.detect_layout_complexity(metrics)
        assert complexity == "single_column"


class TestExtractionConfidence:
    """Unit tests for extraction confidence scoring"""
    
    def test_fast_text_confidence_high(self):
        """Test high confidence for good native PDF"""
        from src.strategies.fast_text import FastTextExtractor
        from src.models.document_profile import DocumentProfile, OriginType, LayoutComplexity, DomainHint, ExtractionCost
        
        profile = DocumentProfile(
            doc_id="test",
            filename="test.pdf",
            origin_type=OriginType.NATIVE_DIGITAL,
            layout_complexity=LayoutComplexity.SINGLE_COLUMN,
            language="en",
            language_confidence=0.95,
            domain_hint=DomainHint.GENERAL,
            estimated_extraction_cost=ExtractionCost.FAST_TEXT_SUFFICIENT,
            total_pages=10,
            character_density=0.05,
            image_ratio=0.1,
            has_font_metadata=True,
            table_count_estimate=2
        )
        
        extractor = FastTextExtractor()
        confidence = extractor._calculate_confidence(profile, [], [])
        assert confidence > 0.7
    
    def test_fast_text_confidence_low(self):
        """Test low confidence for poor quality PDF"""
        from src.strategies.fast_text import FastTextExtractor
        from src.models.document_profile import DocumentProfile, OriginType, LayoutComplexity, DomainHint, ExtractionCost
        
        profile = DocumentProfile(
            doc_id="test",
            filename="test.pdf",
            origin_type=OriginType.SCANNED_IMAGE,
            layout_complexity=LayoutComplexity.MIXED,
            language="en",
            language_confidence=0.95,
            domain_hint=DomainHint.GENERAL,
            estimated_extraction_cost=ExtractionCost.NEEDS_VISION_MODEL,
            total_pages=10,
            character_density=0.001,
            image_ratio=0.9,
            has_font_metadata=False,
            table_count_estimate=0
        )
        
        extractor = FastTextExtractor()
        confidence = extractor._calculate_confidence(profile, [], [])
        assert confidence < 0.7
