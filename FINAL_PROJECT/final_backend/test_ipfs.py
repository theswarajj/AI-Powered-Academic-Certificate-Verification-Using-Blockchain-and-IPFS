"""Quick IPFS diagnostic script."""
import os, sys, requests
sys.path.insert(0, r"C:\Users\swrjk\OneDrive\Desktop\hafiz\blockchain-smart-contract\blockchain")
from dotenv import load_dotenv
load_dotenv(r"C:\Users\swrjk\OneDrive\Desktop\hafiz\blockchain-smart-contract\blockchain\.env")

jwt = os.environ.get("PINATA_JWT", "")

# 1. List files on Pinata
print("=== Pinata Files ===")
resp = requests.get("https://api.pinata.cloud/v3/files", headers={"Authorization": f"Bearer {jwt}"}, timeout=15)
print(f"API status: {resp.status_code}")
data = resp.json()
files = data.get("data", {}).get("files", [])
print(f"Total files: {len(files)}")

for f in files[:3]:
    cid = f.get("cid", "")
    name = f.get("name", "?")
    network = f.get("network", "?")
    fid = f.get("id", "")
    print(f"\n  File: {name}")
    print(f"  CID: {cid}")
    print(f"  Network: {network}")
    print(f"  ID: {fid}")

    # Test ipfs.io
    try:
        r = requests.head(f"https://ipfs.io/ipfs/{cid}", timeout=10, allow_redirects=True)
        print(f"  ipfs.io HEAD: {r.status_code}")
    except Exception as e:
        print(f"  ipfs.io HEAD: ERROR - {str(e)[:80]}")

    # Test Pinata public gateway
    try:
        r = requests.head(f"https://gateway.pinata.cloud/ipfs/{cid}", timeout=10, allow_redirects=True)
        print(f"  pinata gateway HEAD: {r.status_code}")
    except Exception as e:
        print(f"  pinata gateway HEAD: ERROR - {str(e)[:80]}")

    # Test Pinata dedicated gateway with signed URL
    try:
        sign_resp = requests.post(
            "https://api.pinata.cloud/v3/files/sign",
            headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
            json={"url": f"https://coral-permanent-penguin-539.mypinata.cloud/files/{cid}", "expires": 3600},
            timeout=10,
        )
        print(f"  Signed URL status: {sign_resp.status_code}")
        if sign_resp.status_code == 200:
            signed = sign_resp.json().get("data", "")
            print(f"  Signed URL: {signed[:80]}...")
            # Try fetching with signed URL
            r = requests.head(signed, timeout=10, allow_redirects=True)
            print(f"  Signed URL HEAD: {r.status_code}")
    except Exception as e:
        print(f"  Signed URL: ERROR - {str(e)[:80]}")

# 2. Check Pinata gateway config
print("\n=== Pinata Gateway Config ===")
try:
    r = requests.get("https://api.pinata.cloud/v3/ipfs/gateways", headers={"Authorization": f"Bearer {jwt}"}, timeout=10)
    print(f"Gateways status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Gateways ERROR: {str(e)[:80]}")
