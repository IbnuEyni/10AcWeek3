#!/usr/bin/env python3
"""Demo: Stage 3 Semantic Chunking Engine"""

from pathlib import Path
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel

console = Console()


def demo_stage3_chunking():
    """Demonstrate Stage 3 semantic chunking"""
    
    console.print("\n[bold cyan]Stage 3: Semantic Chunking Engine Demo[/bold cyan]\n")
    
    # Select a document from corpus
    pdf_path = "data/Consumer Price Index July 2025.pdf"
    
    if not Path(pdf_path).exists():
        console.print(f"[red]Document not found: {pdf_path}[/red]")
        return
    
    console.print(f"[green]Processing:[/green] {pdf_path}\n")
    
    # Stage 1: Triage
    console.print("[yellow]Stage 1:[/yellow] Document Profiling...")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    console.print(f"  ✓ Origin: {profile.origin_type}")
    console.print(f"  ✓ Layout: {profile.layout_complexity}")
    console.print(f"  ✓ Domain: {profile.domain_hint}")
    console.print(f"  ✓ Pages: {profile.total_pages}\n")
    
    # Stage 2: Extraction
    console.print("[yellow]Stage 2:[/yellow] Content Extraction...")
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    
    console.print(f"  ✓ Text blocks: {len(extracted_doc.text_blocks)}")
    console.print(f"  ✓ Tables: {len(extracted_doc.tables)}")
    console.print(f"  ✓ Figures: {len(extracted_doc.figures)}")
    console.print(f"  ✓ Confidence: {extracted_doc.confidence_score:.2f}\n")
    
    # Stage 3: Semantic Chunking
    console.print("[yellow]Stage 3:[/yellow] Semantic Chunking...")
    chunking_agent = ChunkingAgent()
    ldus = chunking_agent.process_document(extracted_doc, pdf_path)
    
    console.print(f"  ✓ Total LDUs: {len(ldus)}\n")
    
    # Analyze LDU distribution
    chunk_types = {}
    for ldu in ldus:
        chunk_types[ldu.chunk_type] = chunk_types.get(ldu.chunk_type, 0) + 1
    
    # Display results
    table = RichTable(title="LDU Distribution by Type")
    table.add_column("Chunk Type", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")
    
    for chunk_type, count in sorted(chunk_types.items()):
        percentage = (count / len(ldus)) * 100
        table.add_row(chunk_type, str(count), f"{percentage:.1f}%")
    
    console.print(table)
    console.print()
    
    # Show sample LDUs
    console.print("[bold]Sample LDUs:[/bold]\n")
    
    for i, ldu in enumerate(ldus[:3]):
        content_preview = ldu.content[:150] + "..." if len(ldu.content) > 150 else ldu.content
        
        panel = Panel(
            f"[cyan]Type:[/cyan] {ldu.chunk_type}\n"
            f"[cyan]Pages:[/cyan] {ldu.page_refs}\n"
            f"[cyan]Tokens:[/cyan] {ldu.token_count}\n"
            f"[cyan]Section:[/cyan] {ldu.parent_section or 'N/A'}\n"
            f"[cyan]Hash:[/cyan] {ldu.content_hash}\n\n"
            f"[yellow]Content:[/yellow]\n{content_preview}",
            title=f"LDU {i+1}: {ldu.ldu_id}",
            border_style="green"
        )
        console.print(panel)
    
    # Show chunking rules applied
    console.print("\n[bold]Chunking Rules Applied:[/bold]\n")
    rules_table = RichTable()
    rules_table.add_column("Rule", style="cyan")
    rules_table.add_column("Description", style="white")
    rules_table.add_column("Status", style="green")
    
    rules_table.add_row(
        "1. Table Integrity",
        "Tables never split across chunks",
        f"✓ {sum(1 for ldu in ldus if ldu.chunk_type == 'table')} tables preserved"
    )
    rules_table.add_row(
        "2. Figure-Caption Binding",
        "Figures kept with captions",
        f"✓ {sum(1 for ldu in ldus if ldu.chunk_type == 'figure')} figures bound"
    )
    rules_table.add_row(
        "3. List Coherence",
        "Lists kept as single units",
        f"✓ {sum(1 for ldu in ldus if ldu.chunk_type == 'list')} lists preserved"
    )
    rules_table.add_row(
        "4. Section Hierarchy",
        "Parent section metadata attached",
        f"✓ {sum(1 for ldu in ldus if ldu.parent_section)} LDUs with section"
    )
    rules_table.add_row(
        "5. Cross-References",
        "Content hash for deduplication",
        f"✓ All {len(ldus)} LDUs hashed"
    )
    
    console.print(rules_table)
    
    console.print(f"\n[green]✓ Stage 3 Complete![/green]")
    console.print(f"[dim]LDUs saved to: .refinery/ldus/{profile.doc_id}_ldus.json[/dim]\n")


if __name__ == "__main__":
    demo_stage3_chunking()
