from pydantic import BaseModel
from typing import List

class SubjectInput(BaseModel):
    subject_name: str
    marks_obtained: int
    max_marks: int = 100

class StudentCreate(BaseModel):
    admission_number: int
    name: str
    roll_number: int
    class_name: int
    section: str
    number_of_subjects: int
    subjects: List[SubjectInput]

class StudentUpdate(BaseModel):
    name: str
    roll_number: int
    class_name: int
    section: str

class MarksUpdate(BaseModel):
    marks_obtained: int
    max_marks: int = 100