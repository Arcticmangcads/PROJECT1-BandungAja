# test_nearby.py
from nearby import get_nearby, get_user_location, hitung_jarak, supabase

# ✅ Test 1 — Cek data Supabase langsung
print("=== CEK DATA SUPABASE ===")
response = supabase.table("destinations").select("id, Nama, Latitude, Longitude").limit(5).execute()
print(response.data)

# ✅ Test 2 — Cek deteksi lokasi user
print("\n=== TEST LOKASI USER ===")
lokasi = get_user_location()
print(lokasi)

# ✅ Test 3 — Cek hitung jarak
print("\n=== TEST HITUNG JARAK ===")
jarak = hitung_jarak(-6.9147, 107.6098, -6.9147, 107.6098)
print(f"Jarak titik sama: {jarak} km")  # Harusnya 0.0

# ✅ Test 4 — Semua kategori radius 20km
print("\n=== NEARBY SEMUA (radius 20km) ===")
hasil = get_nearby(radius_km=20.0)
print(f"Lokasi user: {hasil['lokasi_user']['city']}")
print(f"Ditemukan: {hasil['jumlah_ditemukan']} tempat")
for t in hasil['tempat_terdekat']:
    print(f"  - {t['Nama']} ({t['jarak_km']} km)")

# ✅ Test 5 — Filter Wisata
print("\n=== NEARBY WISATA (radius 20km) ===")
hasil_wisata = get_nearby(radius_km=20.0, kategori="Wisata")
print(f"Ditemukan: {hasil_wisata['jumlah_ditemukan']} tempat wisata")
for t in hasil_wisata['tempat_terdekat']:
    print(f"  - {t['Nama']} ({t['jarak_km']} km)")

# ✅ Test 6 — Filter Kuliner
print("\n=== NEARBY KULINER (radius 20km) ===")
hasil_kuliner = get_nearby(radius_km=20.0, kategori="Kuliner")
print(f"Ditemukan: {hasil_kuliner['jumlah_ditemukan']} tempat kuliner")
for t in hasil_kuliner['tempat_terdekat']:
    print(f"  - {t['Nama']} ({t['jarak_km']} km)")