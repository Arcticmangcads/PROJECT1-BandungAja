from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from datetime import datetime
import models, schemas

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])

# GET untuk melihat semua wishlist milik user yang login
@router.get("/", response_model=list[schemas.TempatResponse])
def get_wishlist(
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    wishlist = db.query(models.Wishlist)\
        .filter(models.Wishlist.user_id == current_user.id)\
        .all()

    hasil = []
    for item in wishlist:
        tempat = db.query(models.Tempat).filter(models.Tempat.id == item.tempat_id).first()
        if tempat:
            hasil.append(tempat)
    return hasil

# POST untuk menyimpan tempat ke wishlist
@router.post("/{tempat_id}")
def tambah_wishlist(
    tempat_id    : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    # Periksa tempat ada atau tidak
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    # Periksa sudah ada di wishlist atau belum
    existing = db.query(models.Wishlist).filter(
        models.Wishlist.user_id   == current_user.id,
        models.Wishlist.tempat_id == tempat_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tempat sudah ada di wishlist")

    wishlist_baru = models.Wishlist(
        user_id    = current_user.id,
        tempat_id  = tempat_id,
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    )
    db.add(wishlist_baru)
    db.commit()
    return {"message": f"{tempat.nama} berhasil ditambahkan ke wishlist"}

# DELETE untuk menghapus tempat dari wishlist
@router.delete("/{tempat_id}")
def hapus_wishlist(
    tempat_id    : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    wishlist = db.query(models.Wishlist).filter(
        models.Wishlist.user_id   == current_user.id,   
        models.Wishlist.tempat_id == tempat_id
    ).first()
    if not wishlist:
        raise HTTPException(status_code=404, detail="Tempat tidak ada di wishlist")

    db.delete(wishlist)
    db.commit()
    return {"message": "Tempat berhasil dihapus dari wishlist"}
