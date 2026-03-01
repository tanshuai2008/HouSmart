from fastapi import FastAPI
from app.api.routes import health
from app.api import median_price

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(median_price.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}