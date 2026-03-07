#!/usr/bin/env python3
"""
Phase 5 Demo: Query Interface Agent
Demonstrates natural language querying with provenance
Accepts PDF file path and runs full pipeline
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable
from rich.panel import Panel

from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent
from src.agents.pageindex_builder_ai import PageIndexBuilderAI
from src.agents.query_agent import QueryAgent
from src.utils.fact_extractor_ai import FactExtractorAI

console = Console()


def run_pipeline(pdf_path: str):
    """
    Run full pipeline on PDF file
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        tuple: (profile, extracted_doc, ldus, page_index)
    """
    console.print("\n[yellow]Running full pipeline...[/yellow]")
    
    # Stage 1: Triage
    console.print("[cyan]Stage 1:[/cyan] Triage Agent")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    console.print(f"[green]✓[/green] Classified as {profile.origin_type}")
    
    # Stage 2: Extraction
    console.print("[cyan]Stage 2:[/cyan] Extraction Router")
    router = ExtractionRouter()
    extracted_doc = router.extract(pdf_path, profile)
    console.print(f"[green]✓[/green] Extracted {len(extracted_doc.text_blocks)} blocks")
    
    # Stage 3: Chunking
    console.print("[cyan]Stage 3:[/cyan] Chunking Agent")
    chunker = ChunkingAgent()
    ldus = chunker.process_document(extracted_doc, pdf_path)
    console.print(f"[green]✓[/green] Created {len(ldus)} LDUs")
    
    # Stage 4: PageIndex
    console.print("[cyan]Stage 4:[/cyan] PageIndex Builder")
    indexer = PageIndexBuilderAI()
    page_index = indexer.build_index(extracted_doc, ldus, pdf_path=pdf_path)
    console.print(f"[green]✓[/green] Built index with {len(page_index.root_sections)} sections")
    
    # Stage 4.5: Fact Extraction
    console.print("[cyan]Stage 4.5:[/cyan] Fact Extraction")
    try:
        fact_extractor = FactExtractorAI()
        facts = fact_extractor.extract_facts(extracted_doc, pdf_path)
        console.print(f"[green]✓[/green] Extracted {len(facts)} facts")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Fact extraction skipped: {e}")
    
    console.print("[green]✓ Pipeline complete[/green]\n")
    
    return profile, extracted_doc, ldus, page_index


def demo_query_interface(doc_id: str):
    """
    Demonstrate Query Interface Agent capabilities
    
    Args:
        doc_id: Document ID to query
    """
    console.print("\n" + "="*70)
    console.print("[bold cyan]Phase 5: Query Interface Agent Demo[/bold cyan]")
    console.print("="*70 + "\n")
    
    # Initialize agent
    console.print("[yellow]Initializing Query Agent...[/yellow]")
    agent = QueryAgent()
    console.print("[green]✓ Agent ready[/green]\n")
    
    # Example queries
    queries = [
        {
            "query": "What are the main sections in this document?",
            "method": "pageindex",
            "description": "PageIndex Navigation"
        },
        {
            "query": "What is the total revenue?",
            "method": "structured",
            "description": "Structured Query (SQL)"
        },
        {
            "query": "Explain the financial performance",
            "method": "semantic",
            "description": "Semantic Search"
        }
    ]
    
    for i, query_info in enumerate(queries, 1):
        console.print(f"\n[bold yellow]Query {i}: {query_info['description']}[/bold yellow]")
        console.print(f"[dim]Method: {query_info['method']}[/dim]")
        console.print(f"[cyan]Q:[/cyan] {query_info['query']}\n")
        
        # Execute query
        try:
            result = agent.query(
                query_info['query'], 
                doc_id=doc_id,
                method=query_info['method']
            )
            
            # Display answer
            console.print(f"[green]A:[/green] {result.answer}\n")
            
            # Display provenance
            if result.citations:
                console.print("[bold]Provenance Chain:[/bold]")
                
                citations_table = RichTable()
                citations_table.add_column("Source", style="cyan")
                citations_table.add_column("Page", style="yellow")
                citations_table.add_column("Excerpt", style="dim")
                
                for citation in result.citations:
                    citations_table.add_row(
                        citation.document_name,
                        str(citation.page_number),
                        citation.excerpt[:80] + "..."
                    )
                
                console.print(citations_table)
                
                # Display confidence
                console.print(f"\n[cyan]Confidence:[/cyan] {result.confidence:.2%}")
                console.print(f"[cyan]Method:[/cyan] {result.retrieval_method}")
            else:
                console.print("[yellow]No citations found[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    # Audit Mode Demo
    console.print("\n" + "="*70)
    console.print("[bold yellow]Audit Mode: Claim Verification[/bold yellow]")
    console.print("="*70 + "\n")
    
    claim = "The report states revenue was $4.2B in Q3"
    console.print(f"[cyan]Claim:[/cyan] {claim}\n")
    
    try:
        verification = agent.verify_claim(claim, doc_id)
        
        if verification['verified']:
            console.print("[green]✓ VERIFIED[/green]")
            console.print(f"\n[bold]Source Citation:[/bold]")
            
            citation = verification['citation']
            panel = Panel(
                f"[cyan]Document:[/cyan] {citation['document_name']}\n"
                f"[cyan]Page:[/cyan] {citation['page_number']}\n"
                f"[cyan]LDU:[/cyan] {citation['ldu_id']}\n"
                f"[cyan]Hash:[/cyan] {citation['content_hash'][:16]}...\n\n"
                f"[yellow]Excerpt:[/yellow]\n{citation['excerpt']}",
                title="Verification Source",
                border_style="green"
            )
            console.print(panel)
        else:
            console.print(f"[red]✗ UNVERIFIABLE[/red]")
            console.print(f"[dim]Reason: {verification['reason']}[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    # Summary
    console.print("\n" + "="*70)
    console.print("[bold green]✓ Query Interface Demo Complete[/bold green]")
    console.print("="*70 + "\n")
    
    console.print("[bold]Key Features Demonstrated:[/bold]")
    console.print("  ✓ PageIndex navigation for section-based queries")
    console.print("  ✓ Semantic search over LDUs")
    console.print("  ✓ Structured SQL queries over fact tables")
    console.print("  ✓ Provenance chain with source citations")
    console.print("  ✓ Audit mode for claim verification")


def demo_fact_extraction(doc_id: str):
    """
    Demonstrate FactTable extraction
    
    Args:
        doc_id: Document ID
    """
    console.print("\n" + "="*70)
    console.print("[bold cyan]FactTable Extraction Demo[/bold cyan]")
    console.print("="*70 + "\n")
    
    # Initialize extractor
    try:
        extractor = FactExtractorAI()
        
        # Query facts
        console.print("[cyan]Querying fact database...[/cyan]\n")
        
        facts = extractor.query_facts(doc_id=doc_id, limit=10)
        
        if facts:
            facts_table = RichTable(title="Extracted Facts")
            facts_table.add_column("Key", style="cyan")
            facts_table.add_column("Value", style="green")
            facts_table.add_column("Page", style="yellow")
            
            for fact in facts[:10]:
                value_str = f"{fact.value} {fact.unit or ''}".strip()
                facts_table.add_row(
                    fact.key[:40],
                    value_str[:30],
                    str(fact.page_number)
                )
            
            console.print(facts_table)
            console.print(f"\n[green]Total facts shown: {len(facts)}[/green]")
        else:
            console.print("[yellow]No facts found[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Fact extraction not available: {e}[/yellow]")


if __name__ == "__main__":
    import sys
    
    # CHANGE THIS LINE TO YOUR PDF PATH
    PDF_PATH = "data/tax_expenditure_ethiopia_2021_22.pdf"  # <-- Edit this path
    
    # Or use command line argument
    if len(sys.argv) >= 2:
        PDF_PATH = sys.argv[1]
    
    # Validate file exists
    pdf_file = Path(PDF_PATH)
    if not pdf_file.exists():
        console.print(f"[red]Error: File not found: {PDF_PATH}[/red]")
        console.print("[yellow]Usage: python demo_query_interface.py <path_to_pdf>[/yellow]")
        console.print("[dim]Example: python demo_query_interface.py data/sample.pdf[/dim]")
        console.print("\n[yellow]Or edit the PDF_PATH variable in the script[/yellow]")
        sys.exit(1)
    
    console.print(f"\n[bold cyan]Processing PDF:[/bold cyan] {pdf_file.name}")
    
    # Run full pipeline
    profile, extracted_doc, ldus, page_index = run_pipeline(str(pdf_file))
    
    # Run demos
    demo_query_interface(profile.doc_id)
    demo_fact_extraction(profile.doc_id)
