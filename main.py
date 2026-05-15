from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routers import tempat, auth, wishlist, itinerary, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os
load_dotenv()

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

app.mount("/static", StaticFiles(
    directory="../bandungaja-frontend",
    html=True
    ), name="static")

# Routers
app.include_router(tempat.router)
app.include_router(auth.router)
app.include_router(wishlist.router)
app.include_router(itinerary.router)
app.include_router(status.router)

@app.get("/")
def root():
    return {"message": "BandungAja API is running!"}

frontend_path = os.getenv("FRONTEND_PATH")
if frontend_path:
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
