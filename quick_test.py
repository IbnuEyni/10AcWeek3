#!/usr/bin/env python3
"""Quick End-to-End Test - Uses smallest native digital PDF"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from src.data_quality import PDFValidator, OutputValidator, AnomalyDetector
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.performance import ResourceManager, CacheManager

console = Console()


def find_best_test_pdf():
    """Find smallest native digital PDF for quick testing"""
    data_dir = Path("data")
    pdfs = list(data_dir.glob("*.pdf"))
    
    if not pdfs:
        return None
    
    # Get PDF with size and page info
    pdf_info = []
    for pdf in pdfs[:20]:  # Check first 20
        try:
            size = pdf.stat().st_size / (1024 * 1024)
            if size < 5:  # Less than 5MB
                pdf_info.append((pdf, size))
        except:
            continue
    
    if pdf_info:
        # Return smallest
        return str(sorted(pdf_info, key=lambda x: x[1])[0][0])
    
    return str(pdfs[0])


def main():
    console.print(Panel.fit(
        "[bold cyan]Quick End-to-End Test[/bold cyan]\n"
        "[white]Complete Pipeline Demo[/white]",
        border_style="cyan"
    ))
    
    # Find suitable PDF
    pdf_path = find_best_test_pdf()
    if not pdf_path:
        console.print("[red]No PDFs found[/red]")
        return
    
    pdf_name = Path(pdf_path).name
    console.print(f"\n[cyan]📄 Testing: {pdf_name}[/cyan]\n")
    
    # Step 1: Validate
    console.print("[bold yellow]⏳ Step 1/7:[/bold yellow] Validating input...")
    try:
        PDFValidator.validate_file(pdf_path)
        size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
        console.print(f"[green]✅ Valid PDF ({size_mb:.2f} MB)[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed: {e}[/red]")
        return
    
    # Step 2: Triage
    console.print("\n[bold yellow]⏳ Step 2/7:[/bold yellow] Analyzing document...")
    triage = TriageAgent()
    profile = triage.profile_document(pdf_path)
    console.print(f"[green]✅ Type: {profile.origin_type} | Layout: {profile.layout_complexity}[/green]")
    console.print(f"[green]✅ Domain: {profile.domain_hint} | Pages: {profile.total_pages}[/green]")
    
    # Step 3: Extract
    console.print(f"\n[bold yellow]⏳ Step 3/7:[/bold yellow] Extracting content ({profile.estimated_extraction_cost})...")
    router = ExtractionRouter()
    doc = router.extract(pdf_path, profile)
    confidence = doc.confidence_score
    console.print(f"[green]✅ Extracted {len(doc.text_blocks)} blocks, {len(doc.tables)} tables[/green]")
    console.print(f"[green]✅ Confidence: {confidence:.2f}[/green]")
    
    # Step 4: Validate Output
    console.print("\n[bold yellow]⏳ Step 4/7:[/bold yellow] Validating quality...")
    result = OutputValidator.validate_extraction(doc)
    console.print(f"[green]✅ Quality Score: {result['quality_score']:.2f} | Valid: {result['valid']}[/green]")
    if result['issues']:
        console.print(f"[yellow]⚠️  {len(result['issues'])} issues found[/yellow]")
    
    # Step 5: Anomaly Detection
    console.print("\n[bold yellow]⏳ Step 5/7:[/bold yellow] Detecting anomalies...")
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(doc, profile)
    if anomalies:
        console.print(f"[yellow]⚠️  {len(anomalies)} anomalies detected[/yellow]")
    else:
        console.print("[green]✅ No anomalies[/green]")
    
    # Step 6: Check Resources
    console.print("\n[bold yellow]⏳ Step 6/7:[/bold yellow] Checking resources...")
    manager = ResourceManager()
    memory = manager.check_memory_usage()
    console.print(f"[green]✅ Memory: {memory['rss_mb']:.1f} MB[/green]")
    
    # Step 7: Verify Artifacts
    console.print("\n[bold yellow]⏳ Step 7/7:[/bold yellow] Verifying artifacts...")
    profile_path = Path(f".refinery/profiles/{profile.doc_id}.json")
    ledger_path = Path(".refinery/extraction_ledger.jsonl")
    console.print(f"[green]✅ Profile: {profile_path.exists()}[/green]")
    console.print(f"[green]✅ Ledger: {ledger_path.exists()}[/green]")
    
    # Summary
    console.print("\n" + "="*60)
    console.print(Panel(
        f"[bold green]🎉 SUCCESS![/bold green]\n\n"
        f"[white]Document:[/white] {pdf_name[:40]}\n"
        f"[white]Pages:[/white] {profile.total_pages}\n"
        f"[white]Strategy:[/white] {doc.extraction_strategy}\n"
        f"[white]Confidence:[/white] {confidence:.2f}\n"
        f"[white]Quality:[/white] {result['quality_score']:.2f}\n"
        f"[white]Blocks:[/white] {len(doc.text_blocks)}\n"
        f"[white]Tables:[/white] {len(doc.tables)}\n"
        f"[white]Characters:[/white] {sum(len(b.content) for b in doc.text_blocks):,}",
        title="[bold cyan]Test Results[/bold cyan]",
        border_style="green"
    ))
    
    # Show sample content
    if doc.text_blocks:
        console.print("\n[bold]Sample Content:[/bold]")
        sample = doc.text_blocks[0].content[:200].replace('\n', ' ')
        console.print(f"[dim]{sample}...[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
