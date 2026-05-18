import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from os import getenv

env_path = Path(__file__).parent / '.env'

DATABASE_URL = os.getenv('DATABASE_URL')

with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('DATABASE_URL='):
            DATABASE_URL = line.split('=', 1)[1].strip()
            break

if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,       # Reset koneksi setiap 5 menit
    pool_size=5,            # Batasi jumlah koneksi agar tidak membebani Supabase free tier
    max_overflow=10,
    execution_options={"prepare_threshold": None},
    connect_args={
        "options": "-c timezone=utc",
        "sslmode": "require"
    }
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
