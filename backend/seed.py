from database import SessionLocal, engine
from models import Tempat, Base

# Buat tabel (jika belum ada)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

dummy_data = [
    Tempat(nama="Batagor Riri", kategori="kuliner", alamat="Jl. Burangrang No.41, Bandung",
           rating=4.5, harga_min=15000, harga_max=35000, sumber="dummy",
           deskripsi="Batagor legendaris Bandung sejak 1980.", jam_buka="08.00", jam_tutup="20.00",
           latitude=-6.9218, longitude=107.6070, jumlah_review=850),

    Tempat(nama="Mie Kocok Mang Dadeng", kategori="kuliner", alamat="Jl. Gardujati No.61, Bandung",
           rating=4.3, harga_min=20000, harga_max=40000, sumber="dummy",
           deskripsi="Mie kocok khas Bandung dengan kuah sapi gurih.", jam_buka="07.00", jam_tutup="16.00",
           latitude=-6.9175, longitude=107.6082, jumlah_review=420),

    Tempat(nama="Kafe Filosofi Kopi", kategori="kuliner", alamat="Jl. Riau No.12, Bandung",
           rating=4.1, harga_min=30000, harga_max=80000, sumber="dummy",
           deskripsi="Kafe estetik dengan konsep filosofi di setiap cangkir.", jam_buka="09.00",  jam_tutup="22.00",
           latitude=-6.9050, longitude=107.6150, jumlah_review=1200),

    Tempat(nama="Warung Nasi Ampera", kategori="kuliner", alamat="Jl. Gatot Subroto No.25, Bandung",
           rating=4.0, harga_min=15000, harga_max=30000, sumber="dummy",
           deskripsi="Nasi Sunda lengkap dengan lauk pauk khas Jawa Barat.", jam_buka="06.00", jam_tutup="22.00",
           latitude=-6.9300, longitude=107.6100, jumlah_review=65),

    Tempat(nama="Surabi Enhaii", kategori="kuliner", alamat="Jl. Setiabudi No.186, Bandung",
           rating=4.2, harga_min=10000, harga_max=25000, sumber="dummy",
           deskripsi="Surabi tradisional Bandung dengan berbagai topping.", jam_buka="07.00", jam_tutup="21.00",
           latitude=-6.8920, longitude=107.6080, jumlah_review=55),

    Tempat(nama="Kawah Putih", kategori="wisata", alamat="Ciwidey, Bandung Selatan",
           rating=4.7, harga_min=25000, harga_max=25000, sumber="dummy",
           deskripsi="Danau kawah vulkanik dengan air berwarna putih kehijauan.", jam_buka="07.00", jam_tutup="17.00",
           latitude=-7.1668, longitude=107.4017, jumlah_review=3200),

    Tempat(nama="Tangkuban Perahu", kategori="wisata", alamat="Lembang, Bandung Barat",
           rating=4.4, harga_min=20000, harga_max=20000, sumber="dummy",
           deskripsi="Gunung berapi aktif berbentuk perahu terbalik.", jam_buka="07.00", jam_tutup="17.00",
           latitude=-6.7593, longitude=107.6099, jumlah_review=4100),

    Tempat(nama="Farm House Lembang", kategori="wisata", alamat="Jl. Raya Lembang No.108",
           rating=4.2, harga_min=40000, harga_max=40000, sumber="dummy",
           deskripsi="Wisata bertema Eropa dengan berbagai wahana dan hewan.", jam_buka="09.00", jam_tutup="21.00",
           latitude=-6.8120, longitude=107.6170, jumlah_review=80),

    Tempat(nama="Floating Market Lembang", kategori="wisata", alamat="Jl. Grand Hotel No.33E, Lembang",
           rating=4.3, harga_min=35000, harga_max=35000, sumber="dummy",
           deskripsi="Pasar terapung unik di danau dengan berbagai kuliner.", jam_buka="08.00", jam_tutup="20.00",
           latitude=-6.8201, longitude=107.6180, jumlah_review=70),

    Tempat(nama="Gedung Sate", kategori="wisata", alamat="Jl. Diponegoro No.22, Bandung",
           rating=4.6, harga_min=0, harga_max=0, sumber="dummy",
           deskripsi="Ikon arsitektur bersejarah Kota Bandung.", jam_buka="08.00", jam_tutup="16.00",
           latitude=-6.9025, longitude=107.6187, jumlah_review=45),
]

db.add_all(dummy_data)
db.commit()
db.close()

print(f"Selesai! {len(dummy_data)} data dummy berhasil dimasukkan.")
