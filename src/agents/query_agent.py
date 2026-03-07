"""
Query Interface Agent - Stage 5
Natural language query interface with provenance tracking
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..models.pageindex import PageIndex, Section
from ..models.ldu import LDU
from ..models.provenance import ProvenanceChain, SourceCitation
from ..logging_config import get_logger

logger = get_logger("query_agent")


class QueryAgent:
    """Query interface with pageindex navigation, semantic search, and structured queries"""
    
    def __init__(
        self, 
        pageindex_dir: str = ".refinery/pageindex",
        ldu_dir: str = ".refinery/ldus",
        vector_store_path: Optional[str] = None,
        fact_db_path: str = ".refinery/facts.db"
    ):
        self.pageindex_dir = Path(pageindex_dir)
        self.ldu_dir = Path(ldu_dir)
        self.fact_db_path = fact_db_path
        
        # Load vector store if available
        self.vector_store = None
        if vector_store_path:
            try:
                import chromadb
                self.vector_store = chromadb.PersistentClient(path=vector_store_path)
                logger.info("Vector store loaded")
            except ImportError:
                logger.warning("ChromaDB not available, semantic search disabled")
        
        logger.info("Query agent initialized")
    
    def query(
        self, 
        query_text: str, 
        doc_id: Optional[str] = None,
        method: str = "auto",
        description: Optional[str] = None  # Unused, kept for compatibility
    ) -> ProvenanceChain:
        """
        Execute query - just pass the query text, method is auto-selected
        
        Args:
            query_text: Natural language query (required)
            doc_id: Optional document ID to restrict search
            method: auto (default) | pageindex | semantic | structured
            description: Unused parameter for compatibility
            
        Returns:
            ProvenanceChain with answer and citations
        """
        logger.info(f"Query: {query_text} | doc_id={doc_id} | method={method}")
        
        # Auto-select method
        if method == "auto":
            method = self._select_method(query_text)
        
        # Execute query
        if method == "pageindex":
            return self._pageindex_query(query_text, doc_id)
        elif method == "semantic":
            return self._semantic_query(query_text, doc_id)
        elif method == "structured":
            return self._structured_query(query_text, doc_id)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _select_method(self, query_text: str) -> str:
        """Auto-select query method based on query type"""
        query_lower = query_text.lower()
        
        # Structured query indicators
        if any(kw in query_lower for kw in ["how much", "what is the", "total", "sum", "revenue", "expenditure"]):
            return "structured"
        
        # PageIndex navigation indicators
        if any(kw in query_lower for kw in ["section", "chapter", "where", "which page", "table of contents"]):
            return "pageindex"
        
        # Default to semantic search
        return "semantic"
    
    def pageindex_navigate(
        self, 
        doc_id: str, 
        section_query: str
    ) -> List[Section]:
        """
        Tool 1: Navigate PageIndex to find relevant sections
        
        Args:
            doc_id: Document identifier
            section_query: Section search query
            
        Returns:
            List of relevant sections
        """
        logger.info(f"PageIndex navigate: {doc_id} | query={section_query}")
        
        # Load PageIndex
        pageindex_path = self.pageindex_dir / f"{doc_id}_pageindex.json"
        if not pageindex_path.exists():
            logger.warning(f"PageIndex not found: {pageindex_path}")
            return []
        
        with open(pageindex_path) as f:
            pageindex_data = json.load(f)
            pageindex = PageIndex(**pageindex_data)
        
        # Search sections
        sections = pageindex.find_section_by_query(section_query)
        logger.info(f"Found {len(sections)} matching sections")
        
        return sections
    
    def semantic_search(
        self, 
        query_text: str, 
        doc_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[LDU]:
        """
        Tool 2: Semantic vector search over LDUs
        
        Args:
            query_text: Search query
            doc_id: Optional document filter
            top_k: Number of results
            
        Returns:
            List of relevant LDUs
        """
        logger.info(f"Semantic search: {query_text} | doc_id={doc_id} | top_k={top_k}")
        
        if not self.vector_store:
            # Fallback: keyword search over LDUs
            return self._keyword_search(query_text, doc_id, top_k)
        
        # Vector search
        try:
            collection = self.vector_store.get_collection("ldus")
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where={"doc_id": doc_id} if doc_id else None
            )
            
            # Convert to LDUs
            ldus = []
            for metadata in results['metadatas'][0]:
                ldu_path = Path(metadata['ldu_path'])
                if ldu_path.exists():
                    with open(ldu_path) as f:
                        ldu_data = json.load(f)
                        ldus.append(LDU(**ldu_data))
            
            logger.info(f"Found {len(ldus)} relevant LDUs")
            return ldus
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return self._keyword_search(query_text, doc_id, top_k)
    
    def structured_query(
        self, 
        sql_query: str
    ) -> List[Dict[str, Any]]:
        """
        Tool 3: SQL query over extracted fact table
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Query results
        """
        logger.info(f"Structured query: {sql_query}")
        
        if not Path(self.fact_db_path).exists():
            logger.warning("Fact database not found")
            return []
        
        try:
            conn = sqlite3.connect(self.fact_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            logger.info(f"Query returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"SQL query failed: {e}")
            return []
    
    def _pageindex_query(self, query_text: str, doc_id: Optional[str]) -> ProvenanceChain:
        """Execute query using PageIndex navigation"""
        
        if not doc_id:
            # Find all documents
            doc_ids = [p.stem.replace("_pageindex", "") for p in self.pageindex_dir.glob("*_pageindex.json")]
            if not doc_ids:
                return self._empty_result(query_text, "pageindex")
            doc_id = doc_ids[0]  # Use first document
        
        # Navigate to relevant sections
        sections = self.pageindex_navigate(doc_id, query_text)
        
        if not sections:
            return self._empty_result(query_text, "pageindex")
        
        # Get LDUs from sections
        ldus = self._get_ldus_from_sections(doc_id, sections)
        
        # Generate answer
        answer = self._generate_answer(query_text, ldus)
        citations = self._create_citations(ldus, doc_id)
        
        return ProvenanceChain(
            query=query_text,
            answer=answer,
            citations=citations,
            confidence=0.8,
            retrieval_method="pageindex"
        )
    
    def _semantic_query(self, query_text: str, doc_id: Optional[str]) -> ProvenanceChain:
        """Execute query using semantic search"""
        
        # Search LDUs
        ldus = self.semantic_search(query_text, doc_id)
        
        if not ldus:
            return self._empty_result(query_text, "semantic_search")
        
        # Generate answer
        answer = self._generate_answer(query_text, ldus)
        citations = self._create_citations(ldus, doc_id or ldus[0].doc_id)
        
        return ProvenanceChain(
            query=query_text,
            answer=answer,
            citations=citations,
            confidence=0.75,
            retrieval_method="semantic_search"
        )
    
    def _structured_query(self, query_text: str, doc_id: Optional[str]) -> ProvenanceChain:
        """Execute query using structured SQL"""
        
        # Convert natural language to SQL (simplified)
        sql_query = self._nl_to_sql(query_text)
        
        # Execute query
        results = self.structured_query(sql_query)
        
        if not results:
            return self._empty_result(query_text, "structured_query")
        
        # Format answer
        answer = self._format_structured_results(results)
        
        # Create citations from fact table
        citations = self._create_citations_from_facts(results)
        
        return ProvenanceChain(
            query=query_text,
            answer=answer,
            citations=citations,
            confidence=0.9,
            retrieval_method="structured_query"
        )
    
    def _keyword_search(self, query_text: str, doc_id: Optional[str], top_k: int) -> List[LDU]:
        """Fallback keyword search over LDUs"""
        keywords = query_text.lower().split()
        ldus = []
        
        # Search LDU files
        ldu_files = list(self.ldu_dir.glob("*_ldus.json"))
        if doc_id:
            ldu_files = [f for f in ldu_files if f.stem.startswith(doc_id)]
        
        for ldu_file in ldu_files:
            with open(ldu_file) as f:
                ldu_list = json.load(f)
                for ldu_data in ldu_list:
                    ldu = LDU(**ldu_data)
                    content_lower = ldu.content.lower()
                    
                    # Score by keyword matches
                    score = sum(1 for kw in keywords if kw in content_lower)
                    if score > 0:
                        ldus.append((score, ldu))
        
        # Sort by score and return top_k
        ldus.sort(key=lambda x: x[0], reverse=True)
        return [ldu for _, ldu in ldus[:top_k]]
    
    def _get_ldus_from_sections(self, doc_id: str, sections: List[Section]) -> List[LDU]:
        """Load LDUs referenced by sections"""
        ldu_ids = set()
        for section in sections:
            ldu_ids.update(section.ldu_ids)
        
        # Load LDUs
        ldu_file = self.ldu_dir / f"{doc_id}_ldus.json"
        if not ldu_file.exists():
            return []
        
        with open(ldu_file) as f:
            ldu_list = json.load(f)
            return [LDU(**ldu_data) for ldu_data in ldu_list if ldu_data['ldu_id'] in ldu_ids]
    
    def _generate_answer(self, query: str, ldus: List[LDU]) -> str:
        """Generate answer from LDUs (simplified - no LLM)"""
        if not ldus:
            return "No relevant information found."
        
        # Combine relevant LDU content
        combined_content = "\n\n".join([ldu.content[:500] for ldu in ldus[:3]])
        
        # Simple answer based on query type
        query_lower = query.lower()
        
        if "revenue" in query_lower or "total" in query_lower:
            # Look for numbers in content
            import re
            numbers = re.findall(r'\$?[\d,]+(?:\.\d+)?', combined_content)
            if numbers:
                return f"Based on the document, relevant figures include: {', '.join(numbers[:5])}. See citations for context."
        
        if "table" in query_lower:
            table_count = sum(1 for ldu in ldus if ldu.chunk_type == "table")
            return f"Found {table_count} tables in the relevant sections. See citations for details."
        
        if "summarize" in query_lower or "summary" in query_lower:
            return f"Summary: {combined_content[:400]}... (See full citations below)"
        
        # Default: return first relevant content
        return f"{combined_content[:400]}... (See citations for full context)"
    
    def _create_citations(self, ldus: List[LDU], doc_id: str) -> List[SourceCitation]:
        """Create citations from LDUs"""
        citations = []
        
        for ldu in ldus[:3]:  # Top 3 sources
            page_ref = ldu.page_refs[0] if ldu.page_refs else 0
            
            # Create bbox dict if available
            bbox_dict = None
            if hasattr(ldu, 'bbox') and ldu.bbox:
                bbox_dict = {
                    "x0": ldu.bbox.x0 if hasattr(ldu.bbox, 'x0') else 0,
                    "y0": ldu.bbox.y0 if hasattr(ldu.bbox, 'y0') else 0,
                    "x1": ldu.bbox.x1 if hasattr(ldu.bbox, 'x1') else 100,
                    "y1": ldu.bbox.y1 if hasattr(ldu.bbox, 'y1') else 100,
                }
            
            citation = SourceCitation(
                document_name=f"{doc_id}.pdf",
                doc_id=doc_id,
                page_number=page_ref,
                bbox=bbox_dict,
                content_hash=ldu.content_hash,
                excerpt=ldu.content[:300],
                ldu_id=ldu.ldu_id
            )
            citations.append(citation)
        
        return citations
    
    def _create_citations_from_facts(self, results: List[Dict]) -> List[SourceCitation]:
        """Create citations from fact table results"""
        citations = []
        
        for result in results[:3]:
            citation = SourceCitation(
                document_name=result.get('document_name', 'unknown'),
                doc_id=result.get('doc_id', 'unknown'),
                page_number=result.get('page_number', 0),
                bbox=result.get('bbox'),
                content_hash=result.get('content_hash', ''),
                excerpt=str(result)
            )
            citations.append(citation)
        
        return citations
    
    def _nl_to_sql(self, query: str) -> str:
        """Convert natural language to SQL (simplified)"""
        # This is a placeholder - real implementation would use LLM
        return "SELECT * FROM facts LIMIT 10"
    
    def _format_structured_results(self, results: List[Dict]) -> str:
        """Format SQL results as natural language"""
        if not results:
            return "No results found."
        
        # Simple formatting
        return f"Found {len(results)} results: {results[0]}"
    
    def _empty_result(self, query: str, method: str) -> ProvenanceChain:
        """Return empty result"""
        return ProvenanceChain(
            query=query,
            answer="No relevant information found.",
            citations=[],
            confidence=0.0,
            retrieval_method=method
        )
    
    def verify_claim(self, claim: str, doc_id: str) -> Dict[str, Any]:
        """
        Audit Mode: Verify a claim against source documents
        
        Args:
            claim: Claim to verify
            doc_id: Document to check
            
        Returns:
            Verification result with citation or unverifiable flag
        """
        logger.info(f"Verifying claim: {claim} | doc_id={doc_id}")
        
        # Search for supporting evidence
        ldus = self.semantic_search(claim, doc_id, top_k=3)
        
        if not ldus:
            return {
                "claim": claim,
                "verified": False,
                "status": "unverifiable",
                "reason": "No supporting evidence found"
            }
        
        # Check if claim is supported
        for ldu in ldus:
            if self._claim_matches_content(claim, ldu.content):
                citation = SourceCitation(
                    document_name=f"{doc_id}.pdf",
                    doc_id=doc_id,
                    page_number=ldu.page_refs[0] if ldu.page_refs else 0,
                    bbox=None,
                    content_hash=ldu.content_hash,
                    excerpt=ldu.content[:200],
                    ldu_id=ldu.ldu_id
                )
                
                return {
                    "claim": claim,
                    "verified": True,
                    "status": "verified",
                    "citation": citation.model_dump()
                }
        
        return {
            "claim": claim,
            "verified": False,
            "status": "unverifiable",
            "reason": "No exact match found"
        }
    
    def _claim_matches_content(self, claim: str, content: str) -> bool:
        """Check if claim is supported by content (simplified)"""
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        # Simple keyword matching
        keywords = [w for w in claim_lower.split() if len(w) > 3]
        matches = sum(1 for kw in keywords if kw in content_lower)
        
        return matches >= len(keywords) * 0.7  # 70% keyword match
