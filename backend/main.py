from fastapi import FastAPI
from app.api.routes import health

app = FastAPI(title="HouSmart API")

app.include_router(health.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}