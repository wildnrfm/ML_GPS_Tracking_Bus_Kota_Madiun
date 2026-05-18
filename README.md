# 🚌 ML-ETA — ETA Prediction untuk GPS Tracker Bus Sekolah

Modul Machine Learning untuk prediksi **Estimated Time of Arrival (ETA)**  
yang terintegrasi dengan backend Laravel dan aplikasi Flutter.

> 📖 **Panduan menjalankan** → lihat [RUN.md](./RUN.md)

---

## 📁 Struktur Folder

```
ml-eta/
├── notebooks/
│   ├── 01_eda.ipynb              ← EDA & visualisasi dataset Porto Taxi
│   └── 02_modeling.ipynb         ← Training, tuning, evaluasi, simpan model
├── api/
│   ├── main.py                   ← FastAPI server (endpoint /predict)
│   └── inference.py              ← Logic load model & prediksi
├── models/
│   ├── eta_model_best.pkl        ← Pipeline model LightGBM (hasil training)
│   └── feature_info.json         ← Metadata fitur & metrik model
├── data/
│   └── train.csv                 ← Dataset Porto Taxi (download dari Kaggle)
├── ini_nanti_ketika_saya_gabung_di_root_laravel/
│   ├── ETAController.php         ← Controller Laravel untuk endpoint ETA
│   └── ETAService.php            ← Service HTTP ke FastAPI
├── Dockerfile.fastapi            ← Docker image untuk FastAPI
├── docker-compose.yml            ← Orkestrasi Laravel + FastAPI + MySQL
├── requirements.txt              ← Dependency Python
├── .env.example                  ← Template environment variable
└── RUN.md                        ← Panduan menjalankan
```

---

## ✅ Checklist ML yang Dicakup

| # | Item | File |
|---|------|------|
| 1 | EDA & Eksplorasi Data | `notebooks/01_eda.ipynb` |
| 2 | Preprocessing + sklearn Pipeline | `notebooks/02_modeling.ipynb` |
| 3 | Train / Val / Test Split (64/16/20%) | `notebooks/02_modeling.ipynb` |
| 4 | Minimal 2 Model (Ridge + XGBoost + LightGBM) | `notebooks/02_modeling.ipynb` |
| 5 | Hyperparameter Tuning (Optuna, 50 trial) | `notebooks/02_modeling.ipynb` |
| 6 | Cross-Validation (5-Fold KFold) | `notebooks/02_modeling.ipynb` |
| 7 | Evaluasi: MAE, RMSE, R² | `notebooks/02_modeling.ipynb` |
| 8 | Feature Importance | `notebooks/02_modeling.ipynb` |
| 9 | Simpan model `.pkl` | `models/eta_model_best.pkl` |
| 10 | Inference sederhana | `notebooks/02_modeling.ipynb` + `api/inference.py` |
| 11 | REST API (FastAPI) | `api/main.py` |
| 12 | Generative AI — penjelasan ETA (Groq / LLaMA3) | `api/main.py` → `/predict/explain` |
| 13 | Logging & Monitoring (MLflow) | `notebooks/02_modeling.ipynb` |
| 14 | Visualisasi lengkap (distribusi, korelasi, residual) | `notebooks/01_eda.ipynb` + `02_modeling.ipynb` |

---

## 📡 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET`  | `/` | Health check |
| `GET`  | `/model-info` | Info model & metrik performa |
| `POST` | `/predict` | Prediksi ETA dari koordinat GPS |
| `POST` | `/predict/explain` | Prediksi ETA + penjelasan natural (Groq AI) |
| `GET`  | `/docs` | Swagger UI |

### Contoh Request `/predict`

```json
POST http://localhost:8001/predict
{
  "start_lat": 41.149,
  "start_lon": -8.610,
  "end_lat": 41.157,
  "end_lon": -8.650,
  "departure_time": "2024-09-02T07:00:00",
  "bus_id": "BUS-001",
  "route_name": "Rute Sekolah A",
  "student_count": 25
}
```

### Contoh Response

```json
{
  "success": true,
  "eta_minutes": 12.5,
  "eta_seconds": 750,
  "estimated_arrival": "07:12",
  "distance_km": 5.1,
  "straight_dist_km": 4.2,
  "departure_time": "2024-09-02T07:00:00",
  "message": "ETA berhasil diprediksi. Bus diperkirakan tiba pukul 07:12."
}
```

---

## 🔗 Integrasi dengan Laravel

Tambahkan di `routes/api.php`:

```php
use App\Http\Controllers\Api\ETAController;

Route::prefix('eta')->group(function () {
    Route::post('/predict',         [ETAController::class, 'predict']);
    Route::post('/predict/explain', [ETAController::class, 'predictWithExplanation']);
    Route::get('/health',           [ETAController::class, 'health']);
});
```

Tambahkan di `.env` Laravel:

```env
ML_ETA_URL=http://localhost:8001
```

Salin file `ETAController.php` dan `ETAService.php` dari folder  
`ini_nanti_ketika_saya_gabung_di_root_laravel/` ke lokasi yang sesuai di project Laravel.

---

## 📊 Target Performa Model

| Metrik | Target | Keterangan |
|--------|--------|------------|
| MAE    | ≤ 2.0 menit | Error rata-rata prediksi |
| RMSE   | ≤ 4.0 menit | Root Mean Square Error |
| R²     | ≥ 0.85 | Koefisien determinasi |

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|---|---|
| Model | LightGBM (tuned via Optuna) |
| Pipeline | scikit-learn Pipeline + ColumnTransformer |
| API | FastAPI + Uvicorn |
| Generative AI | Groq API (LLaMA3 8B) |
| Logging | MLflow |
| Dataset | Porto Taxi Trajectory — [Kaggle](https://www.kaggle.com/datasets/crailtap/taxi-trajectory) |
| Deploy | Docker Compose |

---

## 📝 Dataset

**Taxi Trajectory Data — ECML/PKDD 15 (Porto, Portugal)**  
🔗 https://www.kaggle.com/datasets/crailtap/taxi-trajectory

Letakkan file `train.csv` di folder `data/` sebelum menjalankan notebook.  
Ukuran file: ±1.85 GB.
