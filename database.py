import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
# load_dotenv(dotenv_path=dotenv_path) # Membaca file .env

DATABASE_URL = None

with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        # Abaikan baris kosong dan komentar
        if not line or line.startswith('#'):
            continue
        if line.startswith('DATABASE_URL='):
            # Ambil semua karakter setelah '=' pertama
            DATABASE_URL = line.split('=', 1)[1].strip()
            break

if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di .env")

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency, digunakan pada setiap endpoint yang membutuhkan akses database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
