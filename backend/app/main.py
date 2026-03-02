from fastapi import FastAPI
from app.api.routes import health
from app.api.routes import flood

app = FastAPI(title="HouSmart Flood Risk API")

app.include_router(health.router)
app.include_router(flood.router)

@app.get("/")
def root():
    return {"message": "HouSmart Flood Risk Backend Running"}
