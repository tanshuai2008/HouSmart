from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.api_call_logger import api_call_logger_middleware
from app.api.routes import (
    analysis,
    amenity_score,
    onboarding,
    crime_score,
    education,
    flood,
    health,
    income,
    median_house_price,
    noise_estimator,
    rent_estimate,
    transit,
    school_scores,
)
from app.api.routes import auth

load_dotenv(Path(__file__).resolve().parent / ".env")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

app = FastAPI(title="HouSmart API")
app.middleware("http")(api_call_logger_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(analysis.router)
app.include_router(education.router)
app.include_router(income.router)
app.include_router(amenity_score.router)
app.include_router(crime_score.router)
app.include_router(flood.router)
app.include_router(transit.router)
app.include_router(rent_estimate.router)
app.include_router(noise_estimator.router)
app.include_router(median_house_price.router)
app.include_router(school_scores.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
