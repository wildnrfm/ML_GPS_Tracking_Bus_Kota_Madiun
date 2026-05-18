# 🚀 RUN.md — Panduan Menjalankan ML-ETA

> Pastikan sudah membaca [README.md](./README.md) untuk memahami struktur project.

---

## 1️⃣ Persiapan Dataset

Download dataset dari Kaggle:  
🔗 https://www.kaggle.com/datasets/crailtap/taxi-trajectory

Letakkan file `train.csv` di folder `data/`:

```
ml-eta/
└── data/
    └── train.csv   ← taruh di sini (±1.85 GB)
```

---

## 2️⃣ Cara A — Google Colab (Direkomendasikan)

> Gunakan cara ini jika folder `ml-eta` sudah diunggah ke Google Drive.

### Langkah:

1. Upload seluruh folder `ml-eta` ke **Google Drive** kamu
2. Buka [Google Colab](https://colab.research.google.com/)
3. Buka file `notebooks/01_eda.ipynb` via Colab
4. Jalankan **Cell pertama** → akan muncul popup izin akses Drive → klik **Allow**
5. Jalankan semua cell dari atas ke bawah
6. Buka `notebooks/02_modeling.ipynb`, ulangi langkah 4–5
7. Setelah selesai, file `models/eta_model_best.pkl` akan terbuat otomatis di Drive

> ⚠️ Jika nama folder di Drive bukan `ml-eta`, ubah variabel `BASE_PATH` di cell pertama:
> ```python
> BASE_PATH = '/content/drive/MyDrive/nama-folder-kamu'
> ```

---

## 3️⃣ Cara B — Lokal (Jupyter Notebook)

### Prasyarat
- Python 3.10+
- pip

### Langkah:

```bash
# 1. Masuk ke folder ml-eta
cd ml-eta

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan Jupyter
jupyter notebook

# 4. Buka dan jalankan notebook secara berurutan:
#    notebooks/01_eda.ipynb    → terlebih dahulu
#    notebooks/02_modeling.ipynb → setelah NB01 selesai
```

Setelah training selesai, file berikut akan terbuat:
- `models/eta_model_best.pkl`
- `models/feature_info.json`

---

## 4️⃣ Menjalankan FastAPI (Development)

```bash
# 1. Copy dan isi .env
cp .env.example .env
# Edit .env: isi GROQ_API_KEY
# Dapatkan API key gratis di: https://console.groq.com/keys

# 2. Install dependencies (jika belum)
pip install -r requirements.txt

# 3. Jalankan server
uvicorn api.main:app --reload --port 8001
```

Akses Swagger UI: **http://localhost:8001/docs**

> ⚠️ Pastikan `models/eta_model_best.pkl` sudah ada sebelum menjalankan API.  
> Jika belum, jalankan notebook training terlebih dahulu.

---

## 5️⃣ Menjalankan via Docker Compose

> Gunakan cara ini jika sudah digabungkan dengan project Laravel.  
> File `docker-compose.yml` dan `Dockerfile.fastapi` harus berada di lokasi yang benar.

```bash
# Di root project Laravel (sejajar folder ml-eta)

# Jalankan semua service (Laravel + FastAPI + MySQL)
docker compose up --build

# Dengan phpMyAdmin (development):
docker compose --profile dev up --build

# Stop semua service
docker compose down
```

Service yang berjalan:

| Service | URL |
|---|---|
| Laravel | http://localhost:8000 |
| FastAPI | http://localhost:8001 |
| Swagger | http://localhost:8001/docs |
| MySQL | localhost:3306 |
| phpMyAdmin | http://localhost:8080 *(profile dev)* |

---

## 6️⃣ Monitoring dengan MLflow

Setelah menjalankan `02_modeling.ipynb`:

```bash
# Jalankan MLflow UI
mlflow ui

# Buka di browser:
# http://localhost:5000
```

---

## 🔑 Konfigurasi `.env`

```env
# FastAPI
APP_HOST=0.0.0.0
APP_PORT=8001

# Groq AI (wajib untuk endpoint /predict/explain)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama3-8b-8192

# Laravel (untuk CORS)
LARAVEL_URL=http://localhost:8000
```

**Pilihan model Groq:**

| Model | Keterangan |
|---|---|
| `llama3-8b-8192` | Default — cepat & ringan |
| `llama3-70b-8192` | Lebih akurat |
| `mixtral-8x7b-32768` | Konteks panjang |

---

## ⚠️ Urutan Eksekusi yang Benar

```
01_eda.ipynb  →  02_modeling.ipynb  →  FastAPI / Docker
     ↓                  ↓
 data_clean.csv   eta_model_best.pkl
```

Jangan menjalankan `02_modeling.ipynb` sebelum `01_eda.ipynb` selesai,  
karena NB02 membutuhkan `data/data_clean.csv` yang dihasilkan NB01.
