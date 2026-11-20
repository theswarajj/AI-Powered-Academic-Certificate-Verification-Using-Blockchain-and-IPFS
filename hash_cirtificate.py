"""
STORAGE LAYER — Part 1: Hashing.

Generates the cryptographic fingerprint of a certificate file. This hash
is what eventually gets written to the blockchain — small, fixed-size,
and any single-bit change to the file produces a completely different
hash, which is exactly the tamper-evidence property we want.

We generate TWO hashes, not one:
  1. file_hash — SHA-256 of the raw file bytes. Detects ANY change to the
     file at all, even a re-compression or re-scan that doesn't change
     the visible content.
  2. content_hash — SHA-256 of just the extracted structured fields
     (name, register number, degree, etc.) as JSON. This lets you tell
     the difference between "the file bytes changed" (could be an
     innocent re-scan) and "the actual data changed" (a grade was
     altered) — a nice touch worth mentioning in your report as it goes
     beyond the base paper's design.

Run it with:
    python hash_certificate.py path/to/certificate.png
"""
import sys
import json
import hashlib


def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 of the raw file bytes — the primary tamper-evidence anchor."""
    return hashlib.sha256(file_bytes).hexdigest()


def compute_content_hash(fields: dict) -> str:
    """
    SHA-256 of the extracted structured fields, as canonical JSON
    (sorted keys, no extra whitespace) so the same data always produces
    the same hash regardless of dict ordering.
    
    Fields are normalized (lowercase, stripped) before hashing so that
    minor OCR casing differences at verification time don't cause false
    mismatches. The verification engine applies the same normalization.
    """
    def _normalize(val):
        return (val or "").strip().lower()

    normalized_fields = {k: _normalize(v) for k, v in fields.items()}
    canonical = json.dumps(normalized_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash_certificate.py path/to/certificate.png")
        sys.exit(1)

    path = sys.argv[1]
    print("=" * 60)
    print("STORAGE LAYER — Hashing")
    print("=" * 60)

    with open(path, "rb") as f:
        file_bytes = f.read()

    file_hash = compute_file_hash(file_bytes)
    print(f"\nFile: {path}")
    print(f"File size: {len(file_bytes)} bytes")
    print(f"\nfile_hash (SHA-256 of raw bytes):")
    print(f"  0x{file_hash}")

    # Example structured fields — in the real pipeline these come from
    # Step 3's OCR + field extraction output.
    example_fields = {
        "student_name": "Priya Ramesh Nair",
        "register_number": "22CS08234",
        "certificate_id": "CERT-2026-00891",
        "degree": "B.Tech",
        "issue_date": "12/05/2026",
    }
    content_hash = compute_content_hash(example_fields)
    print(f"\ncontent_hash (SHA-256 of extracted fields):")
    print(f"  0x{content_hash}")

    print("\n--- Demonstrating tamper-evidence ---")
    tampered_fields = dict(example_fields)
    tampered_fields["register_number"] = "22CS99999"  # simulate one field changed
    tampered_content_hash = compute_content_hash(tampered_fields)
    print(f"Original content_hash: 0x{content_hash[:16]}...")
    print(f"Tampered content_hash: 0x{tampered_content_hash[:16]}...")
    print(f"Hashes match: {content_hash == tampered_content_hash}  <- changing ONE field changes everything")

    print("\n" + "=" * 60)
    print("SUCCESS — hashing works as expected.")
    print("=" * 60)