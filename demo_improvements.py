#!/usr/bin/env python3
"""Demo script for Phase 4, 5, 6 improvements"""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.performance import BatchProcessor, CacheManager, ResourceManager
from src.data_quality import PDFValidator, OutputValidator, AnomalyDetector
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

console = Console()


def demo_input_validation():
    """Demo Phase 6: Input Validation"""
    console.print("\n[bold cyan]Phase 6: Input Validation Demo[/bold cyan]")
    
    # Find a sample PDF
    data_dir = Path("data")
    sample_pdfs = list(data_dir.glob("*.pdf"))[:3]
    
    if not sample_pdfs:
        console.print("[yellow]No PDFs found in data/ directory[/yellow]")
        return
    
    table = Table(title="PDF Validation Results")
    table.add_column("File", style="cyan")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Hash (first 16)", style="dim")
    table.add_column("Status", style="green")
    
    for pdf_path in sample_pdfs:
        try:
            PDFValidator.validate_file(str(pdf_path))
            size_mb = pdf_path.stat().st_size / (1024 * 1024)
            hash_val = PDFValidator.compute_hash(str(pdf_path))[:16]
            table.add_row(
                pdf_path.name[:40],
                f"{size_mb:.2f}",
                hash_val,
                "✅ Valid"
            )
        except Exception as e:
            table.add_row(pdf_path.name[:40], "-", "-", f"❌ {str(e)[:30]}")
    
    console.print(table)


async def demo_batch_processing():
    """Demo Phase 4: Batch Processing"""
    console.print("\n[bold cyan]Phase 4: Batch Processing Demo[/bold cyan]")
    
    data_dir = Path("data")
    sample_pdfs = [str(p) for p in list(data_dir.glob("*.pdf"))[:5]]
    
    if not sample_pdfs:
        console.print("[yellow]No PDFs found for batch processing[/yellow]")
        return
    
    console.print(f"Processing {len(sample_pdfs)} documents in batch...")
    
    triage = TriageAgent()
    
    def process_single(path):
        return triage.profile_document(path)
    
    processor = BatchProcessor(max_workers=3)
    
    with console.status("[bold green]Processing batch..."):
        results = await processor.process_batch(sample_pdfs, process_single)
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    
    console.print(f"✅ Processed: {successful}/{len(sample_pdfs)} documents")


def demo_output_validation():
    """Demo Phase 6: Output Validation"""
    console.print("\n[bold cyan]Phase 6: Output Validation Demo[/bold cyan]")
    
    data_dir = Path("data")
    sample_pdf = next(data_dir.glob("*.pdf"), None)
    
    if not sample_pdf:
        console.print("[yellow]No PDFs found for validation demo[/yellow]")
        return
    
    # Process document
    triage = TriageAgent()
    router = ExtractionRouter()
    
    console.print(f"Processing: {sample_pdf.name[:50]}...")
    
    profile = triage.profile_document(str(sample_pdf))
    doc, confidence = router.extract(str(sample_pdf), profile)
    
    # Validate output
    result = OutputValidator.validate_extraction(doc)
    
    # Display results
    panel_content = f"""
[bold]Validation Status:[/bold] {'✅ Valid' if result['valid'] else '❌ Invalid'}
[bold]Quality Score:[/bold] {result['quality_score']:.2f}
[bold]Confidence:[/bold] {confidence:.2f}

[bold]Metrics:[/bold]
  • Text Blocks: {result['metrics']['total_blocks']}
  • Tables: {result['metrics']['total_tables']}
  • Characters: {result['metrics']['total_chars']:,}

[bold]Issues:[/bold] {len(result['issues'])}
"""
    
    if result['issues']:
        panel_content += "\n" + "\n".join(f"  • {issue}" for issue in result['issues'])
    
    console.print(Panel(panel_content, title="Quality Validation", border_style="green"))


def demo_anomaly_detection():
    """Demo Phase 6: Anomaly Detection"""
    console.print("\n[bold cyan]Phase 6: Anomaly Detection Demo[/bold cyan]")
    
    data_dir = Path("data")
    sample_pdfs = list(data_dir.glob("*.pdf"))[:3]
    
    if not sample_pdfs:
        console.print("[yellow]No PDFs found for anomaly detection[/yellow]")
        return
    
    triage = TriageAgent()
    router = ExtractionRouter()
    detector = AnomalyDetector()
    
    all_docs = []
    all_profiles = []
    
    for pdf_path in sample_pdfs:
        try:
            profile = triage.profile_document(str(pdf_path))
            doc, _ = router.extract(str(pdf_path), profile)
            
            anomalies = detector.detect_anomalies(doc, profile)
            
            status = "⚠️  Anomalies" if anomalies else "✅ Normal"
            console.print(f"{status}: {pdf_path.name[:40]}")
            
            if anomalies:
                for anomaly in anomalies:
                    console.print(f"  • {anomaly}", style="yellow")
            
            all_docs.append(doc)
            all_profiles.append(profile)
        except Exception as e:
            console.print(f"❌ Error: {pdf_path.name[:40]} - {str(e)[:50]}")
    
    # Update baseline
    if all_docs:
        detector.update_baseline(all_docs, all_profiles)
        console.print(f"\n[green]Baseline updated from {len(all_docs)} documents[/green]")


def demo_resource_management():
    """Demo Phase 4: Resource Management"""
    console.print("\n[bold cyan]Phase 4: Resource Management Demo[/bold cyan]")
    
    manager = ResourceManager()
    
    # Check memory
    memory = manager.check_memory_usage()
    
    console.print(f"Memory Usage:")
    console.print(f"  • RSS: {memory['rss_mb']:.1f} MB")
    console.print(f"  • Percent: {memory['percent']:.1f}%")
    
    # Cleanup temp files
    count = manager.cleanup_temp_files(max_age_hours=24)
    console.print(f"\n✅ Cleaned up {count} temporary files")


def demo_caching():
    """Demo Phase 4: Caching"""
    console.print("\n[bold cyan]Phase 4: Caching Demo[/bold cyan]")
    
    data_dir = Path("data")
    sample_pdf = next(data_dir.glob("*.pdf"), None)
    
    if not sample_pdf:
        console.print("[yellow]No PDFs found for caching demo[/yellow]")
        return
    
    # Clear cache
    CacheManager.clear_cache()
    
    # First call (cache miss)
    import time
    start = time.time()
    profile1 = CacheManager.get_cached_profile(str(sample_pdf))
    time1 = time.time() - start
    
    # Second call (cache hit)
    start = time.time()
    profile2 = CacheManager.get_cached_profile(str(sample_pdf))
    time2 = time.time() - start
    
    console.print(f"First call (cache miss): {time1*1000:.1f}ms")
    console.print(f"Second call (cache hit): {time2*1000:.1f}ms")
    console.print(f"[green]Speedup: {time1/time2:.1f}x faster[/green]")
    
    # Cache stats
    info = CacheManager.get_cached_profile.cache_info()
    console.print(f"\nCache Stats:")
    console.print(f"  • Hits: {info.hits}")
    console.print(f"  • Misses: {info.misses}")
    console.print(f"  • Size: {info.currsize}/{info.maxsize}")


async def main():
    """Run all demos"""
    console.print(Panel.fit(
        "[bold cyan]Document Intelligence Refinery[/bold cyan]\n"
        "[white]Phase 4, 5, 6 Improvements Demo[/white]",
        border_style="cyan"
    ))
    
    try:
        # Phase 6: Data Quality & Validation
        demo_input_validation()
        demo_output_validation()
        demo_anomaly_detection()
        
        # Phase 4: Performance Optimization
        await demo_batch_processing()
        demo_caching()
        demo_resource_management()
        
        console.print("\n[bold green]✅ All demos completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
