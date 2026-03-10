<<<<<<< HEAD
<<<<<<< HEAD
from pathlib import Path
=======
# HouSmart/backend/main.py
from fastapi import FastAPI
from app.api.routes import health, property, education, income, evaluation
>>>>>>> origin/Census-Tract-Mapping
=======
from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import health
from app.api.routes import crime_score

# Load environment variables from .env
load_dotenv()
>>>>>>> origin/Jhanvi_CrimeScore

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
<<<<<<< HEAD
<<<<<<< HEAD
app.include_router(median_house_price.router)
app.include_router(noise_estimator.router)
app.include_router(road_map.router)

=======
app.include_router(property.router)
app.include_router(education.router)
app.include_router(income.router)
app.include_router(evaluation.router)
>>>>>>> origin/Census-Tract-Mapping
=======
app.include_router(crime_score.router)
>>>>>>> origin/Jhanvi_CrimeScore

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
