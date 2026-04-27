from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session
from math import radians, sin, cos, sqrt, atan2
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from typing import Optional, List
from database import get_db

import models, schemas
import pandas as pd
import io

router = APIRouter(prefix="/api/tempat", tags=["Tempat"])

# GET semua tempat, dengan filter opsional
@router.get("/", response_model=List[schemas.TempatResponse])
def get_tempat(
    kategori: Optional[str] = Query(None, description="wisata / kuliner"),
    budget  : Optional[int] = Query(None, description="Harga maksimal"),
    nama    : Optional[str] = Query(None, description="Cari berdasarkan nama"),
    sort_by : Optional[str] = Query(None, description="rating / harga_min"),
    limit   : Optional[int] = Query(None, description="Batasi jumlah hasil"),
    db      : Session       = Depends(get_db)
    
    ):
        query = db.query(models.Tempat)

        if kategori:
            query = query.filter(models.Tempat.kategori == kategori)
        if budget:
            query = query.filter(models.Tempat.harga_min <= budget)
        if nama:
            query = query.filter(models.Tempat.nama.contains(nama))
        if sort_by == "rating":
            query = query.order_by(desc(models.Tempat.rating))
        elif sort_by == "harga_min":
            query = query.order_by(asc(models.Tempat.harga_min))

        if limit:
                query = query.limit(limit)
        return query.all()

# Hidden Gem
@router.get("/hidden-gem", response_model=List[schemas.TempatResponse])
def get_hidden_gem(
        min_rating : float = Query(4.0, description="Rating minimal"),
        max_review : int   = Query(100, description="Jumlah review maksimal"),
        db         : Session = Depends(get_db) 
):
        query = db.query(models.Tempat)\
                .filter(models.Tempat.rating >= min_rating)\
                .filter(models.Tempat.jumlah_review <= max_review)\
                .order_by(desc(models.Tempat.rating))
        return query.all()

@router.get("/nearby", response_model=List[schemas.TempatResponse])
def get_nearby(
        lat     : float = Query(..., description="Latitude pengguna"),
        lon     : float = Query(..., description="Longitude pengguna"),
        radius  : float = Query(5.0, description="Radius dalam kilometer"),
        db      : Session = Depends(get_db)
):
        semua_tempat = db.query(models.Tempat)\
                .filter(models.Tempat.latitude != None)\
                .filter(models.Tempat.longitude != None)\
                .all()
        
        hasil = []
        for tempat in semua_tempat:
                jarak = hitung_jarak(lat, lon, tempat.latitude, tempat.longitude)
                if jarak <= radius:
                        hasil.append(tempat)

        return hasil

# GET detail satu tempat berdasarkan ID
@router.get("/{tempat_id}", response_model=schemas.TempatResponse)
def get_tempat_by_id(tempat_id: int, db: Session = Depends(get_db)):
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")
    return tempat

# POST untuk menambah satu tempat baru
@router.post("/", response_model=schemas.TempatResponse)
def tambah_tempat(tempat: schemas.TempatCreate, db: Session = Depends(get_db)):
        data_baru = models.Tempat(**tempat.model_dump())
        db.add(data_baru)
        db.commit()
        db.refresh(data_baru)
        return data_baru

# POST untuk menambah banyak tempat sekaligus (dari hasil scraping)
@router.post("/bulk", response_model=List[schemas.TempatResponse])
def tambah_banyak_tempat(tempat_list: List[schemas.TempatCreate], db: Session = Depends(get_db)):
        data_list = [models.Tempat(**t.model_dump()) for t in tempat_list]
        db.add_all(data_list)
        db.commit()
        for data in data_list:
                db.refresh(data)
        return data_list

@router.post("/import-csv")
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
        # Validasi eksistensi file
        if not file.filename.lower().endswith(".csv"):
                raise HTTPException(status_code=400, detail="File harus berformat CSV")

        # Baca isi file CSV
        contents = file.file.read()
        try:
                csv_str = contents.decode("utf-8-sig")
        except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Encoding file harus UTF-8")
        try:
                df = pd.read_csv(io.BytesIO(contents), dtype = {
                        "jam_buka"  : str,
                        "jam_tutup" : str
                })
        except Exception as e:
                raise HTTPException(status_code=400, detail=f"Gagal membaca CSV: {str(e)}")
                
        # Kolom yang diharapkan ada di CSV
        kolom_wajib = ["nama"]
        for kolom in kolom_wajib:
                if kolom not in df.columns:
                        raise HTTPException(
                                status_code=400,
                                detail=f"Kolom wajib '{kolom}' tidak ditemukan di CSV. Kolom tersedia: {list(df.columns)}"
                              )

        # Normalisasi nama kolom (strip spasi, lowercase), berguna saat ada spasi ekstra
        df.columns = df.columns.str.strip()

        # Masukan ke database baris per baris
        berhasil = 0
        gagal = 0
        errors = [] # mencatat detail error
        
        for idx, row in df.iterrows():
                try:
                        # Fungsi bantu konversi aman
                        def save_float(val):
                                if pd.isna(val) or str(val).strip() == "":
                                        return None
                                return float(val)
                        
                        def save_int(val):
                                if pd.isna(val) or str(val).strip() == "":
                                        return None
                                return int(float(val)) # jika angaka desimal "(4.6)"
                        
                        tempat = models.Tempat(
                                nama          = row.get("nama").strip(),
                                kategori      = row.get("kategori"),
                                alamat        = row.get("alamat"),
                                rating        = save_float(row.get("rating")),
                                harga_min     = save_int(row.get("harga_min")),
                                harga_max     = save_int(row.get("harga_max")),
                                sumber        = row.get("sumber"),
                                deskripsi     = row.get("deskripsi"),
                                jam_buka      = row.get("jam_buka"),
                                jam_tutup     = row.get("jam_tutup"),
                                latitude      = save_float(row.get("latitude")),
                                longitude     = save_float(row.get("longitude")),
                                jumlah_review = save_int(row.get("jumlah_review"))
                        )
                        db.add(tempat)
                        berhasil = berhasil + 1
                except Exception as e:
                        gagal = gagal + 1
                        errors.append(f"Baris {idx + 2}: {str(e)}") # +2 karena header & index 0
        if berhasil > 0:
                db.commit()

        return {
                "message"      : "Import selesai",
                "berhasil"     : berhasil,
                "gagal"        : gagal,
                "detail_error" : errors[:5] # menapilkan 5 error pertama (untuk debugging)
                }

# PUT - edit data tempat berdasarkan ID
@router.put("/{tempat_id}", response_model=schemas.TempatResponse)
def update_tempat(tempat_id: int, data: schemas.TempatCreate, db: Session = Depends(get_db)):
        tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
        if not tempat:
                raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

        for key, value in data.model_dump().items():
                setattr(tempat, key, value)

        db.commit()
        db.refresh(tempat)
        return tempat

# DELETE - hapus data tempat berdasarkan ID
@router.delete("/{tempat_id}")
def delete_tempat(tempat_id: int, db: Session = Depends(get_db)):
        tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
        if not tempat:
                raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

        db.delete(tempat)
        db.commit()
        return {"message": f"Tempat dengan ID {tempat_id} berhasil dihapus"}

# PATCH - edit sebagian field saja
@router.patch("/{tempat_id}", response_model=schemas.TempatResponse)
def patch_tempat(tempat_id: int, data: schemas.TempatUpdate, db: Session = Depends(get_db)):
        tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
        if not tempat:
                raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

        # Hanya update field yang diisi, skip yang None
        for key, value in data.model_dump(exclude_none=True).items():
                setattr(tempat, key, value)

        db.commit()
        db.refresh(tempat)
        return tempat


def hitung_jarak(lat1, lon1, lat2, lon2):
        # Haversine Formula
        R = 6371 # Radius bumi dalam kilometer
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c # Jarak dalam kilometer



