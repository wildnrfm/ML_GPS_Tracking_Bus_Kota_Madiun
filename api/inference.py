"""
inference.py
============
Module untuk load model dan melakukan prediksi ETA.
Digunakan oleh FastAPI endpoint.
"""

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

# Path relatif dari folder api/
BASE_DIR   = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "eta_model_best.pkl"
FEAT_PATH  = BASE_DIR / "models" / "feature_info.json"

# ── Load model satu kali saat module di-import ──────────────────────────────
_model        = None
_feature_info = None

def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model tidak ditemukan di {MODEL_PATH}. "
                "Jalankan notebook 02_modeling.ipynb terlebih dahulu."
            )
        _model = joblib.load(MODEL_PATH)
    return _model

def get_feature_info():
    global _feature_info
    if _feature_info is None:
        with open(FEAT_PATH, "r") as f:
            _feature_info = json.load(f)
    return _feature_info


# ── Helper: Haversine ────────────────────────────────────────────────────────
def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Jarak (km) antara dua titik GPS."""
    R = 6371
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ── Kategori waktu (konteks bus sekolah) ─────────────────────────────────────
def time_category(hour: int) -> str:
    if 6  <= hour < 9:  return "pagi_sekolah"
    if 9  <= hour < 12: return "pagi_siang"
    if 12 <= hour < 15: return "siang"
    if 15 <= hour < 18: return "pulang_sekolah"
    if 18 <= hour < 21: return "sore_malam"
    return "malam"


# ── Build input DataFrame dari raw request ───────────────────────────────────
def build_features(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    departure_time: datetime,
    distance_km: float | None = None,
    call_type: str = "C",
) -> pd.DataFrame:
    """
    Konversi input raw (koordinat + waktu) menjadi DataFrame
    yang siap di-predict oleh model.
    """
    straight_dist = haversine(start_lon, start_lat, end_lon, end_lat)

    # Jika jarak aktual tidak diberikan, estimasi dengan detour ratio 1.3×
    if distance_km is None:
        distance_km = straight_dist * 1.3

    hour         = departure_time.hour
    day_of_week  = departure_time.weekday()   # 0=Senin
    month        = departure_time.month
    is_weekend   = int(day_of_week in [5, 6])
    is_rush_hour = int(hour in [7, 8, 9, 17, 18, 19])
    detour_ratio = distance_km / (straight_dist + 1e-9)

    return pd.DataFrame([{
        "start_lat":        start_lat,
        "start_lon":        start_lon,
        "end_lat":          end_lat,
        "end_lon":          end_lon,
        "straight_dist_km": straight_dist,
        "distance_km":      distance_km,
        "detour_ratio":     detour_ratio,
        "hour_sin":         np.sin(2 * np.pi * hour / 24),
        "hour_cos":         np.cos(2 * np.pi * hour / 24),
        "dow_sin":          np.sin(2 * np.pi * day_of_week / 7),
        "dow_cos":          np.cos(2 * np.pi * day_of_week / 7),
        "is_weekend":       is_weekend,
        "is_rush_hour":     is_rush_hour,
        "month":            month,
        "time_category":    time_category(hour),
        "CALL_TYPE":        call_type,
    }])


# ── Fungsi prediksi utama ─────────────────────────────────────────────────────
def predict_eta(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    departure_time: datetime | None = None,
    distance_km: float | None = None,
    call_type: str = "C",
) -> dict:
    """
    Prediksi ETA dan kembalikan result lengkap.

    Returns:
        dict dengan:
        - eta_minutes        : durasi estimasi (float)
        - eta_seconds        : durasi estimasi dalam detik (int)
        - estimated_arrival  : string jam tiba "HH:MM"
        - distance_km        : jarak yang digunakan
        - straight_dist_km   : jarak garis lurus
        - departure_time     : waktu berangkat (ISO string)
    """
    if departure_time is None:
        departure_time = datetime.now()

    model    = get_model()
    features = build_features(
        start_lat, start_lon,
        end_lat, end_lon,
        departure_time,
        distance_km,
        call_type,
    )

    eta_minutes = float(model.predict(features)[0])
    eta_seconds = int(eta_minutes * 60)
    arrival_dt  = departure_time + timedelta(minutes=eta_minutes)

    straight_dist = haversine(start_lon, start_lat, end_lon, end_lat)
    used_dist     = features["distance_km"].iloc[0]

    return {
        "eta_minutes":       round(eta_minutes, 2),
        "eta_seconds":       eta_seconds,
        "estimated_arrival": arrival_dt.strftime("%H:%M"),
        "distance_km":       round(used_dist, 3),
        "straight_dist_km":  round(straight_dist, 3),
        "departure_time":    departure_time.isoformat(),
    }
