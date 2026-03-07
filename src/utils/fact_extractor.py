"""
FactTable Extractor - Extract key-value facts for SQL querying
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models.extracted_document import ExtractedDocument
from ..models.ldu import LDU
from ..logging_config import get_logger

logger = get_logger("fact_extractor")


class FactExtractor:
    """Extract structured facts from documents for SQL querying"""
    
    def __init__(self, db_path: str = ".refinery/facts.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create facts table
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
        
        # Create index
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
        Extract facts from document and store in database
        
        Args:
            extracted_doc: Extracted document
            ldus: List of LDUs
            
        Returns:
            Number of facts extracted
        """
        logger.info(f"Extracting facts from {extracted_doc.doc_id}")
        
        facts = []
        
        # Extract from tables
        for table in extracted_doc.tables:
            table_facts = self._extract_from_table(table, extracted_doc.doc_id)
            facts.extend(table_facts)
        
        # Extract from text (numerical facts)
        for ldu in ldus:
            if ldu.chunk_type == "text":
                text_facts = self._extract_from_text(ldu, extracted_doc.doc_id)
                facts.extend(text_facts)
        
        # Store in database
        self._store_facts(facts)
        
        logger.info(f"Extracted {len(facts)} facts")
        return len(facts)
    
    def _extract_from_table(self, table: Any, doc_id: str) -> List[Dict[str, Any]]:
        """Extract facts from table"""
        facts = []
        
        if not table.rows or len(table.rows) < 2:
            return facts
        
        # Assume first row is header
        headers = table.rows[0]
        
        for row_idx, row in enumerate(table.rows[1:], start=1):
            for col_idx, cell_value in enumerate(row):
                if col_idx >= len(headers):
                    continue
                
                header = headers[col_idx]
                
                # Extract numerical facts
                if self._is_numerical(cell_value):
                    fact = {
                        "doc_id": doc_id,
                        "document_name": f"{doc_id}.pdf",
                        "page_number": table.bbox.page,
                        "fact_type": "table_cell",
                        "key": f"{header}",
                        "value": cell_value,
                        "unit": self._extract_unit(cell_value),
                        "context": f"Row {row_idx}",
                        "content_hash": "",
                        "bbox": str(table.bbox.model_dump()),
                        "ldu_id": None
                    }
                    facts.append(fact)
        
        return facts
    
    def _extract_from_text(self, ldu: LDU, doc_id: str) -> List[Dict[str, Any]]:
        """Extract numerical facts from text"""
        facts = []
        
        # Pattern: "Key: Value" or "Key is Value"
        patterns = [
            r'([A-Za-z\s]+):\s*([0-9,.$%]+(?:\s*[A-Za-z]+)?)',
            r'([A-Za-z\s]+)\s+is\s+([0-9,.$%]+(?:\s*[A-Za-z]+)?)',
            r'([A-Za-z\s]+)\s+was\s+([0-9,.$%]+(?:\s*[A-Za-z]+)?)',
            r'([A-Za-z\s]+)\s+of\s+([0-9,.$%]+(?:\s*[A-Za-z]+)?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, ldu.content)
            for match in matches:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # Filter out noise
                if len(key) < 3 or len(key) > 100:
                    continue
                
                page_ref = ldu.page_refs[0] if ldu.page_refs else 0
                
                fact = {
                    "doc_id": doc_id,
                    "document_name": f"{doc_id}.pdf",
                    "page_number": page_ref,
                    "fact_type": "text_extraction",
                    "key": key,
                    "value": value,
                    "unit": self._extract_unit(value),
                    "context": ldu.content[:100],
                    "content_hash": ldu.content_hash,
                    "bbox": None,
                    "ldu_id": ldu.ldu_id
                }
                facts.append(fact)
        
        return facts
    
    def _is_numerical(self, value: str) -> bool:
        """Check if value contains numbers"""
        return bool(re.search(r'\d', str(value)))
    
    def _extract_unit(self, value: str) -> Optional[str]:
        """Extract unit from value"""
        # Common units
        units = ['USD', 'EUR', 'GBP', '%', 'million', 'billion', 'thousand', 'kg', 'km', 'years']
        
        value_str = str(value).lower()
        for unit in units:
            if unit.lower() in value_str:
                return unit
        
        return None
    
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
