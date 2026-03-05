#!/usr/bin/env python3
"""Fast Demo: Test PDF classification without heavy initialization"""

from pathlib import Path
from src.utils.pdf_classifier import PDFClassifier
from rich.console import Console
from rich.table import Table as RichTable

console = Console()

console.print("\n[bold cyan]Fast Demo: PDF Classification[/bold cyan]")
console.print("[dim]Tests Tier routing without Docling initialization[/dim]\n")

# Test documents
test_docs = [
    "data/test_native_digital.pdf",
    "data/2013-E.C-Assigned-regular-budget-and-expense.pdf",
]

# Initialize classifier (fast, no heavy models)
console.print("[yellow]Initializing classifier...[/yellow]")
classifier = PDFClassifier()
console.print("[green]✓ Classifier ready[/green]\n")

# Results table
table = RichTable(title="Document Classification Results")
table.add_column("Document", style="cyan")
table.add_column("Type", style="yellow")
table.add_column("Tier", style="green")
table.add_column("Strategy", style="magenta")

for pdf_path in test_docs:
    if not Path(pdf_path).exists():
        console.print(f"[red]Skipping {pdf_path} (not found)[/red]")
        continue
    
    console.print(f"[bold]Classifying:[/bold] {Path(pdf_path).name}")
    
    # Classify (fast, <1 second)
    is_native = classifier.is_native_pdf(pdf_path)
    
    doc_type = "Native Digital" if is_native else "Scanned Image"
    tier = "Tier 1" if is_native else "Tier 2"
    strategy = "Docling + Camelot + PyMuPDF" if is_native else "Gemini Vision"
    
    console.print(f"  Type: {doc_type}")
    console.print(f"  Tier: {tier}")
    console.print(f"  Strategy: {strategy}\n")
    
    table.add_row(
        Path(pdf_path).name[:40],
        doc_type,
        tier,
        strategy
    )

console.print(table)

console.print("\n[bold green]✓ Classification Complete![/bold green]")
console.print("\n[dim]Next steps:[/dim]")
console.print("  1. Native PDFs → Use Tier 1 (free, ~15s)")
console.print("  2. Scanned PDFs → Use Tier 2 ($0.0002/page, ~5s)")
console.print("\n[dim]To run full extraction (slow):[/dim]")
console.print("  python3 demo_hybrid_pipeline.py")
