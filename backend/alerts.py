"""
Alert module – sends email notifications for HIGH/CRITICAL anomalies.
Falls back to console logging when SMTP is not configured.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_FROM, ALERT_TO

logger = logging.getLogger("alerts")


def send_alert(patient_id: str, severity: str, vitals: dict, notes: str = ""):
    subject = f"[{severity}] Anomaly Detected – Patient {patient_id}"
    body = (
        f"HEALTHCARE ANOMALY ALERT\n"
        f"{'='*45}\n"
        f"Patient ID  : {patient_id}\n"
        f"Severity    : {severity}\n"
        f"Heart Rate  : {vitals.get('heart_rate', 'N/A')} bpm\n"
        f"SpO₂        : {vitals.get('spo2', 'N/A')} %\n"
        f"Blood Press : {vitals.get('systolic_bp', 'N/A')}/{vitals.get('diastolic_bp', 'N/A')} mmHg\n"
        f"Temperature : {vitals.get('temperature', 'N/A')} °C\n"
        f"Notes       : {notes}\n"
        f"{'='*45}\n"
        f"Please review the patient immediately.\n"
    )

    # Always log to console
    logger.warning(f"\n{body}")

    # Send real email only if SMTP is configured
    if not SMTP_HOST or not SMTP_USER:
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = ALERT_FROM
        msg["To"] = ALERT_TO
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())

        logger.info(f"[Alert] Email sent to {ALERT_TO} for patient {patient_id}")
    except Exception as e:
        logger.error(f"[Alert] Failed to send email: {e}")
