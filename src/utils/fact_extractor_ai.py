"""
Fact Extractor - AI-Native (LLM Structured Outputs)
Uses DeepSeek API with Pydantic schemas instead of regex.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..models.extracted_document import ExtractedDocument
from ..models.ldu import LDU
from ..logging_config import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("fact_extractor_ai")


class ExtractedFact(BaseModel):
    """Pydantic schema for LLM-extracted facts"""
    key: str = Field(..., description="Fact name/key (e.g., 'Total Revenue')")
    value: str = Field(..., description="Fact value (e.g., '$4.2B')")
    unit: Optional[str] = Field(None, description="Unit if applicable (USD, %, million)")
    context: Optional[str] = Field(None, description="Brief context")


class FactList(BaseModel):
    """List of extracted facts"""
    facts: List[ExtractedFact]


class FactExtractorAI:
    """Extract structured facts using LLM with Pydantic schemas (no regex)"""
    
    def __init__(self, db_path: str = ".refinery/facts.db"):
        self.db_path = db_path
        self._init_database()
        
        # Initialize LLM client (OpenAI by default)
        self.llm_available = False
        self.llm_provider = None
        self.llm_model = None

        # Only DeepSeek is supported for fact extraction in this deployment
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        deepseek_api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.ai/v1/completions")
        if deepseek_api_key:
            try:
                import requests

                self.llm_provider = "deepseek"
                self.llm_model = os.getenv("DEEPSEEK_MODEL", "deepseek-v2")
                self.llm_client = requests
                self.deepseek_api_key = deepseek_api_key
                self.deepseek_api_url = deepseek_api_url
                self.llm_available = True
                logger.info(f"DeepSeek model '{self.llm_model}' initialized for fact extraction")
            except ImportError:
                logger.warning("Requests library not available for DeepSeek API calls")
            except Exception as e:
                logger.warning(f"DeepSeek initialization failed: {e}")

        if not self.llm_available:
            logger.warning("No LLM configured for fact extraction (set DEEPSEEK_API_KEY)")

    def _call_llm(self, prompt: str) -> str:
        """Call configured LLM and return the raw text response."""
        if not self.llm_available:
            raise RuntimeError("No LLM configured")

        if self.llm_provider == "deepseek":
            try:
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.llm_model,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 1500,
                }
                response = self.llm_client.post(
                    self.deepseek_api_url,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                # DeepSeek response formats vary; try common fields
                if isinstance(data, dict):
                    if "choices" in data and data["choices"]:
                        first = data["choices"][0]
                        if isinstance(first, dict) and "text" in first:
                            return first["text"]
                        if isinstance(first, dict) and "message" in first:
                            return first["message"].get("content", "")
                    if "output" in data:
                        if isinstance(data["output"], list):
                            return "\n".join(str(x) for x in data["output"])
                        return str(data["output"])

                # Fallback: return raw string
                return str(data)
            except Exception as e:
                logger.debug(f"DeepSeek API unavailable: {e}")
                raise

        raise RuntimeError(f"Unsupported LLM provider: {self.llm_provider}")

    def _normalize_json_response(self, text: str) -> str:
        """Normalize LLM output so it can be parsed as JSON."""
        if not text:
            return text

        txt = text.strip()

        # Extract JSON from Markdown-style code fences if present
        if "```" in txt:
            parts = txt.split("```")
            # Pick the first candidate that looks like JSON
            candidates = [p.strip() for p in parts if p.strip().startswith(('{', '['))]
            if candidates:
                txt = candidates[0]

        # Extract JSON object/array if wrapped in extraneous text
        if not txt.startswith(('{', '[')) and '{' in txt and '}' in txt:
            start = txt.find('{')
            end = txt.rfind('}')
            if end > start:
                txt = txt[start : end + 1]
        if not txt.startswith(('{', '[')) and '[' in txt and ']' in txt:
            start = txt.find('[')
            end = txt.rfind(']')
            if end > start:
                txt = txt[start : end + 1]

        # Stripped quotes around JSON
        if (txt.startswith('"') and txt.endswith('"')) or (txt.startswith("'") and txt.endswith("'")):
            txt = txt[1:-1]

        return txt

    def _init_database(self):
        """Initialize SQLite database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                page_number INTEGER,
                fact_type TEXT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                unit TEXT,
                context TEXT,
                content_hash TEXT,
                bbox TEXT,
                ldu_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON facts(doc_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_key ON facts(key)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Fact database initialized: {self.db_path}")
    
    def extract_facts(
        self, 
        extracted_doc: ExtractedDocument,
        ldus: List[LDU]
    ) -> int:
        """
        Extract facts using LLM with structured output
        
        Args:
            extracted_doc: Extracted document
            ldus: List of LDUs
            
        Returns:
            Number of facts extracted
        """
        if not self.llm_available:
            logger.warning("LLM not available, skipping fact extraction")
            return 0
        
        logger.info(f"Extracting facts from {extracted_doc.doc_id}")
        
        all_facts = []
        
        # Extract from tables
        for table in extracted_doc.tables:
            facts = self._extract_from_table_llm(table, extracted_doc.doc_id)
            all_facts.extend(facts)
        
        # Extract from text LDUs
        for ldu in ldus:
            if ldu.chunk_type == "text" and len(ldu.content) > 50:
                facts = self._extract_from_text_llm(ldu, extracted_doc.doc_id)
                all_facts.extend(facts)
        
        # Store in database
        self._store_facts(all_facts)
        
        logger.info(f"Extracted {len(all_facts)} facts")
        return len(all_facts)
    
    def _extract_from_table_llm(self, table: Any, doc_id: str) -> List[Dict[str, Any]]:
        """Extract facts from table using LLM"""
        if not table.rows or len(table.rows) < 2:
            return []
        
        table_text = self._format_table(table)
        
        prompt = f"""Extract key-value facts from this table. Focus on numerical data, financial figures, and important metrics.

Table:
{table_text}

Return ONLY valid JSON (no explanations). The output must be an object with a single key "facts" whose value is an array of objects with keys: key, value, unit (optional), context (optional)."""
        
        try:
            response_text = self._call_llm(prompt)
            response_text = self._normalize_json_response(response_text)

            import json
            result = json.loads(response_text)
            fact_list = FactList(**result)
            
            facts = []
            for fact in fact_list.facts:
                facts.append({
                    "doc_id": doc_id,
                    "document_name": f"{doc_id}.pdf",
                    "page_number": table.bbox.page,
                    "fact_type": "table_cell",
                    "key": fact.key,
                    "value": fact.value,
                    "unit": fact.unit,
                    "context": fact.context,
                    "content_hash": "",
                    "bbox": str(table.bbox.model_dump()),
                    "ldu_id": None
                })
            
            return facts
            
        except Exception as e:
            logger.debug(f"Skipping table fact extraction: {e}")
            return []
    
    def _extract_from_text_llm(self, ldu: LDU, doc_id: str) -> List[Dict[str, Any]]:
        """Extract facts from text using LLM"""
        prompt = f"""Extract key-value facts from this text. Focus on numerical data, dates, names, and important information.

Text:
{ldu.content[:1000]}

Return ONLY valid JSON (no explanations). The output must be an object with a single key "facts" whose value is an array of objects with keys: key, value, unit (optional), context (optional)."""
        
        try:
            response_text = self._call_llm(prompt)
            response_text = self._normalize_json_response(response_text)

            import json
            result = json.loads(response_text)
            fact_list = FactList(**result)
            
            facts = []
            page_ref = ldu.page_refs[0] if ldu.page_refs else 0
            
            for fact in fact_list.facts:
                facts.append({
                    "doc_id": doc_id,
                    "document_name": f"{doc_id}.pdf",
                    "page_number": page_ref,
                    "fact_type": "text_extraction",
                    "key": fact.key,
                    "value": fact.value,
                    "unit": fact.unit,
                    "context": fact.context or ldu.content[:100],
                    "content_hash": ldu.content_hash,
                    "bbox": None,
                    "ldu_id": ldu.ldu_id
                })
            
            return facts
            
        except Exception as e:
            logger.debug(f"Skipping text fact extraction: {e}")
            return []
    
    def _format_table(self, table: Any) -> str:
        """Format table as text for LLM"""
        lines = []
        for row in table.rows[:10]:  # Limit to first 10 rows
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)
    
    def _store_facts(self, facts: List[Dict[str, Any]]):
        """Store facts in database"""
        if not facts:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for fact in facts:
            cursor.execute("""
                INSERT INTO facts (
                    doc_id, document_name, page_number, fact_type,
                    key, value, unit, context, content_hash, bbox, ldu_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fact['doc_id'],
                fact['document_name'],
                fact['page_number'],
                fact['fact_type'],
                fact['key'],
                fact['value'],
                fact['unit'],
                fact['context'],
                fact['content_hash'],
                fact['bbox'],
                fact['ldu_id']
            ))
        
        conn.commit()
        conn.close()
    
    def query_facts(
        self, 
        doc_id: Optional[str] = None,
        key_pattern: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query facts from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM facts WHERE 1=1"
        params = []
        
        if doc_id:
            query += " AND doc_id = ?"
            params.append(doc_id)
        
        if key_pattern:
            query += " AND key LIKE ?"
            params.append(f"%{key_pattern}%")
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return results
