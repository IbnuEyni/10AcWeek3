"""Figure-caption binding using spatial proximity and pattern matching"""

import re
from typing import List, Optional, Tuple
from .figure_extractor import Figure
from ..models.extracted_document import TextBlock
from ..logging_config import get_logger

logger = get_logger("caption_binder")


class CaptionBinder:
    """Bind figures to their captions"""
    
    CAPTION_PATTERNS = [
        r"Figure\s+(\d+)[:\.]?\s*(.*)",
        r"Fig\.\s+(\d+)[:\.]?\s*(.*)",
        r"Fig\s+(\d+)[:\.]?\s*(.*)",
        r"Image\s+(\d+)[:\.]?\s*(.*)",
        r"Exhibit\s+(\d+)[:\.]?\s*(.*)",
    ]
    
    MAX_DISTANCE = 100  # Maximum pixels between figure and caption
    
    def bind_figures_to_captions(self, figures: List[Figure], text_blocks: List[TextBlock]) -> List[Figure]:
        """
        Bind all figures to their captions
        
        Args:
            figures: List of extracted figures
            text_blocks: List of text blocks from document
            
        Returns:
            Figures with captions attached
        """
        for figure in figures:
            caption = self.find_caption(figure, text_blocks)
            if caption:
                figure.caption = caption[0]
                figure.metadata['caption_confidence'] = caption[1]
                logger.debug(f"Bound caption to {figure.figure_id}: {caption[0][:50]}...")
        
        bound_count = sum(1 for f in figures if f.caption)
        logger.info(f"Bound {bound_count}/{len(figures)} figures to captions")
        
        return figures
    
    def find_caption(self, figure: Figure, text_blocks: List[TextBlock]) -> Optional[Tuple[str, float]]:
        """
        Find caption for a figure
        
        Args:
            figure: Figure to find caption for
            text_blocks: Available text blocks
            
        Returns:
            Tuple of (caption_text, confidence) or None
        """
        candidates = []
        
        for block in text_blocks:
            # Must be on same page
            if block.bbox.page != figure.page:
                continue
            
            # Check spatial proximity
            distance = self._calculate_distance(figure.bbox, block.bbox)
            if distance > self.MAX_DISTANCE:
                continue
            
            # Check for caption patterns
            for pattern in self.CAPTION_PATTERNS:
                match = re.search(pattern, block.content, re.IGNORECASE)
                if match:
                    caption_text = match.group(0).strip()
                    confidence = self._calculate_confidence(distance, match)
                    candidates.append((caption_text, confidence, distance))
        
        # Return best candidate
        if candidates:
            # Sort by confidence (desc) then distance (asc)
            candidates.sort(key=lambda x: (-x[1], x[2]))
            return (candidates[0][0], candidates[0][1])
        
        # Fallback: look for nearby text
        nearby = self._find_nearby_text(figure, text_blocks)
        if nearby:
            return (nearby, 0.5)  # Lower confidence
        
        return None
    
    def _calculate_distance(self, bbox1, bbox2) -> float:
        """Calculate distance between two bounding boxes"""
        # Simple vertical distance (figures usually have captions below)
        if bbox2.y0 > bbox1.y1:  # Caption below figure
            return bbox2.y0 - bbox1.y1
        elif bbox1.y0 > bbox2.y1:  # Caption above figure
            return bbox1.y0 - bbox2.y1
        else:  # Overlapping or side-by-side
            return abs(bbox1.x0 - bbox2.x0)
    
    def _calculate_confidence(self, distance: float, match: re.Match) -> float:
        """Calculate binding confidence"""
        # Base confidence from pattern match
        confidence = 0.8
        
        # Reduce confidence based on distance
        if distance > 50:
            confidence -= 0.2
        if distance > 75:
            confidence -= 0.1
        
        # Increase if figure number is present
        if match.group(1):  # Figure number captured
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _find_nearby_text(self, figure: Figure, text_blocks: List[TextBlock]) -> Optional[str]:
        """Find text near figure as fallback caption"""
        nearby_blocks = []
        
        for block in text_blocks:
            if block.bbox.page != figure.page:
                continue
            
            distance = self._calculate_distance(figure.bbox, block.bbox)
            if distance < self.MAX_DISTANCE:
                nearby_blocks.append((block, distance))
        
        if nearby_blocks:
            # Get closest block
            nearby_blocks.sort(key=lambda x: x[1])
            closest = nearby_blocks[0][0]
            # Return first sentence or first 100 chars
            text = closest.content.strip()
            if '.' in text:
                text = text.split('.')[0] + '.'
            return text[:100]
        
        return None
