"""
Flood-specific AI anomaly detection engine for an IoT hackathon.

Install:
    python -m pip install numpy scikit-learn

Expected input:
    {
        "zone": "Zone A",
        "water_level": 72.5,          # cm
        "rainfall": 45.0,             # mm/hour
        "rise_rate": 1.8              # cm/minute (optional; defaults to 0)
    }

This module detects unusual patterns. It does NOT replace a calibrated
flood-risk model or official flood warnings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
from sklearn.ensemble import IsolationForest


FEATURES = ("water_level", "rainfall", "rise_rate")

# Synthetic, illustrative ranges for the hackathon demo.
# Replace with real local sensor data before any real-world use.
MODEL: Optional[IsolationForest] = None


def generate_training_data(samples: int = 2500, seed: int = 42) -> np.ndarray:
    """Generate synthetic examples of ordinary conditions for model training."""
    if samples < 100:
        raise ValueError("Use at least 100 training samples.")

    rng = np.random.default_rng(seed)

    # Ordinary water levels are spread across low and moderate levels.
    water_level = rng.normal(loc=45.0, scale=18.0, size=samples)
    water_level = np.clip(water_level, 5.0, 95.0)

    # Most ordinary periods have little rainfall, with occasional light rain.
    rainfall = rng.gamma(shape=1.8, scale=3.0, size=samples)
    rainfall = np.clip(rainfall, 0.0, 18.0)

    # Typical short-term water-level movement is small.
    rise_rate = rng.normal(loc=0.10, scale=0.22, size=samples)
    rise_rate = np.clip(rise_rate, -0.5, 0.8)

    return np.column_stack((water_level, rainfall, rise_rate))


def train_model(
    samples: int = 2500,
    seed: int = 42,
) -> IsolationForest:
    """Train and cache the Isolation Forest model."""
    global MODEL

    training_data = generate_training_data(samples=samples, seed=seed)
    MODEL = IsolationForest(
        n_estimators=120,
        contamination=0.05,
        random_state=seed,
    )
    MODEL.fit(training_data)
    return MODEL


def _validated_features(reading: Dict[str, Any]) -> np.ndarray:
    """Validate one reading and return features in the model's expected order."""
    if not isinstance(reading, dict):
        raise ValueError("reading must be a dictionary.")

    try:
        values = np.array(
            [
                float(reading["water_level"]),
                float(reading["rainfall"]),
                float(reading.get("rise_rate", 0.0)),
            ],
            dtype=float,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Provide numeric water_level and rainfall; rise_rate is optional."
        ) from exc

    if not np.all(np.isfinite(values)):
        raise ValueError("Sensor values must be finite numbers.")

    if values[0] < 0 or values[1] < 0:
        raise ValueError("water_level and rainfall cannot be negative.")

    return values


def detect_anomaly(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect unusual sensor patterns.

    Returns a dictionary suitable for a Streamlit app or JSON API.
    `anomaly_score` is a model score, NOT a probability.
    """
    if MODEL is None:
        train_model()

    values = _validated_features(reading)
    row = values.reshape(1, -1)

    prediction = int(MODEL.predict(row)[0])
    decision_score = float(MODEL.decision_function(row)[0])
    is_anomaly = prediction == -1

    water_level, rainfall, rise_rate = values
    unusual_features = []

    # Human-readable hints for the dashboard; these do not replace the model.
    if water_level >= 80:
        unusual_features.append("high_water_level")
    if rainfall >= 35:
        unusual_features.append("heavy_rainfall")
    if rise_rate >= 1.0:
        unusual_features.append("rapidly_rising_water")

    if is_anomaly:
        status = "ANOMALY"
        message = "Unusual flood-related sensor pattern detected."
        alert_level = "WARNING" if unusual_features else "CHECK"
    else:
        status = "NORMAL"
        message = "No unusual pattern detected by the AI model."
        alert_level = "NONE"

    return {
        "zone": str(reading.get("zone", "Unknown Zone")),
        "status": status,
        "is_anomaly": is_anomaly,
        "alert_level": alert_level,
        "anomaly_score": round(decision_score, 4),
        "sensor_readings": {
            "water_level": round(float(water_level), 2),
            "rainfall": round(float(rainfall), 2),
            "rise_rate": round(float(rise_rate), 2),
        },
        "unusual_features": unusual_features,
        "message": message,
    }


def make_demo_reading(scenario: str = "normal", zone: str = "Zone A") -> Dict[str, Any]:
    """Create reproducible demo readings for normal and emergency buttons."""
    scenarios = {
        "normal": {
            "water_level": 42.0,
            "rainfall": 4.0,
            "rise_rate": 0.1,
        },
        "heavy_rain": {
            "water_level": 68.0,
            "rainfall": 65.0,
            "rise_rate": 0.6,
        },
        "rising_water": {
            "water_level": 78.0,
            "rainfall": 18.0,
            "rise_rate": 2.4,
        },
        "extreme": {
            "water_level": 96.0,
            "rainfall": 85.0,
            "rise_rate": 3.2,
        },
    }

    if scenario not in scenarios:
        raise ValueError(
            f"Unknown scenario {scenario!r}. Choose from: {', '.join(scenarios)}"
        )

    return {"zone": zone, **scenarios[scenario].copy()}


if __name__ == "__main__":
    train_model()
    print("Flood AI model trained successfully.\n")

    for scenario in ("normal", "heavy_rain", "rising_water", "extreme"):
        demo = make_demo_reading(scenario, zone="Zone A")
        result = detect_anomaly(demo)
        print(f"--- {scenario.upper()} ---")
        print(result)
        print()
