from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import tempfile
import os

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


@router.get("/dashboard")
@limiter.limit("30/minute")
async def dashboard(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if user.get("role") == "student":
        return RedirectResponse(url="/my-report", status_code=302)

    classes = await database.fetch_all(
        "SELECT DISTINCT class_name FROM students ORDER BY class_name"
    )

    all_students = await database.fetch_all(
        """SELECT sr.*, s.class_name, s.section
           FROM student_results sr
           JOIN students s ON sr.admission_number = s.admission_number
           ORDER BY s.class_name, s.section, s.roll_number"""
    )

    class_data = {}
    for student in all_students:
        cls = student["class_name"]
        sec = student["section"]
        if cls not in class_data:
            class_data[cls] = {}
        if sec not in class_data[cls]:
            class_data[cls][sec] = []
        class_data[cls][sec].append(dict(student))

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "class_data": class_data,
        "user": user
    })


@router.get("/students/add")
@limiter.limit("30/minute")
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


@router.post("/students/add")
@limiter.limit("20/minute")
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
        "SELECT admission_number FROM students WHERE admission_number = :a",
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
    return RedirectResponse(url=f"/students/{admission_number}/marks", status_code=302)


@router.get("/students/{admission_number}")
@limiter.limit("30/minute")
async def student_detail(request: Request, admission_number: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    student = await database.fetch_one(
        "SELECT * FROM student_results WHERE admission_number = :a",
        values={"a": admission_number}
    )
    if not student:
        return RedirectResponse(url="/dashboard", status_code=302)

    marks = await database.fetch_all(
        """SELECT ss.*, sub.subject_name,
           ROUND((ss.marks_obtained::NUMERIC / ss.max_marks::NUMERIC) * 100, 2) AS subject_percentage
           FROM student_subjects ss
           JOIN subjects sub ON ss.subject_id = sub.id
           WHERE ss.admission_number = :a
           ORDER BY sub.subject_name""",
        values={"a": admission_number}
    )
    return templates.TemplateResponse("student_detail.html", {
        "request": request,
        "student": student,
        "marks": marks,
        "add_marks": False,
        "user": user
    })


@router.post("/students/{admission_number}/delete")
@limiter.limit("10/minute")
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


@router.post("/students/{admission_number}/update")
@limiter.limit("20/minute")
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


@router.get("/students/{admission_number}/download")
async def download_marksheet(request: Request, admission_number: int):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    student = await database.fetch_one(
        "SELECT * FROM student_results WHERE admission_number = :a",
        values={"a": admission_number}
    )
    if not student:
        return RedirectResponse(url="/dashboard", status_code=302)

    marks = await database.fetch_all(
        """SELECT ss.marks_obtained, ss.max_marks, sub.subject_name,
           ROUND((ss.marks_obtained::NUMERIC / ss.max_marks::NUMERIC) * 100, 2) AS subject_percentage
           FROM student_subjects ss
           JOIN subjects sub ON ss.subject_id = sub.id
           WHERE ss.admission_number = :a
           ORDER BY sub.subject_name""",
        values={"a": admission_number}
    )

    # convert to plain dicts so Jinja2 can read them
    student_dict = dict(student)
    marks_list = [dict(m) for m in marks]

    env = Environment(loader=FileSystemLoader("frontend/templates"))
    template = env.get_template("marksheet_pdf.html")
    html_content = template.render(student=student_dict, marks=marks_list)

    pdf = HTML(string=html_content).write_pdf()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=marksheet_{admission_number}.pdf"
        }
    )


@router.get("/my-report")
@limiter.limit("20/minute")
async def my_report(request: Request):
    user = get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=302)

    admission_number = user.get("admission_number")
    if not admission_number:
        return templates.TemplateResponse("my_report.html", {
            "request": request,
            "student": None,
            "marks": [],
            "classmates": [],
            "user": user,
            "error": "No admission number linked. Contact your teacher."
        })

    student = await database.fetch_one(
        "SELECT * FROM student_results WHERE admission_number = :a",
        values={"a": int(admission_number)}
    )

    marks = []
    classmates = []

    if student:
        marks = await database.fetch_all(
            """SELECT ss.marks_obtained, ss.max_marks, sub.subject_name,
               ROUND((ss.marks_obtained::NUMERIC / ss.max_marks::NUMERIC) * 100, 2) AS subject_percentage
               FROM student_subjects ss
               JOIN subjects sub ON ss.subject_id = sub.id
               WHERE ss.admission_number = :a
               ORDER BY sub.subject_name""",
            values={"a": student["admission_number"]}
        )

        # fetch only students from same class and section
        classmates = await database.fetch_all(
            """SELECT sr.admission_number, sr.name, sr.roll_number,
               sr.percentage, s.class_name, s.section
               FROM student_results sr
               JOIN students s ON sr.admission_number = s.admission_number
               WHERE s.class_name = :c AND s.section = :sec
               ORDER BY s.roll_number""",
            values={"c": student["class_name"], "sec": student["section"]}
        )

    return templates.TemplateResponse("my_report.html", {
        "request": request,
        "student": student,
        "marks": marks,
        "classmates": classmates,
        "user": user
    })