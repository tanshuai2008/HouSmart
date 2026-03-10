from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routes import health, median_house_price

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HouSmart Median House Price API")

app.include_router(health.router)
app.include_router(median_house_price.router)


@app.get("/")
def root():
    return {"message": "HouSmart Median House Price Backend Running"}