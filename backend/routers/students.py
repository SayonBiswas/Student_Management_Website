from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.database import database
from backend.security.jwt_handler import decode_token

router = APIRouter()
templates = Jinja2Templates(directory = "frontend/templates")

def get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return decode_token(token)
    except:
        return None

@router.get("/dashboard")
async def dashboard(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    students = await database.fetch_all(
        """SELECT * FROM student_results
        ORDER BY class_name, section, roll_number"""
    )
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "students": students,
        "user": user
    })

@router.get("/student/add")
async def add_student_page(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("student_detail.html", {
        "request": request,
        "student": None,
        "marks": [],
        "add_marks": False,
        "user": user
    })

@router.post("/student/add")
async def add_student(
    request: Request,
    admission_number: int = Form(...),
    name: str = Form(...),
    roll_number: int = Form(...),
    class_name: int = Form(...),
    section: str = Form(...),
    number_of_subjects: int = Form(...)
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    existing = await database.fetch_one(
        "SELECT * FROM students WHERE admission_number = :a",
        values={"a": admission_number}
    )
    if existing:
        return templates.TemplateResponse("student_detail.html", {
            "request": request,
            "student": None,
            "marks": [],
            "error": "Admission number already exists.",
            "user": user
        })
    
    await database.execute(
        """INSERT INTO students
        (admission_number, name, roll_number, class_name, section, number_of_subjects)
        VALUES (:a, :n, :r, :c, :s, :ns)""",
        values={
            "a": admission_number, "n": name, "r": roll_number,
            "c": class_name, "s": section, "ns": number_of_subjects
        }
    )
    return RedirectResponse(url=f"/student/{admission_number}/marks", status_code=302)

@router.get("/student/{admission_number}")
async def student_detail(request: Request, admission_number: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    student = await database.fetch_one(
        "SELECT * FROM results WHERE admission_number = :a",
        values = {"a": admission_number}
    )
    if not student:
        return templates.TemplateResponse(url = "/dashboard.html", status_code = 302)
    
    marks = await database.fetch_all(
        """SELECT ss.*, sub.subject_name,
        ROUND((ss.marks_obtained::NUMBERIC / ss.max_marks::NUMERIC) * 100, 2) AS subject_percentage
        FROM student_subjects ss
        JOIN subjects sub ON ss.subject_id = sub.id
        WHERE ss.admission_number = :a
        ORDER by sub.subject_name""",
        values={"a": admission_number}
    )
    return templates.TemplateResponse("student_detail.html", {
        "request": request,
        "student": student,
        "marks": marks,
        "add_marks": False,
        "user": user
    })

@router.post("/student/{admission_number}/delete")
async def delete_student(request: Request, admission_number: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if user.get("role") != "admin":
        return RedirectResponse(url=f"/students/{admission_number}", status_code=302)
    
    await database.execute(
        "DELETE FROM students WHERE admission_number = :a",
        values={"a": admission_number}
    )
    return RedirectResponse(url="/dashboard", status_code=302)

@router.post("/student/{admission_number}/update")
async def update_student(
    request: Request,
    admission_number: int,
    name: str = Form(...),
    roll_number: int = Form(...),
    class_name: int = Form(...),
    section: str = Form(...)
):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    await database.execute(
        """UPDATE students SET name = :n, roll_number = :r,
        class_name = :c, section = :s
        WHERE admission_number = :a""",
        values={"n": name, "r": roll_number, "c": class_name,
                "s": section, "a": admission_number}
    )
    return RedirectResponse(url=f"/students/{admission_number}", status_code=302)