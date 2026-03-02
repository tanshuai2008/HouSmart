from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.routes import health
from app.api.routes import rent_estimate

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="HouSmart API")

app.include_router(health.router)
app.include_router(rent_estimate.router)

@app.get("/")
def root():
    return {"message": "HouSmart Backend Running"}
