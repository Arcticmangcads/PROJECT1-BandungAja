# backend/nearby.py
import requests
from supabase import create_client
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv
import os

load_dotenv()

# Koneksi ke Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_location():
    """Ambil lokasi user otomatis berdasarkan IP"""
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return {
                "lat"    : data['lat'],
                "lon"    : data['lon'],
                "city"   : data['city'],
                "status" : "success"
            }
        else:
            raise Exception("Gagal mendapatkan lokasi")
    except requests.exceptions.RequestException:
        return {
            "lat"    : -6.914744,
            "lon"    : 107.609810,
            "city"   : "Bandung",
            "status" : "default"
        }

def hitung_jarak(lat1, lon1, lat2, lon2):
    """Hitung jarak dua koordinat pakai Haversine Formula"""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 2)

def get_nearby(radius_km=5.0, kategori=None):
    """
    Ambil lokasi user lalu filter tempat terdekat dari Supabase
    kategori: 'Wisata' / 'Kuliner' / None (semua)
    """
    # 1. Ambil lokasi user
    lokasi = get_user_location()
    user_lat = lokasi['lat']
    user_lon = lokasi['lon']

    # 2. Ambil semua data dari Supabase
    query = supabase.table("destinations").select(
        "id, Nama, Kategori, Deskripsi, Image_url, Latitude, Longitude"
    )

    # Filter kategori kalau ada
    if kategori:
        query = query.eq("Kategori", kategori)

    response = query.execute()

    # Handle kalau data kosong atau Supabase gagal
    if not response.data:
        return {
            "lokasi_user"     : lokasi,
            "radius_km"       : radius_km,
            "jumlah_ditemukan": 0,
            "tempat_terdekat" : []
        }

    semua_tempat = response.data

    # 3. Hitung jarak dan filter radius
    hasil = []
    for tempat in semua_tempat:
        lat = tempat.get("Latitude")
        lon = tempat.get("Longitude")

        # Skip kalau koordinat kosong
        if lat is None or lon is None:
            continue

        jarak = hitung_jarak(user_lat, user_lon, lat, lon)

        if jarak <= radius_km:
            tempat["jarak_km"] = jarak
            hasil.append(tempat)

    # 4. Urutkan dari terdekat
    hasil.sort(key=lambda x: x["jarak_km"])

    return {
        "lokasi_user"     : lokasi,
        "radius_km"       : radius_km,
        "jumlah_ditemukan": len(hasil),
        "tempat_terdekat" : hasil
    }