from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Section(BaseModel):
    section_id: str
    title: str
    page_start: int
    page_end: int
    level: int = Field(ge=0, description="Hierarchy level, 0 is root")
    
    # Content metadata
    summary: Optional[str] = None
    key_entities: List[str] = Field(default_factory=list)
    data_types_present: List[str] = Field(default_factory=list, description="tables, figures, equations")
    
    # Hierarchy
    parent_id: Optional[str] = None
    child_sections: List['Section'] = Field(default_factory=list)
    
    # LDU references
    ldu_ids: List[str] = Field(default_factory=list)


class PageIndex(BaseModel):
    """Hierarchical navigation structure for document"""
    doc_id: str
    filename: str
    root_sections: List[Section]
    total_pages: int
    
    def find_section_by_page(self, page: int) -> Optional[Section]:
        """Find section containing given page"""
        def search(sections: List[Section]) -> Optional[Section]:
            for section in sections:
                if section.page_start <= page <= section.page_end:
                    child_result = search(section.child_sections)
                    return child_result if child_result else section
            return None
        return search(self.root_sections)
    
    def find_section_by_query(self, query: str) -> List[Section]:
        """Find sections relevant to query (simple keyword match)"""
        results = []
        def search(sections: List[Section]):
            for section in sections:
                if query.lower() in section.title.lower() or \
                   (section.summary and query.lower() in section.summary.lower()):
                    results.append(section)
                search(section.child_sections)
        search(self.root_sections)
        return results
