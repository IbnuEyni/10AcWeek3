"""List detection for semantic chunking Rule 3"""

import re
from typing import List, Tuple
from ..models.extracted_document import TextBlock

class ListDetector:
    """Detect and preserve list structures"""
    
    # Patterns for list detection
    BULLET_PATTERN = re.compile(r'^\s*[•●○■□▪▫–—-]\s+')
    NUMBERED_PATTERN = re.compile(r'^\s*(\d+|[a-z]|[A-Z]|[ivxIVX]+)[.)]\s+')
    
    def detect_list(self, blocks: List[TextBlock]) -> List[Tuple[int, int]]:
        """Detect list boundaries in text blocks
        
        Returns:
            List of (start_idx, end_idx) tuples for each list
        """
        lists = []
        current_list_start = None
        
        for idx, block in enumerate(blocks):
            lines = block.content.split('\n')
            is_list_block = any(
                self.BULLET_PATTERN.match(line) or self.NUMBERED_PATTERN.match(line)
                for line in lines if line.strip()
            )
            
            if is_list_block:
                if current_list_start is None:
                    current_list_start = idx
            else:
                if current_list_start is not None:
                    lists.append((current_list_start, idx - 1))
                    current_list_start = None
        
        # Close final list
        if current_list_start is not None:
            lists.append((current_list_start, len(blocks) - 1))
        
        return lists
    
    def is_list_item(self, text: str) -> bool:
        """Check if text is a list item"""
        lines = text.strip().split('\n')
        if not lines:
            return False
        first_line = lines[0].strip()
        return bool(self.BULLET_PATTERN.match(first_line) or self.NUMBERED_PATTERN.match(first_line))
