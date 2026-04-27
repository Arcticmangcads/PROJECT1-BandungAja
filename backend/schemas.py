from pydantic import BaseModel
from typing import Optional

class TempatResponse(BaseModel):
    id            : int
    nama          : str
    kategori      : Optional[str]
    alamat        : Optional[str]
    rating        : Optional[float]
    harga_min     : Optional[int]
    harga_max     : Optional[int]
    sumber        : Optional[str]   = None
    deskripsi     : Optional[str]   = None  # detail tempat
    jam_buka      : Optional[str]   = None  # waktu buka
    jam_tutup     : Optional[str]   = None  # waktu tutup
    latitude      : Optional[float] = None  # Nerby
    longitude     : Optional[float] = None  # Nerby
    jumlah_review : Optional[int]   = None  # Hidden Gem


    class Config:
        from_attributes = True

class TempatCreate(BaseModel):
    nama          : str
    kategori      : Optional[str]   = None
    alamat        : Optional[str]   = None
    rating        : Optional[float] = None
    harga_min     : Optional[int]   = None
    harga_max     : Optional[int]   = None
    sumber        : Optional[str]   = None
    deskripsi     : Optional[str]   = None  
    jam_buka      : Optional[str]   = None  
    jam_tutup     : Optional[str]   = None  
    latitude      : Optional[float] = None  
    longitude     : Optional[float] = None  
    jumlah_review : Optional[int]   = None  

class TempatUpdate(BaseModel):
    nama          : Optional[str]   = None
    kategori      : Optional[str]   = None
    alamat        : Optional[str]   = None
    rating        : Optional[float] = None
    harga_min     : Optional[int]   = None
    harga_max     : Optional[int]   = None
    sumber        : Optional[str]   = None
    deskripsi     : Optional[str]   = None  
    jam_buka      : Optional[str]   = None
    jam_tutup     : Optional[str]   = None
    latitude      : Optional[float] = None  
    longitude     : Optional[float] = None  
    jumlah_review : Optional[int]   = None

# === AUTH ===
class UserRegister(BaseModel):
    nama     : Optional[str] = None
    email    : str
    password : str

class UserLogin(BaseModel):
    email    : str
    password : str

class UserResponse(BaseModel):
    id     : int
    nama   : Optional[str]
    email  : str
    foto   : Optional[str] = None
    lokasi : Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    nama   : Optional[str] = None
    foto   : Optional[str] = None
    lokasi : Optional[str] = None

class TokenResponse(BaseModel):
    access_token : str
    token_type   : str
    user         : UserResponse
