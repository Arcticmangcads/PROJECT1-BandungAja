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

    user = db.query(models.User).filter(models.User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user

# POST /register
@router.post("/register", response_model=schemas.UserResponse)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    # Cek email sudah terdaftar atau belum
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    user_baru = models.User(
        nama     = data.nama,
        email    = data.email,
        password = hash_password(data.password)
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

@router.patch("/me", response_model=schemas.UserResponse)
def update_me(data: schemas.UserUpdate, db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user
