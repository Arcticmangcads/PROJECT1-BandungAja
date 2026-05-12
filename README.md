# 🎯 BandungAja - Electron Desktop App

Aplikasi wisata **BandungAja** yang dikonversi menjadi aplikasi desktop menggunakan Electron.js.

---

## 📁 Struktur Folder

```
bandungaja-electron/
├── main.js          ← Entry point Electron (JANGAN HAPUS)
├── package.json     ← Konfigurasi project & build
├── index.html       ← Halaman utama aplikasi
├── style.css        ← Tampilan / desain UI
├── app.js           ← Logika aplikasi
├── asset/           ← Folder gambar & ikon (buat folder ini)
│   ├── ICON-APP-BDGAJA.png
│   ├── MASJIDALJABBAR.png
│   ├── ASIAAFRIKA.png
│   └── tagline-1.png
└── dist/            ← Hasil build (otomatis dibuat)
```

---

## 🚀 Cara Menjalankan

### 1. Install Node.js
Download di: https://nodejs.org (versi LTS)

### 2. Install dependencies
Buka terminal di folder `bandungaja-electron`, lalu ketik:
```bash
npm install
```

### 3. Jalankan aplikasi
```bash
npm start
```

---

## 📦 Build menjadi File Instalasi

### Windows (.exe)
```bash
npm run build:win
```

### macOS (.dmg)
```bash
npm run build:mac
```

### Linux (.AppImage / .deb)
```bash
npm run build:linux
```

### Semua platform sekaligus
```bash
npm run build:all
```

Hasil build tersimpan di folder `dist/`.

---

## 🎨 Cara Mengubah Desain UI

Karena Electron hanya membungkus web app, desain bisa diubah seperti biasa:

| File | Apa yang diubah |
|------|-----------------|
| `style.css` | Warna, font, ukuran, layout |
| `index.html` | Struktur halaman, teks |
| `app.js` | Logika & data aplikasi |

Setelah edit, **simpan file → restart app** (`npm start`) untuk melihat perubahan.

### Tips Development:
Buka `main.js` dan hapus komentar pada baris ini untuk membuka DevTools:
```js
// mainWindow.webContents.openDevTools();
// menjadi:
mainWindow.webContents.openDevTools();
```

---

## ⚠️ Catatan Penting

- Pastikan folder `asset/` berisi semua gambar yang dibutuhkan
- Aplikasi membutuhkan koneksi internet untuk:
  - Google Fonts (Plus Jakarta Sans)
  - Leaflet.js (peta di halaman Nearby)
  - OpenStreetMap tiles
- Jika ingin **offline penuh**, download font & Leaflet secara lokal

---

## 💡 Troubleshooting

**App tidak mau buka?**
→ Pastikan sudah `npm install` terlebih dahulu

**Peta tidak tampil?**
→ Periksa koneksi internet, Leaflet butuh online

**Gambar tidak muncul?**
→ Pastikan folder `asset/` ada dan berisi file gambar yang benar
