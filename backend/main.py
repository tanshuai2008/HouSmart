from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, median_house_price, noise_estimator, road_map

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HouSmart Backend API")

# Allow the Next.js dev server (and configurable prod origins) to call the API.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(median_house_price.router)
app.include_router(noise_estimator.router)
app.include_router(road_map.router)


@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
