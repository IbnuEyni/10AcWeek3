"""Multi-column layout detection and reading order correction"""

from typing import List, Tuple, Dict
from ..models.extracted_document import TextBlock, BoundingBox
from ..logging_config import get_logger

logger = get_logger("column_detector")


class ColumnDetector:
    """Detect and handle multi-column layouts"""
    
    MIN_COLUMN_GAP = 30  # Minimum gap between columns in pixels
    MIN_BLOCKS_PER_COLUMN = 3  # Minimum blocks to consider a column
    
    def detect_columns(self, text_blocks: List[TextBlock], page: int) -> List[Tuple[float, float]]:
        """
        Detect column boundaries on a page
        
        Args:
            text_blocks: Text blocks from the page
            page: Page number
            
        Returns:
            List of (x_start, x_end) tuples for each column
        """
        # Filter blocks for this page
        page_blocks = [b for b in text_blocks if b.bbox.page == page]
        
        if len(page_blocks) < self.MIN_BLOCKS_PER_COLUMN * 2:
            # Not enough blocks for multi-column
            return []
        
        # Get x-coordinates of all blocks
        x_coords = [(b.bbox.x0, b.bbox.x1) for b in page_blocks]
        
        # Find gaps in x-coordinates
        gaps = self._find_vertical_gaps(x_coords)
        
        if not gaps:
            return []
        
        # Convert gaps to column boundaries
        columns = self._gaps_to_columns(gaps, x_coords)
        
        logger.debug(f"Detected {len(columns)} columns on page {page}")
        return columns
    
    def _find_vertical_gaps(self, x_coords: List[Tuple[float, float]]) -> List[float]:
        """Find vertical gaps that might separate columns"""
        # Get all x positions
        all_x = []
        for x0, x1 in x_coords:
            all_x.extend([x0, x1])
        
        if not all_x:
            return []
        
        # Sort and find gaps
        all_x.sort()
        gaps = []
        
        for i in range(len(all_x) - 1):
            gap = all_x[i + 1] - all_x[i]
            if gap > self.MIN_COLUMN_GAP:
                # Gap center
                gap_center = (all_x[i] + all_x[i + 1]) / 2
                gaps.append(gap_center)
        
        return gaps
    
    def _gaps_to_columns(self, gaps: List[float], x_coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Convert gaps to column boundaries"""
        if not x_coords:
            return []
        
        # Get page boundaries
        min_x = min(x0 for x0, _ in x_coords)
        max_x = max(x1 for _, x1 in x_coords)
        
        # Create columns
        columns = []
        boundaries = [min_x] + sorted(gaps) + [max_x]
        
        for i in range(len(boundaries) - 1):
            columns.append((boundaries[i], boundaries[i + 1]))
        
        return columns
    
    def reorder_by_columns(self, text_blocks: List[TextBlock], page: int) -> List[TextBlock]:
        """
        Reorder text blocks by column reading order
        
        Args:
            text_blocks: Text blocks to reorder
            page: Page number
            
        Returns:
            Reordered text blocks
        """
        # Detect columns
        columns = self.detect_columns(text_blocks, page)
        
        if not columns:
            # No columns detected, return original order
            return text_blocks
        
        # Assign blocks to columns
        page_blocks = [b for b in text_blocks if b.bbox.page == page]
        other_blocks = [b for b in text_blocks if b.bbox.page != page]
        
        column_blocks = {i: [] for i in range(len(columns))}
        
        for block in page_blocks:
            col_idx = self._assign_to_column(block, columns)
            if col_idx is not None:
                column_blocks[col_idx].append(block)
        
        # Sort within each column (top to bottom)
        reordered = []
        for col_idx in sorted(column_blocks.keys()):
            col_blocks = sorted(column_blocks[col_idx], key=lambda b: b.bbox.y0)
            reordered.extend(col_blocks)
        
        # Update reading order
        for idx, block in enumerate(reordered):
            block.reading_order = idx
        
        # Combine with other pages
        result = other_blocks + reordered
        
        logger.info(f"Reordered {len(reordered)} blocks across {len(columns)} columns on page {page}")
        return result
    
    def _assign_to_column(self, block: TextBlock, columns: List[Tuple[float, float]]) -> int:
        """Assign block to a column based on x-coordinate"""
        block_center = (block.bbox.x0 + block.bbox.x1) / 2
        
        for idx, (col_start, col_end) in enumerate(columns):
            if col_start <= block_center <= col_end:
                return idx
        
        # Fallback: assign to nearest column
        distances = [abs(block_center - (col_start + col_end) / 2) 
                    for col_start, col_end in columns]
        return distances.index(min(distances))
    
    def is_multi_column(self, text_blocks: List[TextBlock], page: int) -> bool:
        """Check if page has multi-column layout"""
        columns = self.detect_columns(text_blocks, page)
        return len(columns) > 1
