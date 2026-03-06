"""
Anomaly logs API routes
GET /api/anomalies  – fetch anomaly log entries (filterable by severity/patient)
GET /api/stats      – KPI summary stats for the dashboard
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc

from db import SessionLocal, AnomalyLog, PatientVital

anomalies_bp = Blueprint("anomalies", __name__)


@anomalies_bp.route("/api/anomalies", methods=["GET"])
def get_anomalies():
    severity   = request.args.get("severity")
    patient_id = request.args.get("patient_id")
    only_anom  = request.args.get("anomalies_only", "false").lower() == "true"
    limit      = min(int(request.args.get("limit", 100)), 500)

    db = SessionLocal()
    try:
        q = db.query(AnomalyLog).join(PatientVital)
        if severity:
            q = q.filter(AnomalyLog.severity == severity.upper())
        if patient_id:
            q = q.filter(PatientVital.patient_id == patient_id)
        if only_anom:
            q = q.filter(AnomalyLog.is_anomaly == True)
        logs = q.order_by(desc(AnomalyLog.timestamp)).limit(limit).all()
        return jsonify([log.to_dict() for log in logs])
    finally:
        db.close()


@anomalies_bp.route("/api/stats", methods=["GET"])
def get_stats():
    db = SessionLocal()
    try:
        total_vitals   = db.query(func.count(PatientVital.id)).scalar() or 0
        total_anomalies = db.query(func.count(AnomalyLog.id)).filter(AnomalyLog.is_anomaly == True).scalar() or 0
        anomaly_rate   = round((total_anomalies / total_vitals * 100) if total_vitals else 0, 2)

        by_severity = {}
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            count = db.query(func.count(AnomalyLog.id)).filter(
                AnomalyLog.is_anomaly == True,
                AnomalyLog.severity == sev
            ).scalar() or 0
            by_severity[sev] = count

        # Recent trend: anomaly count per patient
        per_patient = (
            db.query(PatientVital.patient_id, func.count(AnomalyLog.id).label("count"))
            .join(AnomalyLog, AnomalyLog.vital_id == PatientVital.id)
            .filter(AnomalyLog.is_anomaly == True)
            .group_by(PatientVital.patient_id)
            .all()
        )

        return jsonify({
            "total_vitals":    total_vitals,
            "total_anomalies": total_anomalies,
            "anomaly_rate":    anomaly_rate,
            "by_severity":     by_severity,
            "per_patient":     {r.patient_id: r.count for r in per_patient},
        })
    finally:
        db.close()


@anomalies_bp.route("/api/anomalies/<int:anomaly_id>/alert", methods=["POST"])
def trigger_alert(anomaly_id: int):
    """Manually trigger an email alert for a specific anomaly."""
    from alerts import send_alert
    db = SessionLocal()
    try:
        log = db.query(AnomalyLog).filter(AnomalyLog.id == anomaly_id).first()
        if not log:
            return jsonify({"error": "Anomaly not found"}), 404
        vital = log.vital
        send_alert(
            vital.patient_id, log.severity,
            {
                "heart_rate":   vital.heart_rate,
                "spo2":         vital.spo2,
                "systolic_bp":  vital.systolic_bp,
                "diastolic_bp": vital.diastolic_bp,
                "temperature":  vital.temperature,
            },
            log.notes,
        )
        log.alerted = True
        db.commit()
        return jsonify({"success": True, "message": f"Alert sent for anomaly {anomaly_id}"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
