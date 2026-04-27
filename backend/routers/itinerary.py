from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from datetime import datetime
import models, schemas

router = APIRouter(prefix="/api/itinerary", tags=["Itinerery"])

# GET untuk melihat semua itinerary milik user (user perlu login)
@router.get("/")
def get_itinerary(
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user) 
):
    itinerary_list = db.query(models.Itinerary)\
        .filter(models.Itinerary.user_id == current_user.id)\
        .all()
    return itinerary_list

# POST untuk itinerary baru
@router.post("/")
def buat_itinerary(
    judul        : str,
    total_hari   : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    itinerary_baru = models.Itinerary(
        user_id    = current_user.id,
        judul      = judul,
        total_hari = total_hari,
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(itinerary_baru)
    db.commit()
    db.refresh(itinerary_baru)
    return itinerary_baru

# GET untuk detail satu itinerary besarta dafter tempat per hari
@router.get("/{itinerary_id}")
def get_detail_itinerary(
    itinerary_id : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itenerary tidak ditemukan")

    # Mengambil semua item dan menyusun hari
    item = db.query(models.ItineraryItem)\
        .filter(models.ItineraryItem.itinerary_id == itinerary_id)\
        .order_by(models.ItineraryItem.hari, models.ItineraryItem.urutan)\
        .all()

    jadwal = {}
    for item in item:
        tempat = db.query(models.Tempat).filter(models.Tempat.id == item.tempat_id).first()
        hari_key = f"Hari {item.hari}"
        if hari_key not in jadwal:
            jadwal[hari_key] = []
        jadwal[hari_key].append({
            "item_id" : item.id,
            "urutan"  : item.urutan,
            "jam"     : item.jam,
            "catatan" : item.catatan,
            "tempat"  : {
                "id"       : tempat.id,
                "nama"     : tempat.nama,
                "kategori" : tempat.kategori,
                "alamat"   : tempat.alamat,
                "rating"   : tempat.rating
            } if tempat else None 
        })

    return {
        "id"         : itinerary.id,
        "judul"      : itinerary.judul,
        "total_hari" : itinerary.total_hari,
        "created_at" : itinerary.created_at,
        "jadwal"     : jadwal
    }

# POST untuk menambah tempat ke itinerary pada hari tertentu
@router.post("/{itinerary_id}/item")
def tambah_item(
    itinerary_id : int,
    tempat_id    : int,
    hari         : int,
    urutan       : int,
    jam          : str = None,
    catatan      : str = None,
    db           : Session = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    # Periksa itinerary user ini
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    # Periksa tempat
    tempat = db.query(models.Tempat).filter(models.Tempat.id == tempat_id).first()
    if not tempat:
        raise HTTPException(status_code=404, detail="Tempat tidak ditemukan")

    # Periksa hari agar tidak melebihi total_hari
    if hari > itinerary.total_hari:
        raise HTTPException(
            status_code=404,
            detail=f"Hari {hari} melebihi total hari itinerary ({itinerary.total_hari} hari)"
        )

    item_baru = models.ItineraryItem(
        itinerary_id = itinerary_id,
        tempat_id    = tempat_id,
        hari         = hari,
        urutan       = urutan,
        jam          = jam,
        catatan      = catatan
    )
    db.add(item_baru)
    db.commit()
    db.refresh(item_baru)
    return {"message": f"{tempat.nama} berhasil ditambahkan ke Hari {hari}"}

# DELETE untuk menghapus itinerary
@router.delete("/{itinerary_id}")
def hapus_itinerary(
    itinerary_id : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")

    # Menghapus semua item dahulu baru menghapus itinerary
    db.query(models.ItineraryItem)\
        .filter(models.ItineraryItem.itinerary_id == itinerary_id)\
        .delete()

    db.delete(itinerary)
    db.commit()
    return {"message": f"Itinerary '{itinerary.judul}' berhasil dihapus"}

# DELETE untuk 1 item dari itinerary
@router.delete("/{itinerary_id}/item/{item_id}")
def hapus_item(
    itinerary_id : int,
    item_id      : int,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    # Periksa itinerary milik user
    itinerary = db.query(models.Itinerary).filter(
        models.Itinerary.id      == itinerary_id,
        models.Itinerary.user_id == current_user.id
    ).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary tidak ditemukan")
    
    # Periksa item yang ada
    item = db.query(models.ItineraryItem).filter(
        models.ItineraryItem.id           == item_id,
        models.ItineraryItem.itinerary_id == itinerary_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")

    db.delete(item)
    db.commit()
    return {"message": f"Item berhasil dihapus dari Hari {item.hari}"}
