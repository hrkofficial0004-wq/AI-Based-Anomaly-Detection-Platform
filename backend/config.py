import os
from dotenv import load_dotenv

load_dotenv()

# Database - SQLite in an absolute path for robustness
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'data', 'healthcare.db')}")

# Kafka simulation settings
KAFKA_TOPIC = "patient_vitals"
PRODUCER_INTERVAL_SEC = 2.0   # seconds between synthetic readings

# Email alerts (mock by default – set SMTP_* env vars for real email)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_FROM = os.getenv("ALERT_FROM", "alerts@healthcare.ai")
ALERT_TO = os.getenv("ALERT_TO", "doctor@hospital.com")

# Anomaly severity thresholds (based on Isolation Forest decision score)
SEVERITY_THRESHOLDS = {
    "CRITICAL": 0.65,
    "HIGH":     0.45,
    "MEDIUM":   0.25,
}

# Patient IDs used by the synthetic producer
PATIENT_IDS = ["P001", "P002", "P003", "P004", "P005"]

# Flask
SECRET_KEY = os.getenv("SECRET_KEY", "healthcare-anomaly-key-2024")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
