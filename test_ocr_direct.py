"""
Direct OCR test to verify PaddleOCR is working correctly.
"""
from pathlib import Path
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np

# Initialize PaddleOCR
print("Initializing PaddleOCR...")
ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv5",
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="en_PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

# Test with a sample image
test_image_path = Path("tests/sample_images/test_leon_front.jpeg")

if test_image_path.exists():
    print(f"\nTesting with: {test_image_path}")
    
    # Load and convert image
    image = Image.open(test_image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to numpy array (required by PaddleOCR)
    image_array = np.array(image)
    
    print(f"Image mode: {image.mode}, size: {image.size}, array shape: {image_array.shape}")
    
    # Run OCR
    print("\nRunning OCR...")
    results = list(ocr.predict(image_array))
    
    print(f"Results count: {len(results)}")
    
    if results:
        instance = results[0]
        print(f"Result type: {type(instance)}")
        print(f"Has json attr: {hasattr(instance, 'json')}")
        
        if hasattr(instance, 'json'):
            res_json = instance.json.get("res", {})
            print(f"\nres_json keys: {list(res_json.keys())}")
            
            polys = res_json.get("rec_polys", [])
            texts = res_json.get("rec_texts", [])
            scores = res_json.get("rec_scores", [])
            
            print(f"\nDetected {len(texts)} texts:")
            for text, score in zip(texts, scores):
                print(f"  - {text} (confidence: {float(score):.3f})")
        else:
            print("No json attribute found!")
    else:
        print("No results returned!")
else:
    print(f"Test image not found: {test_image_path}")
    print("\nPlease provide a test image path:")
    import sys
    if len(sys.argv) > 1:
        custom_path = sys.argv[1]
        print(f"Using: {custom_path}")
        # Repeat test with custom path
