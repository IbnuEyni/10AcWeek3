"""Modern OCR with PaddleOCR, RapidOCR, and Surya - Enterprise-grade accuracy"""

import os
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from ..logging_config import get_logger

logger = get_logger("modern_ocr")


class OCRResult:
    """OCR result with confidence and bounding boxes"""
    def __init__(self, text: str, confidence: float, engine: str, boxes: Optional[List[Dict]] = None):
        self.text = text
        self.confidence = confidence
        self.engine = engine
        self.boxes = boxes or []  # List of {text, bbox, confidence}


class ModernOCR:
    """Enterprise OCR with PaddleOCR (fast), RapidOCR (faster), Surya (accurate)"""
    
    def __init__(self):
        self.engines = self._initialize_engines()
        logger.info(f"Initialized {len(self.engines)} modern OCR engines")
    
    def _initialize_engines(self) -> List[str]:
        """Initialize available modern OCR engines"""
        available = []
        
        # Check RapidOCR (fastest, CPU-friendly)
        try:
            from rapidocr_onnxruntime import RapidOCR
            available.append("rapidocr")
            logger.info("RapidOCR available (fastest)")
        except ImportError:
            logger.debug("RapidOCR not available")
        
        # Check PaddleOCR (fast, accurate)
        try:
            from paddleocr import PaddleOCR
            available.append("paddleocr")
            logger.info("PaddleOCR available (fast + accurate)")
        except ImportError:
            logger.debug("PaddleOCR not available")
        
        # Check Surya OCR (highest accuracy, best bboxes)
        try:
            from surya.ocr import run_ocr
            available.append("surya")
            logger.info("Surya OCR available (highest accuracy)")
        except ImportError:
            logger.debug("Surya OCR not available")
        
        # Cloud fallbacks
        if os.getenv("GEMINI_API_KEY"):
            available.append("gemini")
        
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            available.append("google_vision")
        
        if not available:
            logger.warning("No OCR engines available - install rapidocr-onnxruntime or paddleocr")
        
        return available
    
    def recognize(self, image_data: bytes, min_confidence: float = 0.7, need_boxes: bool = False) -> Optional[OCRResult]:
        """
        Recognize text with modern OCR engines
        
        Args:
            image_data: Image bytes
            min_confidence: Minimum confidence threshold
            need_boxes: If True, use Surya for high-fidelity bounding boxes
            
        Returns:
            OCRResult with text, confidence, and optional bounding boxes
        """
        # If bounding boxes needed, prioritize Surya
        engines = ["surya"] + [e for e in self.engines if e != "surya"] if need_boxes else self.engines
        
        for engine in engines:
            try:
                result = self._call_engine(engine, image_data, need_boxes)
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
    
    def _call_engine(self, engine: str, image_data: bytes, need_boxes: bool = False) -> Optional[OCRResult]:
        """Call specific OCR engine"""
        if engine == "rapidocr":
            return self._rapidocr(image_data)
        elif engine == "paddleocr":
            return self._paddleocr(image_data, need_boxes)
        elif engine == "surya":
            return self._surya_ocr(image_data)
        elif engine == "gemini":
            return self._gemini_ocr(image_data)
        elif engine == "google_vision":
            return self._google_vision_ocr(image_data)
        return None
    
    def _rapidocr(self, image_data: bytes) -> Optional[OCRResult]:
        """RapidOCR - Fastest local OCR (ONNX Runtime)"""
        try:
            from rapidocr_onnxruntime import RapidOCR
            from PIL import Image
            import io
            import numpy as np
            
            # Initialize engine (cached)
            if not hasattr(self, '_rapid_engine'):
                self._rapid_engine = RapidOCR()
            
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_data))
            img_array = np.array(image)
            
            # Run OCR
            result, elapse = self._rapid_engine(img_array)
            
            if result:
                # Extract text and confidence
                texts = [line[1] for line in result]
                confidences = [line[2] for line in result]
                
                full_text = "\n".join(texts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                
                return OCRResult(full_text.strip(), avg_conf, "rapidocr")
        
        except Exception as e:
            logger.debug(f"RapidOCR error: {e}")
        
        return None
    
    def _paddleocr(self, image_data: bytes, need_boxes: bool = False) -> Optional[OCRResult]:
        """PaddleOCR - Fast and accurate with optional bounding boxes"""
        try:
            from paddleocr import PaddleOCR
            from PIL import Image
            import io
            import numpy as np
            
            # Initialize engine (cached)
            if not hasattr(self, '_paddle_engine'):
                self._paddle_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_data))
            img_array = np.array(image)
            
            # Run OCR
            result = self._paddle_engine.ocr(img_array, cls=True)
            
            if result and result[0]:
                texts = []
                confidences = []
                boxes = []
                
                for line in result[0]:
                    bbox, (text, conf) = line
                    texts.append(text)
                    confidences.append(conf)
                    
                    if need_boxes:
                        boxes.append({
                            'text': text,
                            'bbox': bbox,  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                            'confidence': conf
                        })
                
                full_text = "\n".join(texts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                
                return OCRResult(full_text.strip(), avg_conf, "paddleocr", boxes if need_boxes else None)
        
        except Exception as e:
            logger.debug(f"PaddleOCR error: {e}")
        
        return None
    
    def _surya_ocr(self, image_data: bytes) -> Optional[OCRResult]:
        """Surya OCR - Highest accuracy with precise bounding boxes"""
        try:
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor
            from PIL import Image
            import io
            
            # Load models (cached)
            if not hasattr(self, '_surya_models'):
                self._surya_models = {
                    'det_model': load_det_model(),
                    'det_processor': load_det_processor(),
                    'rec_model': load_rec_model(),
                    'rec_processor': load_rec_processor()
                }
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Run OCR
            predictions = run_ocr(
                [image],
                [['en']],  # Languages
                self._surya_models['det_model'],
                self._surya_models['det_processor'],
                self._surya_models['rec_model'],
                self._surya_models['rec_processor']
            )
            
            if predictions:
                pred = predictions[0]
                texts = [line.text for line in pred.text_lines]
                confidences = [line.confidence for line in pred.text_lines]
                boxes = [{
                    'text': line.text,
                    'bbox': line.bbox,  # [x1, y1, x2, y2]
                    'confidence': line.confidence
                } for line in pred.text_lines]
                
                full_text = "\n".join(texts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                
                return OCRResult(full_text.strip(), avg_conf, "surya", boxes)
        
        except Exception as e:
            logger.debug(f"Surya OCR error: {e}")
        
        return None
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
        """REMOVED - Tesseract replaced by modern OCR engines"""
        logger.warning("Tesseract OCR removed - use RapidOCR, PaddleOCR, or Surya instead")
        return None
    
    def batch_recognize(self, images: List[bytes], min_confidence: float = 0.7, need_boxes: bool = False) -> List[Optional[OCRResult]]:
        """Recognize multiple images"""
        results = []
        for img_data in images:
            result = self.recognize(img_data, min_confidence, need_boxes)
            results.append(result)
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"Batch OCR: {success_count}/{len(images)} successful")
        
        return results
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines"""
        return self.engines.copy()


# Backward compatibility alias
HandwritingOCR = ModernOCR
