"""Performance optimization utilities"""

import asyncio
from typing import List, Dict, Any, Callable
from pathlib import Path
from functools import lru_cache
from .models.document_profile import DocumentProfile
from .models.extracted_document import ExtractedDocument
from .logging_config import get_logger

logger = get_logger("performance")


class BatchProcessor:
    """Batch process multiple documents efficiently"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    async def process_batch(
        self, 
        pdf_paths: List[str], 
        process_fn: Callable
    ) -> List[tuple]:
        """Process multiple documents concurrently"""
        logger.info(f"Processing batch of {len(pdf_paths)} documents")
        
        tasks = [self._process_single(path, process_fn) for path in pdf_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Batch complete: {successful}/{len(pdf_paths)} successful")
        
        return results
    
    async def _process_single(self, path: str, process_fn: Callable) -> Any:
        """Process single document asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, process_fn, path)
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            return e


class CacheManager:
    """Simple caching layer for document profiles"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_cached_profile(pdf_path: str) -> DocumentProfile:
        """Cache document profiles to avoid reprocessing"""
        from .agents.triage import TriageAgent
        agent = TriageAgent()
        return agent.profile_document(pdf_path)
    
    @staticmethod
    def clear_cache():
        """Clear profile cache"""
        CacheManager.get_cached_profile.cache_clear()
        logger.info("Cache cleared")


class ResourceManager:
    """Manage resources and cleanup"""
    
    def __init__(self, temp_dir: Path = Path(".refinery/temp")):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Remove old temporary files"""
        import time
        
        count = 0
        cutoff = time.time() - (max_age_hours * 3600)
        
        for file in self.temp_dir.glob("*"):
            if file.stat().st_mtime < cutoff:
                file.unlink()
                count += 1
        
        logger.info(f"Cleaned up {count} temporary files")
        return count
    
    def check_memory_usage(self) -> Dict[str, float]:
        """Check current memory usage"""
        import psutil
        process = psutil.Process()
        
        return {
            "rss_mb": process.memory_info().rss / 1024 / 1024,
            "percent": process.memory_percent()
        }


class LazyPDFLoader:
    """Lazy load PDF pages to reduce memory"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._pdf = None
    
    def __enter__(self):
        import pdfplumber
        self._pdf = pdfplumber.open(self.pdf_path)
        return self
    
    def __exit__(self, *args):
        if self._pdf:
            self._pdf.close()
    
    def get_page(self, page_num: int):
        """Load single page on demand"""
        if self._pdf and page_num < len(self._pdf.pages):
            return self._pdf.pages[page_num]
        return None
