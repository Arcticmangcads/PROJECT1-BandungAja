from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import Optional
from datetime import datetime
import models, schemas

router = APIRouter(prefix="/api/status", tags=["Status Tempat"])

VALID_STATUS = [
    "buka",
    "tutup",
    "tutup_sementara",
    "renovasi",
    "pindah",
    "insiden",
    "tutup_permanen"
]

# POST untuk set status tempat
@router.post("/{tempat_id}", response_model=schemas.StatusTempatResponse)
def set_status(
    tempat_id : int,
    data      : schemas.StatusTempatCreate,
    db        : Session = Depends(get_db)
):
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    if data.status not in VALID_STATUS:
        raise HTTPException(
            status_code=400,
            detail=f"Status tidak valid. Pilihan: {', '.join(VALID_STATUS)}"
        )

    status_baru = models.StatusTempat(
        tempat_id  = tempat_id,
        status     = data.status,
        keterangan = data.keterangan,
        mulai      = data.mulai,
        sampai     = data.sampai,
        update_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(status_baru)
    db.commit()
    db.refresh(status_baru)
    return status_baru

# GET untuk melihat status terkini satu tempat
@router.get("/{tempat_id}", response_model=schemas.StatusTempatResponse)
def get_status(tempat_id: int, db: Session = Depends(get_db)):
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    status = db.query(models.StatusTempat)\
             .filter(models.StatusTempat.tempat_id == tempat_id)\
             .order_by(models.StatusTempat.update_at.desc())\
             .first()

    if not status:
        raise HTTPException(status_code=404, detail="Status tempat belum tersedia")

    return status

# GET melihat riwayat status suatu tempat
@router.get("/{tempat_id}/riwayat", response_model=list[schemas.StatusTempatResponse])
def get_riwayat_status(tempat_id: int, db: Session = Depends(get_db)):
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    riwayat = db.query(models.StatusTempat)\
              .filter(models.StatusTempat.tempat_id == tempat_id)\
              .order_by(models.StatusTempat.update_at.desc())\
              .all()
    
    return riwayat

# GET untuk mendapatkan banyak tempat (untuk frontend)
@router.get("/batch/")
def get_status_batch(ids: Optional[str] = None, db: Session = Depends(get_db)):
    if not ids:
        return {}

    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
    except ValueError:
        raise HTTPException(400, "Format ids tidak valid, gunakan angka dipisah koma")

    result = {}
    for tid in id_list:
        status = db.query(models.StatusTempat)\
                 .filter(models.StatusTempat.tempat_id == tid)\
                 .order_by(models.StatusTempat.update_at.desc())\
                 .first()
        if status:
            result[tid] = {
                "id": status.id,
                "tempat_id": status.tempat_id,
                "status": status.status,
                "keterangan": status.keterangan,
                "mulai": status.mulai,
                "sampai": status.sampai,
                "update_at": status.update_at
            }
    return result
