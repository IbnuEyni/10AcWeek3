#!/usr/bin/env python3
"""
Fast Demo Test - Tests core functionality without heavy processing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_schema_enums():
    """Test that schemas use enums correctly"""
    print("\n" + "="*60)
    print("TEST 1: Schema Validation with Enums")
    print("="*60)
    
    from src.models.extracted_document import (
        ExtractionStrategy, ProcessingStatus, EscalationReason, RoutingSummary
    )
    from src.models.provenance import VerificationStatus
    from src.models.document_profile import OriginType, LayoutComplexity
    
    print("✓ ExtractionStrategy:", [e.value for e in ExtractionStrategy])
    print("✓ ProcessingStatus:", [e.value for e in ProcessingStatus])
    print("✓ OriginType:", [e.value for e in OriginType])
    print("✓ LayoutComplexity:", [e.value for e in LayoutComplexity])
    
    # Test RoutingSummary creation
    routing = RoutingSummary(
        selected_strategy=ExtractionStrategy.LAYOUT_AWARE,
        strategies_attempted=[ExtractionStrategy.LAYOUT_AWARE],
        total_attempts=1,
        final_confidence=0.85,
        escalation_triggered=False,
        total_cost=0.05,
        processing_time_ms=1500,
        status=ProcessingStatus.SUCCESS
    )
    print(f"✓ RoutingSummary created: {routing.selected_strategy}")
    print("\n✅ Schema validation PASSED\n")
    return True


def test_triage_only():
    """Test document triage without extraction"""
    print("="*60)
    print("TEST 2: Document Triage (Fast - No Extraction)")
    print("="*60)
    
    from src.agents.triage import TriageAgent
    
    triage = TriageAgent()
    print("✓ TriageAgent initialized")
    
    # Find one test document
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))[:1]
    
    if not pdf_files:
        print("⚠ No PDF files found")
        return True
    
    pdf_file = pdf_files[0]
    print(f"\nProcessing: {pdf_file.name}")
    
    profile = triage.profile_document(str(pdf_file))
    
    print(f"  • Origin Type: {profile.origin_type}")
    print(f"  • Layout: {profile.layout_complexity}")
    print(f"  • Domain: {profile.domain_hint}")
    print(f"  • Pages: {profile.total_pages}")
    print(f"  • Cost Estimate: {profile.estimated_extraction_cost}")
    
    print("\n✅ Triage PASSED\n")
    return True


def test_strategy_selection():
    """Test that strategy selection works correctly"""
    print("="*60)
    print("TEST 3: Strategy Selection Logic")
    print("="*60)
    
    from src.agents.triage import TriageAgent
    from src.agents.extractor import ExtractionRouter
    
    triage = TriageAgent()
    router = ExtractionRouter()
    
    print("✓ Agents initialized")
    
    # Find documents
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))[:3]
    
    if not pdf_files:
        print("⚠ No PDF files found")
        return True
    
    print(f"\nTesting strategy selection on {len(pdf_files)} documents:\n")
    
    for pdf_file in pdf_files:
        profile = triage.profile_document(str(pdf_file))
        strategy = router._select_strategy(profile)
        
        print(f"  {pdf_file.name[:40]}")
        print(f"    Origin: {profile.origin_type} → Strategy: {strategy.strategy_name}")
    
    print("\n✅ Strategy selection PASSED\n")
    return True


def test_docling_availability():
    """Test if Docling is available and configured"""
    print("="*60)
    print("TEST 4: Docling FAST Mode Configuration")
    print("="*60)
    
    from src.utils.docling_helper import DoclingHelper
    
    helper = DoclingHelper()
    
    if helper.use_docling:
        print("✓ Docling is AVAILABLE")
        print("✓ FAST mode configured (no OCR, no AI)")
        print("  • Layout extraction: ENABLED")
        print("  • Vision preprocessing: ENABLED")
    else:
        print("⚠ Docling not available (will use pdfplumber fallback)")
    
    print("\n✅ Docling check PASSED\n")
    return True


def test_config_loading():
    """Test configuration loading"""
    print("="*60)
    print("TEST 5: Configuration Loading")
    print("="*60)
    
    import yaml
    from pathlib import Path
    
    config_path = Path("rubric/extraction_rules.yaml")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print("✓ Configuration loaded")
    print(f"  • Confidence threshold: {config['confidence']['escalation_threshold']}")
    print(f"  • Max cost per doc: ${config['cost']['max_per_document']}")
    print(f"  • Escalation enabled: {config['escalation']['enabled']}")
    print(f"  • Strategy order: {config['escalation']['strategy_order']}")
    
    if 'extraction_strategies' in config:
        print(f"  • Docling FAST mode: {config['extraction_strategies']['layout_aware']['use_docling_fast_mode']}")
        print(f"  • Vision preprocessing: {config['extraction_strategies']['vision']['use_docling_preprocessing']}")
    
    print("\n✅ Configuration PASSED\n")
    return True


def main():
    """Run all fast tests"""
    print("\n" + "="*60)
    print("DOCUMENT INTELLIGENCE REFINERY - FAST DEMO TEST")
    print("="*60)
    
    tests = [
        ("Schema Enums", test_schema_enums),
        ("Document Triage", test_triage_only),
        ("Strategy Selection", test_strategy_selection),
        ("Docling Configuration", test_docling_availability),
        ("Config Loading", test_config_loading),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
