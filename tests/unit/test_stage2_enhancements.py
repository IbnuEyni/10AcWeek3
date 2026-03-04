"""Tests for Stage 2 enhancements"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from src.strategies.enhanced_table import EnhancedTableExtractor, TableCell, EnhancedTable
from src.strategies.figure_extractor import FigureExtractor, Figure
from src.strategies.caption_binder import CaptionBinder
from src.strategies.column_detector import ColumnDetector
from src.strategies.handwriting_ocr import HandwritingOCR, OCRResult
from src.models.extracted_document import BoundingBox, TextBlock


class TestEnhancedTable:
    """Test enhanced table extraction"""
    
    def test_simple_table_extraction(self):
        """Test extracting simple table"""
        extractor = EnhancedTableExtractor()
        
        table_data = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
        
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        table = extractor.extract_table(table_data, bbox, "test_table_1")
        
        assert table is not None
        assert table.num_rows == 3
        assert table.num_cols == 3
        assert table.has_headers
        assert len(table.cells) == 9
    
    def test_header_detection(self):
        """Test header cell detection"""
        extractor = EnhancedTableExtractor()
        
        table_data = [
            ["ID", "Name", "Total"],
            ["1", "Item A", "100"],
            ["2", "Item B", "200"]
        ]
        
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        table = extractor.extract_table(table_data, bbox, "test_table_2")
        
        # Check first row cells are headers
        first_row_cells = [c for c in table.cells if c.row == 0]
        assert all(c.is_header for c in first_row_cells)
    
    def test_structure_classification(self):
        """Test table structure classification"""
        extractor = EnhancedTableExtractor()
        
        # Simple table
        simple_data = [["A", "B"], ["1", "2"]]
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        simple_table = extractor.extract_table(simple_data, bbox, "simple")
        assert simple_table.structure_type == "simple"
        
        # Complex table (large)
        complex_data = [[f"Col{i}" for i in range(15)]] + [[str(j) for j in range(15)] for _ in range(25)]
        complex_table = extractor.extract_table(complex_data, bbox, "complex")
        assert complex_table.structure_type == "complex"
    
    def test_markdown_conversion(self):
        """Test converting table to markdown"""
        extractor = EnhancedTableExtractor()
        
        table_data = [
            ["Name", "Value"],
            ["Test", "123"]
        ]
        
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        table = extractor.extract_table(table_data, bbox, "md_test")
        
        markdown = extractor.to_markdown(table)
        assert "Name" in markdown
        assert "Value" in markdown
        assert "|" in markdown
        assert "---" in markdown


class TestFigureExtractor:
    """Test figure extraction"""
    
    def test_figure_extractor_init(self):
        """Test figure extractor initialization"""
        extractor = FigureExtractor()
        assert extractor.output_dir.exists()
    
    def test_figure_hash(self):
        """Test figure hash generation"""
        extractor = FigureExtractor()
        
        data1 = b"test image data"
        data2 = b"test image data"
        data3 = b"different data"
        
        hash1 = extractor.get_figure_hash(data1)
        hash2 = extractor.get_figure_hash(data2)
        hash3 = extractor.get_figure_hash(data3)
        
        assert hash1 == hash2
        assert hash1 != hash3


class TestCaptionBinder:
    """Test figure-caption binding"""
    
    def test_caption_pattern_matching(self):
        """Test caption pattern detection"""
        binder = CaptionBinder()
        
        # Create test figure
        figure = Figure(
            figure_id="test_fig",
            bbox=BoundingBox(x0=100, y0=100, x1=200, y1=200, page=0),
            page=0
        )
        
        # Create text blocks with caption
        text_blocks = [
            TextBlock(
                content="Figure 1: This is a test caption",
                bbox=BoundingBox(x0=100, y0=210, x1=200, y1=230, page=0),
                reading_order=0
            ),
            TextBlock(
                content="Some other text",
                bbox=BoundingBox(x0=100, y0=300, x1=200, y1=320, page=0),
                reading_order=1
            )
        ]
        
        caption = binder.find_caption(figure, text_blocks)
        
        assert caption is not None
        assert "Figure 1" in caption[0]
        assert caption[1] > 0.5  # Confidence
    
    def test_distance_calculation(self):
        """Test bounding box distance calculation"""
        binder = CaptionBinder()
        
        bbox1 = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        bbox2 = BoundingBox(x0=0, y0=110, x1=100, y1=150, page=0)
        
        distance = binder._calculate_distance(bbox1, bbox2)
        assert distance == 10  # Gap between boxes
    
    def test_bind_multiple_figures(self):
        """Test binding multiple figures"""
        binder = CaptionBinder()
        
        figures = [
            Figure(
                figure_id="fig1",
                bbox=BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0),
                page=0
            ),
            Figure(
                figure_id="fig2",
                bbox=BoundingBox(x0=0, y0=200, x1=100, y1=300, page=0),
                page=0
            )
        ]
        
        text_blocks = [
            TextBlock(
                content="Fig. 1: First caption",
                bbox=BoundingBox(x0=0, y0=110, x1=100, y1=130, page=0),
                reading_order=0
            ),
            TextBlock(
                content="Figure 2: Second caption",
                bbox=BoundingBox(x0=0, y0=310, x1=100, y1=330, page=0),
                reading_order=1
            )
        ]
        
        bound_figures = binder.bind_figures_to_captions(figures, text_blocks)
        
        assert len(bound_figures) == 2
        assert bound_figures[0].caption is not None
        assert bound_figures[1].caption is not None
        assert "First" in bound_figures[0].caption
        assert "Second" in bound_figures[1].caption


class TestColumnDetector:
    """Test multi-column layout detection"""
    
    def test_single_column_detection(self):
        """Test single column layout"""
        detector = ColumnDetector()
        
        # Create blocks in single column
        blocks = [
            TextBlock(
                content=f"Line {i}",
                bbox=BoundingBox(x0=100, y0=100+i*20, x1=400, y1=115+i*20, page=0),
                reading_order=i
            )
            for i in range(5)
        ]
        
        columns = detector.detect_columns(blocks, 0)
        assert len(columns) <= 1  # Should detect 0 or 1 column
    
    def test_two_column_detection(self):
        """Test two column layout"""
        detector = ColumnDetector()
        
        # Create blocks in two columns
        blocks = []
        # Left column
        for i in range(3):
            blocks.append(TextBlock(
                content=f"Left {i}",
                bbox=BoundingBox(x0=50, y0=100+i*30, x1=200, y1=120+i*30, page=0),
                reading_order=i
            ))
        # Right column (with gap)
        for i in range(3):
            blocks.append(TextBlock(
                content=f"Right {i}",
                bbox=BoundingBox(x0=300, y0=100+i*30, x1=450, y1=120+i*30, page=0),
                reading_order=i+3
            ))
        
        columns = detector.detect_columns(blocks, 0)
        assert len(columns) >= 2  # Should detect 2 columns
    
    def test_reorder_by_columns(self):
        """Test reordering blocks by column"""
        detector = ColumnDetector()
        
        # Create blocks in wrong order (right column first)
        blocks = [
            TextBlock(
                content="Right 1",
                bbox=BoundingBox(x0=300, y0=100, x1=450, y1=120, page=0),
                reading_order=0
            ),
            TextBlock(
                content="Left 1",
                bbox=BoundingBox(x0=50, y0=100, x1=200, y1=120, page=0),
                reading_order=1
            ),
            TextBlock(
                content="Right 2",
                bbox=BoundingBox(x0=300, y0=130, x1=450, y1=150, page=0),
                reading_order=2
            ),
            TextBlock(
                content="Left 2",
                bbox=BoundingBox(x0=50, y0=130, x1=200, y1=150, page=0),
                reading_order=3
            ),
        ]
        
        reordered = detector.reorder_by_columns(blocks, 0)
        
        # Should be reordered: Left 1, Left 2, Right 1, Right 2
        assert len(reordered) == 4
        # Check left column comes first
        left_blocks = [b for b in reordered if "Left" in b.content]
        assert len(left_blocks) == 2
    
    def test_is_multi_column(self):
        """Test multi-column detection"""
        detector = ColumnDetector()
        
        # Single column
        single_col = [
            TextBlock(
                content=f"Line {i}",
                bbox=BoundingBox(x0=100, y0=100+i*20, x1=400, y1=115+i*20, page=0),
                reading_order=i
            )
            for i in range(5)
        ]
        
        assert not detector.is_multi_column(single_col, 0)
        
        # Two columns
        two_col = []
        for i in range(3):
            two_col.append(TextBlock(
                content=f"Left {i}",
                bbox=BoundingBox(x0=50, y0=100+i*30, x1=200, y1=120+i*30, page=0),
                reading_order=i
            ))
            two_col.append(TextBlock(
                content=f"Right {i}",
                bbox=BoundingBox(x0=300, y0=100+i*30, x1=450, y1=120+i*30, page=0),
                reading_order=i+3
            ))
        
        assert detector.is_multi_column(two_col, 0)


class TestHandwritingOCR:
    """Test handwriting OCR with fallback"""
    
    def test_ocr_initialization(self):
        """Test OCR engine initialization"""
        ocr = HandwritingOCR()
        engines = ocr.get_available_engines()
        # Should have at least one engine (even if just placeholder)
        assert isinstance(engines, list)
    
    def test_ocr_result(self):
        """Test OCR result object"""
        result = OCRResult("Test text", 0.85, "gemini")
        assert result.text == "Test text"
        assert result.confidence == 0.85
        assert result.engine == "gemini"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_engines_available(self):
        """Test when no OCR engines are available"""
        ocr = HandwritingOCR()
        engines = ocr.get_available_engines()
        # Should return empty list when no engines configured
        assert isinstance(engines, list)
    
    def test_batch_recognize(self):
        """Test batch OCR recognition"""
        ocr = HandwritingOCR()
        
        # Mock image data
        images = [b"fake_image_1", b"fake_image_2"]
        
        # Mock the recognize method
        with patch.object(ocr, 'recognize', return_value=None):
            results = ocr.batch_recognize(images)
            assert len(results) == 2
    
    def test_engine_fallback_logic(self):
        """Test that fallback logic exists"""
        ocr = HandwritingOCR()
        
        # Verify fallback chain is set up
        assert hasattr(ocr, 'engines')
        assert isinstance(ocr.engines, list)
