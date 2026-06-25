from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import database
from backend.security.jwt_handler import decode_token

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


@router.get("/students/{admission_number}/marks")
@limiter.limit("30/minute")
async def add_marks_page(request: Request, admission_number: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    student = await database.fetch_one(
        "SELECT * FROM students WHERE admission_number = :a",
        values={"a": admission_number}
    )
    existing_marks = await database.fetch_all(
        """SELECT ss.*, sub.subject_name FROM student_subjects ss
           JOIN subjects sub ON ss.subject_id = sub.id
           WHERE ss.admission_number = :a""",
        values={"a": admission_number}
    )
    return templates.TemplateResponse("student_detail.html", {
        "request": request,
        "student": student,
        "marks": existing_marks,
        "add_marks": True,
        "user": user
    })


@router.post("/students/{admission_number}/marks")
@limiter.limit("20/minute")
async def add_marks(
    request: Request,
    admission_number: int,
    subject_name: str = Form(...),
    marks_obtained: int = Form(...),
    max_marks: int = Form(100)
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if marks_obtained < 0 or marks_obtained > max_marks:
        student = await database.fetch_one(
            "SELECT * FROM students WHERE admission_number = :a",
            values={"a": admission_number}
        )
        return templates.TemplateResponse("student_detail.html", {
            "request": request,
            "student": student,
            "marks": [],
            "add_marks": True,
            "error": f"Marks must be between 0 and {max_marks}.",
            "user": user
        })

    subject = await database.fetch_one(
        "SELECT id FROM subjects WHERE LOWER(subject_name) = LOWER(:s)",
        values={"s": subject_name}
    )
    if not subject:
        subject_id = await database.execute(
            "INSERT INTO subjects (subject_name) VALUES (:s) RETURNING id",
            values={"s": subject_name}
        )
    else:
        subject_id = subject["id"]

    await database.execute(
        """INSERT INTO student_subjects
           (admission_number, subject_id, marks_obtained, max_marks)
           VALUES (:a, :sid, :m, :mm)
           ON CONFLICT (admission_number, subject_id)
           DO UPDATE SET marks_obtained = :m, max_marks = :mm""",
        values={
            "a": admission_number, "sid": subject_id,
            "m": marks_obtained, "mm": max_marks
        }
    )
    return RedirectResponse(url=f"/students/{admission_number}", status_code=302)


@router.post("/students/{admission_number}/marks/delete")
@limiter.limit("10/minute")
async def delete_marks(
    request: Request,
    admission_number: int,
    subject_name: str = Form(...)
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    subject = await database.fetch_one(
        "SELECT id FROM subjects WHERE LOWER(subject_name) = LOWER(:s)",
        values={"s": subject_name}
    )
    if subject:
        await database.execute(
            """DELETE FROM student_subjects
               WHERE admission_number = :a AND subject_id = :sid""",
            values={"a": admission_number, "sid": subject["id"]}
        )
    return RedirectResponse(url=f"/students/{admission_number}", status_code=302)