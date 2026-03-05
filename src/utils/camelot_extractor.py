"""Camelot table extractor wrapper"""

from typing import List
from ..logging_config import get_logger
from ..models.extracted_document import Table, BoundingBox

logger = get_logger("camelot_extractor")

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logger.warning("Camelot not installed. Table extraction will be limited.")


class CamelotExtractor:
    """Table extraction using Camelot"""
    
    def extract_tables(self, pdf_path: str) -> List[Table]:
        """Extract tables from PDF"""
        if not CAMELOT_AVAILABLE:
            logger.warning("Camelot not available, skipping table extraction")
            return []
        
        tables = []
        
        try:
            # Try lattice mode first (tables with borders)
            camelot_tables = camelot.read_pdf(
                pdf_path,
                pages='all',
                flavor='lattice'
            )
            
            # If no tables found, try stream mode (tables without borders)
            if len(camelot_tables) == 0:
                camelot_tables = camelot.read_pdf(
                    pdf_path,
                    pages='all',
                    flavor='stream'
                )
            
            for idx, ct in enumerate(camelot_tables):
                # Extract table data
                df = ct.df
                
                # First row as headers
                headers = df.iloc[0].tolist() if len(df) > 0 else []
                
                # Remaining rows as data
                rows = df.iloc[1:].values.tolist() if len(df) > 1 else []
                
                # Get bounding box
                bbox = BoundingBox(
                    x0=ct._bbox[0] if hasattr(ct, '_bbox') else 0,
                    y0=ct._bbox[1] if hasattr(ct, '_bbox') else 0,
                    x1=ct._bbox[2] if hasattr(ct, '_bbox') else 0,
                    y1=ct._bbox[3] if hasattr(ct, '_bbox') else 0,
                    page=ct.page - 1  # Camelot uses 1-indexed pages
                )
                
                table = Table(
                    headers=headers,
                    rows=rows,
                    bbox=bbox,
                    table_id=f"table_{ct.page}_{idx}"
                )
                tables.append(table)
            
            logger.info(f"Extracted {len(tables)} tables using Camelot")
            
        except Exception as e:
            logger.error(f"Camelot table extraction failed: {e}")
        
        return tables
