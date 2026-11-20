"""
STORAGE LAYER — Part 2 (Pinata version): IPFS Upload/Retrieval.

Uses Pinata's current v3 API. Needs your Pinata JWT set as an environment
variable called PINATA_JWT — see the setup instructions below the script.

Run it with:
    python pinata_storage.py path/to/certificate.png
"""
import subprocess
import sys
import os


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


if not ensure_package_installed("requests"):
    sys.exit(1)

import requests

UPLOAD_URL = "https://uploads.pinata.cloud/v3/files"
PUBLIC_GATEWAY = "https://gateway.pinata.cloud/ipfs"


def get_jwt() -> str:
    jwt = os.environ.get("PINATA_JWT")
    if not jwt:
        raise RuntimeError(
            "PINATA_JWT environment variable not set.\n"
            "In PowerShell, run:  $env:PINATA_JWT=\"your_jwt_here\"\n"
            "(This only lasts for the current terminal session — see the\n"
            "setup notes for how to make it permanent.)"
        )
    return jwt


def upload_to_pinata(file_path: str, jwt: str) -> dict:
    """
    Uploads a file to Pinata's public IPFS network.
    Returns the API response, including the CID.
    """
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        data = {"network": "public"}
        headers = {"Authorization": f"Bearer {jwt}"}
        resp = requests.post(UPLOAD_URL, headers=headers, files=files, data=data, timeout=60)

    if resp.status_code != 200:
        raise RuntimeError(f"Upload failed ({resp.status_code}): {resp.text}")

    return resp.json()["data"]


def check_availability(cid: str) -> bool:
    """Confirms the file is actually retrievable via Pinata's public gateway."""
    try:
        resp = requests.head(f"{PUBLIC_GATEWAY}/{cid}", timeout=15)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pinata_storage.py path/to/certificate.png")
        sys.exit(1)

    path = sys.argv[1]
    print("=" * 60)
    print("STORAGE LAYER — IPFS Upload via Pinata")
    print("=" * 60)

    try:
        jwt = get_jwt()
    except RuntimeError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)

    print(f"\nUploading: {path}")
    try:
        result = upload_to_pinata(path, jwt)
    except RuntimeError as e:
        print(f"\n[FAIL] {e}")
        print("\nCommon causes:")
        print("  - JWT is wrong or expired -> generate a new one in Pinata dashboard")
        print("  - JWT doesn't have Files:Write permission -> recreate with Admin on")
        sys.exit(1)

    cid = result["cid"]
    print(f"[OK] Uploaded successfully.")
    print(f"  CID   : {cid}")
    print(f"  Name  : {result.get('name')}")
    print(f"  Size  : {result.get('size')} bytes")

    print("\nVerifying it's actually retrievable via the public gateway...")
    print("(this can take a few seconds to propagate)")
    if check_availability(cid):
        print("[OK] Confirmed reachable.")
    else:
        print("[..] Not yet reachable — this is normal, can take up to a minute or two to propagate across the network.")

    print(f"\nView it in any browser at:")
    print(f"  {PUBLIC_GATEWAY}/{cid}")

    print("\n" + "=" * 60)
    print("SUCCESS — store this CID alongside your certificate's hash:")
    print(f"  {cid}")
    print("=" * 60)