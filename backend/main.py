# HouSmart/backend/main.py
from fastapi import FastAPI
from app.api.routes import health, property, education

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(property.router)
app.include_router(education.router)


@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}