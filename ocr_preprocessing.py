"""
STEP 2: OCR + Preprocessing.

Standalone script — takes a certificate image/PDF and runs it through:
  1. Preprocessing (denoise, deskew)
  2. OCR (EasyOCR — the model you downloaded in Step 1)
  3. Structured field extraction (register number, certificate ID, etc.)

Run it with:
    python step2_ocr_preprocessing.py path/to/your/certificate.png

Requires Step 1 to have been run already (EasyOCR installed + downloaded).
Also installs a few small extra packages automatically if missing.
"""
import subprocess
import sys
import re
import io


def ensure_package_installed(package_name: str, import_name: str = None):
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"[..] Installing '{package_name}'...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[FAIL] Could not install '{package_name}': {result.stderr[-1000:]}")
            return False
        print(f"[OK] '{package_name}' installed.")
        return True


REQUIRED = [("opencv-python-headless", "cv2"), ("Pillow", "PIL"), ("numpy", "numpy"), ("easyocr", "easyocr")]
for pkg, mod in REQUIRED:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import cv2
import numpy as np
from PIL import Image
import easyocr


# ---------- Preprocessing ----------

def load_image(path: str) -> np.ndarray:
    if path.lower().endswith(".pdf"):
        ensure_package_installed("pdf2image", "pdf2image")
        from pdf2image import convert_from_path
        pages = convert_from_path(path)
        pil_img = pages[0].convert("RGB")  # first page only
    else:
        pil_img = Image.open(path).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def preprocess(img: np.ndarray) -> np.ndarray:
    """Grayscale -> denoise -> deskew. EasyOCR wants grayscale, NOT binarized."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    return _deskew(denoised)


def _deskew(gray_img: np.ndarray) -> np.ndarray:
    """
    Estimate and correct small rotation. OpenCV's minAreaRect() angle
    convention has changed across versions (older versions: (-90, 0],
    newer versions can report differently), which can cause a wrong
    correction to be applied on some OpenCV builds. To stay robust
    regardless of installed version, we normalize the raw angle into the
    smallest possible correction range (-45, 45] rather than trusting a
    fixed convention, and refuse to apply any correction larger than 20
    degrees — a real certificate scan is essentially never skewed more
    than that, so a bigger number almost certainly means a miscalculation,
    not real skew.
    """
    _, mask = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(mask > 0))
    if coords.shape[0] < 50:
        return gray_img

    raw_angle = cv2.minAreaRect(coords)[-1]

    # Normalize into (-45, 45] regardless of this OpenCV version's convention.
    angle = raw_angle
    while angle > 45:
        angle -= 90
    while angle <= -45:
        angle += 90

    if abs(angle) < 0.5 or abs(angle) > 20:
        return gray_img  # too small to matter, or too large to trust

    (h, w) = gray_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


# ---------- OCR ----------

def run_ocr(gray_img: np.ndarray, reader) -> dict:
    results = reader.readtext(gray_img, detail=1)
    words, lines = [], []
    for bbox, text, conf in results:
        if not text.strip():
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        words.append({
            "text": text, "conf": conf * 100,
            "left": int(min(xs)), "top": int(min(ys)),
            "width": int(max(xs) - min(xs)), "height": int(max(ys) - min(ys)),
        })
        lines.append(text)
    raw_text = "\n".join(lines)
    avg_conf = sum(w["conf"] for w in words) / len(words) if words else 0.0
    return {"raw_text": raw_text, "words": words, "avg_confidence": avg_conf}


# ---------- Field extraction ----------

FIELD_PATTERNS = {
    "register_number": r"(?:reg(?:ister)?\.?\s*no\.?|register\s*number)[:\s]*([A-Z0-9\-/]{4,20})",
    "certificate_id": r"(?:cert(?:ificate)?\.?\s*(?:id|no)\.?)[:\s]*([A-Z0-9\-/]{4,20})",
    "issue_date": r"(?:date\s*of\s*issue|issued\s*on|dated?)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})",
    "degree": r"\b(bachelor|master|b\.?tech|m\.?tech|b\.?sc|m\.?sc|b\.?e\.?|m\.?e\.?|ph\.?d)\b[^\n]{0,40}",
}


def extract_fields(raw_text: str) -> dict:
    text_lower = raw_text.lower()
    fields = {}
    for name, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        fields[name] = match.group(1).strip() if match else None

    name_match = re.search(
        r"certify that\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:has|is|of|bearing))",
        raw_text, re.IGNORECASE
    )
    fields["student_name"] = name_match.group(1).strip() if name_match else None
    fields["missing_field_count"] = sum(1 for v in fields.values() if v is None)
    return fields


# ---------- Main ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python step2_ocr_preprocessing.py path/to/certificate.png")
        sys.exit(1)

    path = sys.argv[1]
    print("=" * 60)
    print("STEP 2: OCR + Preprocessing")
    print("=" * 60)

    print(f"\nLoading: {path}")
    img = load_image(path)

    print("Loading EasyOCR reader (from Step 1's cached weights)...")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    print("Preprocessing (denoise + deskew)...")
    processed = preprocess(img)

    print("Running OCR...")
    ocr_result = run_ocr(processed, reader)

    # Safety net: if the deskewed result looks bad (low confidence, very
    # few words for what should be a text-heavy document), retry on the
    # plain denoised image without any rotation correction, and keep
    # whichever result is actually better. This protects against a bad
    # deskew estimate ruining an otherwise-readable image.
    if ocr_result["avg_confidence"] < 50 or len(ocr_result["words"]) < 3:
        print("Low-confidence result detected — retrying without deskew correction...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised_only = cv2.fastNlMeansDenoising(gray, h=10)
        fallback_result = run_ocr(denoised_only, reader)
        if fallback_result["avg_confidence"] > ocr_result["avg_confidence"]:
            print(f"Fallback improved confidence: {ocr_result['avg_confidence']:.1f}% -> {fallback_result['avg_confidence']:.1f}%")
            ocr_result = fallback_result

    print("\n--- RAW TEXT ---")
    print(ocr_result["raw_text"])
    print(f"\nAverage OCR confidence: {ocr_result['avg_confidence']:.1f}%")
    print(f"Words detected: {len(ocr_result['words'])}")

    fields = extract_fields(ocr_result["raw_text"])
    print("\n--- EXTRACTED FIELDS ---")
    for k, v in fields.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    print("SUCCESS — Step 2 complete.")
    print("=" * 60)