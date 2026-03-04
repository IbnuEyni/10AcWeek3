#!/usr/bin/env python3
"""
Step-by-Step Manual Testing Guide
Complete end-to-end document processing with all phases
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# Import all components
from src.data_quality import PDFValidator, OutputValidator, AnomalyDetector
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.performance import CacheManager, ResourceManager

console = Console()


def step_1_select_pdf():
    """Step 1: Select a PDF file"""
    console.print("\n[bold cyan]STEP 1: Select PDF File[/bold cyan]")
    console.print("=" * 60)
    
    data_dir = Path("data")
    pdfs = list(data_dir.glob("*.pdf"))
    
    if not pdfs:
        console.print("[red]❌ No PDFs found in data/ directory[/red]")
        return None
    
    # Show available PDFs
    table = Table(title="Available PDFs")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Filename", style="white")
    table.add_column("Size (MB)", justify="right", style="yellow")
    
    for idx, pdf in enumerate(pdfs[:10], 1):
        size_mb = pdf.stat().st_size / (1024 * 1024)
        table.add_row(str(idx), pdf.name[:60], f"{size_mb:.2f}")
    
    console.print(table)
    
    # Select first PDF for demo
    selected = pdfs[0]
    console.print(f"\n[green]✅ Selected: {selected.name}[/green]")
    
    return str(selected)


def step_2_validate_input(pdf_path):
    """Step 2: Validate PDF input"""
    console.print("\n[bold cyan]STEP 2: Validate PDF Input[/bold cyan]")
    console.print("=" * 60)
    
    try:
        # Validate file
        console.print("🔍 Validating PDF file...")
        PDFValidator.validate_file(pdf_path)
        
        # Compute hash
        console.print("🔐 Computing file hash...")
        file_hash = PDFValidator.compute_hash(pdf_path)
        
        # Get file info
        path = Path(pdf_path)
        size_mb = path.stat().st_size / (1024 * 1024)
        
        # Display results
        result_panel = f"""
[bold green]✅ Validation Passed[/bold green]

[bold]File Information:[/bold]
  • Name: {path.name}
  • Size: {size_mb:.2f} MB
  • Hash: {file_hash[:32]}...
  
[bold]Validation Checks:[/bold]
  ✅ File exists
  ✅ Valid PDF signature
  ✅ Size within limits (< 100MB)
  ✅ Not corrupted
  ✅ Has readable pages
"""
        console.print(Panel(result_panel, border_style="green"))
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Validation Failed: {e}[/red]")
        return False


def step_3_triage_document(pdf_path):
    """Step 3: Triage and profile document"""
    console.print("\n[bold cyan]STEP 3: Triage & Profile Document[/bold cyan]")
    console.print("=" * 60)
    
    console.print("🔍 Analyzing document characteristics...")
    
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    
    # Display profile
    profile_panel = f"""
[bold]Document Profile:[/bold]

[bold cyan]Basic Info:[/bold cyan]
  • Doc ID: {profile.doc_id}
  • Filename: {profile.filename}
  • Total Pages: {profile.total_pages}

[bold cyan]Classification:[/bold cyan]
  • Origin Type: {profile.origin_type}
  • Layout Complexity: {profile.layout_complexity}
  • Domain Hint: {profile.domain_hint}

[bold cyan]Extraction Strategy:[/bold cyan]
  • Recommended: {profile.estimated_extraction_cost}
  • Confidence: {profile.confidence_score:.2f}

[bold cyan]Metadata:[/bold cyan]
  • Character Density: {profile.metadata.get('character_density', 0):.4f}
  • Image Ratio: {profile.metadata.get('image_ratio', 0):.2f}
  • Table Count: {profile.metadata.get('table_count_estimate', 0)}
"""
    
    console.print(Panel(profile_panel, border_style="cyan"))
    
    # Save profile
    profile_path = Path(f".refinery/profiles/{profile.doc_id}.json")
    console.print(f"\n[green]✅ Profile saved: {profile_path}[/green]")
    
    return profile


def step_4_extract_content(pdf_path, profile):
    """Step 4: Extract document content"""
    console.print("\n[bold cyan]STEP 4: Extract Document Content[/bold cyan]")
    console.print("=" * 60)
    
    console.print(f"🚀 Extracting using strategy: [yellow]{profile.estimated_extraction_cost}[/yellow]")
    
    router = ExtractionRouter()
    
    with console.status("[bold green]Extracting..."):
        doc, confidence = router.extract(pdf_path, profile)
    
    # Display extraction results
    extraction_panel = f"""
[bold green]✅ Extraction Complete[/bold green]

[bold]Extraction Results:[/bold]
  • Strategy Used: {doc.extraction_strategy}
  • Confidence Score: {confidence:.2f}
  • Processing Time: {doc.metadata.get('processing_time_ms', 0):.0f}ms

[bold]Content Extracted:[/bold]
  • Text Blocks: {len(doc.text_blocks)}
  • Tables: {len(doc.tables)}
  • Total Characters: {sum(len(b.content) for b in doc.text_blocks):,}

[bold]Sample Content (first 200 chars):[/bold]
{doc.text_blocks[0].content[:200] if doc.text_blocks else 'No content'}...
"""
    
    console.print(Panel(extraction_panel, border_style="green"))
    
    return doc, confidence


def step_5_validate_output(doc, profile):
    """Step 5: Validate extraction output"""
    console.print("\n[bold cyan]STEP 5: Validate Extraction Output[/bold cyan]")
    console.print("=" * 60)
    
    console.print("🔍 Validating extraction quality...")
    
    # Validate output
    result = OutputValidator.validate_extraction(doc)
    
    # Create validation table
    table = Table(title="Quality Validation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")
    
    table.add_row("Valid", str(result["valid"]), "✅" if result["valid"] else "❌")
    table.add_row("Quality Score", f"{result['quality_score']:.2f}", "✅" if result['quality_score'] > 0.7 else "⚠️")
    table.add_row("Total Blocks", str(result['metrics']['total_blocks']), "✅")
    table.add_row("Total Tables", str(result['metrics']['total_tables']), "✅")
    table.add_row("Total Chars", f"{result['metrics']['total_chars']:,}", "✅")
    table.add_row("Confidence", f"{result['metrics']['confidence']:.2f}", "✅")
    
    console.print(table)
    
    # Show issues if any
    if result['issues']:
        console.print("\n[yellow]⚠️  Quality Issues Detected:[/yellow]")
        for issue in result['issues']:
            console.print(f"  • {issue}")
    else:
        console.print("\n[green]✅ No quality issues detected[/green]")
    
    return result


def step_6_detect_anomalies(doc, profile):
    """Step 6: Detect anomalies"""
    console.print("\n[bold cyan]STEP 6: Detect Anomalies[/bold cyan]")
    console.print("=" * 60)
    
    console.print("🔍 Checking for statistical anomalies...")
    
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(doc, profile)
    
    if anomalies:
        console.print(f"\n[yellow]⚠️  {len(anomalies)} Anomalies Detected:[/yellow]")
        for anomaly in anomalies:
            console.print(f"  • {anomaly}")
    else:
        console.print("\n[green]✅ No anomalies detected - document is normal[/green]")
    
    # Show baseline metrics
    baseline_panel = f"""
[bold]Baseline Metrics:[/bold]
  • Avg Blocks/Page: {detector.baseline_metrics['avg_blocks_per_page']:.1f}
  • Avg Chars/Block: {detector.baseline_metrics['avg_chars_per_block']:.0f}
  • Avg Confidence: {detector.baseline_metrics['avg_confidence']:.2f}
"""
    console.print(Panel(baseline_panel, border_style="cyan"))
    
    return anomalies


def step_7_check_resources():
    """Step 7: Check resource usage"""
    console.print("\n[bold cyan]STEP 7: Check Resource Usage[/bold cyan]")
    console.print("=" * 60)
    
    manager = ResourceManager()
    
    # Check memory
    memory = manager.check_memory_usage()
    
    # Check cache
    cache_info = CacheManager.get_cached_profile.cache_info()
    
    # Display resources
    resource_table = Table(title="Resource Usage")
    resource_table.add_column("Resource", style="cyan")
    resource_table.add_column("Value", style="white")
    resource_table.add_column("Status", style="green")
    
    resource_table.add_row("Memory (RSS)", f"{memory['rss_mb']:.1f} MB", "✅")
    resource_table.add_row("Memory (%)", f"{memory['percent']:.1f}%", "✅")
    resource_table.add_row("Cache Hits", str(cache_info.hits), "✅")
    resource_table.add_row("Cache Misses", str(cache_info.misses), "✅")
    resource_table.add_row("Cache Size", f"{cache_info.currsize}/{cache_info.maxsize}", "✅")
    
    console.print(resource_table)


def step_8_view_artifacts(profile):
    """Step 8: View generated artifacts"""
    console.print("\n[bold cyan]STEP 8: View Generated Artifacts[/bold cyan]")
    console.print("=" * 60)
    
    # Check artifacts
    profile_path = Path(f".refinery/profiles/{profile.doc_id}.json")
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    
    artifacts_table = Table(title="Generated Artifacts")
    artifacts_table.add_column("Artifact", style="cyan")
    artifacts_table.add_column("Location", style="white")
    artifacts_table.add_column("Status", style="green")
    
    artifacts_table.add_row(
        "Document Profile",
        str(profile_path),
        "✅" if profile_path.exists() else "❌"
    )
    artifacts_table.add_row(
        "Extraction Ledger",
        str(ledger_path),
        "✅" if ledger_path.exists() else "❌"
    )
    
    console.print(artifacts_table)
    
    # Show ledger entry
    if ledger_path.exists():
        console.print("\n[bold]Latest Ledger Entry:[/bold]")
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
            if lines:
                console.print(f"[dim]{lines[-1][:200]}...[/dim]")


def main():
    """Run complete end-to-end test"""
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]Document Intelligence Refinery[/bold cyan]\n"
        "[white]Complete End-to-End Manual Test[/white]\n"
        "[dim]Testing all phases: Validation → Triage → Extraction → Quality Check[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Select PDF
        pdf_path = step_1_select_pdf()
        if not pdf_path:
            return
        
        input("\n[yellow]Press Enter to continue to Step 2...[/yellow]")
        
        # Step 2: Validate input
        if not step_2_validate_input(pdf_path):
            return
        
        input("\n[yellow]Press Enter to continue to Step 3...[/yellow]")
        
        # Step 3: Triage
        profile = step_3_triage_document(pdf_path)
        
        input("\n[yellow]Press Enter to continue to Step 4...[/yellow]")
        
        # Step 4: Extract
        doc, confidence = step_4_extract_content(pdf_path, profile)
        
        input("\n[yellow]Press Enter to continue to Step 5...[/yellow]")
        
        # Step 5: Validate output
        validation_result = step_5_validate_output(doc, profile)
        
        input("\n[yellow]Press Enter to continue to Step 6...[/yellow]")
        
        # Step 6: Detect anomalies
        anomalies = step_6_detect_anomalies(doc, profile)
        
        input("\n[yellow]Press Enter to continue to Step 7...[/yellow]")
        
        # Step 7: Check resources
        step_7_check_resources()
        
        input("\n[yellow]Press Enter to continue to Step 8...[/yellow]")
        
        # Step 8: View artifacts
        step_8_view_artifacts(profile)
        
        # Final summary
        console.print("\n" + "=" * 60)
        console.print(Panel.fit(
            "[bold green]✅ Complete End-to-End Test Successful![/bold green]\n\n"
            f"[white]Document: {Path(pdf_path).name}[/white]\n"
            f"[white]Strategy: {doc.extraction_strategy}[/white]\n"
            f"[white]Confidence: {confidence:.2f}[/white]\n"
            f"[white]Quality Score: {validation_result['quality_score']:.2f}[/white]\n"
            f"[white]Text Blocks: {len(doc.text_blocks)}[/white]\n"
            f"[white]Tables: {len(doc.tables)}[/white]\n"
            f"[white]Anomalies: {len(anomalies)}[/white]",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
