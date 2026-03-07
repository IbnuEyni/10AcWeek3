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
        domain, confidence = triage_agent._detect_domain("CBE_Annual_Report_2023.pdf")
        assert domain == DomainHint.FINANCIAL
        assert confidence > 0.5
    
    def test_domain_detection_legal(self, triage_agent):
        """Test legal domain detection"""
        domain, confidence = triage_agent._detect_domain("legal_contract_agreement.pdf")
        assert domain == DomainHint.LEGAL
        assert confidence > 0.5
    
    def test_domain_detection_technical(self, triage_agent):
        """Test technical domain detection"""
        domain, confidence = triage_agent._detect_domain("technical_specification.pdf")
        assert domain == DomainHint.TECHNICAL
        assert confidence > 0.5
    
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
    """Unit tests for PDF analysis with Short-Circuit Waterfall"""
    
    def test_short_circuit_pass1_no_fonts(self):
        """Test Pass 1 short-circuit: no fonts detected"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "character_density": 0.0,
            "has_font_metadata": False,
            "image_ratio": 1.0
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "scanned_image"
        assert confidence == 0.95
    
    def test_short_circuit_pass2_high_image_ratio(self):
        """Test Pass 2 short-circuit: >80% image ratio"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass2_high_image_ratio",
            "character_density": 0.01,
            "has_font_metadata": True,
            "image_ratio": 0.85
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "mixed"
        assert confidence == 0.90
    
    def test_no_short_circuit_native_digital(self):
        """Test Pass 3: native digital (no short-circuit)"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": None,
            "character_density": 0.05,
            "has_font_metadata": True,
            "image_ratio": 0.2,
            "has_form_fields": False,
            "is_mixed_mode": False
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "native_digital"
        assert confidence == 0.9
    
    def test_layout_complexity_skip_on_short_circuit(self):
        """Test layout detection skipped for short-circuited documents"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "table_count_estimate": 0
        }
        
        complexity, confidence = analyzer.detect_layout_complexity(metrics)
        assert complexity == "single_column"
        assert confidence == 0.6
    
    def test_layout_complexity_native_digital(self):
        """Test layout detection for native digital (Pass 3)"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": None,
            "table_count_estimate": 15
        }
        
        complexity, confidence = analyzer.detect_layout_complexity(metrics)
        assert complexity == "table_heavy"
        assert confidence > 0.7
    
    def test_origin_type_detection_digital(self):
        """Test detection of native digital PDF"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": None,
            "character_density": 0.05,
            "has_font_metadata": True,
            "image_ratio": 0.2,
            "has_form_fields": False,
            "is_mixed_mode": False
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "native_digital"
        assert confidence > 0.8
    
    def test_origin_type_detection_scanned(self):
        """Test detection of scanned PDF"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "character_density": 0.0,
            "has_font_metadata": False,
            "image_ratio": 1.0
        }
        
        origin_type, confidence = analyzer.detect_origin_type(metrics)
        assert origin_type == "scanned_image"
        assert confidence > 0.7
    
    def test_layout_complexity_detection_table_heavy(self):
        """Test detection of table-heavy layout"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": None,
            "table_count_estimate": 15
        }
        complexity, confidence = analyzer.detect_layout_complexity(metrics)
        assert complexity == "table_heavy"
        assert confidence > 0.7
    
    def test_layout_complexity_detection_simple(self):
        """Test detection of simple layout"""
        from src.utils.pdf_analyzer import PDFAnalyzer
        
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": None,
            "table_count_estimate": 0
        }
        complexity, confidence = analyzer.detect_layout_complexity(metrics)
        assert complexity == "single_column"
        assert confidence > 0.7


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
            origin_confidence=0.9,
            layout_confidence=0.8,
            domain_confidence=0.7,
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
            origin_confidence=0.8,
            layout_confidence=0.7,
            domain_confidence=0.6,
            character_density=0.001,
            image_ratio=0.9,
            has_font_metadata=False,
            table_count_estimate=0
        )
        
        extractor = FastTextExtractor()
        confidence = extractor._calculate_confidence(profile, [], [])
        assert confidence < 0.7
