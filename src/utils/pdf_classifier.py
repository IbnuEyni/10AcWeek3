"""PDF classifier to determine if native or scanned"""

from ..logging_config import get_logger

logger = get_logger("pdf_classifier")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not installed. Classification will default to scanned.")


class PDFClassifier:
    """Classify PDF as native digital or scanned image"""
    
    def __init__(self, text_threshold: int = 50):
        self.text_threshold = text_threshold
    
    def is_native_pdf(self, pdf_path: str) -> bool:
        """
        Check if PDF is native digital (has extractable text)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if native digital, False if scanned
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available, defaulting to scanned")
            return False
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first page
                if len(pdf.pages) == 0:
                    return False
                
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # If substantial text found, it's native
                if text and len(text.strip()) > self.text_threshold:
                    logger.info(f"{pdf_path} classified as NATIVE (text length: {len(text)})")
                    return True
                
                # Check second page if available
                if len(pdf.pages) > 1:
                    second_page = pdf.pages[1]
                    text = second_page.extract_text()
                    if text and len(text.strip()) > self.text_threshold:
                        logger.info(f"{pdf_path} classified as NATIVE (text on page 2)")
                        return True
                
                logger.info(f"{pdf_path} classified as SCANNED (insufficient text)")
                return False
                
        except Exception as e:
            logger.error(f"Classification failed for {pdf_path}: {e}")
            # Default to scanned if can't determine
            return False
    
    def get_document_stats(self, pdf_path: str) -> dict:
        """Get document statistics for classification"""
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available")
            return {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_text = 0
                total_images = 0
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        total_text += len(text)
                    
                    images = page.images
                    total_images += len(images)
                
                return {
                    'total_pages': len(pdf.pages),
                    'total_text_chars': total_text,
                    'total_images': total_images,
                    'avg_text_per_page': total_text / len(pdf.pages) if pdf.pages else 0,
                    'is_native': total_text > self.text_threshold * len(pdf.pages)
                }
        except Exception as e:
            logger.error(f"Failed to get stats for {pdf_path}: {e}")
            return {}
