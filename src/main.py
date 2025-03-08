import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from api.private.auth import router as auth_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from jobs.epg import get_meo_epg
from utils.logger import logger
from utils.db import initialize_database

# Load environment variables from .env file
load_dotenv()

# Call this before using any database operations
initialize_database()

# Determine if we're in development mode
is_dev = os.getenv("ENVIRONMENT") == "dev"
if is_dev:
    logger.info("Running in development mode.")

# Client API (always with Swagger UI and ReDoc)
public_app = FastAPI(
    title="Client API",
    description="Public API for subscription-based access",
    version="1.0.0",
    docs_url="/docs",  # Always show Swagger UI
    redoc_url="/redoc",  # Always show ReDoc
)

# Dashboard API (Swagger UI and ReDoc only in dev mode)
private_app = FastAPI(
    title="Dashboard API",
    description="Management API for API keys and subscriptions",
    version="1.0.0",
    docs_url="/docs" if is_dev else None,  # Show Swagger UI only in dev
    redoc_url="/redoc" if is_dev else None,  # Show ReDoc only in dev
)

# Add CORS middleware (for frontend access)
for app in [public_app, private_app]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Adjust for your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

private_app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET_KEY", "your-secret-key-here"
    ),  # Use a secure key
)

# Mount routers to respective apps
# Include auth_router without prefix to avoid double '/auth/' in paths
private_app.include_router(auth_router)  # Fixed: Removed prefix="/auth"

# client_app.include_router(client_router, prefix="/api/v1", tags=["Client"])
# dashboard_app.include_router(users_router, prefix="/manage", tags=["Users"])
# dashboard_app.include_router(
#     subscriptions_router, prefix="/manage", tags=["Subscriptions"]
# )
# dashboard_app.include_router(api_keys_router, prefix="/manage", tags=["API Keys"])

# Root app to combine both
root_app = FastAPI()

# Mount the client and dashboard apps under their respective prefixes
# root_app.mount("/api/private", private_app)
root_app.mount("/api", public_app)

root_app.state.scheduler = AsyncIOScheduler()

import asyncio

asyncio.run(get_meo_epg())


# @root_app.on_event("startup")
# async def startup_event():
#     root_app.state.scheduler.add_job(get_meo_epg, "cron", hour=0, minute=0)
#     root_app.state.scheduler.start()


# @root_app.on_event("shutdown")
# async def shutdown_event():
#     root_app.state.scheduler.shutdown()


# Run the app (for development purposes)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(root_app, host="0.0.0.0", port=8000)
