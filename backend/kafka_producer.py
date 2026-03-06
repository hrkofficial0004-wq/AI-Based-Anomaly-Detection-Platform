"""
Simulated Kafka Producer
Generates synthetic patient vital signs and pushes them to an in-memory queue,
mimicking a Kafka topic named 'patient_vitals'.
"""
import time
import random
import threading
from datetime import datetime
from queue import Queue
from config import PRODUCER_INTERVAL_SEC, PATIENT_IDS

# Shared in-memory queue (simulates Kafka broker)
kafka_queue: Queue = Queue(maxsize=500)

# Normal vital ranges
NORMAL = {
    "heart_rate":   (60, 95),
    "spo2":         (96, 100),
    "systolic_bp":  (95, 125),
    "diastolic_bp": (62, 82),
    "temperature":  (36.2, 37.3),
}

# Anomalous ranges (injected ~15% of the time)
ANOMALOUS = {
    "heart_rate":   [(30, 50), (110, 200)],
    "spo2":         [(70, 94)],
    "systolic_bp":  [(60, 88), (145, 210)],
    "diastolic_bp": [(40, 58), (90, 130)],
    "temperature":  [(32.0, 35.4), (38.2, 41.5)],
}


def _sample_vital(key: str, anomaly: bool) -> float:
    if anomaly:
        ranges = ANOMALOUS[key]
        lo, hi = random.choice(ranges)
    else:
        lo, hi = NORMAL[key]
    return round(random.uniform(lo, hi), 2)


def _generate_reading(force_anomaly: bool = False) -> dict:
    is_anomaly = force_anomaly or (random.random() < 0.15)
    patient_id = random.choice(PATIENT_IDS)
    return {
        "patient_id":   patient_id,
        "heart_rate":   _sample_vital("heart_rate",   is_anomaly),
        "spo2":         _sample_vital("spo2",         is_anomaly),
        "systolic_bp":  _sample_vital("systolic_bp",  is_anomaly),
        "diastolic_bp": _sample_vital("diastolic_bp", is_anomaly),
        "temperature":  _sample_vital("temperature",  is_anomaly),
        "timestamp":    datetime.utcnow().isoformat(),
    }


def _producer_loop():
    print("[Kafka Producer] Started – publishing to topic 'patient_vitals'")
    while True:
        try:
            msg = _generate_reading()
            kafka_queue.put(msg, timeout=1)
            time.sleep(PRODUCER_INTERVAL_SEC)
        except Exception as e:
            print(f"[Kafka Producer] Error: {e}")
            time.sleep(1)


def start_producer():
    t = threading.Thread(target=_producer_loop, daemon=True, name="KafkaProducer")
    t.start()
    return t
