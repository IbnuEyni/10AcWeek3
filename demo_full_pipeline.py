#!/usr/bin/env python3
"""
Complete 5-Stage Pipeline Demo: Document Intelligence Refinery
Stages 1-5: Triage → Extraction → Chunking → PageIndex → Query Interface
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
from src.agents.pageindex_builder import PageIndexBuilder
from src.agents.query_agent import QueryAgent
from src.utils.fact_extractor import FactExtractor

console = Console()


def print_stage_header(stage_num: int, stage_name: str):
    """Print stage header"""
    console.print(f"\n[bold yellow]Stage {stage_num}: {stage_name}[/bold yellow]")
    console.print("-" * 70)


def demo_full_pipeline(pdf_path: str):
    """Run complete 5-stage pipeline"""
    
    console.print("\n" + "="*70)
    console.print("[bold cyan]Document Intelligence Refinery - Full Pipeline[/bold cyan]")
    console.print("[dim]Stages 1-5: Complete End-to-End Processing[/dim]")
    console.print("="*70 + "\n")
    
    # Validate file
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
        indexer = PageIndexBuilder()
        query_agent = QueryAgent()
        fact_extractor = FactExtractor()
        progress.update(task, completed=True)
    console.print("[green]✓ All agents ready[/green]\n")
    
    stage_times = {}
    
    # ========================================================================
    # STAGE 1: TRIAGE
    # ========================================================================
    print_stage_header(1, "Document Profiling (Triage)")
    
    start_time = time.time()
    profile = triage.profile_document(pdf_path)
    stage_times['triage'] = time.time() - start_time
    
    console.print(f"[cyan]Origin:[/cyan] {profile.origin_type}")
    console.print(f"[cyan]Layout:[/cyan] {profile.layout_complexity}")
    console.print(f"[cyan]Strategy:[/cyan] {profile.estimated_extraction_cost}")
    console.print(f"[green]✓ Stage 1 complete in {stage_times['triage']:.2f}s[/green]")
    
    # ========================================================================
    # STAGE 2: EXTRACTION
    # ========================================================================
    print_stage_header(2, "Content Extraction")
    
    start_time = time.time()
    extracted_doc = router.extract(pdf_path, profile)
    stage_times['extraction'] = time.time() - start_time
    
    console.print(f"[cyan]Text Blocks:[/cyan] {len(extracted_doc.text_blocks)}")
    console.print(f"[cyan]Tables:[/cyan] {len(extracted_doc.tables)}")
    console.print(f"[cyan]Figures:[/cyan] {len(extracted_doc.figures)}")
    console.print(f"[cyan]Confidence:[/cyan] {extracted_doc.confidence_score:.2%}")
    console.print(f"[green]✓ Stage 2 complete in {stage_times['extraction']:.2f}s[/green]")
    
    # ========================================================================
    # STAGE 3: SEMANTIC CHUNKING
    # ========================================================================
    print_stage_header(3, "Semantic Chunking")
    
    start_time = time.time()
    ldus = chunker.process_document(extracted_doc, pdf_path)
    stage_times['chunking'] = time.time() - start_time
    
    total_tokens = sum(ldu.token_count for ldu in ldus)
    console.print(f"[cyan]LDUs Created:[/cyan] {len(ldus)}")
    console.print(f"[cyan]Total Tokens:[/cyan] {total_tokens:,}")
    console.print(f"[cyan]Avg Tokens/LDU:[/cyan] {total_tokens/len(ldus):.0f}")
    console.print(f"[green]✓ Stage 3 complete in {stage_times['chunking']:.2f}s[/green]")
    
    # ========================================================================
    # STAGE 4: PAGEINDEX BUILDING
    # ========================================================================
    print_stage_header(4, "PageIndex Building")
    
    start_time = time.time()
    pageindex_path = f".refinery/pageindex/{profile.doc_id}_pageindex.json"
    page_index = indexer.build_index(extracted_doc, ldus, pageindex_path)
    stage_times['pageindex'] = time.time() - start_time
    
    console.print(f"[cyan]Root Sections:[/cyan] {len(page_index.root_sections)}")
    console.print(f"[cyan]Total Pages:[/cyan] {page_index.total_pages}")
    console.print(f"[green]✓ Stage 4 complete in {stage_times['pageindex']:.2f}s[/green]")
    
    # Extract facts for structured queries (optional - skip if API unavailable)
    try:
        console.print("[dim]Extracting facts for SQL queries...[/dim]")
        fact_count = fact_extractor.extract_facts(extracted_doc, ldus)
        console.print(f"[cyan]Facts Extracted:[/cyan] {fact_count}")
    except Exception:
        console.print("[dim]Fact extraction skipped (API unavailable)[/dim]")
    
    # ========================================================================
    # STAGE 5: QUERY INTERFACE
    # ========================================================================
    print_stage_header(5, "Query Interface")
    
    # Example queries
    queries = [
        ("What are the main sections?", "pageindex"),
        ("Summarize the key findings", "semantic"),
    ]
    
    for query_text, method in queries:
        console.print(f"\n[cyan]Q:[/cyan] {query_text}")
        
        start_time = time.time()
        result = query_agent.query(query_text, doc_id=profile.doc_id, method=method)
        query_time = time.time() - start_time
        
        console.print(f"[green]A:[/green] {result.answer[:200]}...")
        console.print(f"[dim]Method: {result.retrieval_method} | Time: {query_time:.2f}s | Citations: {len(result.citations)}[/dim]")
    
    stage_times['query'] = time.time() - start_time
    console.print(f"\n[green]✓ Stage 5 complete[/green]")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    console.print("\n" + "="*70)
    console.print("[bold green]✓ Full Pipeline Complete![/bold green]")
    console.print("="*70 + "\n")
    
    # Performance summary
    total_time = sum(stage_times.values())
    
    summary_table = RichTable(title="Performance Summary")
    summary_table.add_column("Stage", style="cyan")
    summary_table.add_column("Time", justify="right", style="green")
    summary_table.add_column("Percentage", justify="right", style="yellow")
    
    for stage, stage_time in stage_times.items():
        percentage = (stage_time / total_time) * 100
        summary_table.add_row(
            stage.capitalize(),
            f"{stage_time:.2f}s",
            f"{percentage:.1f}%"
        )
    
    summary_table.add_row("[bold]Total", f"[bold]{total_time:.2f}s", "[bold]100.0%")
    console.print(summary_table)
    
    # Output locations
    console.print("\n[bold]Output Artifacts:[/bold]")
    console.print(f"  Profile: [dim].refinery/profiles/{profile.doc_id}.json[/dim]")
    console.print(f"  LDUs: [dim].refinery/ldus/{profile.doc_id}_ldus.json[/dim]")
    console.print(f"  PageIndex: [dim].refinery/pageindex/{profile.doc_id}_pageindex.json[/dim]")
    console.print(f"  Facts DB: [dim].refinery/facts.db[/dim]")
    console.print(f"  Ledger: [dim].refinery/extraction_ledger.jsonl[/dim]")
    
    # Query examples
    console.print("\n[bold]Try Querying:[/bold]")
    console.print(f"  python demo_query_interface.py {profile.doc_id}")
    
    return profile.doc_id


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python demo_full_pipeline.py <pdf_path>[/yellow]")
        console.print("[dim]Example: python demo_full_pipeline.py data/sample.pdf[/dim]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    demo_full_pipeline(pdf_path)
