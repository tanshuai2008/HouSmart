from fastapi import FastAPI
from app.api.routes import health, property
from app.core.db_init import init_db

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(property.router)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}