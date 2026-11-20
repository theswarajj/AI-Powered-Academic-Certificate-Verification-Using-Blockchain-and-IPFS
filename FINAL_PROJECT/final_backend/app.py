"""
FINAL BACKEND -- Flask + Socket.IO API for Certificate Verification.

Wraps final_engine.py v3 as a REST + WebSocket API.
Provides real-time layer-by-layer verification progress via Socket.IO.

Run:
  python app.py
"""
import os
import sys
import json
import time
import base64
import hashlib
import io
import random
import string
import logging
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from dotenv import load_dotenv
from web3 import Web3

# --- Add the blockchain directory to sys.path so we can import final_engine ---
BLOCKCHAIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "blockchain-smart-contract", "blockchain")
)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BLOCKCHAIN_DIR)

# Load .env from the blockchain directory
env_path = os.path.join(BLOCKCHAIN_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

# Change cwd to blockchain dir so MODEL_PATH resolves
original_cwd = os.getcwd()
os.chdir(BLOCKCHAIN_DIR)

# Now import the engine
import final_engine as engine

# ============================================================
# App Setup
# ============================================================

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cert-verify-secret-key-2026")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-2026")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["Content-Disposition"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
jwt = JWTManager(app)

# Simple file-based user store (for demo -- in production use MongoDB)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("final_backend")

# Setup MongoDB
try:
    from pymongo import MongoClient
    MONGO_URI = os.environ.get("MONGO_URI", "")
    if MONGO_URI:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Check connection
        mongo_client.server_info()
        db = mongo_client.get_database("certverify")
        mongo_enabled = True
        logger.info("MongoDB connected successfully.")
    else:
        mongo_enabled = False
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}. Falling back to local files.")
    mongo_enabled = False

def _load_users():
    if mongo_enabled:
        users = {}
        for u in db.users.find():
            users[u["username"]] = u
        return users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_users(users):
    if mongo_enabled:
        for username, data in users.items():
            data["username"] = username
            db.users.update_one({"username": username}, {"$set": data}, upsert=True)
        return
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ============================================================
# AUTH ROUTES
# ============================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "verifier").strip()
    full_name = data.get("full_name", "").strip()
    wallet_address = data.get("wallet_address", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if role == "student":
        return jsonify({"error": "Student registration is disabled. Login credentials must be provided by your institution/university."}), 403
    if role not in ("institution", "verifier", "admin"):
        return jsonify({"error": "Invalid role. Must be one of: institution, verifier, admin"}), 400

    users = _load_users()
    if username in users:
        return jsonify({"error": "Username already exists"}), 409

    users[username] = {
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "current_password": password,
        "role": role,
        "full_name": full_name,
        "wallet_address": wallet_address,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _save_users(users)

    token = create_access_token(
        identity=username,
        additional_claims={"role": role, "full_name": full_name}
    )
    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {"username": username, "role": role, "full_name": full_name}
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    users = _load_users()
    user = users.get(username)
    actual_username = username

    # If not found directly by username, allow student to log in using their register_number
    if not user:
        for uname, udata in users.items():
            if udata.get("role") == "student":
                reg = udata.get("register_number", "").strip().lower()
                if reg and reg == username.lower():
                    user = udata
                    actual_username = uname
                    break

    if not user or user["password_hash"] != hashlib.sha256(password.encode()).hexdigest():
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        identity=actual_username,
        additional_claims={"role": user["role"], "full_name": user.get("full_name", "")}
    )
    return jsonify({
        "token": token,
        "user": {
            "username": actual_username,
            "role": user["role"],
            "full_name": user.get("full_name", ""),
            "register_number": user.get("register_number", ""),
            "wallet_address": user.get("wallet_address", ""),
            "institution": user.get("institution", ""),
        }
    })


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_me():
    username = get_jwt_identity()
    claims = get_jwt()
    users = _load_users()
    user = users.get(username, {})
    return jsonify({
        "username": username,
        "role": claims.get("role", "verifier"),
        "full_name": claims.get("full_name", "") or user.get("full_name", ""),
        "register_number": user.get("register_number", ""),
        "wallet_address": user.get("wallet_address", ""),
        "institution": user.get("institution", ""),
    })


@app.route("/api/auth/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Allow students and users to change their password. Updates in users store for university visibility."""
    username = get_jwt_identity()
    data = request.get_json() or {}
    current_password = data.get("current_password", "").strip()
    new_password = data.get("new_password", "").strip()

    if not current_password or not new_password:
        return jsonify({"error": "Current and new passwords are required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    users = _load_users()
    user = users.get(username)
    if not user or user["password_hash"] != hashlib.sha256(current_password.encode()).hexdigest():
        return jsonify({"error": "Current password is incorrect"}), 401

    user["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    user["current_password"] = new_password
    user["updated_at"] = datetime.now().isoformat()
    users[username] = user
    _save_users(users)

    return jsonify({"message": "Password changed successfully"})


# ============================================================
# INSTITUTION STUDENT CREDENTIALS MANAGEMENT
# ============================================================

def _generate_student_username(student_name, register_number, existing_users):
    """Generate a clean, unique student username."""
    clean_first = "".join(c for c in (student_name.split()[0].lower() if student_name and student_name.strip() else "student") if c.isalnum())
    if not clean_first:
        clean_first = "student"

    reg_digits = "".join(c for c in (register_number or "") if c.isdigit())
    if len(reg_digits) >= 2:
        suffix = reg_digits[-4:] if len(reg_digits) >= 4 else reg_digits
    else:
        reg_alnum = "".join(c for c in (register_number or "").lower() if c.isalnum())
        if len(reg_alnum) >= 2:
            suffix = reg_alnum[-4:]
        else:
            suffix = str(random.randint(20, 99))

    base_candidate = f"{clean_first}{suffix}".lower()
    candidate = base_candidate

    counter = 1
    while candidate in existing_users:
        counter += 1
        candidate = f"{base_candidate}{counter}"

    return candidate


def _generate_student_password(student_name=""):
    """Generate a friendly, memorable, secure student password."""
    first_part = "".join(c for c in (student_name.split()[0].capitalize() if student_name and student_name.strip() else "Cert") if c.isalpha())
    if len(first_part) < 3:
        first_part = "Student"
    num = random.randint(1000, 9999)
    special = random.choice(["@", "#", "!"])
    return f"{first_part}{special}{num}"


def _ensure_student_credentials(student_name, register_number, institution_username):
    """
    Find existing student user or automatically generate unique username and password.
    Returns dict with credentials and is_new flag.
    """
    users = _load_users()
    reg_clean = (register_number or "").strip()
    name_clean = (student_name or "").strip()

    # 1. Search for existing student
    matched_uname = None
    matched_user = None

    for uname, udata in users.items():
        if udata.get("role") == "student":
            u_reg = udata.get("register_number", "").strip()
            u_name = udata.get("full_name", "").strip()
            
            # Match by register number if available
            if reg_clean and u_reg and reg_clean.lower() == u_reg.lower():
                matched_uname = uname
                matched_user = udata
                break
            # Match by name and same institution if register number not matched
            elif name_clean and u_name and name_clean.lower() == u_name.lower():
                if not udata.get("institution") or udata.get("institution") == institution_username:
                    matched_uname = uname
                    matched_user = udata
                    break

    if matched_user:
        # Student account already exists! Keep existing password, update any missing details
        updated = False
        if reg_clean and not matched_user.get("register_number"):
            matched_user["register_number"] = reg_clean
            updated = True
        if institution_username and not matched_user.get("institution"):
            matched_user["institution"] = institution_username
            updated = True
        if updated:
            users[matched_uname] = matched_user
            _save_users(users)

        return {
            "username": matched_uname,
            "password": matched_user.get("current_password", "(unchanged)"),
            "full_name": matched_user.get("full_name", name_clean),
            "register_number": matched_user.get("register_number", reg_clean),
            "is_new": False,
        }

    # 2. No student account found: Automatically generate credentials
    new_username = _generate_student_username(name_clean, reg_clean, users)
    new_password = _generate_student_password(name_clean)

    users[new_username] = {
        "password_hash": hashlib.sha256(new_password.encode()).hexdigest(),
        "current_password": new_password,
        "role": "student",
        "full_name": name_clean,
        "register_number": reg_clean,
        "institution": institution_username,
        "auto_generated": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _save_users(users)

    return {
        "username": new_username,
        "password": new_password,
        "full_name": name_clean,
        "register_number": reg_clean,
        "is_new": True,
    }


@app.route("/api/institution/students", methods=["GET"])
@jwt_required()
def list_institution_students():
    """List student accounts controlled by the institution."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")
    if role not in ("institution", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    users = _load_users()
    certs = _load_certs()

    # Auto-sync: ensure credentials exist for any certificates issued by this institution
    certs_modified = False
    for c in certs:
        c_inst = c.get("issued_by", "")
        if role == "institution" and c_inst and c_inst != username:
            continue
        c_reg = c.get("register_number", "").strip()
        c_name = c.get("student_name", "").strip()
        if not c_reg and not c_name:
            continue

        has_user = any(
            udata.get("role") == "student" and (
                (c_reg and c_reg.lower() == udata.get("register_number", "").strip().lower())
                or (c_name and c_name.lower() == udata.get("full_name", "").strip().lower())
                or (c.get("student_username") and c.get("student_username") == uname)
            )
            for uname, udata in users.items()
        )
        if not has_user:
            creds = _ensure_student_credentials(c_name, c_reg, c_inst or username)
            c["student_username"] = creds["username"]
            certs_modified = True
            users = _load_users()

    if certs_modified:
        _save_certs(certs)

    student_list = []
    for uname, udata in users.items():
        if udata.get("role") == "student":
            inst = udata.get("institution", "")
            if role == "institution" and inst and inst != username:
                continue
            reg_no = udata.get("register_number", "").strip().lower()
            student_name = udata.get("full_name", "").strip().lower()
            student_certs = [
                c["cert_id"] for c in certs
                if (reg_no and reg_no == c.get("register_number", "").strip().lower())
                or (student_name and student_name == c.get("student_name", "").strip().lower())
                or c.get("student_username") == uname
            ]
            student_list.append({
                "username": uname,
                "full_name": udata.get("full_name", ""),
                "register_number": udata.get("register_number", ""),
                "current_password": udata.get("current_password", "(encrypted)"),
                "created_at": udata.get("created_at", ""),
                "updated_at": udata.get("updated_at", ""),
                "certificates_count": len(student_certs),
                "cert_ids": student_certs,
            })

    return jsonify({"students": student_list})


@app.route("/api/institution/students", methods=["POST"])
@jwt_required()
def create_institution_student():
    """Create a new student credential by the institution."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")
    if role not in ("institution", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    student_username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()
    register_number = data.get("register_number", "").strip()

    if not student_username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users = _load_users()
    if student_username in users:
        return jsonify({"error": "A user or student with this username already exists"}), 409

    users[student_username] = {
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "current_password": password,
        "role": "student",
        "full_name": full_name,
        "register_number": register_number,
        "institution": username,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _save_users(users)

    return jsonify({
        "message": "Student account created successfully",
        "student": {
            "username": student_username,
            "full_name": full_name,
            "register_number": register_number,
            "current_password": password,
        }
    }), 201


@app.route("/api/institution/students/<student_username>", methods=["PUT"])
@jwt_required()
def update_institution_student(student_username):
    """Update student credentials or details by the institution."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")
    if role not in ("institution", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    users = _load_users()
    user = users.get(student_username)
    if not user or user.get("role") != "student":
        return jsonify({"error": "Student not found"}), 404

    if role == "institution" and user.get("institution") and user.get("institution") != username:
        return jsonify({"error": "You can only manage students created by your institution"}), 403

    data = request.get_json() or {}
    if "password" in data and data["password"]:
        new_pw = data["password"].strip()
        if len(new_pw) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        user["password_hash"] = hashlib.sha256(new_pw.encode()).hexdigest()
        user["current_password"] = new_pw

    if "full_name" in data:
        user["full_name"] = data["full_name"].strip()
    if "register_number" in data:
        user["register_number"] = data["register_number"].strip()

    user["updated_at"] = datetime.now().isoformat()
    users[student_username] = user
    _save_users(users)

    return jsonify({
        "message": "Student credentials updated successfully",
        "student": {
            "username": student_username,
            "full_name": user.get("full_name", ""),
            "register_number": user.get("register_number", ""),
            "current_password": user.get("current_password", ""),
            "updated_at": user.get("updated_at", ""),
        }
    })


@app.route("/api/institution/students/<student_username>", methods=["DELETE"])
@jwt_required()
def delete_institution_student(student_username):
    """Delete a student account."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")
    if role not in ("institution", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    users = _load_users()
    user = users.get(student_username)
    if not user or user.get("role") != "student":
        return jsonify({"error": "Student not found"}), 404

    if role == "institution" and user.get("institution") and user.get("institution") != username:
        return jsonify({"error": "You can only manage students created by your institution"}), 403

    del users[student_username]
    _save_users(users)
    return jsonify({"message": f"Student '{student_username}' deleted successfully"})


# ============================================================
# VERIFICATION ROUTES (REST -- synchronous, single response)
# ============================================================

@app.route("/api/verify", methods=["POST"])
def verify_certificate():
    """Synchronous verification -- upload file + cert_id, get full result."""
    cert_id = request.form.get("cert_id", "").strip()
    if not cert_id:
        return jsonify({"error": "cert_id is required"}), 400

    if "file" not in request.files:
        return jsonify({"error": "Certificate file is required"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save uploaded file temporarily
    filename = f"{cert_id}_{int(time.time())}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        # Run the full 4-layer verification using the engine's verify() function
        result = engine.verify(cert_id, filepath)

        # Re-shape for the frontend
        api_result = _format_result_for_api(cert_id, result)
        return jsonify(api_result)
    except Exception as e:
        logger.exception("Verification failed")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


def _format_result_for_api(cert_id, result):
    """Reshape the engine result dict for the frontend API."""
    h = result.get("hash", {})
    bc = result.get("blockchain", {})
    ipfs_r = result.get("ipfs", {})
    ai = result.get("ai", {})
    risk = result.get("risk", {})
    fields = result.get("fields", {})

    # Remove raw chain data (not JSON-serializable)
    bc_clean = {k: v for k, v in bc.items() if k != "raw"}

    return {
        "cert_id": cert_id,
        "verdict": result.get("verdict", "UNKNOWN"),
        "risk_score": risk.get("total_risk", 0),
        "confidence_band": risk.get("confidence_band", "UNKNOWN"),
        "layers_checked": risk.get("layers_checked", 0),
        "risk_breakdown": risk.get("breakdown", {}),
        "fields": fields,
        "ocr_confidence": fields.get("ocr_avg_confidence", 0),
        "hash": {
            "file_hash_computed": h.get("computed_file_hash", ""),
            "content_hash_computed": h.get("computed_content_hash", ""),
            "onchain_file_hash": h.get("onchain_file_hash"),
            "onchain_content_hash": h.get("onchain_content_hash"),
            "file_hash_match": h.get("file_hash_match"),
            "content_hash_match": h.get("content_hash_match"),
            "layer_available": h.get("layer_available", False),
        },
        "blockchain": bc_clean,
        "ipfs": ipfs_r,
        "ai": {
            "ml_prediction": ai.get("ml_prediction", ""),
            "fraud_probability_pct": ai.get("fraud_probability_pct", 0),
            "hard_rule_failures": ai.get("hard_rule_failures", []),
            "final_ai_verdict": ai.get("final_ai_verdict", ""),
            "explanations": ai.get("all_explanations", []),
            "forensics": ai.get("forensics", {}),
            "signature_detected": ai.get("signature_detected", False),
            "signature_analysis": ai.get("signature_analysis", {}),
        },
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# SOCKET.IO -- Real-time Verification with Layer Progress
# ============================================================

@socketio.on("start_verification")
def handle_start_verification(data):
    """Real-time verification with layer-by-layer progress updates."""
    cert_id = data.get("cert_id", "").strip()
    file_b64 = data.get("file", "")
    filename = data.get("filename", "certificate.png")

    if not cert_id or not file_b64:
        emit("verification_error", {"error": "cert_id and file are required"})
        return

    try:
        file_bytes = base64.b64decode(file_b64)
    except Exception:
        emit("verification_error", {"error": "Invalid base64 file data"})
        return

    # Save temp file
    filepath = os.path.join(UPLOAD_DIR, f"{cert_id}_{int(time.time())}_{filename}")
    with open(filepath, "wb") as f:
        f.write(file_bytes)

    try:
        _run_verification_with_progress(cert_id, filepath, file_bytes)
    except Exception as e:
        logger.exception("Socket.IO verification failed")
        emit("verification_error", {"error": str(e)})
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


def _run_verification_with_progress(cert_id, filepath, file_bytes):
    """Run verification step-by-step, emitting progress after each layer."""
    import joblib

    # --- Preprocessing ---
    emit("layer_progress", {
        "layer": 0, "name": "Preprocessing",
        "status": "running", "data": {}
    })

    img = engine.load_image_cv(file_bytes, from_bytes=True)
    reader = engine.get_ocr_reader()
    ocr_result = engine.run_ocr_with_fallback(img, reader)
    fields = engine.extract_fields(ocr_result["raw_text"])
    vector = engine.build_feature_vector(ocr_result, fields, file_bytes, img)

    emit("layer_progress", {
        "layer": 0, "name": "Preprocessing",
        "status": "done", "data": {
            "ocr_confidence": round(ocr_result["avg_confidence"], 1),
            "fields": fields,
        }
    })

    # --- Layer 2: Blockchain (run first to get chain record) ---
    emit("layer_progress", {
        "layer": 2, "name": "Blockchain Verification",
        "status": "running", "data": {}
    })

    blockchain_result = engine.run_blockchain_layer(cert_id, fields)
    chain_raw = blockchain_result.get("raw", {})
    bc_clean = {k: v for k, v in blockchain_result.items() if k != "raw"}

    emit("layer_progress", {
        "layer": 2, "name": "Blockchain Verification",
        "status": "done", "data": {
            "record_exists": blockchain_result.get("record_exists", False),
            "revoked": blockchain_result.get("revoked", False),
            "issuer_address": blockchain_result.get("issuer_address"),
            "layer_available": blockchain_result.get("layer_available", False),
            "timestamp_coherent": blockchain_result.get("timestamp_coherent"),
        }
    })

    # --- Layer 1: Hash ---
    emit("layer_progress", {
        "layer": 1, "name": "Hash Verification",
        "status": "running", "data": {}
    })

    hash_result = engine.run_hash_layer(file_bytes, fields, chain_raw)

    emit("layer_progress", {
        "layer": 1, "name": "Hash Verification",
        "status": "done", "data": {
            "file_hash_match": hash_result.get("file_hash_match"),
            "content_hash_match": hash_result.get("content_hash_match"),
            "layer_available": hash_result.get("layer_available", False),
            "computed_file_hash": hash_result.get("computed_file_hash", "")[:16] + "...",
        }
    })

    # --- Layer 3: IPFS ---
    emit("layer_progress", {
        "layer": 3, "name": "IPFS Verification",
        "status": "running", "data": {}
    })

    ipfs_result = engine.run_ipfs_layer(chain_raw, file_bytes)

    emit("layer_progress", {
        "layer": 3, "name": "IPFS Verification",
        "status": "done", "data": {
            "file_available": ipfs_result.get("file_available", False),
            "content_integrity": ipfs_result.get("content_integrity"),
            "cid": ipfs_result.get("cid"),
        }
    })

    # --- Layer 4: AI ---
    emit("layer_progress", {
        "layer": 4, "name": "AI Analysis",
        "status": "running", "data": {}
    })

    model = joblib.load(engine.MODEL_PATH)
    ai_result = engine.run_ai_layer(vector, model, fields, img, file_bytes, ocr_result)

    emit("layer_progress", {
        "layer": 4, "name": "AI Analysis",
        "status": "done", "data": {
            "ml_prediction": ai_result.get("ml_prediction", ""),
            "fraud_probability_pct": ai_result.get("fraud_probability_pct", 0),
            "final_ai_verdict": ai_result.get("final_ai_verdict", ""),
            "hard_rule_failures": ai_result.get("hard_rule_failures", []),
            "signature_detected": ai_result.get("signature_detected", False),
            "signature_analysis": ai_result.get("signature_analysis", {}),
        }
    })

    # --- Final Result ---
    risk = engine.compute_risk_score(hash_result, blockchain_result, ipfs_result, ai_result)
    verdict = engine.determine_verdict(hash_result, blockchain_result, ipfs_result, ai_result, risk)

    engine.log_audit(cert_id, verdict, risk["total_risk"],
                     f"file={os.path.basename(filepath)} fraud_pct={ai_result['fraud_probability_pct']}")

    emit("verification_complete", {
        "cert_id": cert_id,
        "verdict": verdict,
        "risk_score": risk["total_risk"],
        "confidence_band": risk["confidence_band"],
        "layers_checked": risk["layers_checked"],
        "risk_breakdown": risk["breakdown"],
        "fields": fields,
        "ocr_confidence": round(ocr_result["avg_confidence"], 1),
        "hash": {
            "file_hash_computed": hash_result.get("computed_file_hash", ""),
            "content_hash_computed": hash_result.get("computed_content_hash", ""),
            "onchain_file_hash": hash_result.get("onchain_file_hash"),
            "onchain_content_hash": hash_result.get("onchain_content_hash"),
            "file_hash_match": hash_result.get("file_hash_match"),
            "content_hash_match": hash_result.get("content_hash_match"),
            "layer_available": hash_result.get("layer_available", False),
        },
        "blockchain": bc_clean,
        "ipfs": ipfs_result,
        "ai": {
            "ml_prediction": ai_result.get("ml_prediction", ""),
            "fraud_probability_pct": ai_result.get("fraud_probability_pct", 0),
            "hard_rule_failures": ai_result.get("hard_rule_failures", []),
            "final_ai_verdict": ai_result.get("final_ai_verdict", ""),
            "explanations": ai_result.get("all_explanations", []),
            "forensics": ai_result.get("forensics", {}),
            "signature_detected": ai_result.get("signature_detected", False),
            "signature_analysis": ai_result.get("signature_analysis", {}),
        },
        "timestamp": datetime.now().isoformat(),
    })


# ============================================================
# ADMIN / STATS ROUTES
# ============================================================

@app.route("/api/admin/audit-log", methods=["GET"])
@jwt_required()
def get_audit_log():
    """Return paginated audit log entries."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    log_path = os.path.join(BLOCKCHAIN_DIR, "verification_audit.log")
    if not os.path.exists(log_path):
        return jsonify({"entries": [], "total": 0, "page": page})

    with open(log_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    entries = []
    for line in reversed(lines):
        parts = line.split(" | ")
        if len(parts) >= 2:
            entry = {"raw": line, "timestamp": parts[0]}
            for part in parts[1:]:
                if "=" in part:
                    key, val = part.split("=", 1)
                    entry[key.strip()] = val.strip()
            entries.append(entry)

    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({
        "entries": entries[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/admin/stats", methods=["GET"])
def get_stats():
    """Return dashboard statistics."""
    log_path = os.path.join(BLOCKCHAIN_DIR, "verification_audit.log")
    stats = {
        "total_verifications": 0,
        "verdicts": {},
        "avg_risk": 0,
        "recent": [],
    }

    if not os.path.exists(log_path):
        return jsonify(stats)

    with open(log_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    total_risk = 0
    for line in lines:
        stats["total_verifications"] += 1
        parts = line.split(" | ")
        entry = {}
        for part in parts:
            if "=" in part:
                key, val = part.split("=", 1)
                entry[key.strip()] = val.strip()
        verdict = entry.get("verdict", "UNKNOWN")
        stats["verdicts"][verdict] = stats["verdicts"].get(verdict, 0) + 1
        try:
            total_risk += int(entry.get("risk", 0))
        except ValueError:
            pass

    if stats["total_verifications"] > 0:
        stats["avg_risk"] = round(total_risk / stats["total_verifications"], 1)

    for line in reversed(lines[-5:]):
        parts = line.split(" | ")
        entry = {"raw": line}
        for part in parts:
            if "=" in part:
                key, val = part.split("=", 1)
                entry[key.strip()] = val.strip()
        stats["recent"].append(entry)

    return jsonify(stats)


# ============================================================
# CERTIFICATE ISSUANCE
# ============================================================

CERTS_LEDGER = os.path.join(os.path.dirname(__file__), "certificates.json")


def _load_certs():
    if mongo_enabled:
        certs = []
        for c in db.certificates.find():
            c.pop("_id", None)
            certs.append(c)
        return certs
    if os.path.exists(CERTS_LEDGER):
        with open(CERTS_LEDGER, "r") as f:
            return json.load(f)
    return []


def _save_certs(certs):
    if mongo_enabled:
        for c in certs:
            db.certificates.update_one({"cert_id": c["cert_id"]}, {"$set": c}, upsert=True)
        return
    with open(CERTS_LEDGER, "w") as f:
        json.dump(certs, f, indent=2)



@app.route("/api/certificates/validate-file", methods=["POST"])
@jwt_required()
def validate_certificate_file():
    """OCR the uploaded certificate file and compare extracted fields to form inputs."""
    if "file" not in request.files:
        return jsonify({"error": "Certificate file is required"}), 400

    file = request.files["file"]
    file_bytes = file.read()

    form_fields = {
        "student_name": request.form.get("student_name", "").strip(),
        "register_number": request.form.get("register_number", "").strip(),
        "degree": request.form.get("degree", "").strip(),
        "certificate_id": request.form.get("cert_id", "").strip(),
        "issue_date": request.form.get("issue_date", "").strip(),
    }

    try:
        from rapidfuzz import fuzz

        img = engine.load_image_cv(file_bytes, from_bytes=True)
        reader = engine.get_ocr_reader()
        ocr_result = engine.run_ocr_with_fallback(img, reader)
        extracted = engine.extract_fields(ocr_result["raw_text"])
        raw_text_lower = ocr_result["raw_text"].lower()

        mismatches = []
        matches = []

        # Compare student name (fuzzy)
        if form_fields["student_name"]:
            ocr_name = extracted.get("student_name") or ""
            if ocr_name:
                score = fuzz.token_sort_ratio(
                    form_fields["student_name"].lower(), ocr_name.lower()
                )
                if score >= 70:
                    matches.append({
                        "field": "Student Name",
                        "form_value": form_fields["student_name"],
                        "ocr_value": ocr_name,
                        "score": score,
                    })
                else:
                    mismatches.append({
                        "field": "Student Name",
                        "form_value": form_fields["student_name"],
                        "ocr_value": ocr_name,
                        "score": score,
                        "message": f"Name on certificate '{ocr_name}' does not match form input '{form_fields['student_name']}'"
                    })
            else:
                # Name not detected by OCR — check raw text
                if form_fields["student_name"].lower() in raw_text_lower:
                    matches.append({
                        "field": "Student Name",
                        "form_value": form_fields["student_name"],
                        "ocr_value": "(found in text)",
                        "score": 100,
                    })
                else:
                    mismatches.append({
                        "field": "Student Name",
                        "form_value": form_fields["student_name"],
                        "ocr_value": "Not detected",
                        "score": 0,
                        "message": f"Student name '{form_fields['student_name']}' was not found on the certificate"
                    })

        # Compare register number (exact substring match)
        if form_fields["register_number"]:
            ocr_reg = extracted.get("register_number") or ""
            form_reg = form_fields["register_number"].lower().replace("-", "").replace("/", "")
            if ocr_reg:
                ocr_reg_clean = ocr_reg.lower().replace("-", "").replace("/", "")
                if form_reg == ocr_reg_clean or form_reg in ocr_reg_clean or ocr_reg_clean in form_reg:
                    matches.append({
                        "field": "Register Number",
                        "form_value": form_fields["register_number"],
                        "ocr_value": ocr_reg,
                        "score": 100,
                    })
                else:
                    mismatches.append({
                        "field": "Register Number",
                        "form_value": form_fields["register_number"],
                        "ocr_value": ocr_reg,
                        "score": 0,
                        "message": f"Register number on certificate '{ocr_reg}' does not match '{form_fields['register_number']}'"
                    })
            elif form_reg in raw_text_lower.replace("-", "").replace("/", ""):
                matches.append({
                    "field": "Register Number",
                    "form_value": form_fields["register_number"],
                    "ocr_value": "(found in text)",
                    "score": 100,
                })
            else:
                mismatches.append({
                    "field": "Register Number",
                    "form_value": form_fields["register_number"],
                    "ocr_value": "Not detected",
                    "score": 0,
                    "message": f"Register number '{form_fields['register_number']}' was not found on the certificate"
                })

        # Compare degree (fuzzy)
        if form_fields["degree"]:
            ocr_deg = extracted.get("degree") or ""
            if ocr_deg:
                score = fuzz.token_sort_ratio(
                    form_fields["degree"].lower(), ocr_deg.lower()
                )
                if score >= 50:
                    matches.append({
                        "field": "Degree",
                        "form_value": form_fields["degree"],
                        "ocr_value": ocr_deg,
                        "score": score,
                    })
                else:
                    mismatches.append({
                        "field": "Degree",
                        "form_value": form_fields["degree"],
                        "ocr_value": ocr_deg,
                        "score": score,
                        "message": f"Degree on certificate '{ocr_deg}' does not match '{form_fields['degree']}'"
                    })
            elif form_fields["degree"].lower() in raw_text_lower:
                matches.append({
                    "field": "Degree",
                    "form_value": form_fields["degree"],
                    "ocr_value": "(found in text)",
                    "score": 100,
                })

        valid = len(mismatches) == 0

        return jsonify({
            "valid": valid,
            "matches": matches,
            "mismatches": mismatches,
            "ocr_confidence": round(ocr_result["avg_confidence"], 1),
            "extracted_fields": {
                "student_name": extracted.get("student_name"),
                "register_number": extracted.get("register_number"),
                "degree": extracted.get("degree"),
                "issue_date": extracted.get("issue_date"),
                "certificate_id": extracted.get("certificate_id"),
            },
        })

    except Exception as e:
        logger.exception("Certificate validation failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/certificates/issue", methods=["POST"])
@jwt_required()
def issue_certificate():
    """Issue a new certificate: hash file, upload to IPFS, record on blockchain."""
    claims = get_jwt()
    username = get_jwt_identity()
    role = claims.get("role", "")

    if role != "institution":
        return jsonify({"error": "Only institutions can issue certificates"}), 403

    # Get form fields
    cert_id = request.form.get("cert_id", "").strip()
    student_name = request.form.get("student_name", "").strip()
    degree = request.form.get("degree", "").strip()
    register_number = request.form.get("register_number", "").strip()
    issue_date = request.form.get("issue_date", "").strip()

    if not cert_id or not student_name:
        return jsonify({"error": "cert_id and student_name are required"}), 400

    # Check for duplicate cert_id
    existing_certs = _load_certs()
    if any(c["cert_id"] == cert_id for c in existing_certs):
        return jsonify({"error": f"Certificate ID '{cert_id}' already exists. Use a unique ID."}), 409

    if "file" not in request.files:
        return jsonify({"error": "Certificate file is required"}), 400

    file = request.files["file"]
    file_bytes = file.read()

    try:
        # 1. Compute hashes (same as engine)
        file_hash = engine.compute_file_hash(file_bytes)
        fields = {
            "student_name": student_name,
            "register_number": register_number,
            "certificate_id": cert_id,
            "degree": degree,
            "issue_date": issue_date,
        }
        content_hash = engine.compute_content_hash(fields)

        file_hash_bytes32 = "0x" + file_hash
        content_hash_bytes32 = "0x" + content_hash

        # 2. Upload to IPFS via Pinata (if PINATA_JWT is set)
        ipfs_cid = ""
        pinata_jwt = os.environ.get("PINATA_JWT", "")
        if pinata_jwt:
            import requests as req
            tmp_path = os.path.join(UPLOAD_DIR, f"issue_{cert_id}_{int(time.time())}_{file.filename}")
            with open(tmp_path, "wb") as tf:
                tf.write(file_bytes)
            try:
                with open(tmp_path, "rb") as tf:
                    resp = req.post(
                        "https://uploads.pinata.cloud/v3/files",
                        headers={"Authorization": f"Bearer {pinata_jwt}"},
                        files={"file": (file.filename, tf)},
                        data={"network": "public"},
                        timeout=60,
                    )
                if resp.status_code == 200:
                    ipfs_cid = resp.json().get("data", {}).get("cid", "")
                else:
                    logger.warning(f"Pinata upload failed: {resp.status_code} {resp.text[:200]}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            logger.warning("PINATA_JWT not set — skipping IPFS upload")

        # 3. Record on blockchain (if PRIVATE_KEY is set)
        tx_hash = ""
        private_key = os.environ.get("PRIVATE_KEY", "")
        rpc_url = os.environ.get("SEPOLIA_RPC_URL", "")

        if private_key and rpc_url:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                acct = w3.eth.account.from_key(private_key)

                issue_abi = [
                    {
                        "inputs": [
                            {"internalType": "string", "name": "certId", "type": "string"},
                            {"internalType": "string", "name": "ipfsCID", "type": "string"},
                            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
                            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
                        ],
                        "name": "issueCertificate",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function",
                    }
                ]

                contract = w3.eth.contract(
                    address=w3.to_checksum_address(engine.CONTRACT_ADDRESS),
                    abi=issue_abi,
                )

                nonce = w3.eth.get_transaction_count(acct.address)
                tx = contract.functions.issueCertificate(
                    cert_id,
                    ipfs_cid or "",
                    bytes.fromhex(file_hash),
                    bytes.fromhex(content_hash),
                ).build_transaction({
                    "from": acct.address,
                    "nonce": nonce,
                    "gasPrice": w3.eth.gas_price,
                    "chainId": w3.eth.chain_id,
                })

                signed = w3.eth.account.sign_transaction(tx, private_key)
                sent = w3.eth.send_raw_transaction(signed.raw_transaction)
                tx_hash = sent.hex()
                logger.info(f"Blockchain TX sent: {tx_hash}")

                # Wait for confirmation (up to 120s)
                receipt = w3.eth.wait_for_transaction_receipt(sent, timeout=120)
                logger.info(f"Blockchain TX confirmed in block {receipt['blockNumber']}")
            except Exception as e:
                logger.exception("Blockchain issuance failed")
                # Continue — save locally even if chain fails
                tx_hash = f"FAILED: {str(e)[:100]}"
        else:
            logger.warning("PRIVATE_KEY or SEPOLIA_RPC_URL not set — skipping blockchain")

        # 4. Save file permanently for download and save to local ledger
        ext = os.path.splitext(file.filename)[1] or ".png"
        stored_file_name = f"{cert_id}{ext}"
        try:
            with open(os.path.join(UPLOAD_DIR, stored_file_name), "wb") as sf:
                sf.write(file_bytes)
        except Exception as fe:
            logger.warning(f"Could not save file to disk: {fe}")
            stored_file_name = ""

        # 5. Automatically generate or link student credentials
        student_creds = _ensure_student_credentials(
            student_name=student_name,
            register_number=register_number,
            institution_username=username,
        )

        certs = _load_certs()
        cert_record = {
            "cert_id": cert_id,
            "student_name": student_name,
            "student_username": student_creds["username"],
            "degree": degree,
            "register_number": register_number,
            "issue_date": issue_date,
            "file_name": stored_file_name,
            "file_hash": file_hash_bytes32,
            "content_hash": content_hash_bytes32,
            "ipfs_cid": ipfs_cid,
            "tx_hash": tx_hash,
            "issued_by": username,
            "issued_at": datetime.now().isoformat(),
            "status": "active",
        }
        certs.append(cert_record)
        _save_certs(certs)

        return jsonify({
            "message": "Certificate issued successfully",
            "certificate": cert_record,
            "student_credentials": student_creds,
        }), 201

    except Exception as e:
        logger.exception("Certificate issuance failed")
        return jsonify({"error": str(e)}), 500


# ============================================================
# CERTIFICATE LISTING & DOWNLOAD
# ============================================================

@app.route("/api/certificates", methods=["GET"])
@jwt_required()
def list_certificates():
    """List issued certificates: institutions see own, students see ONLY their own, admin sees all."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")

    certs = _load_certs()

    # Institutions see only their own; admins see all; students see only their own
    if role == "institution":
        certs = [c for c in certs if c.get("issued_by") == username]
    elif role == "student":
        users = _load_users()
        student_user = users.get(username, {})
        student_reg = student_user.get("register_number", "").strip().lower()
        student_name = student_user.get("full_name", "").strip().lower()
        certs = [
            c for c in certs
            if (student_reg and student_reg == c.get("register_number", "").strip().lower())
            or (student_name and student_name == c.get("student_name", "").strip().lower())
            or c.get("student_username") == username
        ]

    # Search filter
    search = request.args.get("search", "").strip().lower()
    if search:
        certs = [c for c in certs if
                 search in c.get("cert_id", "").lower() or
                 search in c.get("student_name", "").lower() or
                 search in c.get("register_number", "").lower()]

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    total = len(certs)
    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        "certificates": list(reversed(certs))[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/certificates/<cert_id>", methods=["GET"])
@jwt_required()
def get_certificate(cert_id):
    """Get a single certificate by ID. Students can only get their own."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")

    certs = _load_certs()
    cert = next((c for c in certs if c["cert_id"] == cert_id), None)
    if not cert:
        return jsonify({"error": "Certificate not found"}), 404

    if role == "student":
        users = _load_users()
        student_user = users.get(username, {})
        student_reg = student_user.get("register_number", "").strip().lower()
        student_name = student_user.get("full_name", "").strip().lower()
        is_owner = (
            (student_reg and student_reg == cert.get("register_number", "").strip().lower())
            or (student_name and student_name == cert.get("student_name", "").strip().lower())
            or cert.get("student_username") == username
        )
        if not is_owner:
            return jsonify({"error": "Unauthorized: You can only view your own certificate"}), 403

    return jsonify(cert)


def _generate_certificate_pdf(cert):
    """Generate an official academic certificate PDF document when raw file is missing."""
    try:
        from PIL import Image, ImageDraw
        W, H = 1600, 1130
        img = Image.new('RGB', (W, H), color='#FDFAF5')
        draw = ImageDraw.Draw(img)

        # Decorative borders
        draw.rectangle([(25, 25), (W - 25, H - 25)], outline='#1E3A8A', width=10)
        draw.rectangle([(40, 40), (W - 40, H - 40)], outline='#D97706', width=4)
        draw.rectangle([(48, 48), (W - 48, H - 48)], outline='#1E3A8A', width=1)

        # University header
        inst = (cert.get('issued_by') or 'UNIVERSITY').upper()
        draw.text((W // 2, 130), inst, fill='#1E3A8A', anchor='mm')
        draw.text((W // 2, 180), 'OFFICIAL ACADEMIC CREDENTIAL', fill='#D97706', anchor='mm')

        # Title
        draw.text((W // 2, 280), 'CERTIFICATE OF EXCELLENCE', fill='#111827', anchor='mm')
        draw.text((W // 2, 340), 'This is to certify that', fill='#4B5563', anchor='mm')

        # Student Name
        student = (cert.get('student_name') or 'Student').upper()
        draw.text((W // 2, 430), student, fill='#1E3A8A', anchor='mm')
        draw.line([(W // 2 - 250, 470), (W // 2 + 250, 470)], fill='#D97706', width=2)

        # Register Number
        reg = cert.get('register_number', '')
        if reg:
            draw.text((W // 2, 510), f'Register Number: {reg}', fill='#374151', anchor='mm')

        # Degree
        degree = cert.get('degree', 'Bachelor of Technology')
        draw.text((W // 2, 590), 'has successfully demonstrated required proficiency in', fill='#4B5563', anchor='mm')
        draw.text((W // 2, 650), f'Degree of {degree}', fill='#1E3A8A', anchor='mm')

        # Issue Date
        date_str = cert.get('issue_date', '2026-10-01')
        draw.text((W // 2, 720), f'Awarded on: {date_str}', fill='#374151', anchor='mm')

        # Signatures
        draw.line([(250, 930), (550, 930)], fill='#9CA3AF', width=2)
        draw.text((400, 955), 'Dean of Academic Affairs', fill='#4B5563', anchor='mm')

        draw.line([(W - 550, 930), (W - 250, 930)], fill='#9CA3AF', width=2)
        draw.text((W - 400, 955), 'Registrar / Controller of Examinations', fill='#4B5563', anchor='mm')

        # Tamper-proof verification footer
        cert_id = cert.get('cert_id', '')
        fhash = str(cert.get('file_hash', ''))[:36]
        draw.rectangle([(60, 1010), (W - 60, 1070)], fill='#F3F4F6', outline='#E5E7EB', width=1)
        draw.text((W // 2, 1030), f'Cert ID: {cert_id}  |  Secured by CertVerify Blockchain Ledger', fill='#1F2937', anchor='mm')
        draw.text((W // 2, 1050), f'Tamper-proof Cryptographic Verification Hash: {fhash}...', fill='#6B7280', anchor='mm')

        gen_name = f"{cert_id}.pdf"
        out_path = os.path.join(UPLOAD_DIR, gen_name)
        img.save(out_path, format='PDF', resolution=100.0)
        return gen_name
    except Exception as e:
        logger.error(f"Error generating fallback cert pdf: {e}")
        return None


@app.route("/api/certificates/<cert_id>/download", methods=["GET"])
@jwt_required()
def download_certificate(cert_id):
    """Download certificate file (PDF/Image). Accessible by student owner, issuing institution, or admin."""
    username = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")

    certs = _load_certs()
    cert = next((c for c in certs if c["cert_id"] == cert_id), None)
    if not cert:
        return jsonify({"error": "Certificate not found"}), 404

    if role == "student":
        users = _load_users()
        student_user = users.get(username, {})
        student_reg = student_user.get("register_number", "").strip().lower()
        student_name = student_user.get("full_name", "").strip().lower()
        is_owner = (
            (student_reg and student_reg == cert.get("register_number", "").strip().lower())
            or (student_name and student_name == cert.get("student_name", "").strip().lower())
            or cert.get("student_username") == username
        )
        if not is_owner:
            return jsonify({"error": "Unauthorized: You can only download your own certificate"}), 403
    elif role == "institution" and cert.get("issued_by") != username:
        return jsonify({"error": "Unauthorized: Can only download certificates issued by your institution"}), 403

    # 1. Check for recorded file_name in UPLOAD_DIR
    file_name = cert.get("file_name")
    if file_name and os.path.exists(os.path.join(UPLOAD_DIR, file_name)):
        return send_from_directory(UPLOAD_DIR, file_name, as_attachment=True, download_name=file_name)

    # 2. Check for file by cert_id prefix in UPLOAD_DIR
    for fn in os.listdir(UPLOAD_DIR):
        if fn.startswith(cert_id):
            return send_from_directory(UPLOAD_DIR, fn, as_attachment=True, download_name=fn)

    # 3. If file not on disk, fetch the authentic file from IPFS (Pinata)
    if cert.get("ipfs_cid"):
        import requests as req
        try:
            cid = cert["ipfs_cid"]
            resp = req.get(f"https://gateway.pinata.cloud/ipfs/{cid}", timeout=15)
            if resp.status_code == 200:
                ctype = resp.headers.get("Content-Type", "").lower()
                if "pdf" in ctype or resp.content[:4] == b"%PDF":
                    ext = ".pdf"
                elif "jpeg" in ctype or "jpg" in ctype or resp.content[:3] == b"\xff\xd8\xff":
                    ext = ".jpg"
                else:
                    ext = ".png"
                restored_name = f"{cert_id}{ext}"
                with open(os.path.join(UPLOAD_DIR, restored_name), "wb") as rf:
                    rf.write(resp.content)
                cert["file_name"] = restored_name
                _save_certs(certs)
                return send_from_directory(UPLOAD_DIR, restored_name, as_attachment=True, download_name=restored_name)
        except Exception as ie:
            logger.warning(f"Could not fetch from IPFS: {ie}")

    # 4. Check known project certificate files matching file_hash
    target_hash = (cert.get("file_hash") or "").lower().replace("0x", "")
    if target_hash:
        for search_dir in [PROJECT_ROOT, os.path.dirname(UPLOAD_DIR)]:
            for root, _, files in os.walk(search_dir):
                if any(p in root for p in [".git", "node_modules", "dist", ".gemini"]):
                    continue
                for f in files:
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                        full_p = os.path.join(root, f)
                        try:
                            with open(full_p, "rb") as cf:
                                fbytes = cf.read()
                            if hashlib.sha256(fbytes).hexdigest().lower() == target_hash:
                                ext = os.path.splitext(f)[1]
                                restored_name = f"{cert_id}{ext}"
                                with open(os.path.join(UPLOAD_DIR, restored_name), "wb") as rf:
                                    rf.write(fbytes)
                                cert["file_name"] = restored_name
                                _save_certs(certs)
                                return send_from_directory(UPLOAD_DIR, restored_name, as_attachment=True, download_name=restored_name)
                        except Exception:
                            pass

    # 5. Last resort fallback: generate certificate document
    gen_file = _generate_certificate_pdf(cert)
    if gen_file and os.path.exists(os.path.join(UPLOAD_DIR, gen_file)):
        return send_from_directory(UPLOAD_DIR, gen_file, as_attachment=True, download_name=f"{cert_id}.pdf")

    return jsonify({"error": "Certificate file not found on server"}), 404


@app.route("/api/certificates/<cert_id>/revoke", methods=["POST"])
@jwt_required()
def revoke_certificate(cert_id):
    """Revoke a certificate (requires institution or admin role)."""
    claims = get_jwt()
    username = get_jwt_identity()
    role = claims.get("role", "")

    if role not in ("institution", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    certs = _load_certs()
    cert = next((c for c in certs if c["cert_id"] == cert_id), None)
    if not cert:
        return jsonify({"error": "Certificate not found"}), 404

    if role == "institution" and cert.get("issued_by") != username:
        return jsonify({"error": "Can only revoke certificates you issued"}), 403

    # Revoke on blockchain
    private_key = os.environ.get("PRIVATE_KEY", "")
    rpc_url = os.environ.get("SEPOLIA_RPC_URL", "")

    if private_key and rpc_url:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            acct = w3.eth.account.from_key(private_key)

            revoke_abi = [
                {
                    "inputs": [{"internalType": "string", "name": "certId", "type": "string"}],
                    "name": "revokeCertificate",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function",
                }
            ]
            contract = w3.eth.contract(
                address=w3.to_checksum_address(engine.CONTRACT_ADDRESS),
                abi=revoke_abi,
            )

            nonce = w3.eth.get_transaction_count(acct.address)
            tx = contract.functions.revokeCertificate(cert_id).build_transaction({
                "from": acct.address,
                "nonce": nonce,
                "gasPrice": w3.eth.gas_price,
                "chainId": w3.eth.chain_id,
            })

            signed = w3.eth.account.sign_transaction(tx, private_key)
            sent = w3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info(f"Revoke TX sent: {sent.hex()}")
            w3.eth.wait_for_transaction_receipt(sent, timeout=120)
        except Exception as e:
            logger.exception("Blockchain revocation failed")
            return jsonify({"error": "Blockchain revocation failed: " + str(e)}), 500

    # Update local DB
    cert["status"] = "revoked"
    _save_certs(certs)
    
    return jsonify({"message": "Certificate revoked successfully", "cert_id": cert_id})


# ============================================================
# QR CODE GENERATION
# ============================================================

@app.route("/api/qr/<cert_id>", methods=["GET"])
def generate_qr(cert_id):
    """Generate a QR code image for a certificate verification URL."""
    try:
        import qrcode
    except ImportError:
        import subprocess as sp
        sp.run([sys.executable, "-m", "pip", "install", "qrcode[pil]"], capture_output=True)
        import qrcode

    frontend_url = request.args.get("base_url", "http://localhost:5173")
    verify_url = f"{frontend_url}/verify?cert_id={cert_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#6366F1", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    """Public health check endpoint for monitoring."""
    model_path_resolved = os.path.join(BLOCKCHAIN_DIR, engine.MODEL_PATH)
    model_exists = os.path.exists(model_path_resolved)
    env_ok = bool(os.environ.get("SEPOLIA_RPC_URL"))
    ipfs_configured = bool(os.environ.get("PINATA_JWT"))
    return jsonify({
        "status": "ok",
        "model_loaded": model_exists,
        "blockchain_configured": env_ok,
        "ipfs_configured": ipfs_configured,
        "mongo_enabled": mongo_enabled,
        "engine_version": "v3.0",
        "timestamp": datetime.now().isoformat(),
    })


# ============================================================
# SERVE FRONTEND (production)
# ============================================================

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the React frontend in production."""
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    elif os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"error": "Frontend not built. Run 'npm run build' in the frontend directory."}), 404


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Final Backend on port {port}")
    logger.info(f"Engine directory: {BLOCKCHAIN_DIR}")
    logger.info(f"Model path: {os.path.join(BLOCKCHAIN_DIR, engine.MODEL_PATH)}")

    # Pre-load the OCR model on startup
    logger.info("Pre-loading EasyOCR model...")
    engine.get_ocr_reader()
    logger.info("EasyOCR model ready.")

    socketio.run(app, host="0.0.0.0", port=port, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
