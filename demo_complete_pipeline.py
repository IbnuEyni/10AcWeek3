#!/usr/bin/env python3
"""
Complete End-to-End Demo: Document Intelligence Refinery
Demonstrates full pipeline from PDF input to chunked LDUs (Stages 1-3)
"""

import time
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent

console = Console()


def print_header():
    """Print demo header"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]Document Intelligence Refinery - Complete Pipeline Demo[/bold cyan]")
    console.print("[dim]Stages 1-3: Triage → Extraction → Semantic Chunking[/dim]")
    console.print("="*70 + "\n")


def print_stage_header(stage_num: int, stage_name: str):
    """Print stage header"""
    console.print(f"\n[bold yellow]Stage {stage_num}: {stage_name}[/bold yellow]")
    console.print("-" * 70)


def demo_complete_pipeline(pdf_path: str):
    """
    Run complete pipeline on a PDF document
    
    Args:
        pdf_path: Path to PDF file
    """
    # Validate file exists
    if not Path(pdf_path).exists():
        console.print(f"[red]✗ File not found: {pdf_path}[/red]")
        return
    
    file_size = Path(pdf_path).stat().st_size / (1024 * 1024)
    console.print(f"[cyan]Processing:[/cyan] {Path(pdf_path).name}")
    console.print(f"[cyan]File size:[/cyan] {file_size:.1f} MB\n")
    
    # Initialize agents
    console.print("[yellow]Initializing agents...[/yellow]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Loading...", total=None)
        triage = TriageAgent()
        router = ExtractionRouter()
        chunker = ChunkingAgent()
        progress.update(task, completed=True)
    console.print("[green]✓ Agents ready[/green]\n")
    
    # ========================================================================
    # STAGE 1: TRIAGE (Document Profiling)
    # ========================================================================
    print_stage_header(1, "Document Profiling (Triage)")
    
    start_time = time.time()
    profile = triage.profile_document(pdf_path)
    stage1_time = time.time() - start_time
    
    # Display profile
    profile_table = RichTable(title="Document Profile", show_header=False)
    profile_table.add_column("Property", style="cyan", width=25)
    profile_table.add_column("Value", style="white")
    
    profile_table.add_row("Document ID", profile.doc_id)
    profile_table.add_row("Pages", str(profile.total_pages))
    profile_table.add_row("Origin Type", f"[bold]{profile.origin_type}[/bold]")
    profile_table.add_row("Layout", profile.layout_complexity)
    profile_table.add_row("Domain", profile.domain_hint)
    profile_table.add_row("Extraction Cost", profile.estimated_extraction_cost)
    profile_table.add_row("Character Density", f"{profile.character_density:.0f} chars/page")
    profile_table.add_row("Image Ratio", f"{profile.image_ratio:.1%}")
    
    console.print(profile_table)
    console.print(f"\n[green]✓ Stage 1 complete in {stage1_time:.2f}s[/green]")
    
    # ========================================================================
    # STAGE 2: EXTRACTION (Content Extraction)
    # ========================================================================
    print_stage_header(2, "Content Extraction")
    
    console.print(f"[yellow]Strategy:[/yellow] {profile.estimated_extraction_cost}")
    console.print("[dim]Extracting text, tables, and figures...[/dim]\n")
    
    start_time = time.time()
    extracted_doc = router.extract(pdf_path, profile)
    stage2_time = time.time() - start_time
    
    # Display extraction results
    extraction_table = RichTable(title="Extraction Results")
    extraction_table.add_column("Component", style="cyan")
    extraction_table.add_column("Count", justify="right", style="green")
    extraction_table.add_column("Details", style="dim")
    
    extraction_table.add_row(
        "Text Blocks",
        str(len(extracted_doc.text_blocks)),
        f"{sum(len(b.content) for b in extracted_doc.text_blocks):,} chars"
    )
    extraction_table.add_row(
        "Tables",
        str(len(extracted_doc.tables)),
        f"{sum(len(t.rows) for t in extracted_doc.tables)} rows total"
    )
    extraction_table.add_row(
        "Figures",
        str(len(extracted_doc.figures)),
        f"{sum(1 for f in extracted_doc.figures if f.caption) } with captions"
    )
    
    console.print(extraction_table)
    
    # Display confidence and strategy
    console.print(f"\n[cyan]Strategy Used:[/cyan] {extracted_doc.extraction_strategy}")
    console.print(f"[cyan]Confidence:[/cyan] {extracted_doc.confidence_score:.2%}")
    console.print(f"[green]✓ Stage 2 complete in {stage2_time:.2f}s[/green]")
    
    # ========================================================================
    # STAGE 3: SEMANTIC CHUNKING (LDU Creation)
    # ========================================================================
    print_stage_header(3, "Semantic Chunking")
    
    console.print("[dim]Creating Logical Document Units (LDUs)...[/dim]\n")
    
    start_time = time.time()
    ldus = chunker.process_document(extracted_doc, pdf_path)
    stage3_time = time.time() - start_time
    
    # Analyze LDU distribution
    chunk_types = {}
    total_tokens = 0
    for ldu in ldus:
        chunk_types[ldu.chunk_type] = chunk_types.get(ldu.chunk_type, 0) + 1
        total_tokens += ldu.token_count
    
    # Display LDU statistics
    ldu_table = RichTable(title="LDU Distribution")
    ldu_table.add_column("Type", style="cyan")
    ldu_table.add_column("Count", justify="right", style="green")
    ldu_table.add_column("Percentage", justify="right", style="yellow")
    
    for chunk_type, count in sorted(chunk_types.items()):
        percentage = (count / len(ldus)) * 100
        ldu_table.add_row(chunk_type, str(count), f"{percentage:.1f}%")
    
    ldu_table.add_row("[bold]Total", f"[bold]{len(ldus)}", "[bold]100.0%")
    
    console.print(ldu_table)
    console.print(f"\n[cyan]Total Tokens:[/cyan] {total_tokens:,}")
    console.print(f"[cyan]Avg Tokens/LDU:[/cyan] {total_tokens/len(ldus):.0f}")
    console.print(f"[green]✓ Stage 3 complete in {stage3_time:.2f}s[/green]")
    
    # ========================================================================
    # SAMPLE LDUs
    # ========================================================================
    console.print("\n[bold]Sample LDUs:[/bold]")
    
    for i, ldu in enumerate(ldus[:2]):  # Show first 2 LDUs
        content_preview = ldu.content[:200] + "..." if len(ldu.content) > 200 else ldu.content
        
        panel = Panel(
            f"[cyan]Type:[/cyan] {ldu.chunk_type}\n"
            f"[cyan]Pages:[/cyan] {ldu.page_refs}\n"
            f"[cyan]Tokens:[/cyan] {ldu.token_count}\n"
            f"[cyan]Section:[/cyan] {ldu.parent_section or 'N/A'}\n"
            f"[cyan]Hash:[/cyan] {ldu.content_hash[:16]}...\n\n"
            f"[yellow]Content:[/yellow]\n{content_preview}",
            title=f"LDU {i+1}: {ldu.ldu_id}",
            border_style="green"
        )
        console.print(panel)
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    console.print("\n" + "="*70)
    console.print("[bold green]✓ Pipeline Complete![/bold green]")
    console.print("="*70 + "\n")
    
    # Performance summary
    total_time = stage1_time + stage2_time + stage3_time
    
    summary_table = RichTable(title="Performance Summary")
    summary_table.add_column("Stage", style="cyan")
    summary_table.add_column("Time", justify="right", style="green")
    summary_table.add_column("Percentage", justify="right", style="yellow")
    
    summary_table.add_row("Stage 1 (Triage)", f"{stage1_time:.2f}s", f"{(stage1_time/total_time)*100:.1f}%")
    summary_table.add_row("Stage 2 (Extraction)", f"{stage2_time:.2f}s", f"{(stage2_time/total_time)*100:.1f}%")
    summary_table.add_row("Stage 3 (Chunking)", f"{stage3_time:.2f}s", f"{(stage3_time/total_time)*100:.1f}%")
    summary_table.add_row("[bold]Total", f"[bold]{total_time:.2f}s", "[bold]100.0%")
    
    console.print(summary_table)
    
    # Output locations
    console.print("\n[bold]Output Locations:[/bold]")
    console.print(f"  Profile: [dim].refinery/profiles/{profile.doc_id}.json[/dim]")
    console.print(f"  LDUs: [dim].refinery/ldus/{profile.doc_id}_ldus.json[/dim]")
    console.print(f"  Ledger: [dim].refinery/extraction_ledger.jsonl[/dim]")
    
    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Stage 4: Build PageIndex for spatial search")
    console.print("  2. Stage 5: Query Interface for document Q&A")
    console.print("  3. Process more documents in batch")
    
    console.print()


def main():
    """Main demo entry point"""
    import sys
    
    print_header()
    
    # Check for command line argument
    if len(sys.argv) > 1:
        default_pdf = sys.argv[1]
        console.print(f"[cyan]Using provided PDF:[/cyan] {default_pdf}\n")
    else:
        # Default test document
        default_pdf = "data/tax_expenditure_ethiopia_2021_22.pdf"
    
    # Check if file exists, otherwise prompt
    if not Path(default_pdf).exists():
        console.print(f"[yellow]Default PDF not found: {default_pdf}[/yellow]")
        console.print("\n[bold]Available PDFs:[/bold]")
        
        data_dir = Path("data")
        if data_dir.exists():
            pdfs = list(data_dir.glob("*.pdf"))
            if pdfs:
                for i, pdf in enumerate(pdfs[:5], 1):
                    console.print(f"  {i}. {pdf.name}")
                
                default_pdf = str(pdfs[0])
                console.print(f"\n[cyan]Using:[/cyan] {default_pdf}\n")
            else:
                console.print("[red]No PDFs found in data/ directory[/red]")
                return
        else:
            console.print("[red]data/ directory not found[/red]")
            return
    
    # Run demo
    try:
        demo_complete_pipeline(default_pdf)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()
