import os
import base64
from typing import Tuple, List
from pathlib import Path
from .base import BaseExtractor
from ..models.extracted_document import (
    ExtractedDocument, TextBlock, Table, BoundingBox
)
from ..models.document_profile import DocumentProfile


class VisionExtractor(BaseExtractor):
    """Vision-augmented extraction using Gemini Flash 2.5 for scanned documents"""
    
    MAX_COST_PER_DOC = 1.0  # $1 budget cap per document
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash-exp"  # Gemini Flash 2.5
        self.cost_per_image = 0.02  # Estimated cost per page
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                self.use_gemini = True
            except ImportError:
                print("Warning: google-generativeai not available")
                self.use_gemini = False
        else:
            self.use_gemini = False
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Extract using Gemini vision model"""
        # Budget guard
        estimated_cost = self.estimate_cost(profile)
        if estimated_cost > self.MAX_COST_PER_DOC:
            raise ValueError(f"Estimated cost ${estimated_cost:.2f} exceeds budget cap ${self.MAX_COST_PER_DOC}")
        
        text_blocks = []
        tables = []
        
        if self.use_gemini:
            # Convert PDF pages to images and process with Gemini
            images = self._pdf_to_images(pdf_path)
            
            for page_num, image in enumerate(images):
                # Call Gemini with structured extraction prompt
                extracted_content = self._call_gemini(image, page_num, profile)
                
                if extracted_content:
                    bbox = BoundingBox(x0=0, y0=0, x1=1000, y1=1000, page=page_num)
                    text_blocks.append(TextBlock(
                        content=extracted_content,
                        bbox=bbox,
                        reading_order=page_num
                    ))
        else:
            # Fallback: placeholder extraction
            print("Warning: Gemini API not configured, using placeholder")
            for page_num in range(min(profile.total_pages, 5)):
                bbox = BoundingBox(x0=0, y0=0, x1=1000, y1=1000, page=page_num)
                text_blocks.append(TextBlock(
                    content=f"[Placeholder: Page {page_num + 1} content]",
                    bbox=bbox,
                    reading_order=page_num
                ))
        
        confidence = 0.8 if self.use_gemini else 0.5
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            extraction_strategy=self.strategy_name,
            confidence_score=confidence
        )
        
        return extracted_doc, confidence
    
    def _pdf_to_images(self, pdf_path: str) -> List:
        """Convert PDF pages to images"""
        try:
            from pdf2image import convert_from_path
            return convert_from_path(pdf_path, dpi=150)
        except ImportError:
            print("Warning: pdf2image not available")
            return []
    
    def _call_gemini(self, image, page_num: int, profile: DocumentProfile) -> str:
        """Call Gemini API with structured prompt"""
        if not self.use_gemini:
            return ""
        
        # Domain-specific prompts
        domain_prompts = {
            "financial": "Focus on extracting financial data, tables, and numerical values with high precision.",
            "legal": "Extract all text preserving legal structure, clauses, and formatting.",
            "technical": "Extract technical specifications, diagrams descriptions, and structured data.",
            "medical": "Extract medical information, patient data, and clinical findings carefully.",
            "general": "Extract all text and structured data from this document."
        }
        
        domain_hint = domain_prompts.get(profile.domain_hint, domain_prompts["general"])
        
        prompt = f"""You are a document extraction expert. Extract all text from this document page.

{domain_hint}

Instructions:
1. Preserve the reading order and structure
2. Extract tables as structured text with clear headers and rows
3. Include all visible text, numbers, and data
4. Maintain formatting where important (lists, sections, etc.)
5. If there are tables, format them clearly with | separators

Return only the extracted text, no explanations."""
        
        try:
            response = self.client.generate_content([prompt, image])
            return response.text
        except Exception as e:
            print(f"Gemini API error on page {page_num}: {str(e)}")
            return ""
    
    def estimate_cost(self, profile: DocumentProfile) -> float:
        """Estimate Gemini cost"""
        return self.cost_per_image * profile.total_pages
    
    @property
    def strategy_name(self) -> str:
        return "vision_augmented"
