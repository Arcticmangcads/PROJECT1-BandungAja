from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional
import requests
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/tempat", tags=["Tempat"])

def get_user_location_by_ip():
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return {
                "lat": data['lat'],
                "lon": data['lon'],
                "city": data['city'],
                "status": "success"
            }
        else:
            raise Exception("Gagal mendeteksi lokasi")
    except Exception:
        return {
            "lat": -6.914744,
            "lon": 107.609810,
            "city": "Bandung",
            "status": "default"
        }

def hitung_jarak_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 2)

@router.get("/nearby", response_model=List[schemas.TempatResponse])
def get_nearby_places(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius: float = Query(5.0, description="Radius dalam kilometer"),
    kategori: Optional[str] = Query(None, description="wisata / kuliner"),
    db: Session = Depends(get_db)
):
    if lat is None or lon is None:
        lokasi_auto = get_user_location_by_ip()
        user_lat = lokasi_auto["lat"]
        user_lon = lokasi_auto["lon"]
    else:
        user_lat = lat
        user_lon = lon

    query = db.query(models.Tempat)
    if kategori:
        query = query.filter(models.Tempat.kategori == kategori)
    
    semua_tempat = query.all()
    hasil = []

    for tempat in semua_
