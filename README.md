# 🎓 AI-Powered Academic Certificate Verification Using Blockchain & IPFS

> **Tech Stack:** Python, React, Solidity, IPFS, OCR, SHAP, Machine Learning

---

## 📌 Executive Summary & Key Highlights

- **Blockchain-Based Verification Platform:** Implemented **dual SHA-256 hashing** (raw file hash + canonical text content hash), **Solidity smart contracts**, and **decentralized IPFS storage** (via Pinata) to guarantee certificate authenticity, tamper-evidence, and permanent accessibility.
- **Premium React Web Application with 3 Roles:**
  - **Visitors / Verifiers:** Instant real-time verification of certificate images/PDFs and camera QR code scanning with animated progress.
  - **Universities / Institutions:** Secure dashboard to issue on-chain certificates, pin assets to IPFS, manage student profiles & passwords, and revoke invalid credentials.
  - **Students:** Authenticated portal to view all issued academic credentials, inspect blockchain verification proofs, and securely download original certificates.
- **20-Feature Voting Ensemble & Explainable AI:** Built a **20-feature voting ensemble** combined with deep learning OCR (`EasyOCR`) and **weighted risk scoring** to detect subtle forgery, font inconsistencies, and layout anomalies; explained every individual verdict with **SHAP** feature attribution charts.

---

> [!IMPORTANT]
> ### 📍 WHERE THE FINAL PROJECT LIVES (Read First!)
> If you are looking to inspect, run, or review the **completed full-stack application**, everything is organized inside the **`FINAL_PROJECT`** folder:
>
> - **🖥️ Backend Server (`FINAL_PROJECT/final_backend/`):**
>   - The entry point is **[`FINAL_PROJECT/final_backend/app.py`](file:///c:/Users/swrjk/OneDrive/Desktop/hafiz/AI-Powered%20Academic%20Certificate%20Verification%20Using%20Blockchain%20and%20IPFS/FINAL_PROJECT/final_backend/app.py)**.
>   - A Python Flask + Socket.IO server running on port `5000` that coordinates JWT authentication, student password management, real-time WebSocket layer streaming, OCR feature extraction, the 20-feature ML voting ensemble, IPFS pinning, and Ethereum/Polygon smart contract verification.
>
> - **🌐 Frontend Application (`FINAL_PROJECT/frontend/`):**
>   - The client application is located in **[`FINAL_PROJECT/frontend/`](file:///c:/Users/swrjk/OneDrive/Desktop/hafiz/AI-Powered%20Academic%20Certificate%20Verification%20Using%20Blockchain%20and%20IPFS/FINAL_PROJECT/frontend/)**.
>   - Built with **React 18, Vite, and Tailwind CSS** running on port `5173`. Features a responsive UI, real-time WebSocket progress badges, an animated radial Risk Gauge, interactive SHAP bar charts, a webcam QR code scanner, and institutional issuance workflows.
>
> - **⛓️ Smart Contract Suite (`blockchain-smart-contract/blockchain/`):**
>   - Contains the Solidity registry contract (`CertificateRegistry.sol`), Hardhat deployment scripts (`deploy.js`), and 12 automated unit tests (`CertificateRegistry.test.js`).
>
> - **🧪 Standalone Research & Training Scripts (Root Directory):**
>   - The scripts in the root (`ai_pipeline.py`, `feature_extraction.py`, `train_model.py`, `predict_and_explain.py`, etc.) were developed during initial R&D and model training before being integrated into `FINAL_PROJECT`.

---

## 💡 Why I Built This Project

Traditional paper certificates and static PDF files are easily forged with modern image editing software. Employers, academic institutions, and embassies spend weeks manually verifying credentials through third-party background verification agencies.

Existing blockchain verification systems typically only store a single static file hash on-chain. If an attacker tampers with the student's name, degree, or GPA, a standard hash check simply flags the file as "unrecognized" without explaining *what* was modified or *why*.

To solve this, I designed and developed this **hybrid AI + Blockchain architecture**:
1. **AI Anomaly Detection with SHAP Explainability:** Uses computer vision and a 20-feature voting ensemble to analyze visual layout, text density, bounding box alignments, and character spacing. It produces a weighted risk score and generates a SHAP attribution chart so verifiers can visually see what triggered suspicion.
2. **Dual SHA-256 Cryptographic Hashing:** Computes both the *raw file hash* (verifying identical visual document bytes) and the *content hash* (verifying extracted normalized text fields), catching both graphic forgery and textual manipulation.
3. **IPFS Decentralized Storage:** Permanently stores tamper-evident copies on IPFS via Pinata Cloud.
4. **Smart Contract Registry:** Records hashes and issuance metadata on Ethereum Sepolia / Polygon Amoy, creating a trustless, publicly verifiable record that cannot be altered or deleted.

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
│ • Preprocessing  │             │ • Dual SHA-256   │             │ • Polygon Amoy / │
│ • EasyOCR Parser │             │   (File Hash +   │             │   Sepolia Network│
│ • 20-Feature     │             │    Content Hash) │ • Query Registry │
│   Voting Ensemble│             │ • IPFS Gateway   │ • Check Status & │
│ • Weighted Risk  │             │   Verification   │   Revocation     │
│   Scoring        │             │ • Pinata Cloud   │ • Match On-chain │
│ • SHAP Explainer │             │   Pinning        │   Metadata       │
└──────────────────┘             └──────────────────┘             └──────────────────┘
```

---

## 🔍 How the 4-Layer Verification Works

When a certificate is uploaded to `app.py`, the backend executes four sequential verification stages and streams real-time status events to the frontend via WebSockets:

| Layer | Stage | What It Does Under The Hood |
| :--- | :--- | :--- |
| **Layer 1** | **OCR & Preprocessing** | Image cleanup and contrast optimization. Uses `EasyOCR` to detect text blocks, confidence scores, and bounding box coordinates for key fields (Student Name, Register Number, Degree, Issue Date). |
| **Layer 2** | **20-Feature Voting Ensemble & SHAP** | Evaluates a **20-feature engineered vector** (text density variance, box alignment anomalies, font height ratios, line spacing deviations) across a machine learning voting ensemble. Computes a **weighted risk score (0–100%)** and calculates **SHAP feature attribution values** to explain the exact drivers of the verdict. |
| **Layer 3** | **Dual SHA-256 Hashing & IPFS** | Computes **Dual SHA-256 hashes**: the raw binary *file hash* and the canonical *content hash*. Resolves the document against Pinata Cloud IPFS gateways to verify byte-level decentralized storage integrity. |
| **Layer 4** | **Blockchain Smart Contract Audit** | Interacts with `CertificateRegistry.sol` via `Web3.py`. Confirms that the certificate was minted by an authorized university address, validates timestamps, and checks whether the credential is active or revoked. |

---

## 👥 User Roles & Features

### 1. 🏛️ Universities / Institutions
- **Issue On-Chain Certificates:** Upload certificate images and student data; the system automatically computes dual SHA-256 hashes, pins the asset to IPFS, and mints the record on the blockchain.
- **Manage Students & Passwords:** Create student accounts, update student records, and manage or reset student passwords securely.
- **Revoke Certificates:** Invalidate compromised or erroneously issued credentials on-chain with full audit history.
- **View Audit Logs & Stats:** Track all verification attempts, risk scores, and issuance metrics.

### 2. 🛡️ Visitors & Verifiers (Employers / HR / Public)
- **Instant File Verification:** Drag-and-drop any certificate image (PNG, JPG) or PDF to trigger the live 4-layer check.
- **Webcam QR Scanner:** Scan printed certificate QR codes using your device's camera for immediate mobile verification.
- **Inspect Risk Gauge & SHAP Breakdown:** View a visual radial risk meter and interactive SHAP bars detailing why a certificate passed or failed.
- **Verify On-Chain Proofs:** Check transaction hashes directly on Etherscan or Polygonscan.

### 3. 🎓 Students
- **Student Dashboard:** Secure login to view all official degrees and certificates issued by their university.
- **Secure Download:** Download original, high-resolution authentic certificate files directly from IPFS.
- **Shareable QR Codes:** Generate and share verifiable QR codes with potential employers.

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
│   │   │   │   ├── ManageStudents.jsx       # Student record & password management interface
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
├── ai_pipeline.py                           # Standalone AI verification pipeline
├── feature_extraction.py                    # 20-feature extraction for certificate layout
├── ocr_preprocessing.py                     # Image thresholding and OpenCV preprocessing
├── pinata_storage.py                        # Standalone Pinata IPFS upload/fetch tool
├── train_model.py                           # Model training script for voting ensemble
├── model_v2.pkl                             # Trained scikit-learn anomaly detection model
├── synthetic_dataset_v2.csv                 # Synthetic training dataset for model training
├── sample_certificate.png                   # Sample legitimate certificate for testing
├── tampered_certificate.jpg                 # Sample tampered certificate for testing
├── .gitignore                               # Protects credentials, node_modules, and builds
└── .env.example                             # Root environment variable template
```

---

## 🌐 API & WebSocket Reference (`app.py`)

The backend server in `FINAL_PROJECT/final_backend/app.py` exposes the following core endpoints:

| Method / Protocol | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Public | Authenticates user credentials and returns a signed JWT. |
| `POST` | `/api/verify` | Public / Verifier | Uploads certificate file and runs the complete 4-layer verification. |
| `Socket.IO` | `start_verification` | Public / Verifier | Triggers real-time streamed layer progress updates to the frontend. |
| `POST` | `/api/certificates/issue` | Institution | Uploads, generates dual hashes, pins to IPFS, and mints on-chain. |
| `POST` | `/api/certificates/<id>/revoke`| Institution | Revokes an issued certificate on-chain. |
| `GET` | `/api/institution/students` | Institution | Retrieves student roster for the institution. |
| `PUT` | `/api/institution/students/<id>`| Institution | Updates student details and resets passwords. |
| `GET` | `/api/certificates` | Authenticated | Lists issued certificates filtered by user role. |
| `GET` | `/api/qr/<cert_id>` | Public | Generates and serves dynamic QR code image for verification. |
| `GET` | `/api/health` | Public | Healthcheck endpoint reporting model, RPC, and IPFS status. |

---

## 🛠️ Step-by-Step Installation & Running Guide

### Prerequisites
Make sure you have installed:
- **Node.js** (v18.0.0 or higher) & `npm`
- **Python** (v3.10 or higher) & `pip`
- **Git**
- A MetaMask wallet with free Sepolia or Polygon Amoy testnet tokens (optional for local testing)

---

### Step 1: Set Up Environment Variables

1. In `blockchain-smart-contract/blockchain/`, create a `.env` file from `.env.example`:
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
   *(Note: The system contains fallback logic for offline/mock testing if testnet keys are omitted).*

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
4. Deploy the contract to Sepolia testnet (optional):
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

Pre-configured demo accounts in `users.json` for testing without manual signups:

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **University / Institution** | `simat` | `simat@123` | Issue certificates, manage student passwords, revoke certificates |
| **Visitor / Verifier** | `testuser` | `password123` | Upload & verify certificates, view audit logs & SHAP charts |
| **Student** | `priya22` | `password321` | View personal degree, download original certificate, show QR code |

---

## 🧪 Testing the Model with Sample Certificates

The repository root includes sample certificates to test both legitimate and fraudulent verification scenarios:
1. **Legitimate Certificate (`sample_certificate.png`):**
   - Upload on `/verify`.
   - **Result:** Low risk score (< 15%), all 4 layers pass with green checkmarks, dual SHA-256 hashes match on-chain records and IPFS.
2. **Tampered Certificate (`tampered_certificate.jpg`):**
   - Upload on `/verify`.
   - **Result:** High risk score (> 80%), AI voting ensemble flags visual anomalies, SHAP chart reveals bounding box misalignment and font density discrepancies.

---

## 🛡️ Security & Privacy Notice

- **Never Commit Secrets:** Sensitive credentials (`.env`, private keys, Pinata JWTs) are strictly excluded via `.gitignore`.
- **Zero Bloat:** All `node_modules/`, `dist/` builds, and `artifacts/` are excluded to keep git lightweight.
- **Privacy Protection:** Personal student information is hashed before writing to the blockchain; only cryptographic verification digests and IPFS CIDs reside on-chain.

---

## 👨‍💻 Author & Engineering Credits

This project was conceptualized, architected, and engineered by:

### **Swaraj Krishna P P**
- 🎓 **Academic Background:** Computer Science and Engineering Graduate (Class of 2026)
- 🏛️ **University:** APJ Abdul Kalam Technological University (KTU)
- 💡 **Specialization:** AI / ML Enthusiast, Decentralized Systems & Full-Stack Web3
- 📬 **Email:** [swrjkrishna@gmail.com](mailto:swrjkrishna@gmail.com)

> **Attribution Notice:**  
> All conceptualization, full-stack architecture, machine learning modeling (OCR extraction, 20-feature voting ensemble, SHAP explainability), smart contract development, and platform engineering credits for this project belong to **Swaraj Krishna P P**.

---

## 🤝 Tech Stack Overview

- **Machine Learning & OCR:** [EasyOCR](https://github.com/JaidedAI/EasyOCR), [scikit-learn](https://scikit-learn.org/), [SHAP](https://github.com/slundberg/shap), [OpenCV](https://opencv.org/)
- **Blockchain & Web3:** [Solidity](https://soliditylang.org/), [Hardhat](https://hardhat.org/), [Ethers.js](https://docs.ethers.org/), [Web3.py](https://web3py.readthedocs.io/)
- **Decentralized Storage:** [IPFS](https://ipfs.tech/) via [Pinata Cloud](https://pinata.cloud/)
- **Backend:** [Python Flask](https://flask.palletsprojects.com/), [Flask-SocketIO](https://flask-socketio.readthedocs.io/), [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- **Frontend:** [React 18](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Lucide Icons](https://lucide.dev/)
