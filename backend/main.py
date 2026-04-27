from fastapi import FastAPI
from fastapi.security import HTTPBearer
from database import Base, engine
from routers import tempat, auth, wishlist, itinerary
from fastapi.middleware.cors import CORSMiddleware

security = HTTPBearer()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BandungAja API",
    version="1.6.2",
    swagger_ui_init_oauth={}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Diganti menjadi URL frontend saat deployment
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Routers
app.include_router(tempat.router)
app.include_router(auth.router)
app.include_router(wishlist.router)
app.include_router(itinerary.router)

@app.get("/")
def root():
    return {"message": "BandungAja API is running!"}
