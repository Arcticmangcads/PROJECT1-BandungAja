from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Security, UploadFile, File
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import hash_password, verify_password, create_token, decode_token
import models, schemas, os, httpx

SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "profile-photos")

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
    if data.image_url is not None:
        current_user.image_url = data.image_url
    if data.lokasi is not None:
        current_user.lokasi = data.lokasi

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/photo", response_model=schemas.UserResponse)
async def upload_photo(
    file         : UploadFile  = File(...),
    db           : Session     = Depends(get_db),
    current_user : models.User = Depends(get_current_user)
):

    # Validasi tipe file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus barupa gambar")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran foto maksimal 5MB")

    # Nama file unik per user
    ext        = file.filename.split(".")[-1]
    filename   = f"user_{current_user.id}.{ext}"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            upload_url,
            content  = contents,
            headers  = {
                "Authorization" : f"Bearer {SUPABASE_KEY}",
                "Content-Type"  : file.content_type,
                "x-upsert"      : "true"    # overwrite jika sudah ada
            }
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail="Gagal upload ke Supabase")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
    current_user.image_url = public_url
    db.commit()
    db.refresh(current_user)
    return current_user
    
