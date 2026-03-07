"""PDF analysis utilities with enterprise-level error handling"""

import pdfplumber
from typing import Dict, Tuple, List
from pathlib import Path
from ..logging_config import get_logger
from ..exceptions import DocumentValidationError, TriageError
from ..validation_utils import validate_pdf_file
from ..utils.docling_helper import DoclingHelper

logger = get_logger("pdf_analyzer")


class PDFAnalyzer:
    """Analyze PDF characteristics using Short-Circuit Waterfall algorithm"""
    
    def __init__(self, origin_config: dict = None, layout_config: dict = None):
        """Initialize with config thresholds"""
        self.origin_config = origin_config or {
            'min_char_density': 0.01,
            'max_image_ratio': 0.8,  # 80% threshold for hybrid detection
            'font_metadata_weight': 0.3
        }
        self.layout_config = layout_config or {
            'table_heavy_threshold': 10,
            'multi_column_threshold': 2
        }
        # Lazy load Docling only if needed (Pass 3)
        self._docling_helper = None
        logger.info("PDFAnalyzer initialized with Short-Circuit Waterfall")
    
    @staticmethod
    def analyze_document(pdf_path: str) -> Dict[str, any]:
        """
        Analyze PDF using Short-Circuit Waterfall algorithm
        
        Pass 1 (Microsecond): PyMuPDF font check
        Pass 2 (Millisecond): pdfplumber image ratio
        Pass 3 (Second): Docling layout detection (only if native digital)
        
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
            # PASS 1: Microsecond Check (PyMuPDF) - Font metadata
            import fitz
            doc = fitz.open(path)
            total_pages = doc.page_count
            first_page = doc[0]
            fonts = first_page.get_fonts()
            doc.close()
            
            has_fonts = len(fonts) > 0
            logger.debug(f"Pass 1 (PyMuPDF): fonts={len(fonts)}")
            
            # Short-circuit: No fonts = scanned image
            if not has_fonts:
                logger.info("SHORT-CIRCUIT: No fonts detected → scanned_image")
                return {
                    "total_pages": total_pages,
                    "character_density": 0.0,
                    "image_ratio": 1.0,
                    "has_font_metadata": False,
                    "table_count_estimate": 0,
                    "page_char_densities": [],
                    "page_image_ratios": [],
                    "has_form_fields": False,
                    "is_mixed_mode": False,
                    "short_circuit": "pass1_no_fonts"
                }
            
            # PASS 2: Millisecond Check (pdfplumber) - Image ratio
            with pdfplumber.open(path) as pdf:
                total_pages = len(pdf.pages)
                logger.debug(f"Document has {total_pages} pages")
                
                char_counts: List[float] = []
                image_ratios: List[float] = []
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages[:5]):  # Sample first 5 pages only
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
                        
                        # Table detection (lightweight)
                        tables = page.find_tables()
                        table_count += len(tables)
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing page {page_num}: {e}")
                        continue
                
                avg_char_density = sum(char_counts) / len(char_counts) if char_counts else 0
                avg_image_ratio = sum(image_ratios) / len(image_ratios) if image_ratios else 0
                
                logger.debug(f"Pass 2 (pdfplumber): image_ratio={avg_image_ratio:.2f}")
                
                # Short-circuit: >80% image = hybrid/scanned
                if avg_image_ratio > 0.8:
                    logger.info(f"SHORT-CIRCUIT: Image ratio {avg_image_ratio:.2f} > 0.8 → hybrid")
                    return {
                        "total_pages": total_pages,
                        "character_density": avg_char_density,
                        "image_ratio": avg_image_ratio,
                        "has_font_metadata": has_fonts,
                        "table_count_estimate": table_count,
                        "page_char_densities": char_counts,
                        "page_image_ratios": image_ratios,
                        "has_form_fields": False,
                        "is_mixed_mode": True,
                        "short_circuit": "pass2_high_image_ratio"
                    }
                
                # PASS 3: No short-circuit - document is native digital
                # Return full metrics for layout detection
                logger.debug("Pass 3: Native digital confirmed, proceeding to layout detection")
                
                metrics = {
                    "total_pages": total_pages,
                    "character_density": avg_char_density,
                    "image_ratio": avg_image_ratio,
                    "has_font_metadata": has_fonts,
                    "table_count_estimate": table_count,
                    "page_char_densities": char_counts,
                    "page_image_ratios": image_ratios,
                    "has_form_fields": any(getattr(page, 'annots', []) for page in pdf.pages),
                    "is_mixed_mode": avg_char_density > 0 and avg_image_ratio > 0.1,
                    "short_circuit": None
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
        Detect if PDF is native digital or scanned (uses short-circuit results)
        
        Args:
            metrics: Analysis metrics from analyze_document
            
        Returns:
            Tuple of (origin_type, confidence)
        """
        # Check if short-circuited
        short_circuit = metrics.get("short_circuit")
        
        if short_circuit == "pass1_no_fonts":
            logger.info("Origin: scanned_image (Pass 1 short-circuit)")
            return "scanned_image", 0.95
        
        if short_circuit == "pass2_high_image_ratio":
            logger.info("Origin: hybrid (Pass 2 short-circuit)")
            return "mixed", 0.90
        
        # Pass 3: Native digital classification
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
        
        # Native digital (confirmed by passing all checks)
        if has_fonts and char_density > self.origin_config['min_char_density']:
            return "native_digital", 0.9
        
        # Fallback
        return "mixed", 0.7
    
    def detect_layout_complexity(self, metrics: Dict[str, any], pdf_path: str = None) -> tuple[str, float]:
        """
        Detect layout complexity (Pass 3: Only for native digital PDFs)
        Uses Docling fast mode if available and document passed short-circuit checks
        
        Args:
            metrics: Analysis metrics from analyze_document
            pdf_path: Optional path to PDF for Docling analysis
            
        Returns:
            Tuple of (layout complexity classification, confidence)
        """
        # Check if short-circuited (scanned/hybrid documents)
        short_circuit = metrics.get("short_circuit")
        if short_circuit:
            logger.debug(f"Skipping layout detection (short-circuited: {short_circuit})")
            return "single_column", 0.6  # Default for scanned/hybrid
        
        # PASS 3: Docling fast mode for native digital PDFs only
        if pdf_path:
            # Lazy load Docling
            if self._docling_helper is None:
                self._docling_helper = DoclingHelper(use_fast_mode=True)
            
            if self._docling_helper.use_docling:
                try:
                    logger.debug("Pass 3 (Docling): Detecting layout complexity")
                    layout_info = self._docling_helper.classify_page_layout(pdf_path, page_num=0)
                    
                    if layout_info['multi_column']:
                        return "multi_column", 0.85
                    elif layout_info['table_heavy']:
                        return "table_heavy", 0.85
                    elif layout_info['table_count'] > 0:
                        return "mixed", 0.75
                    else:
                        return "single_column", 0.8
                except Exception as e:
                    logger.warning(f"Docling layout detection failed, falling back to pdfplumber: {e}")
        
        # Fallback to pdfplumber metrics
        table_count = metrics["table_count_estimate"]
        
        if table_count > self.layout_config['table_heavy_threshold']:
            confidence = min(0.9, 0.7 + (table_count - self.layout_config['table_heavy_threshold']) * 0.02)
            return "table_heavy", confidence
        elif table_count > 0:
            confidence = 0.7 + (table_count * 0.05)
            return "mixed", min(confidence, 0.85)
        else:
            return "single_column", 0.8
