from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import health, noise_estimator, road_map

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HouSmart Noise Score API")

app.include_router(health.router)
app.include_router(noise_estimator.router)
app.include_router(road_map.router)


@app.get("/")
def root():
    return {"message": "HouSmart Noise Score Backend Running"}