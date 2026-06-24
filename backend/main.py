from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.database import connect_db, disconnect_db
from backend.routers import auth, students, marks, feedback, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(title="Report Card System", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(marks.router)
app.include_router(feedback.router)
app.include_router(analytics.router)