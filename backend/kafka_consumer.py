"""
Simulated Kafka Consumer
Reads messages from the shared in-memory queue, runs each through the ML
anomaly detector, persists data to SQLite, and emits SocketIO events for
real-time dashboard updates.
"""
import threading
from datetime import datetime

from kafka_producer import kafka_queue
from ml.anomaly_detector import detector
from alerts import send_alert


def _consumer_loop(app, socketio, db_factory):
    print("[Kafka Consumer] Started – consuming topic 'patient_vitals'")
    from db import PatientVital, AnomalyLog

    with app.app_context():
        while True:
            try:
                msg = kafka_queue.get(timeout=5)
            except Exception:
                continue

            try:
                db = db_factory()

                # 1. Persist raw vital signs
                vital = PatientVital(
                    patient_id   = msg["patient_id"],
                    heart_rate   = msg["heart_rate"],
                    spo2         = msg["spo2"],
                    systolic_bp  = msg["systolic_bp"],
                    diastolic_bp = msg["diastolic_bp"],
                    temperature  = msg["temperature"],
                    timestamp    = datetime.utcnow(),
                )
                db.add(vital)
                db.flush()

                # 2. Run ML anomaly detection
                result = detector.predict({
                    "heart_rate":   vital.heart_rate,
                    "spo2":         vital.spo2,
                    "systolic_bp":  vital.systolic_bp,
                    "diastolic_bp": vital.diastolic_bp,
                    "temperature":  vital.temperature,
                })

                # 3. Persist anomaly log
                log = AnomalyLog(
                    vital_id      = vital.id,
                    anomaly_score = result["anomaly_score"],
                    severity      = result["severity"],
                    is_anomaly    = result["is_anomaly"],
                    alerted       = False,
                    notes         = result["notes"],
                    timestamp     = datetime.utcnow(),
                )
                db.add(log)

                # 4. Send alert for HIGH / CRITICAL
                if result["is_anomaly"] and result["severity"] in ("HIGH", "CRITICAL"):
                    send_alert(vital.patient_id, result["severity"], msg, result["notes"])
                    log.alerted = True

                db.commit()

                # 5. Emit SocketIO event with anomaly data
                payload = {
                    "patient_id":    vital.patient_id,
                    "heart_rate":    vital.heart_rate,
                    "spo2":          vital.spo2,
                    "systolic_bp":   vital.systolic_bp,
                    "diastolic_bp":  vital.diastolic_bp,
                    "temperature":   vital.temperature,
                    "anomaly_score": round(result["anomaly_score"], 4),
                    "severity":      result["severity"],
                    "is_anomaly":    result["is_anomaly"],
                    "notes":         result["notes"],
                    "timestamp":     vital.timestamp.isoformat(),
                }
                socketio.emit("vital_update", payload)
                if result["is_anomaly"]:
                    socketio.emit("new_anomaly", payload)

                db.close()

            except Exception as e:
                print(f"[Kafka Consumer] Processing error: {e}")
                try:
                    db.rollback()
                    db.close()
                except Exception:
                    pass


def start_consumer(app, socketio, db_factory):
    t = threading.Thread(
        target=_consumer_loop,
        args=(app, socketio, db_factory),
        daemon=True,
        name="KafkaConsumer",
    )
    t.start()
    return t
