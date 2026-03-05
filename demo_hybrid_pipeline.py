#!/usr/bin/env python3
"""Demo: Hybrid Extraction Pipeline (Tier 1 + Tier 2)"""

from pathlib import Path
from src.agents.triage import TriageAgent
from src.strategies.hybrid_pipeline import HybridExtractionPipeline
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel
import time

console = Console()


def demo_hybrid_pipeline():
    """Demonstrate hybrid extraction pipeline"""
    
    console.print("\n[bold cyan]Hybrid Extraction Pipeline Demo[/bold cyan]")
    console.print("[dim]Tier 1: Native PDFs | Tier 2: Scanned PDFs[/dim]\n")
    
    # Test documents
    test_docs = [
        "data/test_native_digital.pdf",  # Native PDF we created
        "data/2013-E.C-Assigned-regular-budget-and-expense.pdf"  # Scanned PDF
    ]
    
    # Initialize pipeline
    console.print("[yellow]Initializing hybrid pipeline...[/yellow]")
    triage = TriageAgent()
    pipeline = HybridExtractionPipeline()
    console.print("[green]✓ Pipeline ready[/green]\n")
    
    results = []
    
    for pdf_path in test_docs:
        if not Path(pdf_path).exists():
            console.print(f"[red]Skipping {pdf_path} (not found)[/red]\n")
            continue
        
        console.print(f"[bold]Processing:[/bold] {Path(pdf_path).name}")
        console.print(f"{'='*60}")
        
        # Stage 1: Triage
        console.print("[yellow]Stage 1:[/yellow] Document Profiling...")
        profile = triage.profile_document(pdf_path)
        console.print(f"  ✓ Pages: {profile.total_pages}")
        console.print(f"  ✓ Origin: {profile.origin_type}")
        console.print(f"  ✓ Layout: {profile.layout_complexity}\n")
        
        # Stage 2: Hybrid Extraction
        console.print("[yellow]Stage 2:[/yellow] Hybrid Extraction...")
        start_time = time.time()
        
        try:
            extracted_doc, confidence = pipeline.extract(pdf_path, profile)
            elapsed = time.time() - start_time
            
            console.print(f"  ✓ Strategy: {extracted_doc.extraction_strategy}")
            console.print(f"  ✓ Confidence: {confidence:.2f}")
            console.print(f"  ✓ Time: {elapsed:.2f}s")
            console.print(f"  ✓ Text blocks: {len(extracted_doc.text_blocks)}")
            console.print(f"  ✓ Tables: {len(extracted_doc.tables)}")
            console.print(f"  ✓ Figures: {len(extracted_doc.figures)}\n")
            
            results.append({
                'filename': Path(pdf_path).name,
                'strategy': extracted_doc.extraction_strategy,
                'confidence': confidence,
                'time': elapsed,
                'text_blocks': len(extracted_doc.text_blocks),
                'tables': len(extracted_doc.tables),
                'figures': len(extracted_doc.figures)
            })
            
        except Exception as e:
            console.print(f"[red]✗ Extraction failed: {e}[/red]\n")
            continue
    
    # Summary table
    if results:
        console.print("\n[bold]Extraction Summary[/bold]")
        console.print(f"{'='*60}\n")
        
        table = RichTable(title="Performance Metrics")
        table.add_column("Document", style="cyan")
        table.add_column("Strategy", style="yellow")
        table.add_column("Time (s)", justify="right", style="green")
        table.add_column("Confidence", justify="right", style="magenta")
        table.add_column("Elements", justify="right", style="blue")
        
        for r in results:
            table.add_row(
                r['filename'][:30],
                r['strategy'],
                f"{r['time']:.2f}",
                f"{r['confidence']:.2f}",
                f"{r['text_blocks']}T + {r['tables']}Tb + {r['figures']}F"
            )
        
        console.print(table)
        
        # Cost analysis
        console.print("\n[bold]Cost Analysis[/bold]")
        tier1_docs = [r for r in results if 'tier1' in r['strategy']]
        tier2_docs = [r for r in results if 'tier2' in r['strategy']]
        
        tier2_cost = len(tier2_docs) * 0.0002  # Gemini cost per page (simplified)
        
        console.print(f"  Tier 1 (Native): {len(tier1_docs)} docs - $0.00")
        console.print(f"  Tier 2 (Scanned): {len(tier2_docs)} docs - ${tier2_cost:.4f}")
        console.print(f"  [bold green]Total Cost: ${tier2_cost:.4f}[/bold green]\n")


if __name__ == "__main__":
    demo_hybrid_pipeline()
