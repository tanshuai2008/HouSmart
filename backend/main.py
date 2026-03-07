from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from app.middleware.api_call_logger import api_call_logger_middleware
from app.api.routes import (
    amenity_score,
    crime_score,
    education,
    flood,
    health,
    income,
    median_house_price,
    noise_estimator,
    rent_estimate,
    transit,
)
from app.api.routes import auth

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HouSmart API")
app.middleware("http")(api_call_logger_middleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(education.router)
app.include_router(income.router)
app.include_router(amenity_score.router)
app.include_router(crime_score.router)
app.include_router(flood.router)
app.include_router(transit.router)
app.include_router(rent_estimate.router)
app.include_router(noise_estimator.router)
app.include_router(median_house_price.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
