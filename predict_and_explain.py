"""
STEP 5: Full Pipeline — OCR to SHAP Explanation.

Standalone script — the complete AI intelligence layer in one file:
  1. Preprocessing + OCR (Step 2)
  2. Feature extraction (Step 3)
  3. Fraud prediction using model.pkl (Step 4)
  4. SHAP explanation — WHY the model predicted what it did

Run it with:
    python step5_predict_and_explain.py path/to/certificate.png

Requires model.pkl to exist in the same folder (produced by Step 4).
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
    ("easyocr", "easyocr"), ("rapidfuzz", "rapidfuzz"), ("joblib", "joblib"),
    ("shap", "shap"), ("pandas", "pandas"),
]
for pkg, mod in REQUIRED:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import os
import cv2
import numpy as np
import pandas as pd
import joblib
import shap
from PIL import Image, ImageChops
from rapidfuzz import fuzz
import easyocr


# ---------- OCR + Preprocessing (Steps 1-2) ----------

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
    return cv2.fastNlMeansDenoising(gray, h=10)


def run_ocr(gray_img: np.ndarray, reader) -> dict:
    results = reader.readtext(gray_img, detail=1)
    words, lines = [], []
    for bbox, text, conf in results:
        if not text.strip():
            continue
        xs, ys = [p[0] for p in bbox], [p[1] for p in bbox]
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


# ---------- Feature Extraction (Step 3) ----------

FEATURE_NAMES = [
    "missing_field_count", "ocr_avg_confidence", "register_number_format_valid",
    "certificate_id_format_valid", "issue_date_valid", "issue_date_plausible_range",
    "institution_name_match_score", "text_block_count", "text_position_variance",
    "font_height_variance", "degree_field_recognized", "ela_unevenness_score",
]

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
    return float(diff_array.std() / mean_error) if mean_error > 1e-6 else 0.0


def build_feature_vector(ocr_result: dict, fields: dict, file_bytes: bytes) -> dict:
    reg_no = fields.get("register_number") or ""
    cert_id = fields.get("certificate_id") or ""
    issue_date = _parse_date(fields.get("issue_date"))
    date_plausible = bool(issue_date and 2000 <= issue_date.year <= datetime.now().year)
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


# ---------- NEW: Prediction + SHAP Explanation (Step 4/5) ----------

EXPLANATION_TEMPLATES = {
    "missing_field_count": {"toward_suspicious": "Expected certificate fields were not detected", "toward_genuine": "All expected certificate fields were detected"},
    "ocr_avg_confidence": {"toward_suspicious": "Text recognition confidence is unusually low", "toward_genuine": "Text recognition confidence is high and consistent"},
    "register_number_format_valid": {"toward_suspicious": "Register number does not match the expected format", "toward_genuine": "Register number follows the expected format"},
    "certificate_id_format_valid": {"toward_suspicious": "Certificate ID does not match the expected format", "toward_genuine": "Certificate ID follows the expected format"},
    "issue_date_valid": {"toward_suspicious": "Issue date is missing or incorrectly formatted", "toward_genuine": "Issue date is present and correctly formatted"},
    "issue_date_plausible_range": {"toward_suspicious": "Issue date falls outside a plausible range", "toward_genuine": "Issue date falls within a plausible range"},
    "institution_name_match_score": {"toward_suspicious": "Institution name does not closely match any known institution", "toward_genuine": "Institution name closely matches a known institution"},
    "text_block_count": {"toward_suspicious": "Document contains unusually little text content", "toward_genuine": "Document contains a typical amount of text content"},
    "text_position_variance": {"toward_suspicious": "Unusual document structure (text positioning is inconsistent)", "toward_genuine": "Document structure is consistent with a standard template"},
    "font_height_variance": {"toward_suspicious": "Inconsistent font sizing detected, a common tamper signal", "toward_genuine": "Font sizing is consistent throughout the document"},
    "degree_field_recognized": {"toward_suspicious": "Degree information could not be clearly recognized", "toward_genuine": "Degree information was clearly recognized"},
    "ela_unevenness_score": {"toward_suspicious": "Image compression pattern shows uneven error, consistent with local editing", "toward_genuine": "Image compression pattern is consistent across the document"},
}


def predict_and_explain(vector: dict, model) -> dict:
    X = pd.DataFrame([vector], columns=FEATURE_NAMES)
    proba = model.predict_proba(X)[0]
    fraud_probability = float(proba[1])
    prediction = "SUSPICIOUS" if fraud_probability >= 0.5 else "LIKELY_GENUINE"

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    fraud_class_shap = shap_values[1][0] if isinstance(shap_values, list) else (
        shap_values[0][:, 1] if shap_values.ndim == 3 else shap_values[0]
    )

    contributions = sorted(
        zip(FEATURE_NAMES, fraud_class_shap, [vector[n] for n in FEATURE_NAMES]),
        key=lambda x: abs(x[1]), reverse=True
    )

    explanations = []
    for name, shap_val, feat_val in contributions[:4]:
        direction = "toward_suspicious" if shap_val > 0 else "toward_genuine"
        message = EXPLANATION_TEMPLATES.get(name, {}).get(direction)
        if message:
            explanations.append({
                "feature": name, "value": float(feat_val),
                "pushes_toward": "suspicious" if shap_val > 0 else "genuine",
                "message": message,
            })

    return {
        "prediction": prediction,
        "fraud_probability_pct": round(fraud_probability * 100, 2),
        "top_explanations": explanations,
    }


# ---------- Main ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python step5_predict_and_explain.py path/to/certificate.png")
        sys.exit(1)

    path = sys.argv[1]
    print("=" * 60)
    print("STEP 5: Full Pipeline — OCR to SHAP Explanation")
    print("=" * 60)

    if not os.path.exists("model.pkl"):
        print("\n[FAIL] model.pkl not found in this folder.")
        print("Run step4_train_model.py first — it must be run from the")
        print("same folder as this script (or move model.pkl here).")
        sys.exit(1)

    with open(path, "rb") as f:
        file_bytes = f.read()

    print(f"\nLoading: {path}")
    img = load_image_cv(path)

    print("Loading EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    print("Running OCR + feature extraction...")
    processed = preprocess(img)
    ocr_result = run_ocr(processed, reader)
    fields = extract_fields(ocr_result["raw_text"])
    vector = build_feature_vector(ocr_result, fields, file_bytes)

    print("Loading trained model...")
    model = joblib.load("model.pkl")

    print("Running prediction + SHAP explanation...")
    result = predict_and_explain(vector, model)

    print("\n" + "-" * 60)
    print("FINAL RESULT")
    print("-" * 60)
    print(f"Prediction         : {result['prediction']}")
    print(f"Fraud probability  : {result['fraud_probability_pct']}%")
    print("\nTop reasons (from SHAP):")
    for exp in result["top_explanations"]:
        arrow = "⚠" if exp["pushes_toward"] == "suspicious" else "✓"
        print(f"  {arrow} {exp['message']}  (value={exp['value']:.2f})")

    print("\n" + "=" * 60)
    print("SUCCESS — Step 5 complete. Full pipeline working end to end.")
    print("=" * 60)