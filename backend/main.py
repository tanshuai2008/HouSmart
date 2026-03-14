from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.api_call_logger import api_call_logger_middleware
from app.api.routes import (
    analysis,
    onboarding,
    health,
    market_trends,
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
        "https://housmart.onrender.com",
        "https://hou-smart.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(analysis.router)
app.include_router(market_trends.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
