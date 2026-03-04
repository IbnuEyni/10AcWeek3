"""Figure and image extraction with metadata"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib
from ..models.extracted_document import BoundingBox, Figure
from ..logging_config import get_logger

logger = get_logger("figure_extractor")


class FigureExtractor:
    """Extract figures and images from PDFs"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(".refinery/figures")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_figures(self, pdf_path: str, doc_id: str) -> List[Figure]:
        """
        Extract all figures from PDF
        
        Args:
            pdf_path: Path to PDF file
            doc_id: Document identifier
            
        Returns:
            List of extracted figures
        """
        import pdfplumber
        
        figures = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_figures = self._extract_page_figures(page, page_num, doc_id)
                    figures.extend(page_figures)
            
            logger.info(f"Extracted {len(figures)} figures from {doc_id}")
            
        except Exception as e:
            logger.error(f"Figure extraction failed: {e}")
        
        return figures
    
    def _extract_page_figures(self, page, page_num: int, doc_id: str) -> List[Figure]:
        """Extract figures from single page"""
        figures = []
        
        try:
            images = page.images
            
            for img_idx, img in enumerate(images):
                # Create figure ID
                fig_id = f"{doc_id}_p{page_num}_fig{img_idx}"
                
                # Extract bounding box
                bbox = BoundingBox(
                    x0=float(img.get('x0', 0)),
                    y0=float(img.get('y0', 0)),
                    x1=float(img.get('x1', 0)),
                    y1=float(img.get('y1', 0)),
                    page=page_num
                )
                
                # Extract metadata
                metadata = {
                    'width': img.get('width', 0),
                    'height': img.get('height', 0),
                    'object_type': img.get('object_type', 'unknown'),
                }
                
                # Create figure
                figure = Figure(
                    figure_id=fig_id,
                    bbox=bbox,
                    page=page_num,
                    metadata=metadata
                )
                
                # Try to save image
                try:
                    image_path = self._save_figure(page, img, doc_id, page_num, img_idx)
                    figure.image_path = image_path
                except Exception as e:
                    logger.warning(f"Could not save figure {fig_id}: {e}")
                
                figures.append(figure)
        
        except Exception as e:
            logger.warning(f"Error extracting figures from page {page_num}: {e}")
        
        return figures
    
    def _save_figure(self, page, img_info: Dict, doc_id: str, page_num: int, img_idx: int) -> Path:
        """Save figure image to disk"""
        from PIL import Image
        import io
        
        # Create doc-specific directory
        doc_dir = self.output_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = f"p{page_num}_fig{img_idx}.png"
        output_path = doc_dir / filename
        
        try:
            # Get image from page
            im = page.within_bbox((img_info['x0'], img_info['y0'], img_info['x1'], img_info['y1']))
            img_obj = im.to_image(resolution=150)
            
            # Save as PIL Image
            img_obj.save(str(output_path), format='PNG')
            logger.debug(f"Figure saved: {output_path}")
            
        except Exception as e:
            logger.warning(f"Could not save image: {e}")
            # Create placeholder if actual save fails
            pass
        
        return output_path
    
    def get_figure_hash(self, image_data: bytes) -> str:
        """Generate hash for image deduplication"""
        return hashlib.md5(image_data).hexdigest()
