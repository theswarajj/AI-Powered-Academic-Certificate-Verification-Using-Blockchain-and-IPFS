# AI-Powered Academic Certificate Verification Using Blockchain and IPFS

A multi-layered system for issuing, validating, and verifying academic certificates using **Machine Learning (OCR & Feature Extraction)**, **Ethereum Smart Contracts**, and **Decentralized Storage (IPFS via Pinata)**.

---

## 🏗️ Architecture Overview

The system operates across three interconnected layers to ensure certificate authenticity:

```
[ Academic Certificate Image / Document ]
                   │
                   ▼
       1. AI & OCR Verification Layer
   ├── Preprocessing & EasyOCR Extraction
   ├── Random Forest & XGBoost Anomaly Detection
   └── SHAP Feature Explainability
                   │
                   ▼
       2. Decentralized Storage Layer
   ├── Cryptographic SHA-256 Hash Computation
   └── IPFS Pinning via Pinata Cloud
                   │
                   ▼
       3. Blockchain Trust Layer
   ├── Ethereum / Polygon Smart Contract (CertificateRegistry.sol)
   ├── Immutable On-chain Hash & Metadata Storage
   └── Public Verification & Anti-tampering Checks
```

---

## 📁 Repository Structure

```
├── blockchain-smart-contract/
│   └── blockchain/
│       ├── contracts/               # Solidity Smart Contracts (CertificateRegistry.sol)
│       ├── scripts/                 # Hardhat deployment scripts (deploy.js)
│       ├── test/                    # Hardhat unit tests (CertificateRegistry.test.js)
│       ├── hardhat.config.js        # Hardhat configuration (Sepolia & Polygon Amoy)
│       ├── final_engine.py          # Unified AI + Blockchain + IPFS verification engine
│       └── .env.example             # Blockchain environment variable template
│
├── FINAL/
│   ├── frontend/                    # Modern React + Vite + Tailwind CSS Web Application
│   │   ├── src/                     # UI Pages (Admin, Verify, Dashboard, QR Scanner, etc.)
│   │   └── package.json
│   ├── final_backend/               # Flask + Socket.IO Real-time API
│   │   ├── app.py                   # Main backend application server
│   │   ├── requirements.txt         # Backend Python dependencies
│   │   └── uploads/                 # Local uploads directory for demo certificates
│   └── scratch/                     # Developer verification and test scripts
│
├── haneena/
│   └── final_backend/               # Alternative backend configuration
│
├── ai_pipeline.py                   # End-to-end AI OCR and anomaly detection pipeline
├── feature_extraction.py            # Feature engineering for certificate layout analysis
├── ocr_preprocessing.py             # Image cleanup and OCR thresholding
├── pinata_storage.py                # Standalone IPFS upload and retrieval utility
├── train_model.py                   # Model training script for certificate tampering detection
├── model_v2.pkl                     # Pretrained anomaly detection model
├── .gitignore                       # Git ignore rules (hides secrets, node_modules, builds)
└── .env.example                     # Root environment configuration template
```

---

## ⚙️ Quick Start Guide

### 1. Configure Environment Variables
Copy `.env.example` in `blockchain-smart-contract/blockchain/` to `.env`:
```bash
cp blockchain-smart-contract/blockchain/.env.example blockchain-smart-contract/blockchain/.env
```
Fill in the values in your `.env`:
```env
AMOY_RPC_URL=https://polygon-amoy.infura.io/v3/YOUR_INFURA_KEY
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
PRIVATE_KEY=your_metamask_private_key
PINATA_JWT=your_pinata_jwt_token
```
> **Security Note:** The `.env` file is listed in `.gitignore` and will never be committed to GitHub.

---

### 2. Smart Contract (Hardhat)
Navigate to the blockchain directory:
```bash
cd blockchain-smart-contract/blockchain
npm install
npx hardhat compile
npx hardhat test
```
To deploy to Sepolia testnet:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

---

### 3. Backend (Flask + Socket.IO)
Navigate to the backend directory:
```bash
cd FINAL/final_backend
pip install -r requirements.txt
python app.py
```
The backend server runs on `http://localhost:5000`.

---

### 4. Frontend (React + Vite)
Navigate to the frontend directory:
```bash
cd FINAL/frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🔒 Security & Privacy Notice
- Sensitive configuration files (`.env`), private keys, and build folders (`node_modules/`, `artifacts/`, `dist/`, `cache/`) are automatically excluded from git tracking via `.gitignore`.
- Always keep your private keys safe and never share or commit them publicly.
