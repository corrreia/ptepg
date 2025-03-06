from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader

app = FastAPI(
    title="Client API",
    docs_url="/docs",  # Always show Swagger UI
    redoc_url="/redoc",
)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


def get_api_key(key: str = Depends(API_KEY_HEADER)):
    if key != "your_secret_api_key":  # Replace with actual validation logic
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key


@app.get("/api/data")
async def get_data(key: str = Depends(get_api_key)):
    return {"data": "protected data"}
