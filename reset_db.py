from database import engine
from models import Base

# 1. Hapus semua tabel yang ada
print("Menghapus tabel lama...")
Base.metadata.drop_all(bind=engine)

# 2. Buat ulang tabel dengan struktur terbaru dari models.py
print("Membuat tabel baru dengan struktur terbaru...")
Base.metadata.create_all(bind=engine)

print("Reset database selesai! Struktur sekarang sudah sinkron.")
