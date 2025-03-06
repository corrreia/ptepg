import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi import FastAPI
from starlette.responses import RedirectResponse
from typing import Optional

# Main FastAPI app - add this to your main.py
app = FastAPI()

# Add session middleware - critical for OAuth flow
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key-for-development"),
)

app_url = os.getenv("APP_URL", "http://localhost:8000")
prod = os.getenv("ENVIRONMENT") != "dev"

router = APIRouter()
config = Config(environ=os.environ)
oauth = OAuth(config)

# Register Google OAuth
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Register GitHub OAuth
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# GitHub OAuth2 security scheme for Swagger UI
github_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{app_url}/manage/auth/login/github",
    tokenUrl=f"{app_url}/manage/auth/callback/github",
    scopes={"user:email": "Read user email"},
)

# Google OAuth2 security scheme for Swagger UI
google_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{app_url}/manage/auth/login/google",
    tokenUrl=f"{app_url}/manage/auth/callback/google",
    scopes={"openid email profile": "Read user info and email"},
)


# Dependency to get the current user from session
def get_current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Safe token getter for GitHub (won't fail if token missing)
def get_optional_github_token(
    token: str = Depends(github_oauth2_scheme),
) -> Optional[str]:
    try:
        return token
    except:
        return None


# Safe token getter for Google (won't fail if token missing)
def get_optional_google_token(
    token: str = Depends(google_oauth2_scheme),
) -> Optional[str]:
    try:
        return token
    except:
        return None


# Authentication verification that checks both session and OAuth2 token
def verify_auth(
    request: Request,
    github_token: Optional[str] = Depends(get_optional_github_token),
    google_token: Optional[str] = Depends(get_optional_google_token),
) -> dict:
    # First check if user is in session (browser flow)
    user = request.session.get("user")
    if user:
        return user

    # Otherwise check if OAuth2 token was provided (API flow)
    if github_token or google_token:
        # In a real app, you would validate these tokens
        # For now we'll just return a placeholder user
        return {"authenticated_via": "token"}

    raise HTTPException(status_code=401, detail="Not authenticated")


# Google login route
@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = f"{app_url}/manage/auth/callback/google"
    return await oauth.google.authorize_redirect(request, redirect_uri)


# Google callback route
@router.get("/callback/google")
async def auth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)

    # Store user info in session
    request.session["user"] = user_info

    # Store the access token for API usage
    request.session["tokens"] = {"google": token}

    # Redirect to a success page or dashboard
    return RedirectResponse(url="/dashboard")


# GitHub login route
@router.get("/login/github")
async def login_github(request: Request):
    redirect_uri = f"{app_url}/manage/auth/callback/github"
    return await oauth.github.authorize_redirect(request, redirect_uri)


# GitHub callback route
@router.get("/callback/github")
async def auth_github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    user_info = await resp.json()

    # Get email if not provided in user info
    if "email" not in user_info or not user_info["email"]:
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = await emails_resp.json()
        primary_email = next(
            (email for email in emails if email.get("primary")),
            emails[0] if emails else None,
        )
        if primary_email:
            user_info["email"] = primary_email.get("email")

    # Store user info in session
    request.session["user"] = user_info

    # Store the access token for API usage
    request.session["tokens"] = {"github": token}

    # Redirect to a success page or dashboard
    return RedirectResponse(url="/dashboard")


# Protected endpoint that works with both authentication methods
@router.get("/protected", summary="Protected endpoint requiring authentication")
async def protected_endpoint(user: dict = Depends(verify_auth)):
    # Use appropriate user identifier based on which SSO was used
    user_identifier = user.get("email") or user.get("login") or "authenticated user"
    return {"message": f"Hello, {user_identifier}! Protected endpoint."}


# GitHub-specific protected endpoint
@router.get("/protected/github", summary="GitHub-protected endpoint")
async def protected_github_endpoint(token: str = Depends(github_oauth2_scheme)):
    # In a real application, you would validate the token
    # and fetch user information
    return {"message": "Hello, GitHub user! Protected by GitHub SSO."}


# Google-specific protected endpoint
@router.get("/protected/google", summary="Google-protected endpoint")
async def protected_google_endpoint(token: str = Depends(google_oauth2_scheme)):
    # In a real application, you would validate the token
    # and fetch user information
    return {"message": "Hello, Google user! Protected by Google SSO."}


# Logout route
@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    request.session.pop("tokens", None)
    return RedirectResponse(url="/")


# Login page that offers both options
@router.get("/login")
async def login_page():
    return {
        "google_login_url": "/manage/auth/login/google",
        "github_login_url": "/manage/auth/login/github",
    }
