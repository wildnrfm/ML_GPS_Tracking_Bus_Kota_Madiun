---
title: ML GPS Tracking Bus Kota Madiun
emoji: 🐨
colorFrom: purple
colorTo: purple
sdk: docker
pinned: false
---

# 🚌 ML-ETA — ETA Prediction untuk GPS Tracker Bus Sekolah

Modul Machine Learning untuk prediksi **Estimated Time of Arrival (ETA)**  
yang terintegrasi dengan backend Laravel dan aplikasi Flutter.

> 📖 **Panduan menjalankan secara lokal** → lihat [RUN.md](./RUN.md)

---

## 📁 Struktur Folder

```
ml-eta/
├── .github/
│   └── workflows/
│       └── keep_alive.yml        ← Workflow GitHub Actions untuk monitoring berkala
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
├── Dockerfile                    ← Dockerfile standar HuggingFace Spaces (port 7860, user 1000)
├── Dockerfile.fastapi            ← Dockerfile bawaan lokal (port 8001)
├── docker-compose.yml            ← Orkestrasi Laravel + FastAPI + MySQL
├── ping_service.py               ← Skrip keep-alive & logger status kesehatan ke Discord
├── requirements.txt              ← Dependency lengkap Python (Development)
├── requirements-prod.txt         ← Dependency minimal Python (Inference/Spaces Only)
├── .env.example                  ← Template environment variable
└── RUN.md                        ← Panduan menjalankan lokal
```

---

## 📡 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET`  | `/` | Health check (mengembalikan status online) |
| `GET`  | `/model-info` | Info model & metrik performa |
| `POST` | `/predict` | Prediksi ETA dari koordinat GPS |
| `GET`  | `/docs` | Swagger UI |

### Contoh Request `/predict`

```json
POST https://username-ml-eta.hf.space/predict
{
  "start_lat": 41.149,
  "start_lon": -8.610,
  "end_lat": 41.157,
  "end_lon": -8.650,
  "departure_time": "2026-05-30T07:00:00",
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
  "departure_time": "2026-05-30T07:00:00",
  "message": "ETA berhasil diprediksi. Bus diperkirakan tiba pukul 07:12."
}
```

---

## 🚀 Deploy ke HuggingFace Spaces (Docker SDK)

Agar model prediksi ETA dapat diakses secara publik dan dikonsumsi oleh Backend API (Laravel) secara stabil, ikuti langkah-langkah deployment berikut:

### Langkah 1: Buat Space Baru di HuggingFace
1. Buka [HuggingFace Spaces](https://huggingface.co/spaces) dan buat Space baru.
2. Isi nama Space, pilih **Docker** sebagai SDK.
3. Pilih **Blank** (atau custom template) pada pilihan Docker template.
4. Pilih opsi visibilitas **Public** atau **Private** (disarankan **Public** agar backend Laravel dapat mengakses endpoint API tanpa ribet mengelola bearer token HuggingFace, namun pastikan tidak ada data rahasia hardcoded di repository Anda).

### Langkah 2: Hubungkan Repositori GitHub ke HuggingFace Spaces
Anda dapat menggunakan GitHub Actions untuk deploy otomatis setiap kali Anda melakukan `git push` ke repositori GitHub:
1. Generate **Write Access Token** di akun HuggingFace Anda: **Settings** -> **Access Tokens** -> **New Token** (pilih role `write`).
2. Di repositori GitHub Anda ([wildnrfm/ML_GPS_Tracking_Bus_Kota_Madiun](https://github.com/wildnrfm/ML_GPS_Tracking_Bus_Kota_Madiun)), buka **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
3. Buat secret bernama `HF_TOKEN` dan isi dengan access token HuggingFace yang telah disalin.
4. Anda dapat membuat workflow deployment GitHub Action (contoh: `.github/workflows/deploy.yml`) untuk sinkronisasi otomatis ke HuggingFace Space. Berikut template sederhananya:
   ```yaml
   name: Sync to Hugging Face Spaces
   on:
     push:
       branches: [ main ]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             lfs: true
         - name: Push to HF
           env:
             HF_TOKEN: ${{ secrets.HF_TOKEN }}
           run: |
             git push --force https://wildnrfm:$HF_TOKEN@huggingface.co/spaces/wildnrfm/ML_GPS_Tracking_Bus_Kota_Madiun main:main
   ```

---

## 🩺 Peringatan Status Sleep & Monitor (Discord Alert)

HuggingFace Spaces versi gratis akan otomatis masuk ke mode **Sleep (Hibernasi)** jika tidak ada aktivitas selama beberapa waktu. Kami menyediakan solusi otomatis menggunakan GitHub Actions:

### Langkah 1: Konfigurasi Secrets di GitHub
Pada repositori GitHub Anda, tambahkan Repository Secrets berikut:
1. `HF_SPACE_URL`: URL utama HuggingFace Space Anda (tanpa garis miring di akhir), contoh: `https://wildnrfm-ml-eta.hf.space`.
2. `DISCORD_WEBHOOK_URL`: URL Webhook saluran Discord Anda (untuk menerima notifikasi log jika Space mati atau hidup kembali).

### Langkah 2: Cara Kerja Pengecekan Keep-Alive
* Workflow `.github/workflows/keep_alive.yml` telah diprogram untuk berjalan otomatis setiap **25 menit** (cron).
* Script `ping_service.py` akan dipicu untuk:
  1. Mengirim `GET /` ke Space Anda agar status Space terbangun (Wake Up) kembali.
  2. Melakukan panggilan hangat ke `/model-info` untuk memuat model ke memori.
  3. Mengirim pesan status (Hijau jika sehat, Merah jika error/down) ke Discord Webhook Anda beserta rincian *response time*.

---

## 📱 Alur Real-time ETA Halte untuk Aplikasi Mobile Siswa

Untuk menampilkan estimasi kedatangan bus secara real-time ke halte tempat siswa menunggu, ikuti arsitektur integrasi berikut:

1. **Simpan Titik Halte**: Setiap siswa terasosiasi dengan satu titik halte (`halte` table) yang memiliki koordinat statis `latitude` dan `longitude` (berfungsi sebagai `end_lat` dan `end_lon`).
2. **Kirim GPS Bus secara Real-time**: Bus sekolah secara berkala mengirimkan koordinat GPS terbarunya (melalui alat tracker/mobile driver) yang disimpan di tabel `gps_tracks` backend Laravel.
3. **Panggil API ML-ETA via Laravel**:
   Ketika siswa membuka aplikasi mobile untuk melacak bus:
   * Backend Laravel mengambil **GPS bus terakhir** dari tabel `gps_tracks` (`start_lat`, `start_lon`).
   * Backend Laravel mengambil **koordinat halte tujuan siswa** dari tabel `haltes` (`end_lat`, `end_lon`).
   * Backend Laravel melakukan `POST` request ke HuggingFace Space API (`/predict` endpoint) dengan payload tersebut.
   * ML-ETA memprediksi berapa menit (`eta_minutes`) bus tersebut akan sampai ke halte siswa.
   * Backend Laravel memformat respons dan meneruskannya secara aman ke aplikasi mobile Flutter siswa.

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
| Deploy | Docker SDK (HuggingFace Spaces) |
| Keep-Alive | GitHub Actions (Python `requests`) |
| Logging | Discord Webhooks |
