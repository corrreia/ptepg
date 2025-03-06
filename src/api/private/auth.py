import datetime
import os

from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyCookie
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.github import GithubSSO
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi_sso.sso.base import OpenID
from jose import jwt


app_url = os.getenv("APP_URL", "http://localhost:8000")
prod = os.getenv("ENVIRONMENT") != "dev"

google_sso = GoogleSSO(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri=f"{app_url}/auth/google/callback",
)

github_sso = GithubSSO(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_uri=f"{app_url}/auth/github/callback",
)

router = APIRouter()


async def get_logged_user(cookie: str = Security(APIKeyCookie(name="token"))) -> OpenID:
    """Get user's JWT stored in cookie 'token', parse it and return the user's OpenID."""
    try:
        claims = jwt.decode(
            cookie, key=os.getenv("SESSION_SECRET_KEY"), algorithms=["HS256"]
        )
        return OpenID(**claims["pld"])
    except Exception as error:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        ) from error


@router.get("/protected")
async def protected_endpoint(user: OpenID = Depends(get_logged_user)):
    """This endpoint will say hello to the logged user.
    If the user is not logged, it will return a 401 error from `get_logged_user`."""
    return {
        "message": f"You are very welcome, {user.email}!",
    }


@router.get("/auth/google/login")
async def login_google():
    """Redirect the user to the Google login page."""
    async with google_sso:
        return await google_sso.get_login_redirect()


@router.get("/auth/google/callback")
async def login_google_callback(request: Request):
    """Process login and redirect the user to the protected endpoint."""
    async with google_sso:
        openid = await google_sso.verify_and_process(request)
        if not openid:
            raise HTTPException(status_code=401, detail="Authentication failed")
    # Create a JWT with the user's OpenID
    expiration = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        days=1
    )
    token = jwt.encode(
        {"pld": openid.dict(), "exp": expiration, "sub": openid.id},
        key=os.getenv("SESSION_SECRET_KEY"),
        algorithm="HS256",
    )
    response = RedirectResponse(url="/protected")
    response.set_cookie(
        key="token", value=token, expires=expiration
    )  # This cookie will make sure /protected knows the user
    return response

@router.get("/auth/github/login")
async def login_github():
    """Redirect the user to the GitHub login page."""
    async with github_sso:
        return await github_sso.get_login_redirect()
    
@router.get("/auth/github/callback")
async def login_github_callback(request: Request):
    """Process login and redirect the user to the protected endpoint."""
    async with github_sso:
        openid = await github_sso.verify_and_process(request)
        if not openid:
            raise HTTPException(status_code=401, detail="Authentication failed")
    # Create a JWT with the user's OpenID
    expiration = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        days=1
    )
    token = jwt.encode(
        {"pld": openid.dict(), "exp": expiration, "sub": openid.id},
        key=os.getenv("SESSION_SECRET_KEY"),
        algorithm="HS256",
    )
    response = RedirectResponse(url="/protected")
    response.set_cookie(
        key="token", value=token, expires=expiration
    )
    return response


@router.get("/auth/logout")
async def logout():
    """Forget the user's session."""
    response = RedirectResponse(url="/protected")
    response.delete_cookie(key="token")
    return response
