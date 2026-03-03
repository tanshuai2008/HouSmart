# HouSmart/backend/main.py
from fastapi import FastAPI
from app.api.routes import health, property, education, income, evaluation

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(property.router)
app.include_router(education.router)
app.include_router(income.router)
app.include_router(evaluation.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}