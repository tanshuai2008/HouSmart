from fastapi import FastAPI
from app.api.routes import health
from app.api.evaluation import router as evaluation_router
from app.api.test_endpoint import router as test_router


app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(evaluation_router)
app.include_router(test_router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}