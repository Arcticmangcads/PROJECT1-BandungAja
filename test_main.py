import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from auth_utils import create_token, hash_password
import models

# Setup database test in-memory
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Fixture untuk menyiapkan tabel sebelum test
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ========= AUTH TESTS =========
def test_register():
    res = client.post("/api/auth/register", json={
        "nama": "Test User",
        "email": "test@example.com",
        "password": "rahasia123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_register_duplicate():
    client.post("/api/auth/register", json={"nama":"A","email":"dupe@example.com","password":"pw"})
    res = client.post("/api/auth/register", json={"nama":"B","email":"dupe@example.com","password":"pw"})
    assert res.status_code == 400

def test_login_success():
    # register dulu
    client.post("/api/auth/register", json={"email":"login@test.com","password":"secret"})
    res = client.post("/api/auth/login", json={"email":"login@test.com","password":"secret"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_fail():
    res = client.post("/api/auth/login", json={"email":"wrong@test.com","password":"wrong"})
    assert res.status_code == 401

def test_get_me():
    # buat user dan token
    db = TestingSessionLocal()
    user = models.User(email="me@test.com", password=hash_password("pw"), nama="Me")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"user_id": user.id, "email": user.email})
    db.close()

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@test.com"

def test_update_me():
    db = TestingSessionLocal()
    user = models.User(email="update@test.com", password=hash_password("pw"), nama="Old")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"user_id": user.id, "email": user.email})
    db.close()

    res = client.patch("/api/auth/me", json={"nama": "New Name"},
                        headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["nama"] == "New Name"

# ========= TEMPAT TESTS =========
def test_get_tempat_empty():
    res = client.get("/api/tempat/")
    assert res.status_code == 200
    assert res.json() == []

def test_create_tempat():
    res = client.post("/api/tempat/", json={
        "nama": "Test Kafe",
        "kategori": "kuliner",
        "rating": 4.5,
        "harga_min": 20000
    })
    assert res.status_code == 200
    data = res.json()
    assert data["nama"] == "Test Kafe"

def test_get_tempat_by_id():
    # buat dulu
    create_res = client.post("/api/tempat/", json={"nama":"Tempat X"})
    id = create_res.json()["id"]
    res = client.get(f"/api/tempat/{id}")
    assert res.status_code == 200
    assert res.json()["nama"] == "Tempat X"

def test_get_tempat_by_id_notfound():
    res = client.get("/api/tempat/9999")
    assert res.status_code == 404

def test_filter_tempat_kategori():
    client.post("/api/tempat/", json={"nama":"Wisata A","kategori":"wisata"})
    client.post("/api/tempat/", json={"nama":"Kuliner B","kategori":"kuliner"})
    res = client.get("/api/tempat/?kategori=wisata")
    data = res.json()
    assert len(data) == 1 and data[0]["nama"] == "Wisata A"

def test_filter_tempat_budget():
    client.post("/api/tempat/", json={"nama":"Murah","harga_min":10000})
    client.post("/api/tempat/", json={"nama":"Mahal","harga_min":50000})
    res = client.get("/api/tempat/?budget=30000")
    data = res.json()
    assert len(data) == 1 and data[0]["nama"] == "Murah"

def test_sort_by_rating():
    client.post("/api/tempat/", json={"nama":"B","rating":4.0})
    client.post("/api/tempat/", json={"nama":"A","rating":4.5})
    res = client.get("/api/tempat/?sort_by=rating")
    data = res.json()
    assert data[0]["rating"] == 4.5

def test_hidden_gem():
    client.post("/api/tempat/", json={"nama":"Hidden","rating":4.5,"jumlah_review":50})
    client.post("/api/tempat/", json={"nama":"Populer","rating":4.0,"jumlah_review":200})
    res = client.get("/api/tempat/hidden-gem?min_rating=4.0&max_review=100")
    data = res.json()
    assert len(data) == 1 and data[0]["nama"] == "Hidden"

def test_nearby():
    client.post("/api/tempat/", json={
        "nama":"Dekat",
        "latitude": -6.9050,
        "longitude": 107.6150
    })
    client.post("/api/tempat/", json={
        "nama":"Jauh",
        "latitude": -6.5000,
        "longitude": 107.0000
    })
    res = client.get("/api/tempat/nearby?lat=-6.905&lon=107.615&radius=1")
    data = res.json()
    assert len(data) == 1 and data[0]["nama"] == "Dekat"

def test_import_csv():
    csv_content = "nama,kategori,rating\nDago Dreampark,wisata,4.3\nParis Van Java,wisata,4.5\n"
    file = io.BytesIO(csv_content.encode("utf-8"))
    res = client.post("/api/tempat/import-csv", files={"file": ("test.csv", file, "text/csv")})
    assert res.status_code == 200
    data = res.json()
    assert data["berhasil"] == 2
    assert data["gagal"] == 0

def test_update_tempat():
    create_res = client.post("/api/tempat/", json={"nama":"Update Me"})
    id = create_res.json()["id"]
    res = client.put(f"/api/tempat/{id}", json={"nama":"Updated"})
    assert res.status_code == 200 and res.json()["nama"] == "Updated"

def test_patch_tempat():
    create_res = client.post("/api/tempat/", json={"nama":"Patch Me","rating":4.0})
    id = create_res.json()["id"]
    res = client.patch(f"/api/tempat/{id}", json={"rating": 3.0})
    assert res.status_code == 200 and res.json()["rating"] == 3.0
    assert res.json()["nama"] == "Patch Me"  # tidak berubah

def test_delete_tempat():
    create_res = client.post("/api/tempat/", json={"nama":"Delete Me"})
    id = create_res.json()["id"]
    res = client.delete(f"/api/tempat/{id}")
    assert res.status_code == 200
    res2 = client.get(f"/api/tempat/{id}")
    assert res2.status_code == 404

# ========= WISHLIST TESTS =========
@pytest.fixture
def auth_user():
    db = TestingSessionLocal()
    user = models.User(email="wish@test.com", password=hash_password("pw"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"user_id": user.id, "email": user.email})
    db.close()
    return token

@pytest.fixture
def sample_tempat():
    res = client.post("/api/tempat/", json={"nama":"Wishlist Place"})
    return res.json()["id"]

def test_add_wishlist(auth_user, sample_tempat):
    res = client.post(f"/api/wishlist/{sample_tempat}",
                      headers={"Authorization": f"Bearer {auth_user}"})
    assert res.status_code == 200

def test_add_wishlist_duplicate(auth_user, sample_tempat):
    client.post(f"/api/wishlist/{sample_tempat}", headers={"Authorization": f"Bearer {auth_user}"})
    res = client.post(f"/api/wishlist/{sample_tempat}",
                      headers={"Authorization": f"Bearer {auth_user}"})
    assert res.status_code == 400

def test_get_wishlist(auth_user, sample_tempat):
    client.post(f"/api/wishlist/{sample_tempat}", headers={"Authorization": f"Bearer {auth_user}"})
    res = client.get("/api/wishlist/", headers={"Authorization": f"Bearer {auth_user}"})
    data = res.json()
    assert len(data) == 1 and data[0]["nama"] == "Wishlist Place"

def test_delete_wishlist(auth_user, sample_tempat):
    client.post(f"/api/wishlist/{sample_tempat}", headers={"Authorization": f"Bearer {auth_user}"})
    res = client.delete(f"/api/wishlist/{sample_tempat}",
                        headers={"Authorization": f"Bearer {auth_user}"})
    assert res.status_code == 200
    res2 = client.get("/api/wishlist/", headers={"Authorization": f"Bearer {auth_user}"})
    assert len(res2.json()) == 0

# ========= ITINERARY TESTS (revisi - pakai query params) =========
@pytest.fixture
def auth_user_itinerary():
    db = TestingSessionLocal()
    user = models.User(email="itinerary@test.com", password=hash_password("pw"))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"user_id": user.id, "email": user.email})
    db.close()
    return token

@pytest.fixture
def sample_place_for_itinerary():
    res = client.post("/api/tempat/", json={"nama":"Tempat A"})
    return res.json()["id"]

def test_create_itinerary(auth_user_itinerary):
    # query param: judul & total_hari
    res = client.post(
        "/api/itinerary/?judul=Liburan&total_hari=2",
        headers={"Authorization": f"Bearer {auth_user_itinerary}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["judul"] == "Liburan"
    assert data["total_hari"] == 2

def test_get_itineraries(auth_user_itinerary):
    client.post("/api/itinerary/?judul=Plan A&total_hari=1",
                headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    res = client.get("/api/itinerary/", headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    assert len(res.json()) == 1

def test_add_item_to_itinerary(auth_user_itinerary, sample_place_for_itinerary):
    # buat itinerary dulu
    iti_res = client.post("/api/itinerary/?judul=Trip&total_hari=3",
                          headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    iti_id = iti_res.json()["id"]
    # tambah item (POST item menggunakan query param juga)
    res = client.post(
        f"/api/itinerary/{iti_id}/item?tempat_id={sample_place_for_itinerary}&hari=1&urutan=1",
        headers={"Authorization": f"Bearer {auth_user_itinerary}"}
    )
    assert res.status_code == 200

def test_get_itinerary_detail(auth_user_itinerary, sample_place_for_itinerary):
    iti_res = client.post("/api/itinerary/?judul=Detail&total_hari=1",
                          headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    iti_id = iti_res.json()["id"]
    client.post(f"/api/itinerary/{iti_id}/item?tempat_id={sample_place_for_itinerary}&hari=1&urutan=1",
                headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    res = client.get(f"/api/itinerary/{iti_id}",
                     headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    data = res.json()
    assert "jadwal" in data
    assert "Hari 1" in data["jadwal"]

def test_delete_item_from_itinerary(auth_user_itinerary, sample_place_for_itinerary):
    iti_res = client.post("/api/itinerary/?judul=DelItem&total_hari=1",
                          headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    iti_id = iti_res.json()["id"]
    # tambah item
    client.post(f"/api/itinerary/{iti_id}/item?tempat_id={sample_place_for_itinerary}&hari=1&urutan=1",
                headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    # ambil item_id dari detail
    detail = client.get(f"/api/itinerary/{iti_id}",
                        headers={"Authorization": f"Bearer {auth_user_itinerary}"}).json()
    item_id = detail["jadwal"]["Hari 1"][0]["item_id"]
    # hapus item
    res = client.delete(f"/api/itinerary/{iti_id}/item/{item_id}",
                        headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    assert res.status_code == 200
    detail2 = client.get(f"/api/itinerary/{iti_id}",
                         headers={"Authorization": f"Bearer {auth_user_itinerary}"}).json()
    assert len(detail2["jadwal"]) == 0

def test_delete_itinerary(auth_user_itinerary):
    iti_res = client.post("/api/itinerary/?judul=Hapus&total_hari=1",
                          headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    iti_id = iti_res.json()["id"]
    res = client.delete(f"/api/itinerary/{iti_id}",
                        headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    assert res.status_code == 200
    res2 = client.get("/api/itinerary/", headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    assert len(res2.json()) == 0

def test_create_itinerary_item_excessive_day(auth_user_itinerary, sample_place_for_itinerary):
    iti_res = client.post("/api/itinerary/?judul=Short&total_hari=1",
                          headers={"Authorization": f"Bearer {auth_user_itinerary}"})
    iti_id = iti_res.json()["id"]
    res = client.post(
        f"/api/itinerary/{iti_id}/item?tempat_id={sample_place_for_itinerary}&hari=2&urutan=1",
        headers={"Authorization": f"Bearer {auth_user_itinerary}"}
    )
    assert res.status_code == 404  # melebihi total_hari
