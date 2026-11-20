import os
import requests
from dotenv import load_dotenv

load_dotenv(r"C:\Users\swrjk\OneDrive\Desktop\hafiz\blockchain-smart-contract\blockchain\.env")
jwt = os.environ.get("PINATA_JWT", "")

print(f"Testing upload with JWT (len={len(jwt)})...")

with open("test.txt", "w") as f:
    f.write("Hello Pinata IPFS Test!")

with open("test.txt", "rb") as f:
    try:
        # V3 approach (like in app.py)
        resp = requests.post(
            "https://uploads.pinata.cloud/v3/files",
            headers={"Authorization": f"Bearer {jwt}"},
            files={"file": ("test.txt", f)},
            data={"network": "public"},
            timeout=30,
        )
        print(f"V3 Upload Response: {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print("V3 Exception:", e)

with open("test.txt", "rb") as f:
    try:
        # V1 approach
        resp = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            headers={"Authorization": f"Bearer {jwt}"},
            files={"file": f},
            timeout=30,
        )
        print(f"V1 Upload Response: {resp.status_code}")
        print(resp.text)
    except Exception as e:
        print("V1 Exception:", e)
