from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class PatientVital(Base):
    __tablename__ = "patient_vitals"

    id            = Column(Integer, primary_key=True, index=True)
    patient_id    = Column(String(20), nullable=False, index=True)
    heart_rate    = Column(Float, nullable=False)   # bpm
    spo2          = Column(Float, nullable=False)   # %
    systolic_bp   = Column(Float, nullable=False)   # mmHg
    diastolic_bp  = Column(Float, nullable=False)   # mmHg
    temperature   = Column(Float, nullable=False)   # °C
    timestamp     = Column(DateTime, default=datetime.utcnow, index=True)

    anomaly_log   = relationship("AnomalyLog", back_populates="vital", uselist=False)

    def to_dict(self):
        return {
            "id":           self.id,
            "patient_id":   self.patient_id,
            "heart_rate":   self.heart_rate,
            "spo2":         self.spo2,
            "systolic_bp":  self.systolic_bp,
            "diastolic_bp": self.diastolic_bp,
            "temperature":  self.temperature,
            "timestamp":    self.timestamp.isoformat() if self.timestamp else None,
        }


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id             = Column(Integer, primary_key=True, index=True)
    vital_id       = Column(Integer, ForeignKey("patient_vitals.id"), nullable=False)
    anomaly_score  = Column(Float, nullable=False)
    severity       = Column(String(10), nullable=False)   # LOW/MEDIUM/HIGH/CRITICAL
    is_anomaly     = Column(Boolean, default=False)
    alerted        = Column(Boolean, default=False)
    notes          = Column(Text, default="")
    timestamp      = Column(DateTime, default=datetime.utcnow, index=True)

    vital          = relationship("PatientVital", back_populates="anomaly_log")

    def to_dict(self):
        v = self.vital
        return {
            "id":            self.id,
            "vital_id":      self.vital_id,
            "patient_id":    v.patient_id if v else None,
            "heart_rate":    v.heart_rate if v else None,
            "spo2":          v.spo2 if v else None,
            "systolic_bp":   v.systolic_bp if v else None,
            "diastolic_bp":   v.diastolic_bp if v else None,
            "temperature":   v.temperature if v else None,
            "anomaly_score": round(self.anomaly_score, 4),
            "severity":      self.severity,
            "is_anomaly":    self.is_anomaly,
            "alerted":       self.alerted,
            "notes":         self.notes,
            "timestamp":     self.timestamp.isoformat() if self.timestamp else None,
        }


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
