from fastapi import Depends, FastAPI
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app import crud, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Students REST API")


@app.get("/")
def root():
    return {"message": "Students API is running"}



@app.post("/faculties", response_model=schemas.FacultyOut)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(get_db)):
    return crud.create_faculty(db, faculty)


@app.get("/faculties", response_model=list[schemas.FacultyOut])
def read_faculties(db: Session = Depends(get_db)):
    return crud.get_faculties(db)


@app.get("/faculties/{faculty_id}", response_model=schemas.FacultyOut)
def read_faculty(faculty_id: int, db: Session = Depends(get_db)):
    return crud.get_faculty(db, faculty_id)


@app.put("/faculties/{faculty_id}", response_model=schemas.FacultyOut)
def update_faculty(faculty_id: int, faculty: schemas.FacultyUpdate, db: Session = Depends(get_db)):
    return crud.update_faculty(db, faculty_id, faculty)


@app.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    return crud.delete_faculty(db, faculty_id)



@app.post("/subjects", response_model=schemas.SubjectOut)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    return crud.create_subject(db, subject)


@app.get("/subjects", response_model=list[schemas.SubjectOut])
def read_subjects(db: Session = Depends(get_db)):
    return crud.get_subjects(db)


@app.get("/subjects/{subject_id}", response_model=schemas.SubjectOut)
def read_subject(subject_id: int, db: Session = Depends(get_db)):
    return crud.get_subject(db, subject_id)


@app.put("/subjects/{subject_id}", response_model=schemas.SubjectOut)
def update_subject(subject_id: int, subject: schemas.SubjectUpdate, db: Session = Depends(get_db)):
    return crud.update_subject(db, subject_id, subject)


@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    return crud.delete_subject(db, subject_id)



@app.post("/students", response_model=schemas.StudentOut)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db, student)


@app.get("/students", response_model=list[schemas.StudentOut])
def read_students(db: Session = Depends(get_db)):
    return crud.get_students(db)


@app.get("/students/{student_id}", response_model=schemas.StudentOut)
def read_student(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student(db, student_id)


@app.put("/students/{student_id}", response_model=schemas.StudentOut)
def update_student(student_id: int, student: schemas.StudentUpdate, db: Session = Depends(get_db)):
    return crud.update_student(db, student_id, student)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    return crud.delete_student(db, student_id)



@app.post("/student-subjects", response_model=schemas.StudentSubjectOut)
def create_student_subject(ss: schemas.StudentSubjectCreate, db: Session = Depends(get_db)):
    return crud.create_student_subject(db, ss)


@app.get("/student-subjects", response_model=list[schemas.StudentSubjectOut])
def read_student_subjects(db: Session = Depends(get_db)):
    return crud.get_student_subjects(db)


@app.get("/student-subjects/{ss_id}", response_model=schemas.StudentSubjectOut)
def read_student_subject(ss_id: int, db: Session = Depends(get_db)):
    return crud.get_student_subject(db, ss_id)


@app.put("/student-subjects/{ss_id}", response_model=schemas.StudentSubjectOut)
def update_student_subject(ss_id: int, ss: schemas.StudentSubjectUpdate, db: Session = Depends(get_db)):
    return crud.update_student_subject(db, ss_id, ss)


@app.delete("/student-subjects/{ss_id}")
def delete_student_subject(ss_id: int, db: Session = Depends(get_db)):
    return crud.delete_student_subject(db, ss_id)



@app.post("/import-csv")
def import_csv(db: Session = Depends(get_db)):
    return crud.import_students_from_csv(db, "students.csv")



@app.get("/reports/students/by-faculty/{faculty_name}", response_model=list[schemas.StudentOut])
def students_by_faculty(faculty_name: str, db: Session = Depends(get_db)):
    return crud.get_students_by_faculty_name(db, faculty_name)


@app.get("/reports/subjects/unique", response_model=list[schemas.SubjectOut])
def unique_subjects(db: Session = Depends(get_db)):
    return crud.get_unique_subjects(db)


@app.get("/reports/students/by-subject-low-grade/{subject_name}", response_model=list[schemas.StudentOut])
def students_by_subject_low_grade(subject_name: str, db: Session = Depends(get_db)):
    return crud.get_students_by_subject_with_low_grade(db, subject_name, 30)


@app.get("/reports/faculty-average/{faculty_name}", response_model=schemas.FacultyAverageOut)
def faculty_average(faculty_name: str, db: Session = Depends(get_db)):
    return crud.get_faculty_average_grade(db, faculty_name)



@app.get("/export-csv")
def export_csv(db: Session = Depends(get_db)):
    csv_content = crud.export_all_data_to_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"},
    )