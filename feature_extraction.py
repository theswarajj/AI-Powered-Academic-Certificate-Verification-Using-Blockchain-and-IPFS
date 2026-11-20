"""
STEP 3: Feature Extraction.

Standalone script — runs OCR (same as Step 2) then converts the result
into a fixed-length numeric feature vector: the actual input the fraud
detection model (Step 4) will use.

Run it with:
    python step3_feature_extraction.py path/to/your/certificate.png

Requires Step 1 to have been run already (EasyOCR downloaded).
"""
import subprocess
import sys
import re
import io
from datetime import datetime


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


REQUIRED = [
    ("opencv-python-headless", "cv2"), ("Pillow", "PIL"), ("numpy", "numpy"),
    ("easyocr", "easyocr"), ("rapidfuzz", "rapidfuzz"),
]
for pkg, mod in REQUIRED:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import cv2
import numpy as np
from PIL import Image, ImageChops
from rapidfuzz import fuzz
import easyocr


# ---------- Preprocessing + OCR (same as Step 2) ----------

def load_image_cv(path: str) -> np.ndarray:
    if path.lower().endswith(".pdf"):
        ensure_package_installed("pdf2image", "pdf2image")
        from pdf2image import convert_from_path
        pil_img = convert_from_path(path)[0].convert("RGB")
    else:
        pil_img = Image.open(path).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def preprocess(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.fastNlMeansDenoising(gray, h=10)  # deskew intentionally skipped here — see Step 2 for the full version with the safety-checked deskew


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


# ---------- NEW: Feature Extraction ----------

FEATURE_NAMES = [
    "missing_field_count", "ocr_avg_confidence", "register_number_format_valid",
    "certificate_id_format_valid", "issue_date_valid", "issue_date_plausible_range",
    "institution_name_match_score", "text_block_count", "text_position_variance",
    "font_height_variance", "degree_field_recognized", "ela_unevenness_score",
]

# Extend this list as real institutions register on your platform. In the
# full system this should come from your database's authorized-issuers
# table, not a hardcoded list like this test version.
KNOWN_INSTITUTIONS = [
    "indian institute of technology", "national institute of technology",
    "anna university", "university of kerala", "calicut university",
]

REGISTER_NUMBER_RE = re.compile(r"^[A-Z0-9]{2,4}[A-Z]{0,3}\d{3,8}$", re.IGNORECASE)
CERT_ID_RE = re.compile(r"^CERT-\d{4}-\d{3,6}$", re.IGNORECASE)


def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _institution_match_score(raw_text: str) -> float:
    text_lower = raw_text.lower()
    return max((fuzz.partial_ratio(name, text_lower) for name in KNOWN_INSTITUTIONS), default=0.0)


def _text_position_variance(words: list) -> float:
    if len(words) < 4:
        return 0.0
    tops = [w["top"] for w in words]
    mean = sum(tops) / len(tops)
    return sum((t - mean) ** 2 for t in tops) / len(tops)


def _font_height_variance(words: list) -> float:
    if len(words) < 4:
        return 0.0
    heights = [w["height"] for w in words if w["height"] > 0]
    if not heights:
        return 0.0
    mean = sum(heights) / len(heights)
    return sum((h - mean) ** 2 for h in heights) / len(heights)


def compute_ela_score(file_bytes: bytes, quality: int = 90) -> float:
    """
    Error Level Analysis: re-saves the image at a known JPEG quality and
    measures how UNEVEN the compression error is across the page. A
    genuinely untouched region compresses evenly; a pasted-in or edited
    region tends to stand out. No training data needed for this — it's a
    classical forensics technique, not a model.
    """
    try:
        original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        return 0.0
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer)
    diff_array = np.array(ImageChops.difference(original, resaved), dtype=np.float32)
    mean_error = diff_array.mean()
    if mean_error < 1e-6:
        return 0.0
    return float(diff_array.std() / mean_error)


def build_feature_vector(ocr_result: dict, fields: dict, file_bytes: bytes) -> dict:
    reg_no = fields.get("register_number") or ""
    cert_id = fields.get("certificate_id") or ""
    issue_date = _parse_date(fields.get("issue_date"))
    now_year = datetime.now().year
    date_plausible = bool(issue_date and 2000 <= issue_date.year <= now_year)
    words = ocr_result.get("words", [])

    return {
        "missing_field_count": fields.get("missing_field_count", 0),
        "ocr_avg_confidence": ocr_result.get("avg_confidence", 0.0),
        "register_number_format_valid": 1.0 if REGISTER_NUMBER_RE.match(reg_no) else 0.0,
        "certificate_id_format_valid": 1.0 if CERT_ID_RE.match(cert_id) else 0.0,
        "issue_date_valid": 1.0 if issue_date else 0.0,
        "issue_date_plausible_range": 1.0 if date_plausible else 0.0,
        "institution_name_match_score": _institution_match_score(ocr_result["raw_text"]),
        "text_block_count": len(words),
        "text_position_variance": _text_position_variance(words),
        "font_height_variance": _font_height_variance(words),
        "degree_field_recognized": 1.0 if fields.get("degree") else 0.0,
        "ela_unevenness_score": compute_ela_score(file_bytes),
    }


# ---------- Main ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python step3_feature_extraction.py path/to/certificate.png")
        sys.exit(1)

    path = sys.argv[1]
    print("=" * 60)
    print("STEP 3: Feature Extraction")
    print("=" * 60)

    with open(path, "rb") as f:
        file_bytes = f.read()

    print(f"\nLoading: {path}")
    img = load_image_cv(path)

    print("Loading EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    print("Preprocessing + running OCR...")
    processed = preprocess(img)
    ocr_result = run_ocr(processed, reader)
    fields = extract_fields(ocr_result["raw_text"])

    print("\n--- EXTRACTED FIELDS (from Step 2) ---")
    for k, v in fields.items():
        print(f"  {k}: {v}")

    print("\nBuilding feature vector...")
    vector = build_feature_vector(ocr_result, fields, file_bytes)

    print("\n--- FEATURE VECTOR (12 numbers the model will use) ---")
    for name in FEATURE_NAMES:
        print(f"  {name:35s}: {vector[name]}")

    print("\n" + "=" * 60)
    print("SUCCESS — Step 3 complete.")
    print("=" * 60)