from flask import Flask, request, jsonify
import hashlib
import json
import os
from datetime import datetime

app = Flask(__name__)

HASH_FILE = "/tmp/hashes.json"


# -------- Helper: load JSON --------
def load_hashes():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return json.load(f)
    return {}


# -------- Helper: save JSON --------
def save_hashes(data):
    with open(HASH_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -------- Helper: calculate SHA-256 hash of PDF --------
def calculate_hash(file_storage):
    file_bytes = file_storage.read()
    file_storage.seek(0)  # reset pointer after reading
    return hashlib.sha256(file_bytes).hexdigest()


# ============================
#       ISSUE API
# ============================
@app.route("/issue", methods=["POST"])
def issue_certificate():
    cert_id = request.form.get("cert_id")
    student_name = request.form.get("student_name")
    course = request.form.get("course")
    file = request.files.get("file")

    if not cert_id or not student_name or not course or not file:
        return jsonify({"error": "Missing fields"}), 400

    # Calculate hash
    cert_hash = calculate_hash(file)

    # Load existing certificates
    data = load_hashes()

    # Save new certificate entry
    data[cert_id] = {
        "student_name": student_name,
        "course": course,
        "certificate_hash": cert_hash,
        "issued_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_hashes(data)

    return jsonify({
        "message": "Certificate issued",
        "cert_id": cert_id,
        "hash": cert_hash
    })


# ============================
#       VERIFY API
# ============================
@app.route("/verify", methods=["POST"])
def verify_certificate():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "File missing"}), 400

    uploaded_hash = calculate_hash(file)
    data = load_hashes()

    # Find matching certificate by hash
    for cert_id, details in data.items():
        if details["certificate_hash"] == uploaded_hash:
            return jsonify({
                "status": "VALID",
                "cert_id": cert_id,
                "student_name": details["student_name"],
                "course": details["course"],
                "issued_on": details["issued_on"]
            })

    return jsonify({
        "status": "INVALID",
        "reason": "No matching certificate found"
    })


# ============================
#       LIST ALL CERTS
# ============================
@app.route("/list", methods=["GET"])
def list_certificates():
    return jsonify(load_hashes())


# ============================
#       RAW JSON
# ============================
@app.route("/data", methods=["GET"])
def get_raw_data():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read()
    return "{}"

@app.route("/", methods=["GET"])
def home():
    return {
        "message": "Certificate Verification API is running!",
        "endpoints": {
            "issue": "/issue [POST] - Issue a certificate",
            "verify": "/verify [POST] - Verify a certificate",
            "list": "/list [GET] - List all issued certificates",
            "data": "/data [GET] - View raw JSON of issued certificates"
        }
    }

# Run locally
if __name__ == "__main__":
    app.run(debug=True)
