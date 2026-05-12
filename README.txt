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

Backend: 
http://localhost:8000/docs

Frontend:
http://127.0.0.1:5500/frontend/index.html

UserTest:
{
  "nama": "Galala",
  "email": "lila@gmail.com",
  "password": "Gilali234"
}

UPDATE user_profiles SET role = 'developer' WHERE email = 'Fatih213@devgmail.com';

DevTest:
{
  "nama": "Fatih",
  "email": "Fatih@devgmail.com",
  "password": "Nimi3151"
}
{
  "nama": "AlFatih",
  "email": "Fatih213@devgmail.com",
  "password": "132Nimi1461"
}