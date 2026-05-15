## Database
- Development : SQLite (file `bandungaja.db`, otomatis terbuat saat pertama dijalankan)
- Production  : PostgreSQL (ganti DATABASE_URL di .env)

# Buat virtual environment khusus proyek ini
python -m venv venv

# Aktifkan
venv\Scripts\activate  # Windows

# Install dependency backend
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv

# Run program
uvicorn main:app --reload

http://localhost:8000/docs