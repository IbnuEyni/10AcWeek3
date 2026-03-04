"""Enhanced table extraction with structure preservation"""

from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel
from ..models.extracted_document import BoundingBox
from ..logging_config import get_logger

logger = get_logger("enhanced_table")


class TableCell(BaseModel):
    """Enhanced table cell with span support"""
    content: str
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    bbox: Optional[BoundingBox] = None


class EnhancedTable(BaseModel):
    """Table with preserved structure"""
    table_id: str
    cells: List[TableCell]
    num_rows: int
    num_cols: int
    bbox: BoundingBox
    has_headers: bool = False
    structure_type: str = "simple"  # simple, nested, complex


class EnhancedTableExtractor:
    """Extract tables with structure preservation"""
    
    def extract_table(self, table_data: List[List[str]], bbox: BoundingBox, table_id: str) -> EnhancedTable:
        """
        Extract table with enhanced structure
        
        Args:
            table_data: Raw table data (list of rows)
            bbox: Table bounding box
            table_id: Unique table identifier
            
        Returns:
            EnhancedTable with structure preserved
        """
        if not table_data:
            return None
        
        num_rows = len(table_data)
        num_cols = max(len(row) for row in table_data) if table_data else 0
        
        # Convert to cells
        cells = []
        for row_idx, row in enumerate(table_data):
            for col_idx, cell_content in enumerate(row):
                cell = TableCell(
                    content=str(cell_content) if cell_content else "",
                    row=row_idx,
                    col=col_idx,
                    is_header=self._is_header_cell(row_idx, col_idx, cell_content)
                )
                cells.append(cell)
        
        # Detect structure
        has_headers = any(cell.is_header for cell in cells)
        structure_type = self._classify_structure(cells, num_rows, num_cols)
        
        table = EnhancedTable(
            table_id=table_id,
            cells=cells,
            num_rows=num_rows,
            num_cols=num_cols,
            bbox=bbox,
            has_headers=has_headers,
            structure_type=structure_type
        )
        
        logger.debug(f"Extracted table {table_id}: {num_rows}x{num_cols}, type={structure_type}")
        return table
    
    def _is_header_cell(self, row: int, col: int, content: str) -> bool:
        """Detect if cell is a header"""
        # First row is usually header
        if row == 0:
            return True
        
        # Check for header indicators
        if content and isinstance(content, str):
            content_lower = content.lower().strip()
            # Empty or very short cells in first row
            if row == 0 and len(content_lower) < 3:
                return True
            # Common header words
            header_words = ['total', 'name', 'date', 'amount', 'description', 'id', 'no']
            if any(word in content_lower for word in header_words):
                return True
        
        return False
    
    def _classify_structure(self, cells: List[TableCell], num_rows: int, num_cols: int) -> str:
        """Classify table structure complexity"""
        # Simple: single header row, uniform structure
        if num_rows <= 3 or num_cols <= 3:
            return "simple"
        
        # Check for nested headers (multiple header rows)
        header_rows = sum(1 for cell in cells if cell.is_header and cell.row < 2)
        if header_rows > num_cols:
            return "nested"
        
        # Complex: large tables
        if num_rows > 20 or num_cols > 10:
            return "complex"
        
        return "simple"
    
    def detect_merged_cells(self, table_data: List[List[str]]) -> List[Tuple[int, int, int, int]]:
        """
        Detect merged cells (simplified heuristic)
        
        Returns:
            List of (row, col, row_span, col_span) tuples
        """
        merged = []
        
        # Look for empty cells that might indicate merges
        for row_idx, row in enumerate(table_data):
            for col_idx, cell in enumerate(row):
                if not cell or cell.strip() == "":
                    # Check if previous cell might be merged
                    if col_idx > 0 and table_data[row_idx][col_idx-1]:
                        merged.append((row_idx, col_idx-1, 1, 2))
        
        return merged
    
    def to_markdown(self, table: EnhancedTable) -> str:
        """Convert table to markdown format"""
        if not table.cells:
            return ""
        
        # Build markdown table
        lines = []
        
        # Group cells by row
        rows = {}
        for cell in table.cells:
            if cell.row not in rows:
                rows[cell.row] = []
            rows[cell.row].append(cell)
        
        # Sort and format
        for row_idx in sorted(rows.keys()):
            row_cells = sorted(rows[row_idx], key=lambda c: c.col)
            line = "| " + " | ".join(c.content for c in row_cells) + " |"
            lines.append(line)
            
            # Add separator after header
            if row_idx == 0 and any(c.is_header for c in row_cells):
                separator = "| " + " | ".join("---" for _ in row_cells) + " |"
                lines.append(separator)
        
        return "\n".join(lines)
