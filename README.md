# 🎓 AI-Powered Academic Certificate Verification Using Blockchain & IPFS

> A secure, full-stack, decentralized verification ecosystem that prevents academic credential fraud using **Deep Learning (EasyOCR)**, **Explainable AI (Random Forest + SHAP)**, **Decentralized Storage (IPFS via Pinata)**, and **Smart Contracts (Ethereum / Polygon)**.

---

> [!IMPORTANT]
> ### 📍 WHERE THE FINAL PROJECT LIVES (Read First!)
> If you are looking to run, inspect, or test the **complete working application**, everything is organized inside the **`FINAL_PROJECT`** folder:
>
> - **🖥️ Backend Server (`FINAL_PROJECT/final_backend/`):**
>   - The entry point is **[`FINAL_PROJECT/final_backend/app.py`](file:///c:/Users/swrjk/OneDrive/Desktop/hafiz/AI-Powered%20Academic%20Certificate%20Verification%20Using%20Blockchain%20and%20IPFS/FINAL_PROJECT/final_backend/app.py)**.
>   - It is a Python Flask + Socket.IO server running on port `5000` that handles user authentication (JWT), student management, real-time WebSocket progress streaming, OCR extraction, AI model inferences, IPFS pinning, and blockchain interactions.
>
> - **🌐 Frontend Application (`FINAL_PROJECT/frontend/`):**
>   - The frontend is located in **[`FINAL_PROJECT/frontend/`](file:///c:/Users/swrjk/OneDrive/Desktop/hafiz/AI-Powered%20Academic%20Certificate%20Verification%20Using%20Blockchain%20and%20IPFS/FINAL_PROJECT/frontend/)**.
>   - Built with **React 18, Vite, and Tailwind CSS** running on port `5173`. It includes a responsive dashboard, live multi-layer verification progress, an animated Risk Gauge, SHAP feature importance charts, instant QR code scanner, and institutional issuance forms.
>
> - **⛓️ Smart Contract & Blockchain (`blockchain-smart-contract/blockchain/`):**
>   - The Solidity smart contract (`CertificateRegistry.sol`), Hardhat deployment scripts, and automated test suites live in **[`blockchain-smart-contract/blockchain/`](file:///c:/Users/swrjk/OneDrive/Desktop/hafiz/AI-Powered%20Academic%20Certificate%20Verification%20Using%20Blockchain%20and%20IPFS/blockchain-smart-contract/blockchain/)**.
>
> - **🧪 Standalone Research & Training Scripts (Root Directory):**
>   - The Python files in the root folder (`ai_pipeline.py`, `feature_extraction.py`, `train_model.py`, `predict_and_explain.py`, etc.) were developed during the initial research, data synthesis, and model training phases before packaging everything into the full-stack `FINAL_PROJECT`.

---

## 💡 Why I Built This Project

Traditional paper certificates and static PDF files are easily forged with modern graphic editing tools. Employers and universities spend weeks manually verifying credentials through third-party background check agencies. 

Existing blockchain verification systems only store a file hash on-chain — if a certificate has slightly altered text, formatting, or font inconsistencies, a simple hash check says "invalid" without explaining *why* or detecting *what* was modified.

To solve this, I designed and developed this **hybrid AI + Blockchain architecture**:
1. **Explainable AI Layer:** Uses computer vision and machine learning to analyze the visual layout, font bounding boxes, OCR text integrity, and semantic fields of a certificate. If something is suspicious, it generates a **SHAP (SHapley Additive exPlanations)** score to explain *exactly* which features look tampered with.
2. **IPFS Decentralized Storage:** Permanently stores immutable, tamper-evident copies of original certificates on IPFS through Pinata Cloud.
3. **Smart Contract Registry:** Records cryptographic hashes and metadata on the Ethereum/Polygon blockchain, creating an immutable, publicly verifiable record of truth that cannot be altered or deleted by anyone — even the issuing institution.

---

## 🏛️ System Architecture

```
                                  [ User / Verifier ]
                                           │
                        Uploads Certificate Image (PNG/JPG/PDF)
                                           │
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │       FINAL_PROJECT / Frontend (React + Vite)     │
                 │   - Real-time Socket.IO Layer Progress Listener   │
                 │   - Animated Risk Gauge & SHAP Bar Visualizer     │
                 │   - QR Code Verification Scanner                  │
                 └─────────────────────────┬─────────────────────────┘
                                           │ WebSocket / REST API
                                           ▼
                 ┌───────────────────────────────────────────────────┐
                 │     FINAL_PROJECT / Backend (Flask + Socket.IO)   │
                 │                (app.py on Port 5000)              │
                 └─────────────────────────┬─────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│   LAYER 1 & 2:   │             │     LAYER 3:     │             │     LAYER 4:     │
│  AI & OCR Engine │             │   IPFS Storage   │             │ Smart Contract   │
├──────────────────┤             ├──────────────────┤             ├──────────────────┤
│ • Preprocessing  │             │ • Compute SHA-256│             │ • Polygon Amoy / │
│ • EasyOCR Parser │             │   Cryptographic  │             │   Sepolia Network│
│ • Feature Vector │             │   File Hash      │             │ • Query Registry │
│   Extraction     │             │ • IPFS Gateway   │             │ • Check Status & │
│ • Random Forest  │             │   Verification   │             │   Revocation     │
│   Tamper Model   │             │ • Pinata Cloud   │             │ • Match On-chain │
│ • SHAP Explainer │             │   Pinning        │             │   Metadata       │
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

---

## 🔍 How the 4-Layer Verification Works

When a certificate is uploaded to `app.py`, the backend runs it through four sequential verification stages and streams live progress to the frontend over WebSockets:

| Layer | Stage | What It Does Under The Hood |
| :--- | :--- | :--- |
| **Layer 1** | **OCR & Preprocessing** | Cleans the image, adjusts contrast, and uses `EasyOCR` to extract text blocks, confidence scores, and bounding box coordinates for all certificate fields (Student Name, Register Number, Degree, Issue Date). |
| **Layer 2** | **AI Tamper Detection** | Calculates a 14-dimensional feature vector (OCR text density, spacing variance, box alignment anomalies, aspect ratios) and evaluates it against our trained Random Forest model (`model_v2.pkl`). It generates a **Risk Score (0–100%)** and computes **SHAP values** explaining which specific features triggered suspicion. |
| **Layer 3** | **IPFS Verification** | Generates a deterministic SHA-256 cryptographic digest of the raw certificate bytes. Checks if the corresponding decentralized file exists on the IPFS network via Pinata Cloud gateway. |
| **Layer 4** | **Blockchain Audit** | Queries the deployed `CertificateRegistry.sol` smart contract on Ethereum Sepolia or Polygon Amoy using `Web3.py`. Confirms whether the certificate hash is registered by an authorized institution, matches on-chain records, and has not been revoked. |

---

## 🗂️ Complete Directory Structure

```
.
├── FINAL_PROJECT/                           <-- 🌟 MAIN WORKING APPLICATION
│   │
│   ├── final_backend/                       <-- BACKEND SERVER (Python Flask)
│   │   ├── app.py                           # Application entry point (REST + WebSockets)
│   │   ├── requirements.txt                 # Backend Python dependencies
│   │   ├── certificates.json                # Local certificate database cache
│   │   ├── users.json                       # Mock demo users & institutional credentials
│   │   ├── test_ipfs.py                     # IPFS connectivity test script
│   │   ├── test_upload.py                   # Verification endpoint test script
│   │   └── uploads/                         # Directory for stored demo certificate files
│   │
│   ├── frontend/                            <-- FRONTEND APPLICATION (React + Vite)
│   │   ├── src/
│   │   │   ├── App.jsx                      # Client router and layout wrapper
│   │   │   ├── components/
│   │   │   │   ├── layout/Navbar.jsx        # Navigation bar with role-based links
│   │   │   │   └── verification/
│   │   │   │       ├── LayerProgress.jsx    # Real-time WebSocket layer status badges
│   │   │   │       ├── RiskGauge.jsx        # SVG radial gauge showing AI tamper risk
│   │   │   │       ├── ShapBars.jsx         # Bar chart of SHAP feature importance
│   │   │   │       └── VerdictBanner.jsx    # Final Authenticity badge (PASS / SUSPICIOUS / FRAUD)
│   │   │   ├── pages/
│   │   │   │   ├── Landing.jsx              # Hero landing page explaining the platform
│   │   │   │   ├── Auth.jsx                 # Login & Registration portal
│   │   │   │   ├── Dashboard.jsx            # Analytics & statistics dashboard
│   │   │   │   ├── Verify.jsx               # File dropzone & real-time verification view
│   │   │   │   ├── Results.jsx              # Comprehensive verification report page
│   │   │   │   ├── IssueCertificate.jsx     # Institutional form to mint on-chain certificates
│   │   │   │   ├── ManageStudents.jsx       # Student record management interface
│   │   │   │   ├── ViewCertificates.jsx     # Searchable repository of issued credentials
│   │   │   │   └── QRScanner.jsx            # Webcam/mobile camera QR code verification
│   │   │   └── lib/store.js                 # Global client state management
│   │   ├── package.json
│   │   ├── tailwind.config.js
│   │   └── vite.config.js
│   │
│   └── scratch/                             # Internal backend test scripts
│
├── blockchain-smart-contract/
│   └── blockchain/                          <-- SMART CONTRACT SUITE (Hardhat + Solidity)
│       ├── contracts/
│       │   └── CertificateRegistry.sol      # Core Solidity registry smart contract
│       ├── scripts/
│       │   └── deploy.js                    # Deployment script for Sepolia / Amoy testnets
│       ├── test/
│       │   └── CertificateRegistry.test.js  # 12 automated test cases for contract logic
│       ├── final_engine.py                  # Core Python engine connecting AI, IPFS & Web3
│       ├── check-account.js                 # Wallet address and balance checker
│       ├── hardhat.config.js                # Hardhat network configuration
│       ├── package.json
│       └── .env.example                     # Blockchain environment template
│
├── ai_pipeline.py                           # Original standalone AI verification pipeline
├── feature_extraction.py                    # Feature extraction functions for certificate layout
├── ocr_preprocessing.py                     # Image thresholding and OpenCV preprocessing
├── pinata_storage.py                        # Standalone Pinata IPFS upload/fetch tool
├── train_model.py                           # Model training script for Random Forest / XGBoost
├── model_v2.pkl                             # Trained scikit-learn anomaly detection model
├── synthetic_dataset_v2.csv                 # Synthetic training dataset for model training
├── sample_certificate.png                   # Sample legitimate certificate for testing
├── tampered_certificate.jpg                 # Sample tampered certificate for testing
├── .gitignore                               # Protects credentials, node_modules, and builds
└── .env.example                             # Root environment variable template
```

---

## 👥 User Roles & Features

| Role | What You Can Do in the App |
| :--- | :--- |
| **🏛️ Institution** | Issue new tamper-proof certificates to students, automatically pin them to IPFS, mint records on the blockchain, manage the student registry, view issuance history, and revoke certificates if needed. |
| **🛡️ Verifier / Employer** | Drag and drop any certificate image/PDF or scan its QR code to trigger real-time 4-layer verification. Inspect the Risk Gauge score, examine the SHAP explainability breakdown, and verify the transaction hash on Etherscan/Polygonscan. |
| **🎓 Student** | Log in to your personal student portal, view all verified academic credentials issued to you, download authenticated original certificates, and share your instant verification QR code. |

---

## 🛠️ Step-by-Step Installation & Running Guide

### Prerequisites
Make sure you have installed on your machine:
- **Node.js** (v18.0.0 or higher) & `npm`
- **Python** (v3.10 or higher) & `pip`
- **Git**
- A MetaMask wallet with free Sepolia or Polygon Amoy testnet tokens (optional for local testing)

---

### Step 1: Set Up Environment Variables

1. In `blockchain-smart-contract/blockchain/`, create a `.env` file from the example:
   ```bash
   cd blockchain-smart-contract/blockchain
   cp .env.example .env
   ```
2. Open `.env` and fill in your keys:
   ```env
   AMOY_RPC_URL=https://polygon-amoy.infura.io/v3/YOUR_INFURA_KEY
   SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   PRIVATE_KEY=your_metamask_private_key
   PINATA_JWT=your_pinata_cloud_jwt
   ```
   *(Note: For purely local testing, you can leave these as defaults; the system has graceful fallbacks).*

---

### Step 2: Set Up the Smart Contract (Hardhat)

1. Navigate to the blockchain directory:
   ```bash
   cd blockchain-smart-contract/blockchain
   npm install
   ```
2. Compile the Solidity contracts:
   ```bash
   npx hardhat compile
   ```
3. Run the automated contract unit tests:
   ```bash
   npx hardhat test
   ```
4. *(Optional)* Deploy the contract to Sepolia testnet:
   ```bash
   npx hardhat run scripts/deploy.js --network sepolia
   ```

---

### Step 3: Run the Backend (`FINAL_PROJECT/final_backend`)

1. Open a new terminal and navigate to the backend directory:
   ```bash
   cd FINAL_PROJECT/final_backend
   ```
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Flask + Socket.IO server:
   ```bash
   python app.py
   ```
4. You should see:
   ```
   [INFO] Starting Final Backend on port 5000
   [INFO] Pre-loading EasyOCR model...
   [INFO] EasyOCR model ready.
   * Running on http://127.0.0.1:5000
   ```

---

### Step 4: Run the Frontend (`FINAL_PROJECT/frontend`)

1. Open another terminal and navigate to the frontend directory:
   ```bash
   cd FINAL_PROJECT/frontend
   ```
2. Install the frontend dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 🔑 Demo Login Accounts

For testing the application without creating new accounts, use these pre-seeded accounts configured in `users.json`:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Institution** | `simat` | `simat@123` | Can issue certificates & manage students |
| **Verifier** | `testuser` | `password123` | Can run verifications & inspect audit logs |
| **Student** | `priya22` | `password321` | Can view student profile & issued credentials |

---

## 🧪 Testing the AI Model with Sample Certificates

In the repository root, I included test certificates so you can test both legitimate and fraudulent scenarios:
1. **Legitimate Certificate (`sample_certificate.png`):**
   - Upload this file on the `/verify` page.
   - Result: Low risk score (< 15%), all 4 layers pass with green badges, IPFS and Blockchain hashes match.
2. **Tampered Certificate (`tampered_certificate.jpg`):**
   - Upload this file on the `/verify` page.
   - Result: High risk score (> 80%), AI layer flags visual anomalies, SHAP chart reveals bounding box misalignment and font density discrepancies.

---

## 🛡️ Security & Privacy Best Practices

- **Never Commit Secrets:** Sensitive credentials (`.env`, private keys, Pinata JWTs) are strictly ignored by `.gitignore`.
- **Zero Heavy Bloat:** All `node_modules/`, `dist/` builds, and `artifacts/` are excluded to keep git operations fast and lightweight.
- **On-chain Privacy:** Personal student data is hashed using SHA-256 before interacting with the blockchain; only cryptographic proofs and IPFS CIDs reside on-chain.

---

## 🤝 Acknowledgments & Tech Stack

- **Machine Learning & OCR:** [EasyOCR](https://github.com/JaidedAI/EasyOCR), [scikit-learn](https://scikit-learn.org/), [SHAP](https://github.com/slundberg/shap), [OpenCV](https://opencv.org/)
- **Blockchain & Web3:** [Solidity](https://soliditylang.org/), [Hardhat](https://hardhat.org/), [Ethers.js](https://docs.ethers.org/), [Web3.py](https://web3py.readthedocs.io/)
- **Decentralized Storage:** [IPFS](https://ipfs.tech/) via [Pinata Cloud](https://pinata.cloud/)
- **Backend:** [Python Flask](https://flask.palletsprojects.com/), [Flask-SocketIO](https://flask-socketio.readthedocs.io/), [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- **Frontend:** [React 18](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/)
