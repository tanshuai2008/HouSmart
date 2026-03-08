from fastapi import FastAPI
from app.api.routes import health
from app.api.routes.school_scores import router as school_router


app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(school_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}