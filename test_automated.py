#!/usr/bin/env python3
"""
Automated End-to-End Test - No user input required
Complete document processing pipeline demonstration
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.data_quality import PDFValidator, OutputValidator, AnomalyDetector
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.performance import CacheManager, ResourceManager

console = Console()


def main():
    """Run complete automated test"""
    
    console.print(Panel.fit(
        "[bold cyan]Document Intelligence Refinery[/bold cyan]\n"
        "[white]Automated End-to-End Test[/white]",
        border_style="cyan"
    ))
    
    # Find PDF
    data_dir = Path("data")
    pdfs = list(data_dir.glob("*.pdf"))
    
    if not pdfs:
        console.print("[red]❌ No PDFs found in data/ directory[/red]")
        return
    
    pdf_path = str(pdfs[0])
    console.print(f"\n[cyan]Testing with: {Path(pdf_path).name}[/cyan]\n")
    
    # STEP 1: Validate Input
    console.print("[bold]STEP 1: Input Validation[/bold]")
    try:
        PDFValidator.validate_file(pdf_path)
        file_hash = PDFValidator.compute_hash(pdf_path)
        size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
        console.print(f"  ✅ Valid PDF ({size_mb:.2f} MB)")
        console.print(f"  ✅ Hash: {file_hash[:16]}...")
    except Exception as e:
        console.print(f"  ❌ Validation failed: {e}")
        return
    
    # STEP 2: Triage
    console.print("\n[bold]STEP 2: Document Triage[/bold]")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    console.print(f"  ✅ Origin: {profile.origin_type}")
    console.print(f"  ✅ Layout: {profile.layout_complexity}")
    console.print(f"  ✅ Domain: {profile.domain_hint}")
    console.print(f"  ✅ Strategy: {profile.estimated_extraction_cost}")
    console.print(f"  ✅ Pages: {profile.total_pages}")
    
    # STEP 3: Extract
    console.print("\n[bold]STEP 3: Content Extraction[/bold]")
    router = ExtractionRouter()
    doc, confidence = router.extract(pdf_path, profile)
    console.print(f"  ✅ Strategy: {doc.extraction_strategy}")
    console.print(f"  ✅ Confidence: {confidence:.2f}")
    console.print(f"  ✅ Text Blocks: {len(doc.text_blocks)}")
    console.print(f"  ✅ Tables: {len(doc.tables)}")
    console.print(f"  ✅ Characters: {sum(len(b.content) for b in doc.text_blocks):,}")
    
    # STEP 4: Validate Output
    console.print("\n[bold]STEP 4: Output Validation[/bold]")
    result = OutputValidator.validate_extraction(doc)
    console.print(f"  ✅ Valid: {result['valid']}")
    console.print(f"  ✅ Quality Score: {result['quality_score']:.2f}")
    if result['issues']:
        console.print(f"  ⚠️  Issues: {len(result['issues'])}")
        for issue in result['issues']:
            console.print(f"     • {issue}")
    
    # STEP 5: Anomaly Detection
    console.print("\n[bold]STEP 5: Anomaly Detection[/bold]")
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(doc, profile)
    if anomalies:
        console.print(f"  ⚠️  Anomalies: {len(anomalies)}")
        for anomaly in anomalies:
            console.print(f"     • {anomaly}")
    else:
        console.print("  ✅ No anomalies detected")
    
    # STEP 6: Resources
    console.print("\n[bold]STEP 6: Resource Usage[/bold]")
    manager = ResourceManager()
    memory = manager.check_memory_usage()
    cache_info = CacheManager.get_cached_profile.cache_info()
    console.print(f"  ✅ Memory: {memory['rss_mb']:.1f} MB ({memory['percent']:.1f}%)")
    console.print(f"  ✅ Cache: {cache_info.hits} hits, {cache_info.misses} misses")
    
    # STEP 7: Sample Content
    console.print("\n[bold]STEP 7: Sample Extracted Content[/bold]")
    if doc.text_blocks:
        sample = doc.text_blocks[0].content[:300]
        console.print(f"  [dim]{sample}...[/dim]")
    
    # Final Summary
    console.print("\n" + "="*60)
    summary = Panel(
        f"[bold green]✅ Test Complete![/bold green]\n\n"
        f"Document: {Path(pdf_path).name}\n"
        f"Pages: {profile.total_pages}\n"
        f"Strategy: {doc.extraction_strategy}\n"
        f"Confidence: {confidence:.2f}\n"
        f"Quality: {result['quality_score']:.2f}\n"
        f"Blocks: {len(doc.text_blocks)}\n"
        f"Tables: {len(doc.tables)}\n"
        f"Valid: {result['valid']}",
        border_style="green"
    )
    console.print(summary)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
