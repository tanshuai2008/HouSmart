from fastapi import FastAPI
from app.api.routes import health, property

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(property.router)


@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}