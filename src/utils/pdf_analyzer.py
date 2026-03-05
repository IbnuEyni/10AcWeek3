"""PDF analysis utilities with enterprise-level error handling"""

import pdfplumber
from typing import Dict, Tuple, List
from pathlib import Path
from ..logging_config import get_logger
from ..exceptions import DocumentValidationError, TriageError
from ..validators import validate_pdf_file
from ..utils.docling_helper import DoclingHelper

logger = get_logger("pdf_analyzer")


class PDFAnalyzer:
    """Analyze PDF characteristics for triage"""
    
    def __init__(self, origin_config: dict = None, layout_config: dict = None):
        """Initialize with config thresholds"""
        self.origin_config = origin_config or {
            'min_char_density': 0.01,
            'max_image_ratio': 0.5,
            'font_metadata_weight': 0.3
        }
        self.layout_config = layout_config or {
            'table_heavy_threshold': 10,
            'multi_column_threshold': 2
        }
        # Don't initialize Docling in analyzer - too slow
        # self.docling_helper = DoclingHelper()
    
    @staticmethod
    def analyze_document(pdf_path: str) -> Dict[str, any]:
        """
        Analyze PDF and return metrics for classification
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary of analysis metrics
            
        Raises:
            DocumentValidationError: If PDF is invalid
            TriageError: If analysis fails
        """
        logger.info(f"Analyzing document: {pdf_path}")
        
        # Validate input
        path = validate_pdf_file(pdf_path)
        
        try:
            with pdfplumber.open(path) as pdf:
                total_pages = len(pdf.pages)
                logger.debug(f"Document has {total_pages} pages")
                
                char_counts: List[float] = []
                image_ratios: List[float] = []
                has_fonts = False
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        # Character density
                        text = page.extract_text() or ""
                        char_count = len(text.strip())
                        page_area = page.width * page.height
                        char_density = char_count / page_area if page_area > 0 else 0
                        char_counts.append(char_density)
                        
                        # Image ratio
                        images = page.images
                        image_area = sum(img['width'] * img['height'] for img in images)
                        image_ratio = image_area / page_area if page_area > 0 else 0
                        image_ratios.append(image_ratio)
                        
                        # Font metadata
                        if not has_fonts and page.chars:
                            has_fonts = True
                        
                        # Table detection
                        tables = page.find_tables()
                        table_count += len(tables)
                        
                        # Form field detection
                        form_fields = getattr(page, 'annots', []) or []
                        has_form_fields = len(form_fields) > 0
                        
                        # Mixed mode detection (text + images)
                        mixed_mode = char_density > 0 and image_ratio > 0.1
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing page {page_num}: {e}")
                        continue
                
                avg_char_density = sum(char_counts) / len(char_counts) if char_counts else 0
                avg_image_ratio = sum(image_ratios) / len(image_ratios) if image_ratios else 0
                
                metrics = {
                    "total_pages": total_pages,
                    "character_density": avg_char_density,
                    "image_ratio": avg_image_ratio,
                    "has_font_metadata": has_fonts,
                    "table_count_estimate": table_count,
                    "page_char_densities": char_counts,
                    "page_image_ratios": image_ratios,
                    "has_form_fields": any(getattr(page, 'annots', []) for page in pdf.pages),
                    "is_mixed_mode": avg_char_density > 0 and avg_image_ratio > 0.1
                }
                
                logger.info(f"Analysis complete: char_density={avg_char_density:.4f}, "
                           f"image_ratio={avg_image_ratio:.2f}, tables={table_count}")
                
                return metrics
                
        except DocumentValidationError:
            raise
        except Exception as e:
            raise TriageError(f"Failed to analyze document: {e}")
    
    def detect_origin_type(self, metrics: Dict[str, any]) -> Tuple[str, float]:
        """
        Detect if PDF is native digital or scanned
        
        Args:
            metrics: Analysis metrics from analyze_document
            
        Returns:
            Tuple of (origin_type, confidence)
        """
        char_density = metrics["character_density"]
        has_fonts = metrics["has_font_metadata"]
        image_ratio = metrics["image_ratio"]
        has_form_fields = metrics.get("has_form_fields", False)
        is_mixed_mode = metrics.get("is_mixed_mode", False)
        
        logger.debug(f"Detecting origin: char_density={char_density:.4f}, "
                    f"has_fonts={has_fonts}, image_ratio={image_ratio:.2f}, "
                    f"form_fields={has_form_fields}, mixed_mode={is_mixed_mode}")
        
        # Form-fillable PDFs
        if has_form_fields:
            return "form_fillable", 0.85
        
        # Mixed mode PDFs
        if is_mixed_mode and has_fonts:
            return "mixed", 0.75
        
        # Standard classification
        if has_fonts and char_density > self.origin_config['min_char_density'] and \
           image_ratio < self.origin_config['max_image_ratio']:
            return "native_digital", 0.9
        elif not has_fonts or char_density < self.origin_config['min_char_density'] / 2:
            return "scanned_image", 0.85
        else:
            return "mixed", 0.7
    
    def detect_layout_complexity(self, metrics: Dict[str, any]) -> tuple[str, float]:
        """
        Detect layout complexity
        
        Args:
            metrics: Analysis metrics from analyze_document
            
        Returns:
            Tuple of (layout complexity classification, confidence)
        """
        table_count = metrics["table_count_estimate"]
        
        if table_count > self.layout_config['table_heavy_threshold']:
            confidence = min(0.9, 0.7 + (table_count - self.layout_config['table_heavy_threshold']) * 0.02)
            return "table_heavy", confidence
        elif table_count > 0:
            confidence = 0.7 + (table_count * 0.05)
            return "mixed", min(confidence, 0.85)
        else:
            return "single_column", 0.8
