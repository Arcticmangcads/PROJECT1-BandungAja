from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


# GET untuk melihat semua wishlist milik user yang login
@router.get("/", response_model=list[schemas.TempatResponse])
def get_wishlist(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Ambil wishlist user dengan pagination & urutan
    wishlist = (
        db.query(models.Wishlist)
        .filter(models.Wishlist.user_id == current_user.id)
        .order_by(models.Wishlist.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not wishlist:
        return []

    # Ambil semua tempat terkait dalam 1 query
    tempat_ids = [item.tempat_id for item in wishlist]
    tempat_dict = {
        t.id: t
        for t in db.query(models.Tempat).filter(models.Tempat.id.in_(tempat_ids)).all()
    }

    # Bangun hasil & konversi ke schema
    hasil = [
        schemas.TempatResponse.model_validate(tempat_dict[item.tempat_id])
        for item in wishlist
        if item.tempat_id in tempat_dict
    ]

    return hasil


# POST untuk menyimpan tempat ke wishlist
@router.post("/{tempat_id}")
def tambah_wishlist(
    tempat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Periksa tempat ada atau tidak
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    # Periksa sudah ada di wishlist atau belum
    existing = (
        db.query(models.Wishlist)
        .filter(
            models.Wishlist.user_id == current_user.id,
            models.Wishlist.tempat_id == tempat_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Tempat sudah ada di wishlist")

    wishlist_baru = models.Wishlist(
        user_id=current_user.id,
        tempat_id=tempat_id,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(wishlist_baru)
    db.commit()
    return {"message": f"{tempat.nama} berhasil ditambahkan ke wishlist"}


# DELETE untuk menghapus tempat dari wishlist
@router.delete("/{tempat_id}")
def hapus_wishlist(
    tempat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    wishlist = (
        db.query(models.Wishlist)
        .filter(
            models.Wishlist.user_id == current_user.id,
            models.Wishlist.tempat_id == tempat_id,
        )
        .first()
    )
    if not wishlist:
        raise HTTPException(status_code=404, detail="Tempat tidak ada di wishlist")

    db.delete(wishlist)
    db.commit()
    return {"message": "Tempat berhasil dihapus dari wishlist"}
