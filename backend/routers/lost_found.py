from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from backend.database import database
from backend.security.jwt_handler import decode_token

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
templates = Jinja2Templates(directory="fontend/templates")

def get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return decode_token(token)
    except:
        return None

@router.get("/lost-found")
@limiter.limit("20/minute")
async def lost_found_page(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    items = await database.fetch_all(
        """SELECT lf.*, u.username AS reported_by_name
        FROM lost_found lf
        LEFT JOIN users u ON lf.reported_by = u.id
        ORDER BY lf.created_at DESC"""
    )
    return templates.TemplateResponse("lost_found.html", {
        "request": request,
        "items": items,
        "user": user
    })


@router.post("/lost-found")
@limiter.limit("10/minute")
async def report_item(
    request: Request,
    item_name: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form(...)
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if status not in ("lost", "found"):
        status = "lost"
    
    await database.execute(
        """INSERT INTO lost_found (item_name, description, status, reported_by)
        VALUES (:name, :desc, :status, :user_id)""",
        values={
            "name": item_name,
            "desc": description,
            "status": status,
            "user_id": int(user["sub"])
        }
    )
    return RedirectResponse(url="/lost-found", status_code=302)

@router.post("/lost-found/{item_id}/resolve")
@limiter.limit("10/minute")
async def resolve_item(request: Request, item_id: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    await database.execute(
        "UPDATE lost_found SET status = 'found' WHERE id = :id",
        values={"id": item_id}
    )
    return RedirectResponse(url="/lost-found", status_code=302)