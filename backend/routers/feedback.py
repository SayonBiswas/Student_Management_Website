from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from backend.database import database
from backend.security.jwt_handler import decode_token
from backend.ml.feedback_analyzer import analyze_feedback

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")


def get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return decode_token(token)
    except:
        return None


@router.get("/feedback")
@limiter.limit("20/minute")
async def feedback_page(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    feedbacks = await database.fetch_all(
        """SELECT f.*, s.name AS student_name,
           sub.subject_name, u.username AS submitted_by_name
           FROM feedback f
           LEFT JOIN students s ON f.admission_number = s.admission_number
           LEFT JOIN subjects sub ON f.subject_id = sub.id
           LEFT JOIN users u ON f.submitted_by = u.id
           ORDER BY f.created_at DESC"""
    )
    students = await database.fetch_all(
        "SELECT admission_number, name FROM students ORDER BY name"
    )
    return templates.TemplateResponse("feedback.html", {
        "request": request,
        "feedbacks": feedbacks,
        "students": students,
        "user": user
    })


@router.post("/feedback")
@limiter.limit("10/minute")
async def submit_feedback(
    request: Request,
    admission_number: int = Form(...),
    subject_name: Optional[str] = Form(None),
    feedback_text: str = Form(...),
    role: str = Form("teacher")
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if role not in ("teacher", "student"):
        role = "teacher"

    subject_id = None
    if subject_name:
        subject = await database.fetch_one(
            "SELECT id FROM subjects WHERE LOWER(subject_name) = LOWER(:s)",
            values={"s": subject_name}
        )
        if subject:
            subject_id = subject["id"]

    sentiment, category = analyze_feedback(feedback_text)

    await database.execute(
        """INSERT INTO feedback
           (submitted_by, role, admission_number, subject_id,
            feedback_text, sentiment_score, category)
           VALUES (:u, :r, :a, :s, :f, :sc, :cat)""",
        values={
            "u": int(user["sub"]), "r": role,
            "a": admission_number, "s": subject_id,
            "f": feedback_text, "sc": sentiment, "cat": category
        }
    )
    return RedirectResponse(url="/feedback", status_code=302)