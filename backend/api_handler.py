# backend/api_handler.py
import requests

def get_user_location():
    """Ambil lokasi user otomatis berdasarkan IP"""
    try:
        response = requests.get('http://ip-api.com/json/')
        data = response.json()
        
        if data['status'] == 'success':
            return {
                "lat"    : data['lat'],
                "lon"    : data['lon'],
                "city"   : data['city'],
                "status" : "success"
            }
        else:
            raise Exception("Gagal")
            
    except:
        # Default ke Alun-Alun Bandung kalau gagal/offline
        return {
            "lat"    : -6.914744,
            "lon"    : 107.609810,
            "city"   : "Bandung",
            "status" : "default"
        }

def hitung_jarak(lat1, lon1, lat2, lon2):
    """Hitung jarak antara dua koordinat (km) pakai Haversine Formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Radius bumi dalam kilometer
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 2)  # Jarak dalam km, dibulatkan 2 desimal

def filter_nearby(tempat_list, lat, lon, radius_km=5.0):
    """Filter list tempat berdasarkan radius dari lokasi user"""
    hasil = []
    for tempat in tempat_list:
        jarak = hitung_jarak(lat, lon, tempat['latitude'], tempat['longitude'])
        if jarak <= radius_km:
            tempat['jarak_km'] = jarak  # tambahkan info jarak ke datanya
            hasil.append(tempat)
    
    # Urutkan dari yang terdekat
    hasil.sort(key=lambda x: x['jarak_km'])
    return hasil