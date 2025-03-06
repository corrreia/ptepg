import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from api.private.auth import router as auth_router

# Load environment variables from .env file
load_dotenv()

# Import routers from api and manage modules


# Determine if we're in development mode
is_dev = os.getenv("ENVIRONMENT") == "dev"
if is_dev:
    print("Running in dev mode")

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
private_app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# client_app.include_router(client_router, prefix="/api/v1", tags=["Client"])
# dashboard_app.include_router(users_router, prefix="/manage", tags=["Users"])
# dashboard_app.include_router(
#     subscriptions_router, prefix="/manage", tags=["Subscriptions"]
# )
# dashboard_app.include_router(api_keys_router, prefix="/manage", tags=["API Keys"])

# Root app to combine both
root_app = FastAPI()

# Mount the client and dashboard apps under their respective prefixes
root_app.mount("/api/private", private_app)
root_app.mount("/api", public_app)


# Root endpoint for the main app
@root_app.get("/")
async def root():
    return {
        "message": "Welcome to the Subscription API",
        "client_api": "/api",
        "dashboard_api": "/api/private"
        if is_dev
        else "Dashboard API docs available in dev mode only",
    }


# Run the app (for development purposes)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(root_app, host="0.0.0.0", port=8000)
