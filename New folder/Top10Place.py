import csv
import json
 
# ──────────────────────────────────
# KONFIGURASI
# ──────────────────────────────────
 
INPUT_FILE  = "Data_Kuliner_Wisata_BandungAja.csv"
OUTPUT_CSV  = "top10_bandungaja.csv"
OUTPUT_JSON = "top10_bandungaja.json"
 
 
# ──────────────────────────────────
# FUNGSI
# ──────────────────────────────────
 
def load_csv(filepath):
    """Baca file CSV dan kembalikan list of dict."""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "name":        row["Nama"].strip(),
                "category":    row["Kategori"].strip().lower(),
                "description": row["Deskripsi"].strip(),
                "rating":      float(row["Rating"] or 0),
                "harga_min":   int(row["harga_min"] or 0),
                "harga_max":   int(row["harga_max"] or 0),
                "image_url":   row["Image_Url"].strip(),
                "latitude":    float(row["Latitude"] or 0),
                "longitude":   float(row["Longitude"] or 0),
            })
    return data
 
 
def get_top10(data):
    """Urutkan data berdasarkan rating tertinggi, ambil 10 teratas."""
    sorted_data = sorted(data, key=lambda x: x["rating"], reverse=True)
    return sorted_data[:10]
 
 
def export_csv(data, filepath):
    """Simpan data ke file CSV."""
    columns = ["name", "category", "description",
               "rating", "harga_min", "harga_max",
               "image_url", "latitude", "longitude"]
 
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
 
    print(f"[✓] CSV disimpan ke '{filepath}'")
 
 
def export_json(data, filepath):
    """Simpan data ke file JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
 
    print(f"[✓] JSON disimpan ke '{filepath}'")
 
 
# ──────────────────────────────────
# MAIN
# ──────────────────────────────────
 
def main():
    print("BandungAja - Top 10 Tempat")
    print("=" * 35)
 
    # Load data
    print(f"[i] Membaca data dari '{INPUT_FILE}'...")
    data = load_csv(INPUT_FILE)
    print(f"[✓] Berhasil load {len(data)} data\n")
 
    # Ambil top 10
    top10 = get_top10(data)
 
    # Tampilkan hasil
    print("🏆 TOP 10 Tempat Berdasarkan Rating:")
    print("-" * 45)
    for i, item in enumerate(top10, start=1):
        print(f"  {i:2}. {item['name']:<35} ⭐ {item['rating']}")
    print()
 
    # Export
    export_csv(top10, OUTPUT_CSV)
    export_json(top10, OUTPUT_JSON)
 
    print(f"\n[✓] Selesai!")
 
 
if __name__ == "__main__":
    main()
 