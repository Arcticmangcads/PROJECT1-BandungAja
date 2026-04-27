---
title: "Panduan Pengguna API BandungAja"
author: "Tim Pengembang"
date: "2026"
geometry: margin=2.5cm
---

# Panduan Pengguna & Troubleshooting

API BandungAja menyediakan data tempat wisata/kuliner, manajemen wishlist, itinerary, serta autentikasi pengguna.
**Base URL:** `http://localhost:8000` (sesuaikan dengan deployment)
**Dokumentasi Interaktif:** Buka `http://localhost:8000/docs` untuk Swagger UI.

## 1. Prasyarat Umum

- Semua endpoint (kecuali register & login) yang memerlukan otorisasi wajib menyertakan token JWT di header:  
  `Authorization: Bearer <access_token>`
- Token didapat dari **POST /api/auth/login**.
- Format tanggal/jam: `YYYY-MM-DD HH:MM:SS`.
- Gunakan query parameter sesuai ketentuan.

---

## 2. Autentikasi (`/api/auth`)

### Register – `POST /api/auth/register`

| Error | Penyebab | Solusi |
|-------|----------|--------|
| 400 "Email sudah terdaftar" | Email sudah digunakan | Gunakan email lain atau login |
| 422 Validation Error | Body tidak lengkap/format salah | Kirim JSON `{"email":"...", "password":"...", "nama":"..."}` |

### Login – `POST /api/auth/login`

| Error | Penyebab | Solusi |
|-------|----------|--------|
| 401 "Email atau password salah" | Kombinasi tidak cocok | Periksa kembali atau daftar dahulu |
| 422 | Body tidak sesuai | Sama seperti register |

### Profil Saya – `GET /api/auth/me`

| Error | Penyebab | Solusi |
|-------|----------|--------|
| 403 Forbidden | Token tidak disertakan | Tambahkan header `Authorization` |
| 401 "Token tidak valid atau sudah expired" | Token kedaluwarsa/salah | Login ulang |
| 404 "User tidak ditemukan" | User dihapus setelah token dibuat | Hubungi admin |

### Update Profil – `PATCH /api/auth/me`

| Error | Solusi |
|-------|--------|
| 422 | Kirim JSON dengan field yang ingin diubah: `nama`, `foto`, `lokasi` (boleh sebagian) |

---

## 3. Tempat (`/api/tempat`)

### Semua Tempat – `GET /api/tempat/`

Gunakan filter opsional: `?kategori=wisata&budget=50000&sort_by=rating&limit=10`.

### Hidden Gem – `GET /api/tempat/hidden-gem`

| Error | Solusi |
|-------|--------|
| 422 | Pastikan `min_rating` (float) dan `max_review` (int) dikirim. |

### Nearby – `GET /api/tempat/nearby`

| Error | Solusi |
|-------|--------|
| 422 | Wajib `lat`, `lon`. Contoh: `?lat=-6.9&lon=107.6&radius=5` |

### Detail Tempat – `GET /api/tempat/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 "Tempat tidak ditemukan" | Gunakan ID yang valid dari daftar. |

### Tambah Tempat – `POST /api/tempat/`

| Error | Solusi |
|-------|--------|
| 422 | Body JSON wajib memiliki `nama`. |

### Tambah Banyak (bulk) – `POST /api/tempat/bulk`

| Error | Solusi |
|-------|--------|
| 422 | Kirim list JSON, minimal tiap item punya `nama`. |

### Import CSV – `POST /api/tempat/import-csv`

| Error | Penyebab | Solusi |
|-------|----------|--------|
| 400 "File harus berformat CSV" | File bukan .csv | Gunakan file berakhiran .csv |
| 400 "Encoding file harus UTF-8" | Encoding salah | Simpan ulang dengan UTF-8 (tanpa BOM) |
| 400 "Gagal membaca CSV: ..." | Isi CSV rusak | Periksa delimiter, baris kosong |
| 400 "Kolom wajib 'nama' tidak ditemukan" | Kolom `nama` tidak ada | Pastikan header ada `nama` |
| Gagal di baris (`detail_error`) | Konversi tipe data gagal | Cek baris yang dilaporkan, pastikan angka bersih |

### Edit Tempat (PUT) – `PUT /api/tempat/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 | ID tidak ditemukan |
| 422 | Kirim semua field (seperti skema TempatCreate) |

### Patch Tempat (PATCH) – `PATCH /api/tempat/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 | ID tidak ada |
| 422 | Hanya field yang ingin diubah (jangan kirim field yang tidak berubah) |

### Hapus Tempat – `DELETE /api/tempat/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 | ID tidak ditemukan |

---

## 4. Wishlist (`/api/wishlist`)

> Semua endpoint memerlukan token.

### Lihat Wishlist – `GET /api/wishlist/`

Tidak ada error khusus.

### Tambah Wishlist – `POST /api/wishlist/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 "Tempat tidak ditemukan" | Gunakan ID tempat valid |
| 400 "Tempat sudah ada di wishlist" | Tempat sudah tersimpan |

### Hapus Wishlist – `DELETE /api/wishlist/{tempat_id}`

| Error | Solusi |
|-------|--------|
| 404 "Tempat tidak ada di wishlist" | Belum ditambahkan sebelumnya |

---

## 5. Itinerary (`/api/itinerary`)

> Semua endpoint memerlukan token.  
> **Penting:** POST itinerary & POST item menggunakan **query parameter**, bukan JSON body.

### Lihat Semua Itinerary – `GET /api/itinerary/`

Tidak ada error selain otentikasi.

### Buat Itinerary – `POST /api/itinerary/`

| **PENTING** | **Query parameter:** `?judul=Liburan&total_hari=2` |
|--------------|---------------------------------------------------|
| Error | Solusi |
| 422 | Pastikan `judul` dan `total_hari` (int) dikirim |
| 401 | Token tidak ada |

### Detail Itinerary + Jadwal – `GET /api/itinerary/{itinerary_id}`

| Error | Solusi |
|-------|--------|
| 404 "Itinerary tidak ditemukan" | Bukan milik Anda atau ID salah |

### Tambah Item – `POST /api/itinerary/{itinerary_id}/item`

| **PENTING** | **Query parameter:** `?tempat_id=1&hari=1&urutan=1&jam=08:00&catatan=notes` |
|--------------|-----------------------------------------------------------------------------|
| Error | Solusi |
| 422 | Wajib: `tempat_id`, `hari`, `urutan`. Opsional: `jam`, `catatan` |
| 404 "Itinerary tidak ditemukan" | ID itinerary bukan milik Anda |
| 404 "Tempat tidak ditemukan" | `tempat_id` tidak valid |
| 404 "Hari X melebihi total hari" | `hari` > total_hari, kurangi |

### Hapus Item – `DELETE /api/itinerary/{itinerary_id}/item/{item_id}`

| Error | Solusi |
|-------|--------|
| 404 "Itinerary tidak ditemukan" | ID itinerary salah |
| 404 "Item tidak ditemukan" | `item_id` tidak ada di itinerary tersebut (dapat dari detail) |

### Hapus Itinerary – `DELETE /api/itinerary/{itinerary_id}`

| Error | Solusi |
|-------|--------|
| 404 "Itinerary tidak ditemukan" | Bukan milik Anda atau ID salah |

---

## 6. Kode HTTP Umum

| Kode | Arti | Tindakan |
|------|------|----------|
| 400 | Request tidak valid | Baca pesan detail, perbaiki input |
| 401 | Token tidak valid/expired | Login ulang |
| 403 | Token tidak dikirim | Tambahkan header `Authorization` |
| 404 | Data tidak ditemukan | Cek ID atau kepemilikan |
| 422 | Validasi gagal | Periksa dokumentasi Swagger |
| 500 | Server error | Cek log server |

---

## 7. Tips Penting

- 🔐 Token JWT memiliki masa berlaku, perpanjang di `.env` jika perlu.
- 📄 Untuk import CSV, gunakan UTF-8 tanpa BOM; pastikan kolom `nama` ada.
- 🗺️ Itinerary: buat itinerary → tambahkan item → dapatkan `item_id` dari detail untuk menghapus.
- 🧪 Gunakan Swagger UI (`/docs`) untuk uji coba interaktif, klik Authorize untuk menyimpan token.

---

*Dibuat oleh Tim BandungAja – selalu periksa terminal server untuk log tambahan saat terjadi error.*