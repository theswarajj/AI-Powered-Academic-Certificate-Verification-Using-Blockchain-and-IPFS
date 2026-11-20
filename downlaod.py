"""
STEP 1: Download the pretrained OCR model.

This is a completely standalone script — it doesn't depend on any other
file in the project. Run it first, on its own, before anything else.

What it does:
1. Checks if the 'easyocr' package is installed; installs it if missing.
2. Downloads EasyOCR's pretrained weights (~65MB) and caches them.
3. Runs a tiny test to prove the model actually works.

Run it with:
    python download_models.py
"""
import subprocess
import sys


def ensure_package_installed(package_name: str, import_name: str = None):
    """Checks if a package is importable; installs it via pip if not."""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        print(f"[OK] '{package_name}' is already installed.")
        return True
    except ImportError:
        print(f"[..] '{package_name}' not found. Installing now (this can take a few minutes)...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[FAIL] Could not install '{package_name}'.")
            print("---- pip error output ----")
            print(result.stderr[-2000:])  # last 2000 chars, in case it's long
            print("---------------------------")
            return False
        print(f"[OK] '{package_name}' installed successfully.")
        return True


def download_and_verify_model():
    print("\nDownloading pretrained OCR model weights...")
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False, verbose=True)
    except Exception as e:
        print(f"[FAIL] Could not load the model: {e}")
        return False

    print("\nRunning a quick test to confirm the model actually works...")
    try:
        from PIL import Image, ImageDraw
        import numpy as np

        test_img = Image.new("RGB", (300, 80), "white")
        draw = ImageDraw.Draw(test_img)
        draw.text((10, 25), "TEST CERTIFICATE 123", fill="black")

        result = reader.readtext(np.array(test_img))
        detected_text = " ".join([text for (_, text, _) in result])
        print(f"[OK] Model read back: '{detected_text}'")
        return True
    except Exception as e:
        print(f"[FAIL] Model loaded but test inference failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: Downloading pretrained OCR model (EasyOCR)")
    print("=" * 60)

    if not ensure_package_installed("easyocr"):
        print("\nSetup failed at the install step. Common fixes:")
        print("  - Make sure your virtual environment is activated")
        print("  - Check your internet connection")
        print("  - Try manually: pip install easyocr")
        sys.exit(1)

    if download_and_verify_model():
        print("\n" + "=" * 60)
        print("SUCCESS — model downloaded and verified working.")
        print("Weights are cached in ~/.EasyOCR/model/ (or the Windows")
        print("equivalent) so this won't re-download next time.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\nModel download/verification failed. See errors above.")
        sys.exit(1)