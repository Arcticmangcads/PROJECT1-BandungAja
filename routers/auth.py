from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import hash_password, verify_password, create_token, decode_token
import models, schemas

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Dependency, mengambil user yang sedang login dari token
def get_current_user(
    credentials = Security(HTTPBearer()),
    db: Session = Depends(get_db)
):
    token = credentials.credentials      # Ambil token dari header
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah expired")

    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user

# Dependency, akses developer
def require_developer(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "developer":
        raise HTTPException(status_code=403,
                            detail="Akses ditolak. Hanya developer yang boleh mengakses endpoint ini."
        )
    return current_user

# POST - register
@router.post("/register", response_model=schemas.UserResponse)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    # Cek email sudah terdaftar atau belum
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    hashed_pw = hash_password(data.password)

    user_baru = models.User(
        nama_depan        = data.nama_depan,
        nama_belakang     = data.nama_belakang,
        email             = data.email,
        password          = hashed_pw,
        image_url         = data.image_url,
        lokasi            = data.lokasi
    )
    db.add(user_baru)
    db.commit()
    db.refresh(user_baru)
    return user_baru

# POST /login
@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Email atau password salah")

    token = create_token({"user_id": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type"  : "bearer",
        "user"        : user
    }

# GET /me (melihat profil pengguna)
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# PATCH — Update profil
@router.patch("/me", response_model=schemas.UserResponse)
def update_profile(
    data         : schemas.UserUpdate,
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):
    if data.nama_depan is not None:                    
        current_user.nama_depan = data.nama_depan      
    if data.nama_belakang is not None:                 
        current_user.nama_belakang = data.nama_belakang 
    if data.foto is not None:
        current_user.image_url = data.image_url
    if data.lokasi is not None:
        current_user.lokasi = data.lokasi

    db.commit()
    db.refresh(current_user)
    return current_user
