from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    crime_score,
    education,
    evaluation,
    flood,
    health,
    income,
    market_trends,
    median_house_price,
    noise_estimator,
    property,
    rent_estimate,
    road_map,
    school_scores,
    transit,
)

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HouSmart Backend API")

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
app.include_router(property.router)
app.include_router(education.router)
app.include_router(income.router)
app.include_router(evaluation.router)
app.include_router(crime_score.router)
app.include_router(transit.router)
app.include_router(flood.router)
app.include_router(school_scores.router)
app.include_router(rent_estimate.router)
app.include_router(market_trends.router)


@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
