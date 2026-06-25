from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import database
from backend.security.jwt_handler import decode_token
from backend.ml.predictor import predict_student

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


@router.get("/analytics")
@limiter.limit("20/minute")
async def analytics_page(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    summary = await database.fetch_all(
        """SELECT class_name, section,
           COUNT(*) AS total_students,
           ROUND(AVG(percentage), 2) AS avg_percentage,
           ROUND(MAX(percentage), 2) AS highest,
           ROUND(MIN(percentage), 2) AS lowest
           FROM student_results
           GROUP BY class_name, section
           ORDER BY class_name, section"""
    )
    students = await database.fetch_all(
        "SELECT * FROM student_results ORDER BY percentage DESC"
    )
    predictions = []
    for s in students:
        pred = predict_student(dict(s))
        predictions.append({
            "admission_number": s["admission_number"],
            "name": s["name"],
            "current_percentage": s["percentage"],
            **pred
        })

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "summary": summary,
        "students": students,
        "predictions": predictions,
        "user": user
    })