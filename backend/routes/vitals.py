"""
Vitals API routes
POST /api/vitals  – manually submit patient vital signs
GET  /api/vitals  – fetch recent vitals (with optional patient_id filter)
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from db import SessionLocal, PatientVital, AnomalyLog
from ml.anomaly_detector import detector
from alerts import send_alert

vitals_bp = Blueprint("vitals", __name__)


@vitals_bp.route("/api/vitals", methods=["POST"])
def submit_vital():
    data = request.get_json(force=True)
    required = ["patient_id", "heart_rate", "spo2", "systolic_bp", "diastolic_bp", "temperature"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    db = SessionLocal()
    try:
        vital = PatientVital(
            patient_id   = data["patient_id"],
            heart_rate   = float(data["heart_rate"]),
            spo2         = float(data["spo2"]),
            systolic_bp  = float(data["systolic_bp"]),
            diastolic_bp = float(data["diastolic_bp"]),
            temperature  = float(data["temperature"]),
            timestamp    = datetime.utcnow(),
        )
        db.add(vital)
        db.flush()

        result = detector.predict({
            "heart_rate":   vital.heart_rate,
            "spo2":         vital.spo2,
            "systolic_bp":  vital.systolic_bp,
            "diastolic_bp": vital.diastolic_bp,
            "temperature":  vital.temperature,
        })

        log = AnomalyLog(
            vital_id      = vital.id,
            anomaly_score = result["anomaly_score"],
            severity      = result["severity"],
            is_anomaly    = result["is_anomaly"],
            notes         = result["notes"],
            timestamp     = datetime.utcnow(),
        )
        db.add(log)

        if result["is_anomaly"] and result["severity"] in ("HIGH", "CRITICAL"):
            send_alert(vital.patient_id, result["severity"], data, result["notes"])
            log.alerted = True

        db.commit()
        response = vital.to_dict()
        response.update(result)
        return jsonify(response), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@vitals_bp.route("/api/vitals", methods=["GET"])
def get_vitals():
    patient_id = request.args.get("patient_id")
    limit = min(int(request.args.get("limit", 50)), 200)

    db = SessionLocal()
    try:
        q = db.query(PatientVital)
        if patient_id:
            q = q.filter(PatientVital.patient_id == patient_id)
        vitals = q.order_by(PatientVital.timestamp.desc()).limit(limit).all()
        return jsonify([v.to_dict() for v in vitals])
    finally:
        db.close()
