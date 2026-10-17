# AHSP Item Search & Unit Pricing API

API pencarian cerdas untuk item **Analisis Harga Satuan Pekerjaan (AHSP) Bidang Cipta Karya** berbasis teks bebas (*free-text search*) serta pengambilan rincian komponen (tenaga kerja, bahan, dan peralatan) beserta koefisiennya untuk perhitungan harga satuan pekerjaan konstruksi.

Dataset bersumber dari **Surat Edaran Dirjen Bina Konstruksi No. 182/SE/Dk/2025 Lampiran VI** dan referensi **Permen PUPR No. 8 Tahun 2023**.

---

## 📑 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Struktur Proyek](#-struktur-proyek)
- [Arsitektur & Cara Kerja](#-arsitektur--cara-kerja)
  - [1. Normalisasi Teks Konstruksi](#1-normalisasi-teks-konstruksi)
  - [2. Mesin Pencari Hibrida (Word + Char n-gram TF-IDF)](#2-mesin-pencari-hibrida-word--char-n-gram-tf-idf)
- [Panduan Instalasi](#-panduan-instalasi)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Dokumentasi Endpoint API](#-dokumentasi-endpoint-api)
  - [1. Health Check (`GET /health`)](#1-health-check-get-health)
  - [2. Daftar Item AHSP dengan Pagination (`GET /ahsp-items`)](#2-daftar-item-ahsp-dengan-pagination-get-ahsp-items)
  - [3. Cari Item AHSP (`GET /search`)](#3-cari-item-ahsp-get-search)
  - [4. Detail Item & Komponen (`GET /items/{item_id}`)](#4-detail-item--komponen-get-itemsitem_id)
- [Pengujian (Testing)](#-pengujian-testing)
- [Lisensi & Referensi](#-lisensi--referensi)

---

## ✨ Fitur Utama

- **Pencarian Bebas Toleran Typo & Variasi Istilah**: Menggunakan kombinasi TF-IDF tingkat kata dan karakter (*character n-grams*) untuk menangani singkatan, kesalahan ketik ringan, dan variasi penulisan.
- **Normalisasi Terminologi Konstruksi Indonesia**:
  - Deteksi dan standarisasi rasio adukan/campuran (misal `1SP : 3PP`, `1 sp:3 pp`, `1:3` $\rightarrow$ `rasio_1_3`).
  - Standarisasi mutu beton (misal `f'c 21 MPa`, `fc 21` $\rightarrow$ `fc_21`).
  - Penyeragaman dimensi dan pecahan (misal `40 cm x 40 cm` $\rightarrow$ `40x40`, `3/4"` $\rightarrow$ `frac_3_4`).
  - Kamus sinonim umum konstruksi (contoh: *bekesting/acuan* $\rightarrow$ *bekisting*, *fondasi* $\rightarrow$ *pondasi*, *closet/wc* $\rightarrow$ *kloset*).
- **FastAPI Startup Lifespan**: Matriks TF-IDF dan data diindeks satu kali saat server dinyalakan, menjamin respon pencarian cepat pada setiap *request*.
- **Rincian Komponen Lengkap**: Menyajikan daftar rincian tenaga kerja, bahan, dan alat beserta kode komponen, satuan, dan koefisien standar untuk estimasi RAB.
- **Swagger / OpenAPI Interaktif**: Dokumentasi langsung siap uji di peramban web.

---

## 📂 Struktur Proyek

```text
search-unit-pricing/
├── Main.py                 # FastAPI application, routing, lifespan, & Pydantic schema
├── Search.py               # Mesin pencari SearchUnit (TF-IDF vectorizer & cosine similarity)
├── Normalisasi.py          # Logika normalisasi teks, regex rasio/ukuran, & kamus sinonim
├── ahsp_items.csv          # Master data 2.596 item pekerjaan AHSP Cipta Karya
├── ahsp_components_with_prices.csv # Data rincian komponen dilengkapi harga satuan & pencocokan SHS
├── ahsp_components.csv     # Data rincian komponen pengali (fallback)
├── test_api.py             # Test suite (pytest) untuk normalisasi dan API endpoint
├── requirements.txt        # Dependensi proyek
└── README.md               # Dokumentasi proyek
```

---

## 🧠 Arsitektur & Cara Kerja

### 1. Normalisasi Teks Konstruksi
Modul [`Normalisasi.py`](file:///Users/saktipardano/Documents/PythonProject/search-unit-pricing/Normalisasi.py) menyamakan teks dari dokumen sumber maupun kata kunci pencarian (*query*) pengguna:
1. **Pembersihan Karakter**: Mengubah karakter khusus seperti `m²` $\rightarrow$ `m2`, `m³` $\rightarrow$ `m3`, `×` $\rightarrow$ `x`, dan tanda kutip.
2. **Rasio Adukan**: `(\d+)\s*[a-z]{0,2}\s*:\s*(\d+)` diubah ke format `rasio_X_Y` sehingga teks spesifikasi "1 semen : 3 pasir" cocok dengan pencarian ringkas "1:3".
3. **Mutu Tekan**: Menyerap pola kuat tekan beton `f'c 21` menjadi `fc_21`.
4. **Dimensi & Satuan**: Menggabungkan dimensi (`40 cm x 40 cm` $\rightarrow$ `40x40`) dan memisahkan angka yang menempel ke unit ukuran (`15mm` $\rightarrow$ `15 mm`).
5. **Kamus Sinonim**: Menghubungkan istilah alternatif ke lema tunggal (misal: *pengecatan* $\rightarrow$ *cat*, *pembesian* $\rightarrow$ *penulangan*).

### 2. Mesin Pencari Hibrida (Word + Char n-gram TF-IDF)
Modul [`Search.py`](file:///Users/saktipardano/Documents/PythonProject/search-unit-pricing/Search.py) membuat 2 representasi TF-IDF:
- **Word Vectorizer** ($n$-gram rentang 1-2): Menangkap makna kata dan frasa berurutan.
- **Char-WB Vectorizer** ($n$-gram karakter rentang 3-5 di dalam batas kata): Menangkap kemiripan substring dan ketahanan terhadap *typo*.

Skor akhir dihitung dengan pembobotan seimbang:
$$\text{Skor} = 0.5 \times \text{Similarity}_{\text{kata}} + 0.5 \times \text{Similarity}_{\text{char}}$$

Flag `ada_hasil_yakin` akan bernilai `true` jika skor kandidat teratas memenuhi nilai ambang batas minimal (`SKOR_MIN = 0.25`).

---

## 🚀 Panduan Instalasi

### Prasyarat
- Python 3.10 atau versi yang lebih baru
- Virtual environment (direkomendasikan)

### Langkah Instalasi

1. **Clone repositori**:
   ```bash
   git clone <url-repo-anda>
   cd search-unit-pricing
   ```

2. **Buat dan aktifkan virtual environment**:
   ```bash
   # Di Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate

   # Di Windows (PowerShell):
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Menjalankan Aplikasi

Jalankan server API menggunakan Uvicorn:

```bash
uvicorn Main:app --reload --port 8000
```

> **Catatan**: Jika file data CSV diletakkan di direktori lain, tentukan path melalui *environment variable* `AHSP_DATA_DIR`:
> ```bash
> AHSP_DATA_DIR=/path/ke/data uvicorn Main:app --reload
> ```

Akses dokumentasi interaktif (Swagger UI) di browser:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** atau ReDoc di **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

## 📡 Dokumentasi Endpoint API

### 1. Health Check (`GET /health`)
Memeriksa status layanan dan memastikan data AHSP telah termuat di memori.

- **Request**:
  ```http
  GET /health HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "ok",
    "jumlah_item": 2596
  }
  ```

---

### 2. Daftar Item AHSP dengan Pagination (`GET /ahsp-items`)
Mengambil seluruh daftar master item pekerjaan AHSP dengan dukungan pagination dan filter opsional.

- **Parameter Query**:
  | Parameter | Tipe | Wajib | Default | Batasan | Keterangan |
  | :--- | :--- | :---: | :---: | :---: | :--- |
  | `page` | `integer` | Tidak | `1` | $\ge 1$ | Nomor halaman yang diminta (dimulai dari 1) |
  | `page_size` | `integer` | Tidak | `20` | 1 - 100 | Jumlah item per halaman |
  | `kategori` | `string` | Tidak | `null` | - | Filter parsial berdasarkan nama kategori pekerjaan |
  | `divisi` | `string` | Tidak | `null` | - | Filter parsial berdasarkan nama divisi |

- **Contoh Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/ahsp-items?page=1&page_size=2"
  ```

- **Contoh Response** (`200 OK`):
  ```json
  {
    "total": 2596,
    "page": 1,
    "page_size": 2,
    "total_pages": 1298,
    "items": [
      {
        "id": "1.1.1.1",
        "uraian": "Pembuatan 1 m’ Pagar Sementara dari Kayu Tinggi 2 meter",
        "satuan": "m'",
        "divisi": "PERSIAPAN LAPANGAN/SITE WORK",
        "kategori": "PEKERJAAN PERSIAPAN",
        "subkategori": "Pembuatan pagar proyek",
        "tipe": "standar",
        "sumber": "SE Dirjen Bina Konstruksi 182/SE/Dk/2025 Lampiran VI (AHSP Bidang Cipta Karya)",
        "ref_permen": "Lihat Permen PUPR Nomor 8 Tahun 2023 Lampiran B U.1.1.1 (c)",
        "jumlah_komponen": 13
      },
      {
        "id": "1.1.1.2",
        "uraian": "Pembuatan 1 m’ Pagar Sementara dari Seng Gelombang Rangka Kayu Tinggi 2 meter",
        "satuan": "m'",
        "divisi": "PERSIAPAN LAPANGAN/SITE WORK",
        "kategori": "PEKERJAAN PERSIAPAN",
        "subkategori": "Pembuatan pagar proyek",
        "tipe": "standar",
        "sumber": "SE Dirjen Bina Konstruksi 182/SE/Dk/2025 Lampiran VI (AHSP Bidang Cipta Karya)",
        "ref_permen": "Lihat Permen PUPR Nomor 8 Tahun 2023 Lampiran B U.1.1.2 (c)",
        "jumlah_komponen": 12
      }
    ]
  }
  ```

---

### 3. Cari Item AHSP (`GET /search`)
Mencari item pekerjaan AHSP berdasarkan kalimat atau kata kunci bebas.

- **Parameter Query**:
  | Parameter | Tipe | Wajib | Default | Batasan | Keterangan |
  | :--- | :--- | :---: | :---: | :---: | :--- |
  | `q` | `string` | **Ya** | - | 2 - 200 karakter | Kata kunci teks pekerjaan (mis. `"plesteran 1:3"`) |
  | `k` | `integer` | Tidak | `5` | 1 - 20 | Jumlah kandidat teratas yang ingin ditampilkan |

- **Contoh Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/search?q=plesteran%201:3&k=3"
  ```

- **Contoh Response** (`200 OK`):
  ```json
  {
    "query_ternormalisasi": "plesteran rasio_1_3",
    "ada_hasil_yakin": true,
    "hasil": [
      {
        "id": "3.7.3",
        "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 15 mm",
        "satuan": "m2",
        "divisi": "STRUKTUR/ARSITEKTUR",
        "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
        "tipe": "standar",
        "skor": 0.725
      },
      {
        "id": "3.7.4",
        "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 20 mm",
        "satuan": "m2",
        "divisi": "STRUKTUR/ARSITEKTUR",
        "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
        "tipe": "standar",
        "skor": 0.718
      }
    ]
  }
  ```

> [!NOTE]
> Nilai `ada_hasil_yakin: true` menandakan adanya item dengan skor kemiripan di atas ambang batas, namun aplikasi klien disarankan tetap menampilkan daftar kandidat agar pengguna dapat memvalidasi spesifikasi yang paling tepat.

---

### 4. Detail Item & Komponen (`GET /items/{item_id}`)
Mengambil informasi lengkap satu item AHSP beserta uraian koefisien komponen tenaga kerja, bahan baku, dan peralatan.

- **Parameter Path**:
  - `item_id` (`string`): Kode ID item pekerjaan.
  > [!IMPORTANT]
  > Sebagian ID dokumen sumber memuat karakter `#` (misalnya `2.2.1.1.5#2`). Pastikan melakukan URL-encoding menjadi `%23` saat memanggil URL: `/items/2.2.1.1.5%232`.

- **Contoh Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/items/3.7.3"
  ```

- **Contoh Response** (`200 OK`):
  ```json
  {
    "id": "3.7.3",
    "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 15 mm",
    "satuan": "m2",
    "divisi": "STRUKTUR/ARSITEKTUR",
    "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
    "subkategori": "Plesteran",
    "tipe": "standar",
    "sumber": "SE Dirjen Bina Konstruksi 182/SE/Dk/2025 Lampiran VI (AHSP Bidang Cipta Karya)",
    "ref_permen": "Lihat Permen PUPR Nomor 8 Tahun 2023 Lampiran B U.3.7.3 (a)",
    "komponen": [
      {
        "urutan": 1,
        "jenis": "tenaga_kerja",
        "kode_komponen": "L.01",
        "nama_komponen": "Pekerja",
        "satuan": "OH",
        "koefisien": 0.2,
        "perlu_cek": false,
        "nama_shs_cocok": "Pekerja",
        "harga_satuan": 100000.0,
        "jumlah_harga": 20000.0,
        "status_pencocokan": "Match by Kode"
      },
      {
        "urutan": 2,
        "jenis": "tenaga_kerja",
        "kode_komponen": "L.02",
        "nama_komponen": "Tukang",
        "satuan": "OH",
        "koefisien": 0.1,
        "perlu_cek": false,
        "nama_shs_cocok": "Tukang batu",
        "harga_satuan": 145000.0,
        "jumlah_harga": 14500.0,
        "status_pencocokan": "Match by Kode"
      },
      {
        "urutan": 5,
        "jenis": "bahan",
        "kode_komponen": "M.04",
        "nama_komponen": "Semen Portland",
        "satuan": "kg",
        "koefisien": 7.776,
        "perlu_cek": false,
        "nama_shs_cocok": "Semen portland",
        "harga_satuan": 1300.0,
        "jumlah_harga": 10108.8,
        "status_pencocokan": "Fuzzy Match"
      },
      {
        "urutan": 6,
        "jenis": "bahan",
        "kode_komponen": "M.07",
        "nama_komponen": "Pasir Pasang",
        "satuan": "m3",
        "koefisien": 0.023,
        "perlu_cek": false,
        "nama_shs_cocok": "Pasir pasang",
        "harga_satuan": 200000.0,
        "jumlah_harga": 4600.0,
        "status_pencocokan": "Match by Name & Unit"
      }
    ]
  }
  ```

---

## 🧪 Pengujian (Testing)

Proyek ini telah dilengkapi *test suite* otomatis menggunakan `pytest` untuk memverifikasi logika normalisasi teks, ambang batas keyakinan, validasi input, dan *response payload* endpoint.

Jalankan pengujian dengan perintah:

```bash
pytest -v
```

---

## 📜 Lisensi & Referensi

- **Sumber Standar Analisis**:
  - Surat Edaran Direktur Jenderal Bina Konstruksi Kementerian Pekerjaan Umum dan Perumahan Rakyat Nomor 182/SE/Dk/2025 (Lampiran VI: AHSP Bidang Cipta Karya).
  - Peraturan Menteri PUPR Nomor 8 Tahun 2023 tentang Pedoman Penyusunan Perkiraan Biaya Pekerjaan Konstruksi Bidang Pekerjaan Umum dan Perumahan Rakyat.
# AHSP Item Search & Unit Pricing API

API pencarian cerdas untuk item **Analisis Harga Satuan Pekerjaan (AHSP) Bidang Cipta Karya** berbasis teks bebas (*free-text search*) serta pengambilan rincian komponen (tenaga kerja, bahan, dan peralatan) beserta koefisiennya untuk perhitungan harga satuan pekerjaan konstruksi.

Dataset bersumber dari **Surat Edaran Dirjen Bina Konstruksi No. 182/SE/Dk/2025 Lampiran VI** dan referensi **Permen PUPR No. 8 Tahun 2023**.

---

## 📑 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Struktur Proyek](#-struktur-proyek)
- [Arsitektur & Cara Kerja](#-arsitektur--cara-kerja)
  - [1. Normalisasi Teks Konstruksi](#1-normalisasi-teks-konstruksi)
  - [2. Mesin Pencari Hibrida (Word + Char n-gram TF-IDF)](#2-mesin-pencari-hibrida-word--char-n-gram-tf-idf)
- [Panduan Instalasi](#-panduan-instalasi)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Dokumentasi Endpoint API](#-dokumentasi-endpoint-api)
  - [1. Health Check (`GET /health`)](#1-health-check-get-health)
  - [2. Cari Item AHSP (`GET /search`)](#2-cari-item-ahsp-get-search)
  - [3. Detail Item & Komponen (`GET /items/{item_id}`)](#3-detail-item--komponen-get-itemsitem_id)
- [Pengujian (Testing)](#-pengujian-testing)
- [Lisensi & Referensi](#-lisensi--referensi)

---

## ✨ Fitur Utama

- **Pencarian Bebas Toleran Typo & Variasi Istilah**: Menggunakan kombinasi TF-IDF tingkat kata dan karakter (*character n-grams*) untuk menangani singkatan, kesalahan ketik ringan, dan variasi penulisan.
- **Normalisasi Terminologi Konstruksi Indonesia**:
  - Deteksi dan standarisasi rasio adukan/campuran (misal `1SP : 3PP`, `1 sp:3 pp`, `1:3` $\rightarrow$ `rasio_1_3`).
  - Standarisasi mutu beton (misal `f'c 21 MPa`, `fc 21` $\rightarrow$ `fc_21`).
  - Penyeragaman dimensi dan pecahan (misal `40 cm x 40 cm` $\rightarrow$ `40x40`, `3/4"` $\rightarrow$ `frac_3_4`).
  - Kamus sinonim umum konstruksi (contoh: *bekesting/acuan* $\rightarrow$ *bekisting*, *fondasi* $\rightarrow$ *pondasi*, *closet/wc* $\rightarrow$ *kloset*).
- **FastAPI Startup Lifespan**: Matriks TF-IDF dan data diindeks satu kali saat server dinyalakan, menjamin respon pencarian cepat pada setiap *request*.
- **Rincian Komponen Lengkap**: Menyajikan daftar rincian tenaga kerja, bahan, dan alat beserta kode komponen, satuan, dan koefisien standar untuk estimasi RAB.
- **Swagger / OpenAPI Interaktif**: Dokumentasi langsung siap uji di peramban web.

---

## 📂 Struktur Proyek

```text
search-unit-pricing/
├── Main.py                 # FastAPI application, routing, lifespan, & Pydantic schema
├── Search.py               # Mesin pencari SearchUnit (TF-IDF vectorizer & cosine similarity)
├── Normalisasi.py          # Logika normalisasi teks, regex rasio/ukuran, & kamus sinonim
├── ahsp_items.csv          # Master data 2.596 item pekerjaan AHSP Cipta Karya
├── ahsp_components.csv     # Data rincian komponen pengali (tenaga, bahan, alat, koefisien)
├── test_api.py             # Test suite (pytest) untuk normalisasi dan API endpoint
├── requirements.txt        # Dependensi proyek
└── README.md               # Dokumentasi proyek
```

---

## 🧠 Arsitektur & Cara Kerja

### 1. Normalisasi Teks Konstruksi
Modul [`Normalisasi.py`](file:///Users/saktipardano/Documents/PythonProject/search-unit-pricing/Normalisasi.py) menyamakan teks dari dokumen sumber maupun kata kunci pencarian (*query*) pengguna:
1. **Pembersihan Karakter**: Mengubah karakter khusus seperti `m²` $\rightarrow$ `m2`, `m³` $\rightarrow$ `m3`, `×` $\rightarrow$ `x`, dan tanda kutip.
2. **Rasio Adukan**: `(\d+)\s*[a-z]{0,2}\s*:\s*(\d+)` diubah ke format `rasio_X_Y` sehingga teks spesifikasi "1 semen : 3 pasir" cocok dengan pencarian ringkas "1:3".
3. **Mutu Tekan**: Menyerap pola kuat tekan beton `f'c 21` menjadi `fc_21`.
4. **Dimensi & Satuan**: Menggabungkan dimensi (`40 cm x 40 cm` $\rightarrow$ `40x40`) dan memisahkan angka yang menempel ke unit ukuran (`15mm` $\rightarrow$ `15 mm`).
5. **Kamus Sinonim**: Menghubungkan istilah alternatif ke lema tunggal (misal: *pengecatan* $\rightarrow$ *cat*, *pembesian* $\rightarrow$ *penulangan*).

### 2. Mesin Pencari Hibrida (Word + Char n-gram TF-IDF)
Modul [`Search.py`](file:///Users/saktipardano/Documents/PythonProject/search-unit-pricing/Search.py) membuat 2 representasi TF-IDF:
- **Word Vectorizer** ($n$-gram rentang 1-2): Menangkap makna kata dan frasa berurutan.
- **Char-WB Vectorizer** ($n$-gram karakter rentang 3-5 di dalam batas kata): Menangkap kemiripan substring dan ketahanan terhadap *typo*.

Skor akhir dihitung dengan pembobotan seimbang:
$$\text{Skor} = 0.5 \times \text{Similarity}_{\text{kata}} + 0.5 \times \text{Similarity}_{\text{char}}$$

Flag `ada_hasil_yakin` akan bernilai `true` jika skor kandidat teratas memenuhi nilai ambang batas minimal (`SKOR_MIN = 0.25`).

---

## 🚀 Panduan Instalasi

### Prasyarat
- Python 3.10 atau versi yang lebih baru
- Virtual environment (direkomendasikan)

### Langkah Instalasi

1. **Clone repositori**:
   ```bash
   git clone <url-repo-anda>
   cd search-unit-pricing
   ```

2. **Buat dan aktifkan virtual environment**:
   ```bash
   # Di Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate

   # Di Windows (PowerShell):
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Menjalankan Aplikasi

Jalankan server API menggunakan Uvicorn:

```bash
uvicorn Main:app --reload --port 8000
```

> **Catatan**: Jika file data CSV diletakkan di direktori lain, tentukan path melalui *environment variable* `AHSP_DATA_DIR`:
> ```bash
> AHSP_DATA_DIR=/path/ke/data uvicorn Main:app --reload
> ```

Akses dokumentasi interaktif (Swagger UI) di browser:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** atau ReDoc di **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

## 📡 Dokumentasi Endpoint API

### 1. Health Check (`GET /health`)
Memeriksa status layanan dan memastikan data AHSP telah termuat di memori.

- **Request**:
  ```http
  GET /health HTTP/1.1
  Host: 127.0.0.1:8000
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "ok",
    "jumlah_item": 2596
  }
  ```

---

### 2. Cari Item AHSP (`GET /search`)
Mencari item pekerjaan AHSP berdasarkan kalimat atau kata kunci bebas.

- **Parameter Query**:
  | Parameter | Tipe | Wajib | Default | Batasan | Keterangan |
  | :--- | :--- | :---: | :---: | :---: | :--- |
  | `q` | `string` | **Ya** | - | 2 - 200 karakter | Kata kunci teks pekerjaan (mis. `"plesteran 1:3"`) |
  | `k` | `integer` | Tidak | `5` | 1 - 20 | Jumlah kandidat teratas yang ingin ditampilkan |

- **Contoh Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/search?q=plesteran%201:3&k=3"
  ```

- **Contoh Response** (`200 OK`):
  ```json
  {
    "query_ternormalisasi": "plesteran rasio_1_3",
    "ada_hasil_yakin": true,
    "hasil": [
      {
        "id": "3.7.3",
        "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 15 mm",
        "satuan": "m2",
        "divisi": "STRUKTUR/ARSITEKTUR",
        "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
        "tipe": "standar",
        "skor": 0.725
      },
      {
        "id": "3.7.4",
        "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 20 mm",
        "satuan": "m2",
        "divisi": "STRUKTUR/ARSITEKTUR",
        "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
        "tipe": "standar",
        "skor": 0.718
      }
    ]
  }
  ```

> [!NOTE]
> Nilai `ada_hasil_yakin: true` menandakan adanya item dengan skor kemiripan di atas ambang batas, namun aplikasi klien disarankan tetap menampilkan daftar kandidat agar pengguna dapat memvalidasi spesifikasi yang paling tepat.

---

### 3. Detail Item & Komponen (`GET /items/{item_id}`)
Mengambil informasi lengkap satu item AHSP beserta uraian koefisien komponen tenaga kerja, bahan baku, dan peralatan.

- **Parameter Path**:
  - `item_id` (`string`): Kode ID item pekerjaan.
  > [!IMPORTANT]
  > Sebagian ID dokumen sumber memuat karakter `#` (misalnya `2.2.1.1.5#2`). Pastikan melakukan URL-encoding menjadi `%23` saat memanggil URL: `/items/2.2.1.1.5%232`.

- **Contoh Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/items/3.7.3"
  ```

- **Contoh Response** (`200 OK`):
  ```json
  {
    "id": "3.7.3",
    "uraian": "Pemasangan 1 m2 plesteran 1 SP : 3 PP tebal 15 mm",
    "satuan": "m2",
    "divisi": "STRUKTUR/ARSITEKTUR",
    "kategori": "PEKERJAAN PLESTERAN DAN ACIAN",
    "subkategori": "Plesteran",
    "tipe": "standar",
    "sumber": "SE Dirjen Bina Konstruksi 182/SE/Dk/2025 Lampiran VI (AHSP Bidang Cipta Karya)",
    "ref_permen": "Lihat Permen PUPR Nomor 8 Tahun 2023 Lampiran B U.3.7.3 (a)",
    "komponen": [
      {
        "urutan": 1,
        "jenis": "tenaga_kerja",
        "kode_komponen": "L.01",
        "nama_komponen": "Pekerja",
        "satuan": "OH",
        "koefisien": 0.3,
        "perlu_cek": false
      },
      {
        "urutan": 2,
        "jenis": "tenaga_kerja",
        "kode_komponen": "L.02",
        "nama_komponen": "Tukang batu",
        "satuan": "OH",
        "koefisien": 0.15,
        "perlu_cek": false
      },
      {
        "urutan": 5,
        "jenis": "bahan",
        "kode_komponen": "M.04",
        "nama_komponen": "Semen Portland (PC)",
        "satuan": "kg",
        "koefisien": 7.776,
        "perlu_cek": false
      },
      {
        "urutan": 6,
        "jenis": "bahan",
        "kode_komponen": "M.07",
        "nama_komponen": "Pasir Pasang",
        "satuan": "m3",
        "koefisien": 0.023,
        "perlu_cek": false
      }
    ]
  }
  ```

---

## 🧪 Pengujian (Testing)

Proyek ini telah dilengkapi *test suite* otomatis menggunakan `pytest` untuk memverifikasi logika normalisasi teks, ambang batas keyakinan, validasi input, dan *response payload* endpoint.

Jalankan pengujian dengan perintah:

```bash
pytest -v
```

---

## 📜 Lisensi & Referensi

- **Sumber Standar Analisis**:
  - Surat Edaran Direktur Jenderal Bina Konstruksi Kementerian Pekerjaan Umum dan Perumahan Rakyat Nomor 182/SE/Dk/2025 (Lampiran VI: AHSP Bidang Cipta Karya).
  - Peraturan Menteri PUPR Nomor 8 Tahun 2023 tentang Pedoman Penyusunan Perkiraan Biaya Pekerjaan Konstruksi Bidang Pekerjaan Umum dan Perumahan Rakyat.