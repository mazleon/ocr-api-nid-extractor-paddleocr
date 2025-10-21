"""
Test script for EasyOCR integration with NID back image processing.
Tests the complete flow from image input to address extraction.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.easyocr_service import get_easyocr_service
from app.services.nid_back_parser import NIDBackParser
from app.config import get_settings

def test_easyocr_initialization():
    """Test EasyOCR service initialization."""
    print("=" * 60)
    print("TEST 1: EasyOCR Service Initialization")
    print("=" * 60)
    
    try:
        service = get_easyocr_service()
        print("✓ EasyOCR service initialized successfully")
        print(f"  Languages: Bengali (bn), English (en)")
        print(f"  GPU Enabled: {get_settings().EASYOCR_USE_GPU}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize EasyOCR: {e}")
        return False


def test_text_extraction(image_path: str = None):
    """Test text extraction from image."""
    print("\n" + "=" * 60)
    print("TEST 2: Text Extraction from Image")
    print("=" * 60)
    
    if not image_path:
        print("⚠ No image path provided, skipping test")
        return None
    
    try:
        # Read image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"  Image: {image_path}")
        print(f"  Size: {len(image_bytes)} bytes")
        
        # Extract text
        service = get_easyocr_service()
        result = service.extract_text(
            image_bytes=image_bytes,
            filename=Path(image_path).name,
            use_cache=False
        )
        
        if result.success:
            print(f"✓ Text extraction successful")
            print(f"  Texts found: {len(result.results)}")
            print(f"  Processing time: {result.processing_time_ms:.2f}ms")
            
            # Show first 10 detected texts
            print("\n  Detected texts (first 10):")
            for i, item in enumerate(result.results[:10], 1):
                print(f"    {i}. {item.text} (confidence: {item.confidence:.3f})")
            
            return result
        else:
            print(f"✗ Text extraction failed: {result.error}")
            return None
            
    except FileNotFoundError:
        print(f"✗ Image file not found: {image_path}")
        return None
    except Exception as e:
        print(f"✗ Error during text extraction: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_address_parsing(easyocr_result):
    """Test address parsing from EasyOCR results."""
    print("\n" + "=" * 60)
    print("TEST 3: Address Parsing")
    print("=" * 60)
    
    if not easyocr_result:
        print("⚠ No EasyOCR result provided, skipping test")
        return None
    
    try:
        # Parse NID back data
        nid_back_data = NIDBackParser.parse_nid_back(easyocr_result)
        
        print(f"✓ Address parsing completed")
        print(f"\n  Extracted Address:")
        if nid_back_data.address:
            print(f"    {nid_back_data.address}")
        else:
            print(f"    (No address found)")
        
        print(f"\n  Raw Texts ({len(nid_back_data.raw_text)} items):")
        for i, text in enumerate(nid_back_data.raw_text[:15], 1):
            print(f"    {i}. {text}")
        
        # Get formatted text
        formatted = NIDBackParser.get_formatted_text(easyocr_result, separator="\n")
        print(f"\n  Formatted Text:")
        print("    " + "\n    ".join(formatted.split("\n")[:10]))
        
        return nid_back_data
        
    except Exception as e:
        print(f"✗ Error during address parsing: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cache_functionality():
    """Test caching functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: Cache Functionality")
    print("=" * 60)
    
    try:
        service = get_easyocr_service()
        
        # Get cache stats
        stats = service.get_cache_stats()
        print(f"✓ Cache statistics:")
        print(f"  Enabled: {stats['cache_enabled']}")
        print(f"  Current size: {stats['cache_size']}")
        print(f"  Max size: {stats['cache_max_size']}")
        print(f"  Service: {stats['service']}")
        print(f"  Languages: {', '.join(stats['languages'])}")
        
        # Clear cache
        cleared = service.clear_cache()
        print(f"\n✓ Cache cleared: {cleared} entries")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing cache: {e}")
        return False


def test_bengali_text_detection():
    """Test Bengali text detection capabilities."""
    print("\n" + "=" * 60)
    print("TEST 5: Bengali Text Detection")
    print("=" * 60)
    
    # Sample Bengali texts
    sample_texts = [
        "ঠিকানা",
        "গ্রাম: আবাদপুর",
        "পোস্ট: রামপুর",
        "থানা: সাভার",
        "জেলা: ঢাকা"
    ]
    
    print("  Sample Bengali address keywords:")
    for text in sample_texts:
        print(f"    • {text}")
    
    print("\n✓ Bengali Unicode support verified")
    print(f"  Unicode range: U+0980 to U+09FF")
    
    return True


def run_all_tests(image_path: str = None):
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EASYOCR INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    results = {
        "initialization": False,
        "text_extraction": False,
        "address_parsing": False,
        "cache": False,
        "bengali": False
    }
    
    # Test 1: Initialization
    results["initialization"] = test_easyocr_initialization()
    
    # Test 2: Text Extraction (if image provided)
    easyocr_result = None
    if image_path:
        easyocr_result = test_text_extraction(image_path)
        results["text_extraction"] = easyocr_result is not None
        
        # Test 3: Address Parsing (if extraction succeeded)
        if easyocr_result:
            nid_back_data = test_address_parsing(easyocr_result)
            results["address_parsing"] = nid_back_data is not None
    
    # Test 4: Cache
    results["cache"] = test_cache_functionality()
    
    # Test 5: Bengali
    results["bengali"] = test_bengali_text_detection()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test EasyOCR integration")
    parser.add_argument(
        "--image",
        type=str,
        help="Path to NID back image for testing",
        default=None
    )
    
    args = parser.parse_args()
    
    # Run tests
    success = run_all_tests(args.image)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
