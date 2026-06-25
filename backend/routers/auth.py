from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import database
from backend.security.hashing import hash_password, verify_password
from backend.security.jwt_handler import create_access_token

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

def set_auth_cookie(response: RedirectResponse, token: str) -> RedirectResponse:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600
    )
    return response


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = await database.fetch_one(
        "SELECT * FROM users WHERE username = :u",
        values={"u": username}
    )
    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password."
        })

    if not user["is_active"]:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Account deactivated. Contact admin."
        })

    token = create_access_token({
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"]
    })
    response = RedirectResponse(url="/dashboard", status_code=302)
    return set_auth_cookie(response, token)


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
@limiter.limit("3/minute")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("teacher")
):
    if role not in ("teacher", "admin"):
        role = "teacher"

    existing = await database.fetch_one(
        "SELECT id FROM users WHERE username = :u OR email = :e",
        values={"u": username, "e": email}
    )
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username or email already registered."
        })

    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be at least 6 characters."
        })

    hashed = hash_password(password)
    await database.execute(
        """INSERT INTO users (username, email, hashed_password, role)
           VALUES (:u, :e, :h, :r)""",
        values={"u": username, "e": email, "h": hashed, "r": role}
    )
    return RedirectResponse(url="/login", status_code=302)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
