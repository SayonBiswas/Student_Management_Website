from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.database import connect_db, disconnect_db
from backend.routers import auth, students, marks, feedback, analytics
from backend.routers import lost_found

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(title="Report Card System", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(marks.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(lost_found.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=302)