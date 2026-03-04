from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Section(BaseModel):
    section_id: str = Field(..., min_length=1, description="Unique section identifier")
    title: str = Field(..., min_length=1, description="Section title/heading")
    page_start: int = Field(..., ge=0, description="Starting page number")
    page_end: int = Field(..., ge=0, description="Ending page number")
    level: int = Field(ge=0, description="Hierarchy level, 0 is root")
    
    # Content metadata
    summary: Optional[str] = Field(None, description="Section summary")
    key_entities: List[str] = Field(default_factory=list, description="Named entities in section")
    data_types_present: List[str] = Field(default_factory=list, description="tables, figures, equations")
    
    # Hierarchy
    parent_id: Optional[str] = Field(None, description="Parent section ID")
    child_sections: List['Section'] = Field(default_factory=list, description="Nested subsections")
    
    # LDU references
    ldu_ids: List[str] = Field(default_factory=list, description="LDUs contained in this section")
    
    @field_validator('page_end')
    @classmethod
    def validate_page_range(cls, v, info):
        """Ensure page_end >= page_start"""
        if 'page_start' in info.data and v < info.data['page_start']:
            raise ValueError("page_end must be >= page_start")
        return v


class PageIndex(BaseModel):
    """Hierarchical navigation structure for document"""
    doc_id: str = Field(..., min_length=1, description="Document identifier")
    filename: str = Field(..., min_length=1, description="Source filename")
    root_sections: List[Section] = Field(..., min_length=1, description="Top-level sections")
    total_pages: int = Field(..., gt=0, description="Total page count")
    
    @field_validator('root_sections')
    @classmethod
    def validate_sections(cls, v):
        """Ensure sections don't overlap and cover valid page ranges"""
        for section in v:
            if section.page_start < 0 or section.page_end < section.page_start:
                raise ValueError(f"Invalid page range in section {section.section_id}")
        return v
    
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
