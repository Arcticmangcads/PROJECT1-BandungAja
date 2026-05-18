import csv
import json
 
# ──────────────────────────────────
# KONFIGURASI
# ──────────────────────────────────
 
INPUT_FILE = r"d:\Python\Data Scrape BandungAja\DataScrape\Data_Kuliner_Wisata_BandungAja.csv"
OUTPUT_CSV  = "bandungaja_output.csv"
OUTPUT_JSON = "bandungaja_output.json"
 
 
# ──────────────────────────────────
# FUNGSI UTAMA
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
    print("BandungAja Data Scraper")
    print("=" * 35)
 
    # Load data dari CSV
    print(f"[i] Membaca data dari '{INPUT_FILE}'...")
    data = load_csv(INPUT_FILE)
    print(f"[✓] Berhasil load {len(data)} data\n")
 
    # Preview 3 data pertama
    print("Preview data:")
    for item in data[:3]:
        print(f"  - {item['name']} ({item['category']}) | rating: {item['rating']}")
    print(f"  ... dan {len(data) - 3} data lainnya\n")
 
    # Export
    export_csv(data, OUTPUT_CSV)
    export_json(data, OUTPUT_JSON)
 
    print(f"\n[✓] Selesai! Total {len(data)} tempat berhasil diproses.")
 
 
if __name__ == "__main__":
    main()
