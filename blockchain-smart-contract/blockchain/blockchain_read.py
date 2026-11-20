"""
BLOCKCHAIN LAYER (Python side) — Part 1: Reading from the chain.

This is the bridge between your Flask backend and the smart contract you
deployed with Hardhat. Uses web3.py to call the READ-ONLY
verifyCertificate() function — no private key needed for this, since
reading from the blockchain is free and doesn't require signing a
transaction (only writing/issuing does).

Run it with:
    python blockchain_read.py CERT-2026-00891
"""
import subprocess
import sys
import os
import json


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


for pkg, mod in [("web3", "web3"), ("python-dotenv", "dotenv")]:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# EDIT THIS to your real deployed contract address:
CONTRACT_ADDRESS = "0x099aA35Af18acA4D03d010E861b02A4A790846Ab"

# The contract's ABI — describes what functions exist and their signatures.
# Extracted from Hardhat's compiled artifact
# (artifacts/contracts/CertificateRegistry.sol/CertificateRegistry.json).
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


def get_web3():
    rpc_url = os.environ.get("SEPOLIA_RPC_URL")
    if not rpc_url:
        raise RuntimeError(
            "SEPOLIA_RPC_URL not found. Make sure you have a .env file in this "
            "same folder with SEPOLIA_RPC_URL=your_alchemy_url"
        )
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to {rpc_url}")
    return w3


def verify_certificate_on_chain(cert_id: str) -> dict:
    w3 = get_web3()
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

    result = contract.functions.verifyCertificate(cert_id).call()
    ipfs_cid, file_hash, content_hash, issuer, timestamp, revoked, exists = result

    return {
        "exists": exists,
        "ipfs_cid": ipfs_cid,
        "file_hash": file_hash.hex(),
        "content_hash": content_hash.hex(),
        "issuer": issuer,
        "timestamp": timestamp,
        "revoked": revoked,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python blockchain_read.py <certificate_id>")
        print("Example: python blockchain_read.py CERT-2026-00891")
        sys.exit(1)

    cert_id = sys.argv[1]
    print("=" * 60)
    print("BLOCKCHAIN LAYER — Reading from Sepolia via web3.py")
    print("=" * 60)

    try:
        result = verify_certificate_on_chain(cert_id)
    except RuntimeError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)

    print(f"\nQuerying certId: {cert_id}")
    print(f"\nOn-chain record:")
    for key, value in result.items():
        print(f"  {key:15s}: {value}")

    print("\n" + "=" * 60)
    if result["exists"]:
        print("SUCCESS — certificate found on-chain, read via Python/web3.py.")
    else:
        print("This certId does not exist on-chain (exists=False).")
    print("=" * 60)