import pdfplumber
from typing import Dict, Tuple
from pathlib import Path


class PDFAnalyzer:
    """Analyze PDF characteristics for triage"""
    
    @staticmethod
    def analyze_document(pdf_path: str) -> Dict:
        """Analyze PDF and return metrics for classification"""
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            char_counts = []
            image_ratios = []
            has_fonts = False
            table_count = 0
            
            for page in pdf.pages:
                # Character density
                text = page.extract_text() or ""
                char_count = len(text.strip())
                page_area = page.width * page.height
                char_counts.append(char_count / page_area if page_area > 0 else 0)
                
                # Image ratio
                images = page.images
                image_area = sum(img['width'] * img['height'] for img in images)
                image_ratios.append(image_area / page_area if page_area > 0 else 0)
                
                # Font metadata
                if not has_fonts and page.chars:
                    has_fonts = True
                
                # Table detection
                tables = page.find_tables()
                table_count += len(tables)
            
            avg_char_density = sum(char_counts) / len(char_counts) if char_counts else 0
            avg_image_ratio = sum(image_ratios) / len(image_ratios) if image_ratios else 0
            
            return {
                "total_pages": total_pages,
                "character_density": avg_char_density,
                "image_ratio": avg_image_ratio,
                "has_font_metadata": has_fonts,
                "table_count_estimate": table_count,
                "page_char_densities": char_counts,
                "page_image_ratios": image_ratios
            }
    
    @staticmethod
    def detect_origin_type(metrics: Dict) -> Tuple[str, float]:
        """Detect if PDF is native digital or scanned"""
        char_density = metrics["character_density"]
        has_fonts = metrics["has_font_metadata"]
        image_ratio = metrics["image_ratio"]
        
        # Thresholds
        MIN_CHAR_DENSITY = 0.01
        MAX_IMAGE_RATIO = 0.5
        
        if has_fonts and char_density > MIN_CHAR_DENSITY and image_ratio < MAX_IMAGE_RATIO:
            return "native_digital", 0.9
        elif not has_fonts or char_density < MIN_CHAR_DENSITY / 2:
            return "scanned_image", 0.85
        else:
            return "mixed", 0.7
    
    @staticmethod
    def detect_layout_complexity(metrics: Dict) -> str:
        """Detect layout complexity"""
        table_count = metrics["table_count_estimate"]
        
        if table_count > 10:
            return "table_heavy"
        elif table_count > 0:
            return "mixed"
        else:
            return "single_column"
