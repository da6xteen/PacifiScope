from fastapi import FastAPI
from routes import analytics

app = FastAPI(title="PacifiScope API")

@app.get("/")
async def root():
    return {"message": "Welcome to PacifiScope API"}

app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
