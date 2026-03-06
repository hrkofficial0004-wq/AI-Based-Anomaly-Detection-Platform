"""
Isolation Forest–based anomaly detector.
Trained on synthetic normal ranges at startup; persisted in-memory.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from config import SEVERITY_THRESHOLDS


# Normal physiological ranges used to train the model
NORMAL_RANGES = {
    "heart_rate":   (55, 100),   # bpm
    "spo2":         (95, 100),   # %
    "systolic_bp":  (90, 130),   # mmHg
    "diastolic_bp": (60, 85),    # mmHg
    "temperature":  (36.0, 37.5),# °C
}

FEATURE_ORDER = ["heart_rate", "spo2", "systolic_bp", "diastolic_bp", "temperature"]


def _generate_training_data(n_samples: int = 5000) -> np.ndarray:
    """Generate synthetic normal vital sign data for training."""
    rng = np.random.default_rng(42)
    data = np.column_stack([
        rng.uniform(*NORMAL_RANGES[f], size=n_samples)
        for f in FEATURE_ORDER
    ])
    return data


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=150,
            contamination=0.05,
            random_state=42,
            max_samples="auto",
        )
        self._train()

    def _train(self):
        X_train = _generate_training_data()
        self.model.fit(X_train)
        print("[ML] Isolation Forest trained on synthetic normal data OK")

    def _vitals_to_array(self, vitals: dict) -> np.ndarray:
        return np.array([[vitals[f] for f in FEATURE_ORDER]])

    def predict(self, vitals: dict) -> dict:
        """
        Returns:
            {
                'anomaly_score': float (0→normal, 1→extreme anomaly),
                'is_anomaly': bool,
                'severity': 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
                'notes': str
            }
        """
        X = self._vitals_to_array(vitals)

        # decision_function: negative = anomaly, positive = normal
        raw_score = self.model.decision_function(X)[0]

        # Normalize to [0, 1] where higher = more anomalous
        # Typical range is roughly [-0.5, 0.5]; clip outside it
        normalized = float(np.clip(-raw_score + 0.5, 0.0, 1.0))

        # Convert numpy boolean scalar to standard Python boolean
        is_anomaly = bool(self.model.predict(X)[0] == -1)

        severity = "LOW"
        for sev, threshold in sorted(SEVERITY_THRESHOLDS.items(), key=lambda x: -x[1]):
            if normalized >= threshold:
                severity = sev
                break

        notes = self._generate_notes(vitals, normalized)

        return {
            "anomaly_score": normalized,
            "is_anomaly": is_anomaly,
            "severity": severity,
            "notes": notes,
        }

    def _generate_notes(self, vitals: dict, score: float) -> str:
        flags = []
        hr = vitals.get("heart_rate", 0)
        spo2 = vitals.get("spo2", 100)
        sys_bp = vitals.get("systolic_bp", 120)
        dia_bp = vitals.get("diastolic_bp", 80)
        temp = vitals.get("temperature", 37)

        if hr > 100: flags.append(f"Tachycardia ({hr:.0f} bpm)")
        elif hr < 55: flags.append(f"Bradycardia ({hr:.0f} bpm)")
        if spo2 < 95: flags.append(f"Hypoxemia (SpO2 {spo2:.1f}%)")
        if sys_bp > 140: flags.append(f"Hypertension ({sys_bp:.0f}/{dia_bp:.0f} mmHg)")
        elif sys_bp < 90: flags.append(f"Hypotension ({sys_bp:.0f}/{dia_bp:.0f} mmHg)")
        if temp > 38: flags.append(f"Fever ({temp:.1f}C)")
        elif temp < 35.5: flags.append(f"Hypothermia ({temp:.1f}C)")

        return "; ".join(flags) if flags else "Vitals within acceptable range"


# Singleton instance
detector = AnomalyDetector()
