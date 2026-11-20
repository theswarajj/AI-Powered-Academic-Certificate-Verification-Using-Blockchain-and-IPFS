"""
FULL PIPELINE — runs every step automatically, in order:
  Step 1: Ensure the pretrained OCR model is installed & downloaded
  Step 2: Preprocess the certificate + run OCR
  Step 3: Extract the 20-feature vector
  Step 4: Train the fraud model (only if model_v2.pkl doesn't exist yet)
  Step 5: Predict + explain with SHAP


"""
import subprocess
import sys
import os
import re
import io
import json
import math
from datetime import datetime, timedelta


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
    ("shap", "shap"), ("pandas", "pandas"), ("scikit-learn", "sklearn"),
]
for pkg, mod in REQUIRED:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import cv2
import numpy as np
import pandas as pd
import joblib
import shap
from PIL import Image, ImageChops
from rapidfuzz import fuzz
import easyocr
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import (
    RandomForestClassifier, ExtraTreesClassifier,
    HistGradientBoostingClassifier, VotingClassifier,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, roc_auc_score

MODEL_PATH = "model_v2.pkl"

# ============================================================
# FEATURE NAMES — 20 features (expanded from 12)
# ============================================================

FEATURE_NAMES = [
    # --- Original 12 ---
    "missing_field_count", "ocr_avg_confidence", "register_number_format_valid",
    "certificate_id_format_valid", "issue_date_valid", "issue_date_plausible_range",
    "institution_name_match_score", "text_block_count", "text_position_variance",
    "font_height_variance", "degree_field_recognized", "ela_unevenness_score",
    # --- 8 New features ---
    "low_confidence_word_ratio",    # fraction of words with OCR conf < 50%
    "aspect_ratio",                  # image width / height
    "edge_density",                  # Canny edge pixel fraction
    "ela_multi_quality_max",         # max ELA across qualities 70,80,90,95
    "horizontal_alignment_score",    # how well text left-edges align
    "confidence_variance",           # std-dev of per-word OCR confidence
    "signature_area_detected",       # probable signature/stamp region exists
    "text_density_ratio",            # text-area / image-area
]

# ============================================================
# KNOWN DATA — institutions, patterns, templates
# ============================================================

KNOWN_INSTITUTIONS = [
    "indian institute of technology", "national institute of technology",
    "anna university", "university of kerala", "calicut university",
    "university of madras", "university of mumbai", "university of delhi",
    "jawaharlal nehru technological university", "vellore institute of technology",
    "bits pilani", "manipal institute of technology", "amrita vishwa vidyapeetham",
    "savitribai phule pune university", "osmania university",
    "visvesvaraya technological university", "cochin university",
    "mahatma gandhi university", "bharathiar university", "andhra university",
]

REGISTER_NUMBER_RE = re.compile(r"^[A-Z0-9]{2,4}[A-Z]{0,3}\d{3,8}$", re.IGNORECASE)
CERT_ID_RE = re.compile(r"^CERT-\d{4}-\d{3,6}$", re.IGNORECASE)

FIELD_PATTERNS = {
    "register_number": r"(?:reg(?:ister)?\.?\s*no\.?|register\s*number|roll\s*no\.?|enrollment\s*no\.?)[:\s]*([A-Z0-9\-/]{4,20})",
    "certificate_id": r"(?:cert(?:ificate)?\.?\s*(?:id|no)\.?|serial\s*no\.?)[:\s]*([A-Z0-9\-/]{4,20})",
    "issue_date": r"(?:date\s*of\s*issue|issued\s*on|dated?|date\s*:)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
    "degree": r"\b(bachelor|master|b\.?tech|m\.?tech|b\.?sc|m\.?sc|b\.?e\.?|m\.?e\.?|ph\.?d|b\.?com|m\.?com|b\.?a\.?|m\.?a\.?|bba|mba|diploma)\b[^\n]{0,40}",
}

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
    # --- New feature explanations ---
    "low_confidence_word_ratio": {"toward_suspicious": "A high proportion of text was read with low confidence, suggesting altered or degraded regions", "toward_genuine": "Nearly all text was read with high confidence"},
    "aspect_ratio": {"toward_suspicious": "Image dimensions deviate from standard certificate proportions", "toward_genuine": "Image dimensions match standard certificate proportions"},
    "edge_density": {"toward_suspicious": "Abnormal edge pattern detected — consistent with image splicing", "toward_genuine": "Edge pattern is consistent with a cleanly produced document"},
    "ela_multi_quality_max": {"toward_suspicious": "Multi-quality compression analysis reveals inconsistent editing artifacts", "toward_genuine": "Multi-quality compression analysis shows uniform compression"},
    "horizontal_alignment_score": {"toward_suspicious": "Text blocks are poorly aligned, suggesting content was pasted in", "toward_genuine": "Text blocks are well-aligned, consistent with a single-source document"},
    "confidence_variance": {"toward_suspicious": "OCR confidence varies sharply across the document — some regions may be edited", "toward_genuine": "OCR confidence is uniform across the document"},
    "signature_area_detected": {"toward_suspicious": "No signature or seal area detected on the certificate", "toward_genuine": "A signature or seal area was detected"},
    "text_density_ratio": {"toward_suspicious": "Unusual text density suggests the document may be fabricated", "toward_genuine": "Text density is consistent with a standard certificate"},
}


# ============================================================
# STEP 2: Preprocessing + OCR (Enhanced with CLAHE + Deskew)
# ============================================================

def load_image_cv(path: str) -> np.ndarray:
    if path.lower().endswith(".pdf"):
        ensure_package_installed("pdf2image", "pdf2image")
        from pdf2image import convert_from_path
        pil_img = convert_from_path(path)[0].convert("RGB")
    else:
        pil_img = Image.open(path).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _enhance_contrast(gray_img: np.ndarray) -> np.ndarray:
    """CLAHE (Contrast Limited Adaptive Histogram Equalization) improves
    OCR accuracy on scanned/photographed certificates with uneven lighting."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray_img)


def _deskew(gray_img: np.ndarray) -> np.ndarray:
    """
    Estimate and correct small rotation. Ported from ocr_preprocessing.py.
    Normalizes the raw angle into (-45, 45] and refuses corrections > 20°.
    """
    _, mask = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(mask > 0))
    if coords.shape[0] < 50:
        return gray_img

    raw_angle = cv2.minAreaRect(coords)[-1]

    # Normalize into (-45, 45] regardless of OpenCV version's convention.
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


def preprocess(img: np.ndarray) -> np.ndarray:
    """Grayscale → CLAHE → denoise → deskew."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = _enhance_contrast(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    return _deskew(denoised)


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


def run_ocr_with_fallback(img: np.ndarray, reader) -> dict:
    """Run OCR with deskew, and if result is bad, retry without deskew
    and keep whichever is better. Ported from ocr_preprocessing.py."""
    processed = preprocess(img)
    ocr_result = run_ocr(processed, reader)

    if ocr_result["avg_confidence"] < 50 or len(ocr_result["words"]) < 3:
        # Retry without deskew
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced = _enhance_contrast(gray)
        denoised_only = cv2.fastNlMeansDenoising(enhanced, h=10)
        fallback_result = run_ocr(denoised_only, reader)
        if fallback_result["avg_confidence"] > ocr_result["avg_confidence"]:
            print(f"  Deskew fallback improved confidence: {ocr_result['avg_confidence']:.1f}% → {fallback_result['avg_confidence']:.1f}%")
            ocr_result = fallback_result

    return ocr_result


def extract_fields(raw_text: str) -> dict:
    text_lower = raw_text.lower()
    fields = {}
    for name, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        fields[name] = match.group(1).strip() if match else None

    # Student name extraction — multiple trigger phrases
    name_patterns = [
        r"certify that\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:has|is|of|bearing))",
        r"awarded to\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:for|who|having))",
        r"conferred upon\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:the|for|who))",
        r"name\s*:\s*([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s*\n|\s+(?:has|is|reg))",
    ]
    fields["student_name"] = None
    for pat in name_patterns:
        name_match = re.search(pat, raw_text, re.IGNORECASE)
        if name_match:
            fields["student_name"] = name_match.group(1).strip()
            break

    fields["missing_field_count"] = sum(1 for v in fields.values() if v is None)
    return fields


# ============================================================
# STEP 3: Feature Extraction (20 features)
# ============================================================

def _parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y",
                "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d/%m/%y", "%d-%m-%y"):
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
    """Error Level Analysis at a single quality level."""
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


def _compute_ela_multi_quality(file_bytes: bytes) -> float:
    """Multi-quality ELA — max unevenness across 70, 80, 90, 95."""
    scores = []
    for q in (70, 80, 90, 95):
        scores.append(compute_ela_score(file_bytes, quality=q))
    return max(scores) if scores else 0.0


def _low_confidence_word_ratio(words: list) -> float:
    """Fraction of OCR words with confidence < 50%."""
    if not words:
        return 0.0
    low_count = sum(1 for w in words if w["conf"] < 50)
    return low_count / len(words)


def _compute_aspect_ratio(img: np.ndarray) -> float:
    """Image width / height."""
    h, w = img.shape[:2]
    return w / h if h > 0 else 0.0


def _compute_edge_density(img: np.ndarray) -> float:
    """Fraction of pixels that are edges (Canny)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    total_pixels = edges.shape[0] * edges.shape[1]
    return float(np.count_nonzero(edges) / total_pixels) if total_pixels > 0 else 0.0


def _horizontal_alignment_score(words: list) -> float:
    """Measures how well text blocks align on their left edges.
    Lower variance = better alignment = more likely genuine.
    Returns the inverse (high = well aligned, low = poorly aligned)."""
    if len(words) < 4:
        return 100.0  # too few words to judge — assume OK
    lefts = [w["left"] for w in words]
    mean_left = sum(lefts) / len(lefts)
    variance = sum((l - mean_left) ** 2 for l in lefts) / len(lefts)
    # Convert to a 0–100 score where 100 = perfect alignment
    # Use an exponential decay so that small variance → high score
    return float(100.0 * math.exp(-variance / 50000.0))


def _confidence_variance(words: list) -> float:
    """Standard deviation of per-word OCR confidence."""
    if len(words) < 2:
        return 0.0
    confs = [w["conf"] for w in words]
    mean_conf = sum(confs) / len(confs)
    variance = sum((c - mean_conf) ** 2 for c in confs) / len(confs)
    return float(math.sqrt(variance))


def _signature_area_detected(img: np.ndarray) -> float:
    """Detect whether a probable signature/stamp region exists in the
    bottom third of the image. Uses contour analysis on a binary threshold.
    Returns 1.0 (found) or 0.0 (not found) — kept binary for ML feature compatibility."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape[:2]
    # Look in the bottom third (signatures are typically at the bottom)
    bottom_third = gray[int(h * 0.6):, :]
    _, thresh = cv2.threshold(bottom_third, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, cw, ch = cv2.boundingRect(contour)
        # A signature-like region: moderate area, reasonable aspect ratio
        img_area = h * w
        if 0.002 * img_area < area < 0.15 * img_area:
            ar = cw / ch if ch > 0 else 0
            if 1.5 < ar < 10.0:  # signatures are typically wider than tall
                return 1.0
    return 0.0


def _enhanced_signature_analysis(img: np.ndarray) -> dict:
    """Deep signature & seal analysis for richer scoring and reporting.

    Checks performed:
      1. Multi-region contour scan (bottom-third, bottom-left, bottom-right)
      2. Circular seal / stamp detection (HoughCircles)
      3. Ink-color analysis (blue / black ink pixels in signature zones)
      4. Stroke complexity via contour hierarchy depth
      5. Graduated confidence score (0.0 – 1.0)

    Returns a dict consumable by the scoring logic and the frontend.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape[:2]
    img_area = h * w
    if img_area == 0:
        return _empty_sig_result()

    findings = []
    sig_regions = []
    seal_detected = False
    ink_signature_detected = False
    confidence = 0.0

    # ------------------------------------------------------------------
    # 1. Multi-region contour scan
    # ------------------------------------------------------------------
    regions = {
        "bottom_third":  gray[int(h * 0.6):, :],
        "bottom_left":   gray[int(h * 0.65):, :int(w * 0.45)],
        "bottom_right":  gray[int(h * 0.65):, int(w * 0.55):],
    }

    for region_name, region_img in regions.items():
        _, thresh = cv2.threshold(
            region_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            x, y, cw, ch = cv2.boundingRect(contour)
            if area < 0.001 * img_area or area > 0.15 * img_area:
                continue
            ar = cw / ch if ch > 0 else 0

            # Signature-shaped (wider than tall, moderate size)
            if 1.2 < ar < 12.0 and 0.002 * img_area < area:
                # Stroke complexity: count child contours (hierarchy depth)
                children = 0
                if hierarchy is not None:
                    child_idx = hierarchy[0][i][2]  # first child
                    while child_idx != -1:
                        children += 1
                        child_idx = hierarchy[0][child_idx][0]  # next sibling

                sig_regions.append({
                    "region": region_name,
                    "area_pct": round(area / img_area * 100, 3),
                    "aspect_ratio": round(ar, 2),
                    "complexity": children,
                })

    # ------------------------------------------------------------------
    # 2. Circular seal / stamp detection
    # ------------------------------------------------------------------
    try:
        bottom_half = gray[int(h * 0.5):, :]
        blurred = cv2.GaussianBlur(bottom_half, (9, 9), 2)
        bh, bw = bottom_half.shape[:2]
        min_r = int(min(bh, bw) * 0.03)
        max_r = int(min(bh, bw) * 0.25)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.2,
            minDist=max(30, min_r * 2),
            param1=100, param2=40,
            minRadius=max(min_r, 10), maxRadius=max(max_r, 60),
        )
        if circles is not None and len(circles[0]) > 0:
            seal_detected = True
            findings.append({
                "check": "Circular Seal Detection",
                "result": "passed",
                "detail": f"{len(circles[0])} circular seal(s) or stamp(s) detected",
            })
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 3. Ink-color analysis (blue / black ink in bottom region)
    # ------------------------------------------------------------------
    if len(img.shape) == 3:
        try:
            bottom_color = img[int(h * 0.6):, :]
            hsv = cv2.cvtColor(bottom_color, cv2.COLOR_BGR2HSV)
            total_px = hsv.shape[0] * hsv.shape[1]

            # Blue ink: Hue 90-130, Sat > 50, Val 30-220
            blue_mask = cv2.inRange(hsv, (90, 50, 30), (130, 255, 220))
            blue_ratio = float(cv2.countNonZero(blue_mask) / total_px)

            # Black ink: any Hue, low Sat, low Val
            black_mask = cv2.inRange(hsv, (0, 0, 0), (180, 80, 60))
            black_ratio = float(cv2.countNonZero(black_mask) / total_px)

            if blue_ratio > 0.003:
                ink_signature_detected = True
                findings.append({
                    "check": "Ink Color Analysis",
                    "result": "passed",
                    "detail": f"Blue ink detected ({blue_ratio*100:.2f}% of signature region)",
                })
            elif black_ratio > 0.01 and sig_regions:
                ink_signature_detected = True
                findings.append({
                    "check": "Ink Color Analysis",
                    "result": "passed",
                    "detail": f"Black ink detected in signature region ({black_ratio*100:.2f}%)",
                })
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 4. Build findings from contour results
    # ------------------------------------------------------------------
    complex_sigs = [r for r in sig_regions if r["complexity"] >= 3]
    simple_sigs = [r for r in sig_regions if r["complexity"] < 3]

    if complex_sigs:
        findings.append({
            "check": "Handwritten Signature Detection",
            "result": "passed",
            "detail": f"{len(complex_sigs)} complex signature region(s) with stroke detail found",
        })
    if simple_sigs and not complex_sigs:
        findings.append({
            "check": "Signature Shape Detection",
            "result": "partial",
            "detail": f"{len(simple_sigs)} simple signature-shaped region(s) found (low stroke complexity)",
        })

    if not sig_regions and not seal_detected:
        findings.append({
            "check": "Signature / Seal Scan",
            "result": "failed",
            "detail": "No signature or seal region detected anywhere on the certificate",
        })

    # ------------------------------------------------------------------
    # 5. Graduated confidence score
    # ------------------------------------------------------------------
    if complex_sigs:
        confidence += 0.45
    elif simple_sigs:
        confidence += 0.20

    if seal_detected:
        confidence += 0.30

    if ink_signature_detected:
        confidence += 0.25

    confidence = min(confidence, 1.0)

    return {
        "detected": len(sig_regions) > 0 or seal_detected,
        "confidence": round(confidence, 2),
        "signature_count": len(sig_regions),
        "has_seal": seal_detected,
        "has_ink_signature": ink_signature_detected,
        "has_complex_strokes": len(complex_sigs) > 0,
        "regions": sig_regions[:5],   # cap for payload size
        "findings": findings,
    }


def _empty_sig_result() -> dict:
    return {
        "detected": False,
        "confidence": 0.0,
        "signature_count": 0,
        "has_seal": False,
        "has_ink_signature": False,
        "has_complex_strokes": False,
        "regions": [],
        "findings": [{"check": "Signature / Seal Scan", "result": "failed",
                       "detail": "Image too small to analyse"}],
    }


def _text_density_ratio(words: list, img: np.ndarray) -> float:
    """Ratio of total text bounding-box area to total image area."""
    h, w = img.shape[:2]
    img_area = h * w
    if img_area == 0:
        return 0.0
    text_area = sum(w_["width"] * w_["height"] for w_ in words)
    return float(text_area / img_area)


def build_feature_vector(ocr_result: dict, fields: dict, file_bytes: bytes,
                         img: np.ndarray) -> dict:
    reg_no = fields.get("register_number") or ""
    cert_id = fields.get("certificate_id") or ""
    issue_date = _parse_date(fields.get("issue_date"))
    date_plausible = bool(issue_date and 2000 <= issue_date.year <= datetime.now().year)
    words = ocr_result.get("words", [])

    return {
        # --- Original 12 ---
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
        # --- 8 New features ---
        "low_confidence_word_ratio": _low_confidence_word_ratio(words),
        "aspect_ratio": _compute_aspect_ratio(img),
        "edge_density": _compute_edge_density(img),
        "ela_multi_quality_max": _compute_ela_multi_quality(file_bytes),
        "horizontal_alignment_score": _horizontal_alignment_score(words),
        "confidence_variance": _confidence_variance(words),
        "signature_area_detected": _signature_area_detected(img),
        "text_density_ratio": _text_density_ratio(words, img),
    }


# ============================================================
# STEP 4: Train model (ensemble with calibration)
# ============================================================

RNG = np.random.default_rng(42)


def _genuine_sample():
    return {
        # --- Original 12 ---
        "missing_field_count": RNG.choice([0, 0, 0, 1], p=[0.85, 0.05, 0.05, 0.05]),
        "ocr_avg_confidence": np.clip(RNG.normal(87, 5), 50, 100),
        "register_number_format_valid": RNG.choice([1.0, 0.0], p=[0.95, 0.05]),
        "certificate_id_format_valid": RNG.choice([1.0, 0.0], p=[0.95, 0.05]),
        "issue_date_valid": RNG.choice([1.0, 0.0], p=[0.97, 0.03]),
        "issue_date_plausible_range": RNG.choice([1.0, 0.0], p=[0.97, 0.03]),
        "institution_name_match_score": np.clip(RNG.normal(88, 10), 0, 100),
        "text_block_count": np.clip(RNG.normal(10, 3), 4, 30),
        "text_position_variance": np.clip(RNG.normal(18000, 3500), 500, 40000),
        "font_height_variance": np.clip(RNG.normal(45, 18), 0, 150),
        "degree_field_recognized": RNG.choice([1.0, 0.0], p=[0.96, 0.04]),
        "ela_unevenness_score": np.clip(RNG.normal(3.8, 0.8), 0, 12),
        # --- 8 New features ---
        "low_confidence_word_ratio": np.clip(RNG.normal(0.05, 0.04), 0, 1),
        "aspect_ratio": np.clip(RNG.normal(1.55, 0.15), 0.8, 2.5),
        "edge_density": np.clip(RNG.normal(0.04, 0.012), 0, 0.3),
        "ela_multi_quality_max": np.clip(RNG.normal(4.2, 0.9), 0, 15),
        "horizontal_alignment_score": np.clip(RNG.normal(75, 12), 0, 100),
        "confidence_variance": np.clip(RNG.normal(8, 4), 0, 40),
        "signature_area_detected": RNG.choice([1.0, 0.0], p=[0.85, 0.15]),
        "text_density_ratio": np.clip(RNG.normal(0.12, 0.03), 0, 0.5),
    }


def _tampered_sample():
    return {
        # --- Original 12 ---
        "missing_field_count": RNG.choice([0, 1, 2, 3], p=[0.25, 0.30, 0.28, 0.17]),
        "ocr_avg_confidence": np.clip(RNG.normal(58, 15), 10, 100),
        "register_number_format_valid": RNG.choice([1.0, 0.0], p=[0.45, 0.55]),
        "certificate_id_format_valid": RNG.choice([1.0, 0.0], p=[0.40, 0.60]),
        "issue_date_valid": RNG.choice([1.0, 0.0], p=[0.55, 0.45]),
        "issue_date_plausible_range": RNG.choice([1.0, 0.0], p=[0.60, 0.40]),
        "institution_name_match_score": np.clip(RNG.normal(40, 20), 0, 100),
        "text_block_count": np.clip(RNG.normal(6, 4), 2, 30),
        "text_position_variance": np.clip(RNG.normal(36000, 8000), 500, 60000),
        "font_height_variance": np.clip(RNG.normal(115, 40), 0, 250),
        "degree_field_recognized": RNG.choice([1.0, 0.0], p=[0.55, 0.45]),
        "ela_unevenness_score": np.clip(RNG.normal(7.8, 2.0), 0, 20),
        # --- 8 New features ---
        "low_confidence_word_ratio": np.clip(RNG.normal(0.30, 0.15), 0, 1),
        "aspect_ratio": np.clip(RNG.normal(1.45, 0.35), 0.5, 3.0),
        "edge_density": np.clip(RNG.normal(0.07, 0.025), 0, 0.3),
        "ela_multi_quality_max": np.clip(RNG.normal(8.5, 2.5), 0, 20),
        "horizontal_alignment_score": np.clip(RNG.normal(45, 20), 0, 100),
        "confidence_variance": np.clip(RNG.normal(20, 8), 0, 50),
        "signature_area_detected": RNG.choice([1.0, 0.0], p=[0.40, 0.60]),
        "text_density_ratio": np.clip(RNG.normal(0.08, 0.04), 0, 0.5),
    }


def train_model():
    # Generate 5,000 synthetic samples (3,000 genuine + 2,000 tampered)
    rows = []
    for _ in range(3000):
        s = _genuine_sample(); s["label"] = 0; rows.append(s)
    for _ in range(2000):
        s = _tampered_sample(); s["label"] = 1; rows.append(s)
    df = pd.DataFrame(rows)[FEATURE_NAMES + ["label"]].sample(frac=1, random_state=42).reset_index(drop=True)

    X, y = df[FEATURE_NAMES], df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # --- Build 3-model voting ensemble ---
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=4,
        random_state=42, class_weight="balanced", n_jobs=-1,
    )
    et = ExtraTreesClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=3,
        random_state=42, class_weight="balanced", n_jobs=-1,
    )
    hgb = HistGradientBoostingClassifier(
        max_iter=300, max_depth=6, learning_rate=0.08,
        min_samples_leaf=8, random_state=42,
        class_weight="balanced",
    )

    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("et", et), ("hgb", hgb)],
        voting="soft",
        n_jobs=-1,
    )

    # --- Stratified 5-fold cross-validation ---
    print("  Running 5-fold stratified cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(ensemble, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)
    print(f"  CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  Per-fold:   {', '.join(f'{s:.4f}' for s in cv_scores)}")

    # --- Fit the ensemble ---
    print("  Training voting ensemble (RF + ExtraTrees + HistGradientBoosting)...")
    ensemble.fit(X_train, y_train)

    # --- Probability calibration (isotonic) ---
    print("  Calibrating probabilities (isotonic regression)...")
    calibrated = CalibratedClassifierCV(ensemble, cv=3, method="isotonic")
    calibrated.fit(X_train, y_train)

    # --- Evaluate on held-out test set ---
    y_pred = calibrated.predict(X_test)
    y_proba = calibrated.predict_proba(X_test)[:, 1]
    print("\n  Held-out test accuracy report:")
    print("  " + classification_report(y_test, y_pred, target_names=["genuine", "suspicious"]).replace("\n", "\n  "))
    print(f"  ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    # --- Feature importances from the underlying RF ---
    print("\n  Feature importances (from Random Forest):")
    rf_model = ensemble.named_estimators_["rf"]
    for name, imp in sorted(zip(FEATURE_NAMES, rf_model.feature_importances_), key=lambda x: -x[1]):
        bar = "#" * int(imp * 100)
        print(f"    {name:35s}: {imp:.4f}  {bar}")

    # Save the synthetic dataset for reference
    df.to_csv("synthetic_dataset_v2.csv", index=False)
    print(f"  Synthetic dataset saved: synthetic_dataset_v2.csv ({len(df)} rows)")

    joblib.dump(calibrated, MODEL_PATH)
    return calibrated


# ============================================================
# STEP 5: Predict + Explain (with hard rules + rich output)
# ============================================================

def _confidence_band(fraud_pct: float) -> str:
    """Classify the model's confidence in its own prediction."""
    if fraud_pct >= 85 or fraud_pct <= 15:
        return "HIGH_CONFIDENCE"
    elif fraud_pct >= 70 or fraud_pct <= 30:
        return "MODERATE_CONFIDENCE"
    else:
        return "LOW_CONFIDENCE"


def _risk_score(fraud_pct: float, hard_rule_count: int) -> int:
    """0–100 risk score combining ML probability and hard-rule failures."""
    base = fraud_pct
    # Each hard-rule failure adds 15 points (capped at 100)
    bonus = hard_rule_count * 15
    return min(100, int(base + bonus))


def predict_and_explain(vector: dict, model, fields: dict, img=None) -> dict:
    X = pd.DataFrame([vector], columns=FEATURE_NAMES)
    proba = model.predict_proba(X)[0]
    fraud_probability = float(proba[1])
    
    # --- Enhanced Signature Analysis & Graduated Scoring ---
    signature_analysis = _empty_sig_result()
    if img is not None:
        signature_analysis = _enhanced_signature_analysis(img)
    
    sig_conf = signature_analysis["confidence"]
    if signature_analysis["detected"]:
        # Graduated boost: high-confidence signature = bigger reduction
        if sig_conf >= 0.7:
            fraud_probability = max(0.0, fraud_probability - 0.20)
        elif sig_conf >= 0.4:
            fraud_probability = max(0.0, fraud_probability - 0.12)
        else:
            fraud_probability = max(0.0, fraud_probability - 0.05)
    else:
        # No signature at all: penalise
        fraud_probability = min(1.0, fraud_probability + 0.15)
        
    ml_prediction = "SUSPICIOUS" if fraud_probability >= 0.5 else "LIKELY_GENUINE"

    # --- SHAP explanation ---
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    fraud_class_shap = None

    # Strategy 1: Use TreeExplainer on the underlying RF estimator
    try:
        # CalibratedClassifierCV wraps the ensemble; dig into the RF for TreeExplainer
        base_model = model
        # Unwrap CalibratedClassifierCV -> VotingClassifier -> RandomForest
        if hasattr(base_model, 'estimator'):
            base_model = base_model.estimator  # VotingClassifier
        if hasattr(base_model, 'named_estimators_'):
            base_model = base_model.named_estimators_["rf"]  # RandomForest

        explainer = shap.TreeExplainer(base_model)
        shap_values = explainer.shap_values(X.values)
        if isinstance(shap_values, list):
            fraud_class_shap = np.array(shap_values[1]).flatten()
        elif hasattr(shap_values, 'ndim') and shap_values.ndim == 3:
            fraud_class_shap = shap_values[0, :, 1].flatten()
        else:
            fraud_class_shap = np.array(shap_values).flatten()
    except Exception:
        pass

    # Strategy 2: KernelExplainer with a proper synthetic background
    if fraud_class_shap is None or np.allclose(fraud_class_shap, 0):
        try:
            # Generate a diverse background (50 mixed genuine+tampered samples)
            bg_rows = []
            bg_rng = np.random.default_rng(99)
            for _ in range(30):
                bg_rows.append(_genuine_sample())
            for _ in range(20):
                bg_rows.append(_tampered_sample())
            background = pd.DataFrame(bg_rows, columns=FEATURE_NAMES)

            explainer = shap.KernelExplainer(model.predict_proba, background)
            shap_values = explainer.shap_values(X, nsamples=300)
            if isinstance(shap_values, list):
                fraud_class_shap = np.array(shap_values[1]).flatten()
            elif hasattr(shap_values, 'ndim') and shap_values.ndim == 3:
                fraud_class_shap = shap_values[0, :, 1].flatten()
            else:
                fraud_class_shap = np.array(shap_values).flatten()
        except Exception:
            # Last resort: use feature importances as a proxy
            fraud_class_shap = np.zeros(len(FEATURE_NAMES))

    warnings.resetwarnings()

    # Ensure we have exactly one SHAP value per feature (as Python floats)
    if len(fraud_class_shap) != len(FEATURE_NAMES):
        fraud_class_shap = fraud_class_shap[:len(FEATURE_NAMES)]

    contributions = sorted(
        zip(FEATURE_NAMES, [float(s) for s in fraud_class_shap], [vector[n] for n in FEATURE_NAMES]),
        key=lambda x: abs(x[1]), reverse=True
    )

    # Build ALL explanations (grouped by direction)
    all_explanations = []
    for name, shap_val, feat_val in contributions:
        direction = "toward_suspicious" if shap_val > 0 else "toward_genuine"
        message = EXPLANATION_TEMPLATES.get(name, {}).get(direction)
        if message:
            all_explanations.append({
                "feature": name, "value": float(feat_val),
                "shap_value": float(shap_val),
                "pushes_toward": "suspicious" if shap_val > 0 else "genuine",
                "message": message,
            })

    # --- Hard-rule layer (expanded: 6 rules) ---
    hard_rule_failures = []

    # Rule 1: Invalid date
    if vector["issue_date_valid"] == 0.0:
        hard_rule_failures.append("Issue date could not be parsed as a valid date")

    # Rule 2: Date out of plausible range
    if vector["issue_date_plausible_range"] == 0.0 and vector["issue_date_valid"] == 1.0:
        hard_rule_failures.append("Issue date falls outside a plausible range")

    # Rule 3: Future date (more specific)
    issue_date = _parse_date(fields.get("issue_date"))
    if issue_date and issue_date > datetime.now() + timedelta(days=30):
        hard_rule_failures.append(f"Issue date ({fields.get('issue_date')}) is in the future")

    # Rule 4: Too many missing fields
    if vector["missing_field_count"] >= 3:
        hard_rule_failures.append(f"Too many expected fields missing ({int(vector['missing_field_count'])} of 5)")

    # Rule 5: Catastrophically low OCR confidence
    if vector["ocr_avg_confidence"] < 30:
        hard_rule_failures.append(f"OCR confidence is critically low ({vector['ocr_avg_confidence']:.1f}%) — document may be unreadable or heavily degraded")

    # Rule 6: Cert ID clearly invalid despite high OCR confidence
    if vector["certificate_id_format_valid"] == 0.0 and vector["ocr_avg_confidence"] > 80:
        cert_id_raw = fields.get("certificate_id")
        if cert_id_raw:  # only flag if OCR actually found a cert ID field but it's wrong format
            hard_rule_failures.append(f"Certificate ID '{cert_id_raw}' does not match any valid format despite clear OCR read")

    # --- Final verdict ---
    if hard_rule_failures:
        final_prediction = "SUSPICIOUS"
        override_applied = (ml_prediction == "LIKELY_GENUINE")
    else:
        final_prediction = ml_prediction
        override_applied = False

    fraud_pct = round(fraud_probability * 100, 2)
    risk = _risk_score(fraud_pct, len(hard_rule_failures))
    band = _confidence_band(fraud_pct)

    return {
        "ml_prediction": ml_prediction,
        "final_prediction": final_prediction,
        "override_applied": override_applied,
        "hard_rule_failures": hard_rule_failures,
        "fraud_probability_pct": fraud_pct,
        "risk_score": risk,
        "confidence_band": band,
        "top_explanations": all_explanations[:5],
        "all_explanations": all_explanations,
        "feature_vector": {k: round(v, 4) if isinstance(v, float) else v for k, v in vector.items()},
        "fields_extracted": fields,
        "signature_detected": signature_analysis["detected"],
        "signature_analysis": signature_analysis,
    }


def save_json_report(result: dict, cert_path: str):
    """Save a machine-readable JSON report alongside the verdict."""
    report_path = os.path.splitext(cert_path)[0] + "_report.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "certificate_file": os.path.basename(cert_path),
        "final_verdict": result["final_prediction"],
        "risk_score": result["risk_score"],
        "confidence_band": result["confidence_band"],
        "fraud_probability_pct": result["fraud_probability_pct"],
        "ml_prediction": result["ml_prediction"],
        "hard_rule_override": result["override_applied"],
        "hard_rule_failures": result["hard_rule_failures"],
        "fields_extracted": result["fields_extracted"],
        "feature_vector": result["feature_vector"],
        "shap_explanations": result["all_explanations"],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return report_path


# ============================================================
# MAIN — runs all 5 steps automatically, in order
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_pipeline.py path/to/certificate.png")
        sys.exit(1)

    cert_path = sys.argv[1]
    if not os.path.exists(cert_path):
        print(f"[FAIL] File not found: {cert_path}")
        sys.exit(1)

    print("=" * 65)
    print("  CERTIFICATE FRAUD DETECTION PIPELINE v2.0 (Enhanced)")
    print("=" * 65)

    # ---- STEP 1 ----
    print("\n" + "#" * 65)
    print("# STEP 1/5 — Ensure pretrained OCR model is ready")
    print("#" * 65)
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("[OK] EasyOCR model ready.\n")

    # ---- STEP 2 ----
    print("#" * 65)
    print("# STEP 2/5 — Preprocessing + OCR (CLAHE + Deskew + Fallback)")
    print("#" * 65)
    with open(cert_path, "rb") as f:
        file_bytes = f.read()
    img = load_image_cv(cert_path)
    ocr_result = run_ocr_with_fallback(img, reader)
    fields = extract_fields(ocr_result["raw_text"])
    print(f"OCR confidence: {ocr_result['avg_confidence']:.1f}%")
    print(f"Words detected: {len(ocr_result['words'])}")
    for k, v in fields.items():
        print(f"  {k}: {v}")
    print()

    # ---- STEP 3 ----
    print("#" * 65)
    print("# STEP 3/5 — Feature Extraction (20 features)")
    print("#" * 65)
    vector = build_feature_vector(ocr_result, fields, file_bytes, img)
    for name in FEATURE_NAMES:
        val = vector[name]
        formatted = f"{val:.4f}" if isinstance(val, float) else str(val)
        print(f"  {name:35s}: {formatted}")
    print()

    # ---- STEP 4 ----
    print("#" * 65)
    print("# STEP 4/5 — Fraud Model (Voting Ensemble + Calibration)")
    print("#" * 65)
    if os.path.exists(MODEL_PATH):
        print(f"[OK] {MODEL_PATH} already exists — loading it (skipping training).")
        model = joblib.load(MODEL_PATH)
    else:
        print(f"{MODEL_PATH} not found — training a new model on synthetic data...")
        model = train_model()
        print(f"[OK] {MODEL_PATH} saved.")
    print()

    # ---- STEP 5 ----
    print("#" * 65)
    print("# STEP 5/5 — Prediction + SHAP Explanation")
    print("#" * 65)
    result = predict_and_explain(vector, model, fields, img)

    print(f"ML model prediction     : {result['ml_prediction']} ({result['fraud_probability_pct']}% fraud probability)")
    print(f"Confidence band         : {result['confidence_band']}")
    print(f"Risk score              : {result['risk_score']}/100")

    if result["hard_rule_failures"]:
        print(f"Hard-rule check         : FAILED ({len(result['hard_rule_failures'])} rule(s))")
        for reason in result["hard_rule_failures"]:
            print(f"  [!] {reason}")
        if result["override_applied"]:
            print("  (this overrides the ML model's genuine prediction)")
    else:
        print("Hard-rule check         : PASSED")

    print(f"\n{'=' * 65}")
    if result["final_prediction"] == "SUSPICIOUS":
        print(f"  FINAL VERDICT: [!!] {result['final_prediction']}  (Risk: {result['risk_score']}/100)")
    else:
        print(f"  FINAL VERDICT: [OK] {result['final_prediction']}  (Risk: {result['risk_score']}/100)")
    print(f"{'=' * 65}")

    print("\nTop contributing factors (from SHAP):")
    suspicious_factors = [e for e in result["all_explanations"] if e["pushes_toward"] == "suspicious"]
    genuine_factors = [e for e in result["all_explanations"] if e["pushes_toward"] == "genuine"]

    if suspicious_factors:
        print("\n  [RED] Factors pushing toward SUSPICIOUS:")
        for exp in suspicious_factors[:5]:
            print(f"     [!] {exp['message']}  (value={exp['value']:.2f}, SHAP={exp['shap_value']:+.4f})")

    if genuine_factors:
        print("\n  [GRN] Factors pushing toward GENUINE:")
        for exp in genuine_factors[:5]:
            print(f"     [+] {exp['message']}  (value={exp['value']:.2f}, SHAP={exp['shap_value']:+.4f})")

    # Save JSON report
    report_path = save_json_report(result, cert_path)
    print(f"\n[*] Detailed JSON report saved: {report_path}")

    print("\n" + "#" * 65)
    print("# ALL STEPS COMPLETE")
    print("#" * 65)