"""Handwriting OCR with multiple engine fallback"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from ..logging_config import get_logger

logger = get_logger("handwriting_ocr")


class OCRResult:
    """OCR result with confidence"""
    def __init__(self, text: str, confidence: float, engine: str):
        self.text = text
        self.confidence = confidence
        self.engine = engine


class HandwritingOCR:
    """Enhanced handwriting recognition with fallback chain"""
    
    def __init__(self):
        self.engines = self._initialize_engines()
        logger.info(f"Initialized {len(self.engines)} OCR engines")
    
    def _initialize_engines(self) -> List[str]:
        """Initialize available OCR engines"""
        available = []
        
        # Check Gemini (primary)
        if os.getenv("GEMINI_API_KEY"):
            available.append("gemini")
        
        # Check Azure Computer Vision
        if os.getenv("AZURE_CV_KEY") and os.getenv("AZURE_CV_ENDPOINT"):
            available.append("azure")
        
        # Check Google Cloud Vision
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            available.append("google_vision")
        
        # Tesseract (local fallback)
        try:
            import pytesseract  # type: ignore
            available.append("tesseract")
        except ImportError:
            pass
        
        if not available:
            logger.warning("No OCR engines available")
        
        return available
    
    def recognize(self, image_data: bytes, min_confidence: float = 0.7) -> Optional[OCRResult]:
        """
        Recognize handwritten text with fallback
        
        Args:
            image_data: Image bytes
            min_confidence: Minimum confidence threshold
            
        Returns:
            OCRResult or None
        """
        for engine in self.engines:
            try:
                result = self._call_engine(engine, image_data)
                if result and result.confidence >= min_confidence:
                    logger.info(f"OCR success with {engine}: confidence={result.confidence:.2f}")
                    return result
                else:
                    logger.debug(f"{engine} confidence too low: {result.confidence if result else 0:.2f}")
            except Exception as e:
                logger.warning(f"{engine} OCR failed: {e}")
                continue
        
        logger.warning("All OCR engines failed or low confidence")
        return None
    
    def _call_engine(self, engine: str, image_data: bytes) -> Optional[OCRResult]:
        """Call specific OCR engine"""
        if engine == "gemini":
            return self._gemini_ocr(image_data)
        elif engine == "azure":
            return self._azure_ocr(image_data)
        elif engine == "google_vision":
            return self._google_vision_ocr(image_data)
        elif engine == "tesseract":
            return self._tesseract_ocr(image_data)
        return None
    
    def _gemini_ocr(self, image_data: bytes) -> Optional[OCRResult]:
        """Gemini Vision OCR"""
        try:
            import google.generativeai as genai
            from PIL import Image
            import io
            
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')  # Updated to stable model
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            prompt = "Extract all handwritten text from this image. Return only the text, no explanations."
            response = model.generate_content([prompt, image])
            
            if response.text:
                # Gemini doesn't provide confidence, use default
                return OCRResult(response.text.strip(), 0.85, "gemini")
        
        except Exception as e:
            logger.debug(f"Gemini OCR error: {e}")
        
        return None
    
    
    def _google_vision_ocr(self, image_data: bytes) -> Optional[OCRResult]:
        """Google Cloud Vision OCR"""
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_data)
            
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                # First annotation contains full text
                full_text = texts[0].description
                # Google Vision provides confidence
                confidence = texts[0].confidence if hasattr(texts[0], 'confidence') else 0.8
                return OCRResult(full_text.strip(), confidence, "google_vision")
        
        except Exception as e:
            logger.debug(f"Google Vision OCR error: {e}")
        
        return None
    
    def _tesseract_ocr(self, image_data: bytes) -> Optional[OCRResult]:
        """Tesseract OCR (local fallback)"""
        try:
            import pytesseract  # type: ignore
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            
            # Get text with confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Valid confidence
                    text_parts.append(data['text'][i])
                    confidences.append(int(conf) / 100.0)  # Convert to 0-1
            
            if text_parts:
                text = " ".join(text_parts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.5
                return OCRResult(text.strip(), avg_conf, "tesseract")
        
        except Exception as e:
            logger.debug(f"Tesseract OCR error: {e}")
        
        return None
    
    def batch_recognize(self, images: List[bytes], min_confidence: float = 0.7) -> List[Optional[OCRResult]]:
        """Recognize multiple images"""
        results = []
        for img_data in images:
            result = self.recognize(img_data, min_confidence)
            results.append(result)
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"Batch OCR: {success_count}/{len(images)} successful")
        
        return results
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines"""
        return self.engines.copy()
