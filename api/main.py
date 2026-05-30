"""
main.py — FastAPI Server untuk ML-ETA
======================================
GPS Tracker Bus Sekolah — ETA Prediction Service

Endpoints:
  GET  /              → health check
  GET  /model-info    → info model & performa
  POST /predict       → prediksi ETA dari koordinat GPS
  GET  /docs          → Swagger UI
"""

import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

# Pastikan folder api/ ada di PATH pencarian Python
sys.path.append(str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from inference import predict_eta, get_feature_info

load_dotenv()

# ── Inisialisasi FastAPI ──────────────────────────────────────────────────────
app = FastAPI(
    title="🚌 ML-ETA Bus Sekolah API",
    description=(
        "REST API untuk prediksi Estimated Time of Arrival (ETA) "
        "GPS Tracker Bus Sekolah menggunakan Machine Learning (LightGBM)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for production compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schema Request / Response ─────────────────────────────────────────────────
class ETARequest(BaseModel):
    start_lat:      float = Field(..., description="Latitude titik keberangkatan", example=41.149)
    start_lon:      float = Field(..., description="Longitude titik keberangkatan", example=-8.610)
    end_lat:        float = Field(..., description="Latitude titik tujuan", example=41.157)
    end_lon:        float = Field(..., description="Longitude titik tujuan", example=-8.650)
    departure_time: Optional[str] = Field(
        None,
        description="Waktu berangkat ISO8601 (default: sekarang)",
        example="2024-09-02T07:00:00"
    )
    distance_km:    Optional[float] = Field(
        None,
        description="Jarak aktual (km). Jika kosong, dihitung otomatis.",
        example=5.1
    )
    call_type:      str = Field("C", description="Tipe perjalanan: A, B, atau C", example="C")

    # Konteks tambahan
    bus_id:         Optional[str] = Field(None, description="ID Bus", example="BUS-001")
    route_name:     Optional[str] = Field(None, description="Nama Rute", example="Rute Sekolah A")
    student_count:  Optional[int] = Field(None, description="Jumlah siswa di bus", example=25)


class ETAResponse(BaseModel):
    success:          bool
    eta_minutes:      float
    eta_seconds:      int
    estimated_arrival: str
    distance_km:      float
    straight_dist_km: float
    departure_time:   str
    message:          str


# ── Helper ────────────────────────────────────────────────────────────────────
def parse_departure(departure_str: Optional[str]) -> datetime:
    if departure_str is None:
        return datetime.now()
    try:
        return datetime.fromisoformat(departure_str)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Format departure_time tidak valid. Gunakan ISO8601, contoh: 2024-09-02T07:00:00"
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "ML-ETA Bus Sekolah",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/model-info", tags=["Model"])
def model_info():
    """Informasi model yang sedang digunakan beserta performa di test set."""
    try:
        info = get_feature_info()
        return {
            "model_type":   "LightGBM (Tuned with Optuna)",
            "test_mae":     info.get("test_mae"),
            "test_rmse":    info.get("test_rmse"),
            "test_r2":      info.get("test_r2"),
            "n_features":   len(info.get("all_features", [])),
            "features":     info.get("all_features"),
            "target":       info.get("target"),
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model belum tersedia."
        )


@app.post("/predict", response_model=ETAResponse, tags=["Prediction"])
def predict(req: ETARequest):
    """
    Prediksi ETA berdasarkan koordinat GPS asal & tujuan.
    
    Digunakan oleh Laravel backend untuk mendapatkan estimasi waktu tiba bus.
    """
    try:
        departure = parse_departure(req.departure_time)
        result    = predict_eta(
            start_lat      = req.start_lat,
            start_lon      = req.start_lon,
            end_lat        = req.end_lat,
            end_lon        = req.end_lon,
            departure_time = departure,
            distance_km    = req.distance_km,
            call_type      = req.call_type,
        )
        return ETAResponse(
            success           = True,
            message           = f"ETA berhasil diprediksi. Bus diperkirakan tiba pukul {result['estimated_arrival']}.",
            **result
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {str(e)}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8001)),
        reload=True,
    )
