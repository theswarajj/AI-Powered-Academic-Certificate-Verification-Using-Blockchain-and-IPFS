"""
VERIFICATION ENGINE v3 -- the complete 4-layer verification system.

Combines ALL project layers into one unified engine:
  Layer 1: Hashing       -- dual-hash (file + content) comparison
  Layer 2: Blockchain    -- on-chain record, revocation, issuer, timestamp
  Layer 3: IPFS          -- availability + content integrity
  Layer 4: AI            -- 20-feature ensemble + SHAP + hard rules

Enhancements over v2:
  * Dual-hash verification (file_hash + content_hash vs on-chain)
  * Content hash cross-validation from OCR-extracted fields
  * Blockchain timestamp vs certificate issue-date coherence check
  * IPFS content integrity (download + hash comparison, not just HEAD)
  * Weighted multi-layer risk scoring (0-100)
  * Known issuer address verification
  * Graceful degradation when blockchain/IPFS is unreachable
  * Full JSON verification report
  * Verification audit log
  * All SHAP explanations grouped by direction
  * Windows cp1252-safe ASCII output

Verdicts:
  VERIFIED             -- all layers pass
  NOT_FOUND            -- no blockchain record for this cert ID
  REVOKED              -- certificate revoked by issuer on-chain
  HASH_MISMATCH        -- file hash does not match on-chain record
  CONTENT_MISMATCH     -- file matches but extracted content hash differs
  REQUIRES_INVESTIGATION -- AI flags it despite hash/chain passing
  PARTIALLY_VERIFIED   -- some layers passed, some couldn't be checked

Needs, in the same folder:
  - .env with SEPOLIA_RPC_URL
  - model_v2.pkl

Run:
    python final_engine.py CERT-2026-00891 path/to/certificate.png
"""
import subprocess
import sys
import os
import re
import io
import json
import math
import hashlib
import warnings
import logging
from datetime import datetime, timedelta


# ============================================================
# Auto-install dependencies
# ============================================================

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
    ("shap", "shap"), ("pandas", "pandas"), ("web3", "web3"),
    ("python-dotenv", "dotenv"), ("requests", "requests"), ("scikit-learn", "sklearn"),
]
for pkg, mod in REQUIRED:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import cv2
import numpy as np
import pandas as pd
import joblib
import shap
import requests
from PIL import Image, ImageChops
from rapidfuzz import fuzz
import easyocr
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Configuration
# ============================================================

CONTRACT_ADDRESS = "0x099aA35Af18acA4D03d010E861b02A4A790846Ab"
IPFS_GATEWAYS = [
    "https://gateway.pinata.cloud/ipfs",
    "https://dweb.link/ipfs",
    "https://ipfs.io/ipfs",
    "https://cloudflare-ipfs.com/ipfs"
]
MODEL_PATH = "model_v2.pkl"

# Audit log file
AUDIT_LOG_PATH = "verification_audit.log"

CONTRACT_ABI = [
    {"inputs": [{"internalType": "string", "name": "certId", "type": "string"}],
     "name": "verifyCertificate",
     "outputs": [
         {"internalType": "string", "name": "ipfsCID", "type": "string"},
         {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
         {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
         {"internalType": "address", "name": "issuer", "type": "address"},
         {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
         {"internalType": "bool", "name": "revoked", "type": "bool"},
         {"internalType": "bool", "name": "exists", "type": "bool"},
     ],
     "stateMutability": "view", "type": "function"},
]

# Known authorized issuer addresses (expand as institutions register)
# Maps wallet address -> institution name
KNOWN_ISSUERS = {
    # Add your deployer/institution addresses here
    # "0x1234...": "National Institute of Technology",
}

# --- 20 features, matching ai_pipeline.py v2 exactly ---
FEATURE_NAMES = [
    "missing_field_count", "ocr_avg_confidence", "register_number_format_valid",
    "certificate_id_format_valid", "issue_date_valid", "issue_date_plausible_range",
    "institution_name_match_score", "text_block_count", "text_position_variance",
    "font_height_variance", "degree_field_recognized", "ela_unevenness_score",
    "low_confidence_word_ratio", "aspect_ratio", "edge_density",
    "ela_multi_quality_max", "horizontal_alignment_score", "confidence_variance",
    "signature_area_detected", "text_density_ratio",
]

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
    "low_confidence_word_ratio": {"toward_suspicious": "A high proportion of text was read with low confidence", "toward_genuine": "Nearly all text was read with high confidence"},
    "aspect_ratio": {"toward_suspicious": "Image dimensions deviate from standard certificate proportions", "toward_genuine": "Image dimensions match standard certificate proportions"},
    "edge_density": {"toward_suspicious": "Abnormal edge pattern detected, consistent with image splicing", "toward_genuine": "Edge pattern is consistent with a cleanly produced document"},
    "ela_multi_quality_max": {"toward_suspicious": "Multi-quality compression analysis reveals editing artifacts", "toward_genuine": "Multi-quality compression analysis shows uniform compression"},
    "horizontal_alignment_score": {"toward_suspicious": "Text blocks are poorly aligned, suggesting content was pasted in", "toward_genuine": "Text blocks are well-aligned, consistent with a single-source document"},
    "confidence_variance": {"toward_suspicious": "OCR confidence varies sharply across the document", "toward_genuine": "OCR confidence is uniform across the document"},
    "signature_area_detected": {"toward_suspicious": "No signature or seal area detected on the certificate", "toward_genuine": "A signature or seal area was detected"},
    "text_density_ratio": {"toward_suspicious": "Unusual text density suggests the document may be fabricated", "toward_genuine": "Text density is consistent with a standard certificate"},
}


# ============================================================
# Audit Logger
# ============================================================

def _setup_audit_logger():
    logger = logging.getLogger("verification_audit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(AUDIT_LOG_PATH, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(fh)
    return logger

audit_logger = _setup_audit_logger()


def log_audit(cert_id: str, verdict: str, risk_score: int, details: str = ""):
    """Append to the audit log file."""
    audit_logger.info(f"cert_id={cert_id} | verdict={verdict} | risk={risk_score} | {details}")


# ============================================================
# LAYER 1: Hashing (dual-hash: file + content)
# ============================================================

def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 of the raw file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def compute_content_hash(fields: dict) -> str:
    """SHA-256 of the extracted structured fields as canonical JSON.
    Fields are normalized (lowercase, stripped) so minor OCR casing
    differences don't cause false hash mismatches.
    IMPORTANT: The issuance side (hash_certificate.py) MUST apply the
    same normalization before storing the content hash on-chain."""
    # Only hash the 5 core fields (same as hash_certificate.py)
    def _normalize(val):
        return (val or "").strip().lower()

    core_fields = {
        "student_name": _normalize(fields.get("student_name")),
        "register_number": _normalize(fields.get("register_number")),
        "certificate_id": _normalize(fields.get("certificate_id")),
        "degree": _normalize(fields.get("degree")),
        "issue_date": _normalize(fields.get("issue_date")),
    }
    canonical = json.dumps(core_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_hash_layer(file_bytes: bytes, fields: dict, chain_record: dict) -> dict:
    """Layer 1: Compute both hashes and compare to on-chain values."""
    computed_file_hash = compute_file_hash(file_bytes)
    computed_content_hash = compute_content_hash(fields)

    result = {
        "computed_file_hash": computed_file_hash,
        "computed_content_hash": computed_content_hash,
        "onchain_file_hash": None,
        "onchain_content_hash": None,
        "file_hash_match": False,
        "content_hash_match": False,
        "layer_available": False,
    }

    if chain_record and chain_record.get("exists"):
        result["layer_available"] = True
        onchain_fh = chain_record["file_hash"]
        onchain_ch = chain_record["content_hash"]

        # On-chain hashes come as hex strings (without 0x prefix from .hex())
        # Our computed hashes are also hex strings without prefix
        # Normalize: strip leading zeros and '0x' for comparison
        def normalize_hash(h):
            h = h.lower().strip()
            if h.startswith("0x"):
                h = h[2:]
            return h.lstrip("0") or "0"

        result["onchain_file_hash"] = onchain_fh
        result["onchain_content_hash"] = onchain_ch
        result["file_hash_match"] = (normalize_hash(computed_file_hash) == normalize_hash(onchain_fh))
        result["content_hash_match"] = (normalize_hash(computed_content_hash) == normalize_hash(onchain_ch))

    return result


# ============================================================
# LAYER 2: Blockchain (with timestamp + issuer validation)
# ============================================================

def query_blockchain(cert_id: str) -> dict:
    """Query the smart contract. Returns None on failure (graceful degradation)."""
    rpc_url = os.environ.get("SEPOLIA_RPC_URL")
    if not rpc_url:
        return {"error": "SEPOLIA_RPC_URL not set in .env", "available": False}

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        if not w3.is_connected():
            return {"error": "Cannot connect to Sepolia RPC", "available": False}

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI
        )
        ipfs_cid, file_hash, content_hash, issuer, timestamp, revoked, exists = \
            contract.functions.verifyCertificate(cert_id).call()

        return {
            "available": True,
            "exists": exists,
            "ipfs_cid": ipfs_cid,
            "file_hash": file_hash.hex(),
            "content_hash": content_hash.hex(),
            "issuer": issuer,
            "timestamp": timestamp,
            "revoked": revoked,
            "issuance_date": datetime.utcfromtimestamp(timestamp).isoformat() + "Z" if timestamp > 0 else None,
        }
    except Exception as e:
        return {"error": str(e), "available": False}


def run_blockchain_layer(cert_id: str, fields: dict) -> dict:
    """Layer 2: Query blockchain + validate issuer + check timestamp coherence."""
    chain = query_blockchain(cert_id)

    result = {
        "layer_available": chain.get("available", False),
        "record_exists": False,
        "revoked": False,
        "issuer_address": None,
        "issuer_known": False,
        "issuer_name": None,
        "onchain_timestamp": None,
        "issuance_date": None,
        "timestamp_coherent": None,  # None = can't check, True = ok, False = suspicious
        "raw": chain,
        "warnings": [],
    }

    if not result["layer_available"]:
        result["warnings"].append(f"Blockchain unavailable: {chain.get('error', 'unknown')}")
        return result

    if not chain.get("exists"):
        return result

    result["record_exists"] = True
    result["revoked"] = chain.get("revoked", False)
    result["issuer_address"] = chain.get("issuer")
    result["onchain_timestamp"] = chain.get("timestamp")
    result["issuance_date"] = chain.get("issuance_date")

    # Validate issuer
    issuer_addr = chain.get("issuer", "").lower()
    if issuer_addr in {k.lower(): v for k, v in KNOWN_ISSUERS.items()}:
        result["issuer_known"] = True
        result["issuer_name"] = {k.lower(): v for k, v in KNOWN_ISSUERS.items()}[issuer_addr]
    elif KNOWN_ISSUERS:  # only warn if we have a known-issuer list
        result["warnings"].append(f"Issuer address {chain.get('issuer')} is not in the known issuers list")

    # Timestamp coherence: compare on-chain timestamp to certificate issue date
    issue_date = _parse_date(fields.get("issue_date"))
    if issue_date and chain.get("timestamp", 0) > 0:
        onchain_dt = datetime.utcfromtimestamp(chain["timestamp"])
        diff_days = abs((onchain_dt - issue_date).days)
        if diff_days <= 365:  # within 1 year is reasonable
            result["timestamp_coherent"] = True
        else:
            result["timestamp_coherent"] = False
            result["warnings"].append(
                f"Certificate claims issue date {fields.get('issue_date')} but was recorded on-chain "
                f"on {onchain_dt.strftime('%Y-%m-%d')} ({diff_days} days apart)"
            )

    return result


# ============================================================
# LAYER 3: IPFS (availability + content integrity)
# ============================================================

def run_ipfs_layer(chain_record: dict, file_bytes: bytes) -> dict:
    """Layer 3: Check IPFS availability AND content integrity."""
    result = {
        "layer_available": False,
        "cid": None,
        "file_available": False,
        "content_integrity": None,  # None = couldn't check, True/False
        "ipfs_file_hash": None,
        "warnings": [],
    }

    cid = chain_record.get("ipfs_cid") if chain_record.get("exists") else None
    if not cid:
        result["warnings"].append("No IPFS CID in blockchain record")
        return result

    result["cid"] = cid
    result["layer_available"] = True

    # Try gateways until one works
    get_resp = None
    successful_gateway = None

    for gateway in IPFS_GATEWAYS:
        try:
            head_resp = requests.head(f"{gateway}/{cid}", timeout=10, allow_redirects=True)
            if head_resp.status_code == 200:
                result["file_available"] = True
                successful_gateway = gateway
                break
        except requests.exceptions.RequestException:
            continue

    if not result["file_available"]:
        result["warnings"].append(f"IPFS file not available at any gateway (CID: {cid[:20]}...)")
        return result

    # Step 2: Content integrity -- download and compare hash using the successful gateway
    try:
        get_resp = requests.get(f"{successful_gateway}/{cid}", timeout=20, stream=True)
        if get_resp.status_code == 200:
            ipfs_bytes = get_resp.content
            ipfs_hash = hashlib.sha256(ipfs_bytes).hexdigest()
            result["ipfs_file_hash"] = ipfs_hash
            local_hash = hashlib.sha256(file_bytes).hexdigest()
            result["content_integrity"] = (ipfs_hash == local_hash)
            if not result["content_integrity"]:
                result["warnings"].append(
                    "IPFS content hash does not match local file hash -- "
                    "the file on IPFS differs from the file being verified"
                )
        else:
            result["warnings"].append(f"IPFS GET returned status {get_resp.status_code}")
    except requests.exceptions.RequestException as e:
        result["warnings"].append(f"IPFS content download failed: {str(e)[:100]}")

    return result


# ============================================================
# LAYER 4: AI Intelligence (from ai_pipeline.py v2)
# ============================================================

# --- Advanced Forensic Detection Functions ---

def _detect_copy_move_forgery(img, min_match_count=8):
    """Detect copy-move forgery using ORB keypoint matching.
    Finds duplicated/cloned regions within the same image by
    matching local features (keypoints) across the image.
    Returns a score 0-100 (100 = strong evidence of copy-move)."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        h, w = gray.shape[:2]

        # Resize if too large (for speed)
        scale = 1.0
        if max(h, w) > 1500:
            scale = 1500.0 / max(h, w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        orb = cv2.ORB_create(nfeatures=1000)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(descriptors) < 10:
            return 0.0

        # BFMatcher with Hamming distance for ORB
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=2)

        suspicious_matches = 0
        min_distance_px = 30 * scale  # Minimum pixel distance to count as a "copy"

        for match_pair in matches:
            if len(match_pair) < 2:
                continue
            m, n = match_pair
            # Skip self-matches (same keypoint index)
            if m.queryIdx == m.trainIdx:
                continue
            # Lowe's ratio test — tight for intra-image matching
            if m.distance < 0.6 * n.distance:
                pt1 = keypoints[m.queryIdx].pt
                pt2 = keypoints[m.trainIdx].pt
                dist = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if dist > min_distance_px:
                    suspicious_matches += 1

        if suspicious_matches >= min_match_count:
            # Scale: 8 matches => 40, 20+ matches => 90+
            score = min(40.0 + (suspicious_matches - min_match_count) * 4.0, 100.0)
            return float(score)
        return 0.0
    except Exception:
        return 0.0


def _analyze_noise_inconsistency(img, block_size=64):
    """Detect splicing by analyzing noise variance across image blocks.
    Genuine certificates have uniform noise; spliced regions show
    different noise characteristics. Returns a score 0-100."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        h, w = gray.shape[:2]

        if h < block_size * 2 or w < block_size * 2:
            return 0.0

        # Compute local noise variance for each block
        block_variances = []
        for y in range(0, h - block_size + 1, block_size):
            for x in range(0, w - block_size + 1, block_size):
                block = gray[y:y+block_size, x:x+block_size].astype(np.float32)
                # High-pass filter to isolate noise
                blurred = cv2.GaussianBlur(block, (5, 5), 0)
                noise = block - blurred
                block_variances.append(float(np.var(noise)))

        if len(block_variances) < 4:
            return 0.0

        variances = np.array(block_variances)
        mean_var = np.mean(variances)
        std_var = np.std(variances)

        if mean_var < 1e-6:
            return 0.0

        # Coefficient of variation of noise variance
        # High CV => inconsistent noise => likely spliced
        cv_noise = float(std_var / mean_var)

        # Count outlier blocks (noise variance > 2 std from mean)
        outlier_count = int(np.sum(np.abs(variances - mean_var) > 2.0 * std_var))
        outlier_ratio = outlier_count / len(block_variances)

        # Score: CV > 0.8 is suspicious, outlier ratio > 0.15 is suspicious
        score = min(cv_noise * 40.0 + outlier_ratio * 200.0, 100.0)
        return float(score)
    except Exception:
        return 0.0


def _detect_color_anomalies(img):
    """Detect color channel statistical anomalies that indicate
    digital manipulation. Returns a score 0-100."""
    try:
        if len(img.shape) < 3:
            return 0.0

        h, w = img.shape[:2]
        if h < 100 or w < 100:
            return 0.0

        # Split into color channels
        channels = cv2.split(img)
        channel_stats = []
        for ch in channels:
            ch_float = ch.astype(np.float32)
            channel_stats.append({
                "mean": float(np.mean(ch_float)),
                "std": float(np.std(ch_float)),
                "skew": float(np.mean(((ch_float - np.mean(ch_float)) / max(np.std(ch_float), 1e-6))**3)),
                "kurtosis": float(np.mean(((ch_float - np.mean(ch_float)) / max(np.std(ch_float), 1e-6))**4) - 3.0),
            })

        # Check for unnatural channel correlations
        # Genuine documents have highly correlated channels
        anomaly_score = 0.0

        # Check kurtosis divergence between channels (should be similar)
        kurtoses = [s["kurtosis"] for s in channel_stats]
        kurtosis_range = max(kurtoses) - min(kurtoses)
        if kurtosis_range > 3.0:
            anomaly_score += min(kurtosis_range * 8.0, 40.0)

        # Check for unnatural saturation patterns
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1].astype(np.float32)
        # Very high saturation variance in document images is suspicious
        sat_std = float(np.std(sat))
        if sat_std > 60:
            anomaly_score += min((sat_std - 60) * 1.5, 30.0)

        # Check for JPEG ghosting artifacts (double compression)
        # Different regions with different quantization levels
        dct_score = 0.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for q in [50, 70, 90]:
            buf = io.BytesIO()
            Image.fromarray(gray).save(buf, "JPEG", quality=q)
            buf.seek(0)
            recompressed = np.array(Image.open(buf))
            diff = np.abs(gray.astype(np.float32) - recompressed.astype(np.float32))
            block_means = []
            for y in range(0, h - 8, 8):
                for x in range(0, w - 8, 8):
                    block_means.append(float(np.mean(diff[y:y+8, x:x+8])))
            if block_means:
                dct_cv = float(np.std(block_means) / max(np.mean(block_means), 1e-6))
                dct_score = max(dct_score, dct_cv)

        if dct_score > 1.5:
            anomaly_score += min((dct_score - 1.5) * 20.0, 30.0)

        return float(min(anomaly_score, 100.0))
    except Exception:
        return 0.0


def _check_metadata_tampering(file_bytes):
    """Check image EXIF/metadata for signs of editing software or
    inconsistent metadata. Returns a dict with findings."""
    findings = {
        "has_exif": False,
        "editing_software_detected": False,
        "software_name": None,
        "multiple_save_indicators": False,
        "suspicious_metadata": [],
        "score": 0.0,
    }
    try:
        img = Image.open(io.BytesIO(file_bytes))
        exif_data = img.getexif()

        if not exif_data:
            return findings

        findings["has_exif"] = True

        # Known editing software tags
        editing_indicators = [
            "photoshop", "gimp", "paint", "canva", "pixlr",
            "affinity", "corel", "illustrator", "inkscape",
            "fotor", "befunky", "picmonkey",
        ]

        # Check Software tag (0x0131)
        software = exif_data.get(0x0131, "")
        if software:
            software_lower = str(software).lower()
            findings["software_name"] = str(software)
            for indicator in editing_indicators:
                if indicator in software_lower:
                    findings["editing_software_detected"] = True
                    findings["suspicious_metadata"].append(
                        f"Editing software detected: {software}"
                    )
                    findings["score"] += 35.0
                    break

        # Check for modification date vs creation date discrepancy
        create_date = exif_data.get(0x9003, "")  # DateTimeOriginal
        modify_date = exif_data.get(0x0132, "")  # DateTime
        if create_date and modify_date and create_date != modify_date:
            findings["multiple_save_indicators"] = True
            findings["suspicious_metadata"].append(
                f"Creation date ({create_date}) differs from modification date ({modify_date})"
            )
            findings["score"] += 20.0

        # Check for unusual resolution tags (signs of artificial creation)
        x_res = exif_data.get(0x011A, None)  # XResolution
        y_res = exif_data.get(0x011B, None)  # YResolution
        if x_res and y_res:
            try:
                x_val = float(x_res)
                y_val = float(y_res)
                if x_val != y_val:
                    findings["suspicious_metadata"].append(
                        f"Asymmetric resolution: {x_val}x{y_val} DPI"
                    )
                    findings["score"] += 10.0
            except (TypeError, ValueError):
                pass

        findings["score"] = min(findings["score"], 100.0)
    except Exception:
        pass
    return findings


def _analyze_border_regularity(img):
    """Analyze border/margin regularity. Genuine certificates have
    consistent margins and borders; forgeries often have irregular
    or missing borders. Returns a score 0-100 (higher = more irregular)."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        h, w = gray.shape[:2]

        if h < 200 or w < 200:
            return 0.0

        # Detect edges
        edges = cv2.Canny(gray, 30, 100)

        # Sample margins (top, bottom, left, right - 5% of image)
        margin = 0.05
        top_strip = edges[:int(h * margin), :]
        bottom_strip = edges[int(h * (1 - margin)):, :]
        left_strip = edges[:, :int(w * margin)]
        right_strip = edges[:, int(w * (1 - margin)):]

        strip_densities = [
            float(np.mean(top_strip > 0)),
            float(np.mean(bottom_strip > 0)),
            float(np.mean(left_strip > 0)),
            float(np.mean(right_strip > 0)),
        ]

        # Very uneven margin densities indicate cropping/pasting
        density_range = max(strip_densities) - min(strip_densities)
        mean_density = sum(strip_densities) / 4

        score = 0.0
        if density_range > 0.15:
            score += min(density_range * 150.0, 50.0)
        if mean_density > 0.3:
            score += min((mean_density - 0.3) * 100.0, 30.0)

        # Check for straight-line borders (genuine certs often have them)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80,
                                 minLineLength=min(w, h) * 0.3, maxLineGap=10)
        if lines is None or len(lines) < 2:
            score += 20.0  # No clear border lines detected

        return float(min(score, 100.0))
    except Exception:
        return 0.0


def _analyze_font_consistency(words):
    """Analyze font size consistency across the document.
    Forged certificates often have text pasted from different
    sources with inconsistent sizing. Returns a score 0-100."""
    if len(words) < 5:
        return 0.0

    try:
        heights = sorted([w["height"] for w in words if w["height"] > 5])
        if len(heights) < 5:
            return 0.0

        # Cluster font sizes using simple gap analysis
        clusters = []
        current_cluster = [heights[0]]
        for i in range(1, len(heights)):
            if heights[i] - heights[i-1] > max(3, heights[i-1] * 0.3):
                clusters.append(current_cluster)
                current_cluster = [heights[i]]
            else:
                current_cluster.append(heights[i])
        clusters.append(current_cluster)

        # Genuine certificates typically have 2-4 font size clusters
        # (title, body, small print, maybe a subtitle)
        num_clusters = len(clusters)

        score = 0.0
        if num_clusters > 6:
            score += min((num_clusters - 6) * 12.0, 50.0)
        elif num_clusters <= 1:
            score += 15.0  # Suspicious: all text same size

        # Check within-cluster variance
        if clusters:
            max_intra_cv = 0.0
            for cluster in clusters:
                if len(cluster) >= 3:
                    c_mean = sum(cluster) / len(cluster)
                    c_std = math.sqrt(sum((x - c_mean)**2 for x in cluster) / len(cluster))
                    cv = c_std / max(c_mean, 1e-6)
                    max_intra_cv = max(max_intra_cv, cv)
            if max_intra_cv > 0.3:
                score += min(max_intra_cv * 80.0, 40.0)

        return float(min(score, 100.0))
    except Exception:
        return 0.0


def run_advanced_forensics(img, file_bytes, words):
    """Run all advanced forensic analyses and return a consolidated result."""
    copy_move_score = _detect_copy_move_forgery(img)
    noise_score = _analyze_noise_inconsistency(img)
    color_score = _detect_color_anomalies(img)
    metadata = _check_metadata_tampering(file_bytes)
    border_score = _analyze_border_regularity(img)
    font_score = _analyze_font_consistency(words)

    # Build individual findings
    findings = []

    if copy_move_score > 30:
        findings.append({
            "test": "Copy-Move Forgery Detection",
            "score": copy_move_score,
            "severity": "high" if copy_move_score > 60 else "medium",
            "message": "Duplicated/cloned regions detected within the image",
        })

    if noise_score > 35:
        findings.append({
            "test": "Noise Inconsistency Analysis",
            "score": noise_score,
            "severity": "high" if noise_score > 60 else "medium",
            "message": "Inconsistent noise patterns suggest content from multiple sources",
        })

    if color_score > 25:
        findings.append({
            "test": "Color Channel Anomaly",
            "score": color_score,
            "severity": "high" if color_score > 50 else "medium",
            "message": "Statistical color anomalies indicate potential digital manipulation",
        })

    if metadata["score"] > 20:
        findings.append({
            "test": "Metadata Tampering Check",
            "score": metadata["score"],
            "severity": "high" if metadata["editing_software_detected"] else "medium",
            "message": "; ".join(metadata["suspicious_metadata"]) if metadata["suspicious_metadata"]
                       else "Suspicious metadata patterns detected",
        })

    if border_score > 30:
        findings.append({
            "test": "Border Regularity Analysis",
            "score": border_score,
            "severity": "medium",
            "message": "Irregular borders/margins suggest the document may have been cropped or composited",
        })

    if font_score > 25:
        findings.append({
            "test": "Font Consistency Analysis",
            "score": font_score,
            "severity": "high" if font_score > 50 else "medium",
            "message": "Inconsistent font sizing suggests text from multiple sources",
        })

    # Weighted composite forensic score (0-100)
    weighted_score = (
        copy_move_score * 0.25 +
        noise_score * 0.20 +
        color_score * 0.15 +
        metadata["score"] * 0.15 +
        border_score * 0.10 +
        font_score * 0.15
    )

    # Determine forensic verdict
    if weighted_score > 50:
        forensic_verdict = "TAMPERING_LIKELY"
    elif weighted_score > 25:
        forensic_verdict = "ANOMALIES_DETECTED"
    else:
        forensic_verdict = "NO_TAMPERING_DETECTED"

    return {
        "forensic_score": round(float(weighted_score), 2),
        "forensic_verdict": forensic_verdict,
        "copy_move_score": round(copy_move_score, 2),
        "noise_inconsistency_score": round(noise_score, 2),
        "color_anomaly_score": round(color_score, 2),
        "metadata_score": round(metadata["score"], 2),
        "metadata_details": metadata,
        "border_regularity_score": round(border_score, 2),
        "font_consistency_score": round(font_score, 2),
        "findings": findings,
        "total_findings": len(findings),
    }

_easyocr_reader = None

def get_ocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _easyocr_reader


def load_image_cv(path_or_bytes, from_bytes=False):
    if from_bytes:
        pil_img = Image.open(io.BytesIO(path_or_bytes)).convert("RGB")
    else:
        pil_img = Image.open(path_or_bytes).convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _enhance_contrast(gray_img):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray_img)


def _deskew(gray_img):
    _, mask = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(mask > 0))
    if coords.shape[0] < 50:
        return gray_img
    raw_angle = cv2.minAreaRect(coords)[-1]
    angle = raw_angle
    while angle > 45:
        angle -= 90
    while angle <= -45:
        angle += 90
    if abs(angle) < 0.5 or abs(angle) > 20:
        return gray_img
    (h, w) = gray_img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = _enhance_contrast(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    return _deskew(denoised)


def run_ocr(gray_img, reader):
    results = reader.readtext(gray_img, detail=1)
    words, lines = [], []
    for bbox, text, conf in results:
        if not text.strip():
            continue
        xs, ys = [p[0] for p in bbox], [p[1] for p in bbox]
        words.append({"text": text, "conf": conf * 100, "left": int(min(xs)), "top": int(min(ys)),
                       "width": int(max(xs) - min(xs)), "height": int(max(ys) - min(ys))})
        lines.append(text)
    raw_text = "\n".join(lines)
    avg_conf = sum(w["conf"] for w in words) / len(words) if words else 0.0
    return {"raw_text": raw_text, "words": words, "avg_confidence": avg_conf}


def run_ocr_with_fallback(img, reader):
    processed = preprocess(img)
    ocr_result = run_ocr(processed, reader)
    if ocr_result["avg_confidence"] < 50 or len(ocr_result["words"]) < 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced = _enhance_contrast(gray)
        denoised_only = cv2.fastNlMeansDenoising(enhanced, h=10)
        fallback_result = run_ocr(denoised_only, reader)
        if fallback_result["avg_confidence"] > ocr_result["avg_confidence"]:
            ocr_result = fallback_result
    return ocr_result


def extract_fields(raw_text: str) -> dict:
    text_lower = raw_text.lower()
    fields = {}
    for name, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        fields[name] = match.group(1).strip() if match else None
    name_patterns = [
        r"certify that\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:has|is|of|bearing))",
        r"awarded to\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:for|who|having))",
        r"conferred upon\s+([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s+(?:the|for|who))",
        r"name\s*:\s*([A-Z][a-zA-Z\.\s]{2,50}?)(?:\s*\n|\s+(?:has|is|reg))",
    ]
    fields["student_name"] = None
    for pat in name_patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            fields["student_name"] = m.group(1).strip()
            break
    fields["missing_field_count"] = sum(1 for v in fields.values() if v is None)
    return fields


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


def _institution_match_score(raw_text):
    text_lower = raw_text.lower()
    return max((fuzz.partial_ratio(name, text_lower) for name in KNOWN_INSTITUTIONS), default=0.0)


def _text_position_variance(words):
    if len(words) < 4:
        return 0.0
    tops = [w["top"] for w in words]
    mean = sum(tops) / len(tops)
    return sum((t - mean) ** 2 for t in tops) / len(tops)


def _font_height_variance(words):
    if len(words) < 4:
        return 0.0
    heights = [w["height"] for w in words if w["height"] > 0]
    if not heights:
        return 0.0
    mean = sum(heights) / len(heights)
    return sum((h - mean) ** 2 for h in heights) / len(heights)


def compute_ela_score(file_bytes, quality=90):
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


def _compute_ela_multi_quality(file_bytes):
    return max((compute_ela_score(file_bytes, quality=q) for q in (70, 80, 90, 95)), default=0.0)


def _low_confidence_word_ratio(words):
    if not words:
        return 0.0
    return sum(1 for w in words if w["conf"] < 50) / len(words)


def _compute_aspect_ratio(img):
    h, w = img.shape[:2]
    return w / h if h > 0 else 0.0


def _compute_edge_density(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    edges = cv2.Canny(gray, 50, 150)
    total_pixels = edges.shape[0] * edges.shape[1]
    return float(np.count_nonzero(edges) / total_pixels) if total_pixels > 0 else 0.0


def _horizontal_alignment_score(words):
    if len(words) < 4:
        return 100.0
    lefts = [w["left"] for w in words]
    mean_left = sum(lefts) / len(lefts)
    variance = sum((l - mean_left) ** 2 for l in lefts) / len(lefts)
    return float(100.0 * math.exp(-variance / 50000.0))


def _confidence_variance(words):
    if len(words) < 2:
        return 0.0
    confs = [w["conf"] for w in words]
    mean_conf = sum(confs) / len(confs)
    variance = sum((c - mean_conf) ** 2 for c in confs) / len(confs)
    return float(math.sqrt(variance))


def _signature_area_detected(img):
    """Binary feature for ML model compatibility."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    h, w = gray.shape[:2]
    bottom_third = gray[int(h * 0.6):, :]
    _, thresh = cv2.threshold(bottom_third, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, cw, ch = cv2.boundingRect(contour)
        img_area = h * w
        if 0.002 * img_area < area < 0.15 * img_area:
            ar = cw / ch if ch > 0 else 0
            if 1.5 < ar < 10.0:
                return 1.0
    return 0.0


def _enhanced_signature_analysis(img):
    """Deep signature & seal analysis: multi-region scan, circular seal
    detection, ink-color analysis, stroke complexity, graduated confidence."""
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

    # 1. Multi-region contour scan
    regions = {
        "bottom_third":  gray[int(h * 0.6):, :],
        "bottom_left":   gray[int(h * 0.65):, :int(w * 0.45)],
        "bottom_right":  gray[int(h * 0.65):, int(w * 0.55):],
    }
    for region_name, region_img in regions.items():
        _, thresh = cv2.threshold(region_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            x, y, cw, ch = cv2.boundingRect(contour)
            if area < 0.001 * img_area or area > 0.15 * img_area:
                continue
            ar = cw / ch if ch > 0 else 0
            if 1.2 < ar < 12.0 and 0.002 * img_area < area:
                children = 0
                if hierarchy is not None:
                    child_idx = hierarchy[0][i][2]
                    while child_idx != -1:
                        children += 1
                        child_idx = hierarchy[0][child_idx][0]
                sig_regions.append({
                    "region": region_name,
                    "area_pct": round(area / img_area * 100, 3),
                    "aspect_ratio": round(ar, 2),
                    "complexity": children,
                })

    # 2. Circular seal / stamp detection
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
            findings.append({"check": "Circular Seal Detection", "result": "passed",
                             "detail": f"{len(circles[0])} circular seal(s) or stamp(s) detected"})
    except Exception:
        pass

    # 3. Ink-color analysis
    if len(img.shape) == 3:
        try:
            bottom_color = img[int(h * 0.6):, :]
            hsv = cv2.cvtColor(bottom_color, cv2.COLOR_BGR2HSV)
            total_px = hsv.shape[0] * hsv.shape[1]
            blue_mask = cv2.inRange(hsv, (90, 50, 30), (130, 255, 220))
            blue_ratio = float(cv2.countNonZero(blue_mask) / total_px)
            black_mask = cv2.inRange(hsv, (0, 0, 0), (180, 80, 60))
            black_ratio = float(cv2.countNonZero(black_mask) / total_px)
            if blue_ratio > 0.003:
                ink_signature_detected = True
                findings.append({"check": "Ink Color Analysis", "result": "passed",
                                 "detail": f"Blue ink detected ({blue_ratio*100:.2f}% of signature region)"})
            elif black_ratio > 0.01 and sig_regions:
                ink_signature_detected = True
                findings.append({"check": "Ink Color Analysis", "result": "passed",
                                 "detail": f"Black ink detected in signature region ({black_ratio*100:.2f}%)"})
        except Exception:
            pass

    # 4. Contour findings
    complex_sigs = [r for r in sig_regions if r["complexity"] >= 3]
    simple_sigs = [r for r in sig_regions if r["complexity"] < 3]
    if complex_sigs:
        findings.append({"check": "Handwritten Signature Detection", "result": "passed",
                         "detail": f"{len(complex_sigs)} complex signature region(s) with stroke detail found"})
    if simple_sigs and not complex_sigs:
        findings.append({"check": "Signature Shape Detection", "result": "partial",
                         "detail": f"{len(simple_sigs)} simple signature-shaped region(s) found (low stroke complexity)"})
    if not sig_regions and not seal_detected:
        findings.append({"check": "Signature / Seal Scan", "result": "failed",
                         "detail": "No signature or seal region detected anywhere on the certificate"})

    # 5. Graduated confidence
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
        "regions": sig_regions[:5],
        "findings": findings,
    }


def _empty_sig_result():
    return {
        "detected": False, "confidence": 0.0, "signature_count": 0,
        "has_seal": False, "has_ink_signature": False,
        "has_complex_strokes": False, "regions": [],
        "findings": [{"check": "Signature / Seal Scan", "result": "failed",
                       "detail": "Image too small to analyse"}],
    }


def _text_density_ratio(words, img):
    h, w = img.shape[:2]
    img_area = h * w
    if img_area == 0:
        return 0.0
    text_area = sum(w_["width"] * w_["height"] for w_ in words)
    return float(text_area / img_area)


def build_feature_vector(ocr_result, fields, file_bytes, img):
    reg_no = fields.get("register_number") or ""
    cert_id_field = fields.get("certificate_id") or ""
    issue_date = _parse_date(fields.get("issue_date"))
    date_plausible = bool(issue_date and 2000 <= issue_date.year <= datetime.now().year)
    words = ocr_result.get("words", [])

    return {
        "missing_field_count": fields.get("missing_field_count", 0),
        "ocr_avg_confidence": ocr_result.get("avg_confidence", 0.0),
        "register_number_format_valid": 1.0 if REGISTER_NUMBER_RE.match(reg_no) else 0.0,
        "certificate_id_format_valid": 1.0 if CERT_ID_RE.match(cert_id_field) else 0.0,
        "issue_date_valid": 1.0 if issue_date else 0.0,
        "issue_date_plausible_range": 1.0 if date_plausible else 0.0,
        "institution_name_match_score": _institution_match_score(ocr_result["raw_text"]),
        "text_block_count": len(words),
        "text_position_variance": _text_position_variance(words),
        "font_height_variance": _font_height_variance(words),
        "degree_field_recognized": 1.0 if fields.get("degree") else 0.0,
        "ela_unevenness_score": compute_ela_score(file_bytes),
        "low_confidence_word_ratio": _low_confidence_word_ratio(words),
        "aspect_ratio": _compute_aspect_ratio(img),
        "edge_density": _compute_edge_density(img),
        "ela_multi_quality_max": _compute_ela_multi_quality(file_bytes),
        "horizontal_alignment_score": _horizontal_alignment_score(words),
        "confidence_variance": _confidence_variance(words),
        "signature_area_detected": _signature_area_detected(img),
        "text_density_ratio": _text_density_ratio(words, img),
    }


# Synthetic sample generators (needed for SHAP background)
RNG = np.random.default_rng(42)

def _genuine_sample():
    return {
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
        "low_confidence_word_ratio": np.clip(RNG.normal(0.30, 0.15), 0, 1),
        "aspect_ratio": np.clip(RNG.normal(1.45, 0.35), 0.5, 3.0),
        "edge_density": np.clip(RNG.normal(0.07, 0.025), 0, 0.3),
        "ela_multi_quality_max": np.clip(RNG.normal(8.5, 2.5), 0, 20),
        "horizontal_alignment_score": np.clip(RNG.normal(45, 20), 0, 100),
        "confidence_variance": np.clip(RNG.normal(20, 8), 0, 50),
        "signature_area_detected": RNG.choice([1.0, 0.0], p=[0.40, 0.60]),
        "text_density_ratio": np.clip(RNG.normal(0.08, 0.04), 0, 0.5),
    }


def run_ai_layer(vector: dict, model, fields: dict, img=None, file_bytes=None, ocr_result=None) -> dict:
    """Layer 4: ML prediction + SHAP explanation + Advanced Forensics + hard rules."""
    X = pd.DataFrame([vector], columns=FEATURE_NAMES)
    proba = model.predict_proba(X)[0]
    fraud_probability = float(proba[1])

    # --- Enhanced Signature Analysis & Graduated Scoring ---
    signature_analysis = _empty_sig_result()
    if img is not None:
        signature_analysis = _enhanced_signature_analysis(img)
    
    sig_conf = signature_analysis["confidence"]
    if signature_analysis["detected"]:
        if sig_conf >= 0.7:
            fraud_probability = max(0.0, fraud_probability - 0.20)
        elif sig_conf >= 0.4:
            fraud_probability = max(0.0, fraud_probability - 0.12)
        else:
            fraud_probability = max(0.0, fraud_probability - 0.05)
    else:
        fraud_probability = min(1.0, fraud_probability + 0.15)
        
    ml_prediction = "SUSPICIOUS" if fraud_probability >= 0.5 else "LIKELY_GENUINE"

    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    fraud_class_shap = None

    # Strategy 1: TreeExplainer on the underlying RF
    try:
        base_model = model
        if hasattr(base_model, 'estimator'):
            base_model = base_model.estimator
        if hasattr(base_model, 'named_estimators_'):
            base_model = base_model.named_estimators_["rf"]
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

    # Strategy 2: KernelExplainer with synthetic background
    if fraud_class_shap is None or np.allclose(fraud_class_shap, 0):
        try:
            bg_rows = [_genuine_sample() for _ in range(30)] + [_tampered_sample() for _ in range(20)]
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
            fraud_class_shap = np.zeros(len(FEATURE_NAMES))

    warnings.resetwarnings()

    if len(fraud_class_shap) != len(FEATURE_NAMES):
        fraud_class_shap = fraud_class_shap[:len(FEATURE_NAMES)]

    # Build all explanations grouped by direction
    contributions = sorted(
        zip(FEATURE_NAMES, [float(s) for s in fraud_class_shap], [vector[n] for n in FEATURE_NAMES]),
        key=lambda x: abs(x[1]), reverse=True
    )
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

    # --- 6 hard rules ---
    hard_rule_failures = []
    if vector["issue_date_valid"] == 0.0:
        hard_rule_failures.append("Issue date could not be parsed as a valid date")
    if vector["issue_date_plausible_range"] == 0.0 and vector["issue_date_valid"] == 1.0:
        hard_rule_failures.append("Issue date falls outside a plausible range")
    issue_date = _parse_date(fields.get("issue_date"))
    if issue_date and issue_date > datetime.now() + timedelta(days=30):
        hard_rule_failures.append(f"Issue date ({fields.get('issue_date')}) is in the future")
    if vector["missing_field_count"] >= 3:
        hard_rule_failures.append(f"Too many expected fields missing ({int(vector['missing_field_count'])} of 5)")
    if vector["ocr_avg_confidence"] < 30:
        hard_rule_failures.append(f"OCR confidence is critically low ({vector['ocr_avg_confidence']:.1f}%)")
    if vector["certificate_id_format_valid"] == 0.0 and vector["ocr_avg_confidence"] > 80:
        cert_id_raw = fields.get("certificate_id")
        if cert_id_raw:
            hard_rule_failures.append(f"Certificate ID '{cert_id_raw}' does not match any valid format")

    # --- Run Advanced Forensics ---
    forensics = {}
    if img is not None and file_bytes is not None and ocr_result is not None:
        words = ocr_result.get("words", [])
        forensics = run_advanced_forensics(img, file_bytes, words)
        if forensics["forensic_verdict"] == "TAMPERING_LIKELY":
            hard_rule_failures.append(f"Advanced Forensics detected severe tampering (Score: {forensics['forensic_score']}/100)")
            fraud_probability = max(fraud_probability, 0.90)
            ml_prediction = "SUSPICIOUS"

    final_ai_verdict = "SUSPICIOUS" if hard_rule_failures else ml_prediction

    return {
        "ml_prediction": ml_prediction,
        "fraud_probability_pct": round(fraud_probability * 100, 2),
        "hard_rule_failures": hard_rule_failures,
        "final_ai_verdict": final_ai_verdict,
        "all_explanations": all_explanations,
        "top_explanations": all_explanations[:5],
        "forensics": forensics,
        "signature_detected": signature_analysis["detected"],
        "signature_analysis": signature_analysis,
    }


# ============================================================
# WEIGHTED RISK SCORING (0-100)
# ============================================================

def compute_risk_score(hash_result: dict, blockchain_result: dict,
                       ipfs_result: dict, ai_result: dict) -> dict:
    """
    Weighted multi-layer risk score (0 = safe, 100 = maximum risk).
      Hash layer:       30 points max
      Blockchain layer: 25 points max
      IPFS layer:       15 points max
      AI layer:         30 points max
    """
    risk = 0
    breakdown = {}
    layers_checked = 0
    layers_available = 0

    # --- Hash layer (30 points) ---
    if hash_result["layer_available"]:
        layers_available += 1
        layers_checked += 1
        hash_risk = 0
        if not hash_result["file_hash_match"]:
            hash_risk += 20  # file hash mismatch is very serious
            # Content hash only matters when file hash differs
            if not hash_result["content_hash_match"]:
                hash_risk += 10  # content was also altered
        breakdown["hash"] = {"risk": hash_risk, "max": 30, "available": True}
        risk += hash_risk
    else:
        breakdown["hash"] = {"risk": 0, "max": 30, "available": False}

    # --- Blockchain layer (25 points) ---
    if blockchain_result["layer_available"]:
        layers_available += 1
        bc_risk = 0
        if not blockchain_result["record_exists"]:
            bc_risk += 25  # no record at all
            layers_checked += 1
        else:
            layers_checked += 1
            if blockchain_result["revoked"]:
                bc_risk += 25  # revoked
            else:
                if blockchain_result["timestamp_coherent"] is False:
                    bc_risk += 10  # timestamp mismatch
                if not blockchain_result["issuer_known"] and KNOWN_ISSUERS:
                    bc_risk += 5  # unknown issuer
        breakdown["blockchain"] = {"risk": bc_risk, "max": 25, "available": True}
        risk += bc_risk
    else:
        breakdown["blockchain"] = {"risk": 0, "max": 25, "available": False}

    # --- IPFS layer (15 points) ---
    if ipfs_result["layer_available"]:
        layers_available += 1
        layers_checked += 1
        ipfs_risk = 0
        if not ipfs_result["file_available"]:
            ipfs_risk += 10
        elif ipfs_result["content_integrity"] is False:
            ipfs_risk += 15  # content doesn't match
        breakdown["ipfs"] = {"risk": ipfs_risk, "max": 15, "available": True}
        risk += ipfs_risk
    else:
        breakdown["ipfs"] = {"risk": 0, "max": 15, "available": False}

    # --- AI layer (30 points) ---
    layers_available += 1  # AI is always available (local)
    layers_checked += 1
    ai_risk = 0
    fraud_pct = ai_result["fraud_probability_pct"]
    ai_risk += int(fraud_pct * 0.2)  # scale 0-100% to 0-20 points
    ai_risk += len(ai_result["hard_rule_failures"]) * 5  # 5 points per hard rule
    ai_risk = min(ai_risk, 30)  # cap at 30
    breakdown["ai"] = {"risk": ai_risk, "max": 30, "available": True}
    risk += ai_risk

    risk = min(risk, 100)

    # Confidence band
    if risk <= 15:
        band = "HIGH_CONFIDENCE_GENUINE"
    elif risk <= 35:
        band = "MODERATE_CONFIDENCE"
    elif risk <= 60:
        band = "ELEVATED_RISK"
    else:
        band = "HIGH_RISK"

    return {
        "total_risk": risk,
        "confidence_band": band,
        "breakdown": breakdown,
        "layers_checked": layers_checked,
        "layers_available": layers_available,
    }


# ============================================================
# FINAL VERDICT LOGIC (7 verdicts)
# ============================================================

def determine_verdict(hash_result: dict, blockchain_result: dict,
                      ipfs_result: dict, ai_result: dict,
                      risk: dict) -> str:
    """Determine the final verdict from all 4 layers.

    Content hash logic:
      - If file_hash MATCHES -> the raw file is identical to what was issued.
        Content hash is irrelevant (content can't have changed if bytes match).
      - If file_hash MISMATCHES and content_hash MATCHES -> file was re-scanned
        or re-compressed but the underlying data is unchanged.
      - If file_hash MISMATCHES and content_hash MISMATCHES -> the actual
        certificate data was altered (e.g. a grade or name was changed).
    """

    bc_available = blockchain_result["layer_available"]

    if bc_available and not blockchain_result["record_exists"]:
        return "NOT_FOUND"

    if bc_available and blockchain_result["revoked"]:
        return "REVOKED"

    if bc_available and hash_result["layer_available"]:
        if not hash_result["file_hash_match"]:
            # File bytes differ — check content hash to see if data was altered
            if not hash_result["content_hash_match"]:
                return "CONTENT_MISMATCH"  # data was actually altered
            else:
                return "HASH_MISMATCH"  # file re-scanned but data unchanged

    if ai_result["final_ai_verdict"] == "SUSPICIOUS":
        return "REQUIRES_INVESTIGATION"

    # If some layers couldn't be checked
    if risk["layers_checked"] < 4:
        return "PARTIALLY_VERIFIED"

    return "VERIFIED"


# ============================================================
# JSON REPORT
# ============================================================

def save_json_report(cert_id: str, file_path: str, fields: dict, vector: dict,
                     hash_result: dict, blockchain_result: dict,
                     ipfs_result: dict, ai_result: dict,
                     risk: dict, verdict: str) -> str:
    """Save comprehensive verification report as JSON."""
    report_path = os.path.splitext(file_path)[0] + "_verification_report.json"

    # Clean blockchain result for JSON serialization
    bc_clean = dict(blockchain_result)
    bc_clean.pop("raw", None)  # remove raw web3 response

    report = {
        "timestamp": datetime.now().isoformat(),
        "certificate_id": cert_id,
        "certificate_file": os.path.basename(file_path),
        "final_verdict": verdict,
        "risk_score": risk["total_risk"],
        "confidence_band": risk["confidence_band"],
        "layers_checked": risk["layers_checked"],
        "risk_breakdown": risk["breakdown"],
        "fields_extracted": fields,
        "hash_verification": {
            "file_hash_computed": hash_result["computed_file_hash"],
            "file_hash_onchain": hash_result["onchain_file_hash"],
            "file_hash_match": hash_result["file_hash_match"],
            "content_hash_computed": hash_result["computed_content_hash"],
            "content_hash_onchain": hash_result["onchain_content_hash"],
            "content_hash_match": hash_result["content_hash_match"],
        },
        "blockchain_verification": bc_clean,
        "ipfs_verification": ipfs_result,
        "ai_analysis": {
            "ml_prediction": ai_result["ml_prediction"],
            "fraud_probability_pct": ai_result["fraud_probability_pct"],
            "hard_rule_failures": ai_result["hard_rule_failures"],
            "final_ai_verdict": ai_result["final_ai_verdict"],
            "shap_explanations": ai_result["all_explanations"],
        },
        "feature_vector": {k: round(v, 4) if isinstance(v, float) else v for k, v in vector.items()},
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return report_path


# ============================================================
# CONSOLE REPORT (ASCII-safe)
# ============================================================

VERDICT_LABELS = {
    "VERIFIED": "[OK] VERIFIED -- All checks passed",
    "NOT_FOUND": "[!!] NOT FOUND -- No blockchain record exists",
    "REVOKED": "[!!] REVOKED -- Certificate was revoked by issuer",
    "HASH_MISMATCH": "[!!] HASH MISMATCH -- File has been modified",
    "CONTENT_MISMATCH": "[!!] CONTENT MISMATCH -- Certificate content was altered",
    "REQUIRES_INVESTIGATION": "[!!] REQUIRES INVESTIGATION -- AI flagged suspicious",
    "PARTIALLY_VERIFIED": "[..] PARTIALLY VERIFIED -- Some layers unavailable",
}


def print_report(cert_id: str, fields: dict, hash_result: dict,
                 blockchain_result: dict, ipfs_result: dict,
                 ai_result: dict, risk: dict, verdict: str):
    """Print a comprehensive ASCII-safe console report."""

    W = 65
    print("\n" + "=" * W)
    print("   ACADEMIC CERTIFICATE VERIFICATION REPORT")
    print("   Engine v3.0 -- 4-Layer Verification System")
    print("=" * W)

    # --- Certificate Info ---
    print(f"\n  Certificate ID   : {cert_id}")
    print(f"  Student Name     : {fields.get('student_name') or 'Not detected'}")
    print(f"  Degree           : {fields.get('degree') or 'Not detected'}")
    print(f"  Register No.     : {fields.get('register_number') or 'Not detected'}")
    print(f"  Issue Date       : {fields.get('issue_date') or 'Not detected'}")

    # --- Layer 1: Hash ---
    print(f"\n{'-' * W}")
    print("  LAYER 1: CRYPTOGRAPHIC HASH VERIFICATION")
    print(f"{'-' * W}")
    if hash_result["layer_available"]:
        fh_status = "[PASS]" if hash_result["file_hash_match"] else "[FAIL]"
        ch_status = "[PASS]" if hash_result["content_hash_match"] else "[FAIL]"
        print(f"  File hash    : {fh_status} {'Matches on-chain record' if hash_result['file_hash_match'] else 'DOES NOT match on-chain record'}")
        print(f"    Computed   : {hash_result['computed_file_hash'][:32]}...")
        print(f"    On-chain   : {(hash_result['onchain_file_hash'] or 'N/A')[:32]}...")
        print(f"  Content hash : {ch_status} {'Matches on-chain record' if hash_result['content_hash_match'] else 'DOES NOT match on-chain record'}")
        print(f"    Computed   : {hash_result['computed_content_hash'][:32]}...")
        print(f"    On-chain   : {(hash_result['onchain_content_hash'] or 'N/A')[:32]}...")
    else:
        print("  [SKIP] Cannot verify hashes -- no blockchain record available")

    # --- Layer 2: Blockchain ---
    print(f"\n{'-' * W}")
    print("  LAYER 2: BLOCKCHAIN VERIFICATION")
    print(f"{'-' * W}")
    if blockchain_result["layer_available"]:
        if blockchain_result["record_exists"]:
            print(f"  Record         : [PASS] Found on Sepolia blockchain")
            rev_status = "[FAIL] REVOKED" if blockchain_result["revoked"] else "[PASS] Not revoked"
            print(f"  Revocation     : {rev_status}")
            print(f"  Issuer         : {blockchain_result['issuer_address']}")
            if blockchain_result["issuer_known"]:
                print(f"  Issuer name    : [PASS] {blockchain_result['issuer_name']}")
            elif KNOWN_ISSUERS:
                print(f"  Issuer name    : [WARN] Not in known issuers list")
            if blockchain_result["issuance_date"]:
                print(f"  On-chain date  : {blockchain_result['issuance_date']}")
            if blockchain_result["timestamp_coherent"] is True:
                print(f"  Date coherence : [PASS] On-chain timestamp aligns with issue date")
            elif blockchain_result["timestamp_coherent"] is False:
                print(f"  Date coherence : [WARN] On-chain timestamp does NOT align with issue date")
        else:
            print(f"  Record         : [FAIL] NOT FOUND on blockchain")
        for w in blockchain_result["warnings"]:
            print(f"    [WARN] {w}")
    else:
        print(f"  [SKIP] Blockchain unavailable")
        for w in blockchain_result["warnings"]:
            print(f"    [WARN] {w}")

    # --- Layer 3: IPFS ---
    print(f"\n{'-' * W}")
    print("  LAYER 3: IPFS STORAGE VERIFICATION")
    print(f"{'-' * W}")
    if ipfs_result["layer_available"]:
        avail_status = "[PASS]" if ipfs_result["file_available"] else "[FAIL]"
        print(f"  Availability   : {avail_status} {'Retrievable from IPFS' if ipfs_result['file_available'] else 'NOT retrievable from IPFS'}")
        print(f"  CID            : {ipfs_result['cid'][:40]}...")
        if ipfs_result["content_integrity"] is True:
            print(f"  Integrity      : [PASS] Downloaded content matches local file")
        elif ipfs_result["content_integrity"] is False:
            print(f"  Integrity      : [FAIL] Downloaded content DOES NOT match local file")
        else:
            print(f"  Integrity      : [SKIP] Could not verify content integrity")
        for w in ipfs_result["warnings"]:
            print(f"    [WARN] {w}")
    else:
        print(f"  [SKIP] No IPFS record to check")
        for w in ipfs_result["warnings"]:
            print(f"    [WARN] {w}")

    # --- Layer 4: AI ---
    print(f"\n{'-' * W}")
    print("  LAYER 4: AI FRAUD DETECTION & EXPLAINABILITY")
    print(f"{'-' * W}")
    print(f"  ML Prediction    : {ai_result['ml_prediction']}")
    print(f"  Fraud Probability: {ai_result['fraud_probability_pct']}%")
    print(f"  AI Verdict       : {ai_result['final_ai_verdict']}")

    if ai_result["hard_rule_failures"]:
        print(f"\n  Hard-rule failures ({len(ai_result['hard_rule_failures'])}):")
        for reason in ai_result["hard_rule_failures"]:
            print(f"    [!] {reason}")

    suspicious_factors = [e for e in ai_result["all_explanations"] if e["pushes_toward"] == "suspicious"]
    genuine_factors = [e for e in ai_result["all_explanations"] if e["pushes_toward"] == "genuine"]

    if suspicious_factors:
        print(f"\n  Factors pushing toward SUSPICIOUS:")
        for exp in suspicious_factors[:5]:
            print(f"    [!] {exp['message']}  (SHAP={exp['shap_value']:+.4f})")
    if genuine_factors:
        print(f"\n  Factors pushing toward GENUINE:")
        for exp in genuine_factors[:5]:
            print(f"    [+] {exp['message']}  (SHAP={exp['shap_value']:+.4f})")

    # --- Risk Score ---
    print(f"\n{'-' * W}")
    print("  RISK ASSESSMENT")
    print(f"{'-' * W}")
    print(f"  Overall Risk Score : {risk['total_risk']}/100  ({risk['confidence_band']})")
    print(f"  Layers Checked     : {risk['layers_checked']}/4")
    print(f"  Breakdown:")
    for layer_name, layer_data in risk["breakdown"].items():
        status = f"{layer_data['risk']}/{layer_data['max']}" if layer_data["available"] else "N/A (unavailable)"
        print(f"    {layer_name:12s}: {status}")

    # --- Final Verdict ---
    print(f"\n{'=' * W}")
    label = VERDICT_LABELS.get(verdict, verdict)
    print(f"  FINAL VERDICT: {label}")
    print(f"  Risk Score:    {risk['total_risk']}/100")
    print(f"{'=' * W}")


# ============================================================
# MAIN VERIFICATION ENGINE
# ============================================================

def verify(cert_id: str, file_path: str) -> dict:
    """Run the complete 4-layer verification pipeline."""

    print("\n" + "#" * 65)
    print("# Loading certificate and OCR model...")
    print("#" * 65)

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    img = load_image_cv(file_bytes, from_bytes=True)
    reader = get_ocr_reader()
    print("[OK] EasyOCR model ready.")

    # --- OCR + Field Extraction ---
    print("\n" + "#" * 65)
    print("# Running OCR + Field Extraction...")
    print("#" * 65)
    ocr_result = run_ocr_with_fallback(img, reader)
    fields = extract_fields(ocr_result["raw_text"])
    print(f"OCR confidence: {ocr_result['avg_confidence']:.1f}%")
    for k, v in fields.items():
        print(f"  {k}: {v}")

    # --- Feature Vector ---
    print("\n" + "#" * 65)
    print("# Building 20-feature vector...")
    print("#" * 65)
    vector = build_feature_vector(ocr_result, fields, file_bytes, img)
    for name in FEATURE_NAMES:
        val = vector[name]
        formatted = f"{val:.4f}" if isinstance(val, float) else str(val)
        print(f"  {name:35s}: {formatted}")

    # --- Layer 2: Blockchain (run first to get chain record for other layers) ---
    print("\n" + "#" * 65)
    print("# Layer 2: Querying blockchain...")
    print("#" * 65)
    blockchain_result = run_blockchain_layer(cert_id, fields)
    if blockchain_result["layer_available"]:
        if blockchain_result["record_exists"]:
            print(f"[OK] Record found on-chain for {cert_id}")
        else:
            print(f"[!!] No record found on-chain for {cert_id}")
    else:
        print(f"[WARN] Blockchain unavailable -- continuing with other layers")

    # Get the raw chain record for hash and IPFS layers
    chain_raw = blockchain_result.get("raw", {})

    # --- Layer 1: Hash ---
    print("\n" + "#" * 65)
    print("# Layer 1: Dual-hash verification...")
    print("#" * 65)
    hash_result = run_hash_layer(file_bytes, fields, chain_raw)
    print(f"  File hash (computed)   : {hash_result['computed_file_hash'][:32]}...")
    print(f"  Content hash (computed): {hash_result['computed_content_hash'][:32]}...")
    if hash_result["layer_available"]:
        fh = "MATCH" if hash_result["file_hash_match"] else "MISMATCH"
        ch = "MATCH" if hash_result["content_hash_match"] else "MISMATCH"
        print(f"  File hash vs on-chain  : {fh}")
        print(f"  Content hash vs on-chain: {ch}")

    # --- Layer 3: IPFS ---
    print("\n" + "#" * 65)
    print("# Layer 3: IPFS availability + integrity...")
    print("#" * 65)
    ipfs_result = run_ipfs_layer(chain_raw, file_bytes)
    if ipfs_result["file_available"]:
        print(f"[OK] File retrievable from IPFS (CID: {ipfs_result['cid'][:30]}...)")
        if ipfs_result["content_integrity"] is True:
            print("[OK] IPFS content integrity verified")
        elif ipfs_result["content_integrity"] is False:
            print("[!!] IPFS content does NOT match local file!")
    else:
        print("[WARN] IPFS file not available")

    # --- Layer 4: AI ---
    print("\n" + "#" * 65)
    print("# Layer 4: AI fraud detection + SHAP + Forensics...")
    print("#" * 65)
    model = joblib.load(MODEL_PATH)
    ai_result = run_ai_layer(vector, model, fields, img, file_bytes, ocr_result)
    print(f"  ML prediction: {ai_result['ml_prediction']} ({ai_result['fraud_probability_pct']}% fraud)")

    # --- Risk Score ---
    risk = compute_risk_score(hash_result, blockchain_result, ipfs_result, ai_result)

    # --- Final Verdict ---
    verdict = determine_verdict(hash_result, blockchain_result, ipfs_result, ai_result, risk)

    # --- Print Report ---
    print_report(cert_id, fields, hash_result, blockchain_result, ipfs_result,
                 ai_result, risk, verdict)

    # --- Save JSON Report ---
    report_path = save_json_report(cert_id, file_path, fields, vector,
                                   hash_result, blockchain_result,
                                   ipfs_result, ai_result, risk, verdict)
    print(f"\n[*] JSON verification report saved: {report_path}")

    # --- Audit Log ---
    log_audit(cert_id, verdict, risk["total_risk"],
              f"file={os.path.basename(file_path)} fraud_pct={ai_result['fraud_probability_pct']} "
              f"layers_checked={risk['layers_checked']}")
    print(f"[*] Audit log appended: {AUDIT_LOG_PATH}")

    return {
        "verdict": verdict,
        "risk": risk,
        "hash": hash_result,
        "blockchain": blockchain_result,
        "ipfs": ipfs_result,
        "ai": ai_result,
        "fields": fields,
    }


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python final_engine.py <certificate_id> <file_path>")
        print("Example: python final_engine.py CERT-2026-00891 sample_certificate.png")
        sys.exit(1)

    cert_id_arg = sys.argv[1]
    file_path_arg = sys.argv[2]

    if not os.path.exists(file_path_arg):
        print(f"[FAIL] File not found: {file_path_arg}")
        sys.exit(1)

    if not os.path.exists(MODEL_PATH):
        print(f"[FAIL] Model not found: {MODEL_PATH}")
        print("Run ai_pipeline.py first to train the model, or copy model_v2.pkl here.")
        sys.exit(1)

    result = verify(cert_id_arg, file_path_arg)
    sys.exit(0 if result["verdict"] == "VERIFIED" else 1)