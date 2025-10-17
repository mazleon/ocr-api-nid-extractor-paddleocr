import json

from paddleocr import PaddleOCR
from pathlib import Path

# Define the input and output directory
input_path = Path(__file__).parent / "sample_images/test_leon_front.jpeg"
output_dir = Path(__file__).parent / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

# Initialize PaddleOCR instance
ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv5",
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="en_PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

# Run OCR inference on a sample image
result = list(ocr.predict(str(input_path)))

# Process and persist the results
if result:
    instance = result[0]
    res_json = instance.json.get("res", {})
    polys = res_json.get("rec_polys", [])
    texts = res_json.get("rec_texts", [])
    scores = res_json.get("rec_scores", [])

    json_payload = []
    for poly, text, score in zip(polys, texts, scores):
        print(f"Text: {text} (confidence: {float(score):.4f})")
        json_payload.append(
            {
                "points": poly,
                "text": text,
                "confidence": float(score),
            }
        )

    (output_dir / "leon_ocr_result.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2)
    )

    vis_image = instance.img.get("ocr_res_img") if instance.img else None
    if vis_image is not None:
        vis_image.save(output_dir / "ocr_result.png")
else:
    print("No text detected.")