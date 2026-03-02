from fastapi import FastAPI
from app.api.routes import health
from app.api.routes import transit

app = FastAPI(title="HouSmart Transit Score API")

app.include_router(health.router)
app.include_router(transit.router)

@app.get("/")
def root():
    return {"message": "HouSmart Transit Score Backend Running"}
