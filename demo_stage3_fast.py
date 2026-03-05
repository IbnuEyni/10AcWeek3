#!/usr/bin/env python3
"""Fast Demo: Stage 3 Semantic Chunking (Native Digital PDF)"""

from pathlib import Path
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent
from rich.console import Console
from rich.table import Table as RichTable

console = Console()


def demo_stage3_fast():
    """Fast demo using native digital PDF"""
    
    console.print("\n[bold cyan]Stage 3: Semantic Chunking - Fast Demo[/bold cyan]\n")
    
    # Use a smaller native digital PDF
    pdf_files = [
        "data/Consumer Price Index March 2025.pdf",
        "data/tax_expenditure_ethiopia_2021_22.pdf",
        "data/fta_performance_survey_final_report_2022.pdf"
    ]
    
    pdf_path = None
    for pdf in pdf_files:
        if Path(pdf).exists():
            pdf_path = pdf
            break
    
    if not pdf_path:
        console.print("[red]No suitable PDF found. Using mock data.[/red]")
        return
    
    console.print(f"[green]Processing:[/green] {pdf_path}\n")
    
    # Stage 1: Triage
    console.print("[yellow]Stage 1:[/yellow] Profiling...")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    console.print(f"  ✓ {profile.origin_type} | {profile.layout_complexity} | {profile.total_pages} pages\n")
    
    # Stage 2: Extraction
    console.print("[yellow]Stage 2:[/yellow] Extracting...")
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    console.print(f"  ✓ {len(extracted_doc.text_blocks)} blocks | {len(extracted_doc.tables)} tables | {len(extracted_doc.figures)} figures\n")
    
    # Stage 3: Chunking
    console.print("[yellow]Stage 3:[/yellow] Chunking...")
    chunking_agent = ChunkingAgent()
    ldus = chunking_agent.process_document(extracted_doc, pdf_path)
    console.print(f"  ✓ Created {len(ldus)} LDUs\n")
    
    # Show distribution
    chunk_types = {}
    for ldu in ldus:
        chunk_types[ldu.chunk_type] = chunk_types.get(ldu.chunk_type, 0) + 1
    
    table = RichTable(title="LDU Distribution")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    for chunk_type, count in sorted(chunk_types.items()):
        table.add_row(chunk_type, str(count))
    
    console.print(table)
    
    # Show sample
    console.print(f"\n[bold]Sample LDU:[/bold]")
    if ldus:
        ldu = ldus[0]
        preview = ldu.content[:200] + "..." if len(ldu.content) > 200 else ldu.content
        console.print(f"  ID: {ldu.ldu_id}")
        console.print(f"  Type: {ldu.chunk_type}")
        console.print(f"  Pages: {ldu.page_refs}")
        console.print(f"  Tokens: {ldu.token_count}")
        console.print(f"  Content: {preview}\n")
    
    console.print("[green]✓ Stage 3 Complete![/green]\n")


if __name__ == "__main__":
    demo_stage3_fast()
