import uuid
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class Tempat(Base):
    __tablename__ = "tempat"

    id            = Column(Integer, primary_key=True, index=True)
    nama          = Column(String, nullable=False)
    kategori      = Column(String)  # wisata/kuliner
    alamat        = Column(String)
    rating        = Column(Float)
    harga_min     = Column(Integer)
    harga_max     = Column(Integer)
    sumber        = Column(String)  # sumber scraping
    deskripsi     = Column(String)  # detail tempat
    jam_buka      = Column(String)  # waktu buka
    jam_tutup     = Column(String)  # waktu tutup
    latitude      = Column(Float)   # Nerby
    longitude     = Column(Float)   # Nerby
    jumlah_review = Column(Integer) # Hidden Gem
    image_url     = Column(String)  # Gambar tempat

class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    nama     = Column(String, nullable=True)
    email    = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # disimpan dalam bentuk hash
    foto     = Column(String)
    lokasi   = Column(String)
    role     = Column(String, default="user")

class Wishlist(Base):
    __tablename__ = "wishlist"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    tempat_id  = Column(Integer, ForeignKey("tempat.id"), nullable=False)
    created_at = Column(String)

class Itinerary(Base):
    __tablename__ = "itinerary"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    judul      = Column(String)    # nama rencana perjalanan
    total_hari = Column(Integer)
    created_at = Column(String)

class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id           = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itinerary.id"))
    tempat_id    = Column(Integer, ForeignKey("tempat.id"))
    hari         = Column(Integer)   # hari ke
    urutan       = Column(Integer)   # urutan kunjungan pada hari yang sama
    jam          = Column(String)    # waktu
    catatan      = Column(String)

class StatusTempat(Base):
    __tablename__ = "status_tempat"

    id         = Column(Integer, primary_key=True, index=True)
    tempat_id  = Column(Integer, ForeignKey("tempat.id"), nullable=False)
    status     = Column(String, nullable=False)     # buka / tutup / tutup_sementara / pindah / renovasi / insiden / tutup_permanen
    keterangan = Column(String)                     # penjelasan detail
    mulai      = Column(String)                     # tanggal mulai tutup
    sampai     = Column(String)                     # tanggal buka kembali, None jika tidak menentu
    update_at  = Column(String)                     # terakhir diupdate
