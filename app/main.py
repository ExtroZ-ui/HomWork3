from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db, SessionLocal
from app import crud, schemas
from app.cache import build_cache_key, clear_cache, get_cache, set_cache
from app.models import User, UserSession
from app.security import hash_password, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Students REST API")


def get_current_user(
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    session = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_active == True)
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Session is inactive")

    return user


def require_write_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_read_only:
        raise HTTPException(status_code=403, detail="Read-only user cannot modify data")
    return current_user

def get_or_set_cache(request: Request, data_func, ttl: int = 300):
    cache_key = build_cache_key("get", str(request.url))
    cached_data = get_cache(cache_key)

    if cached_data is not None:
        return cached_data

    data = data_func()
    encoded_data = jsonable_encoder(data)
    set_cache(cache_key, encoded_data, ttl=ttl)
    return encoded_data


def import_csv_background_task(csv_path: str):
    db = SessionLocal()
    try:
        crud.import_students_from_csv(db, csv_path)
        clear_cache()
    finally:
        db.close()


def delete_students_background_task(student_ids: list[int]):
    db = SessionLocal()
    try:
        crud.delete_students_by_ids(db, student_ids)
        clear_cache()
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Students API is running"}


# =========================
# AUTH
# =========================

@app.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        is_read_only=user_in.is_read_only,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login", response_model=schemas.AuthResponse)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session = db.query(UserSession).filter(UserSession.user_id == user.id).first()
    if not session:
        session = UserSession(user_id=user.id, is_active=True)
        db.add(session)
    else:
        session.is_active = True

    db.commit()

    return {
        "message": "Login successful. Use X-User-Id header for authorized requests",
        "user_id": user.id,
    }


@app.post("/auth/logout")
def logout(
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-Id header is required")

    session = db.query(UserSession).filter(UserSession.user_id == x_user_id).first()
    if not session or not session.is_active:
        raise HTTPException(status_code=401, detail="User is not logged in")

    session.is_active = False
    db.commit()

    return {"message": "Logout successful"}


# =========================
# FACULTIES
# =========================

@app.post("/faculties", response_model=schemas.FacultyOut)
def create_faculty(
    faculty: schemas.FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.create_faculty(db, faculty)
    clear_cache()
    return result


@app.get("/faculties", response_model=list[schemas.FacultyOut])
def read_faculties(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_faculties(db))


@app.get("/faculties/{faculty_id}", response_model=schemas.FacultyOut)
def read_faculty(
    faculty_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_faculty(db, faculty_id))


@app.put("/faculties/{faculty_id}", response_model=schemas.FacultyOut)
def update_faculty(
    faculty_id: int,
    faculty: schemas.FacultyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.update_faculty(db, faculty_id, faculty)
    clear_cache()
    return result


@app.delete("/faculties/{faculty_id}")
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.delete_faculty(db, faculty_id)
    clear_cache()
    return result


# =========================
# SUBJECTS
# =========================

@app.post("/subjects", response_model=schemas.SubjectOut)
def create_subject(
    subject: schemas.SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.create_subject(db, subject)
    clear_cache()
    return result


@app.get("/subjects", response_model=list[schemas.SubjectOut])
def read_subjects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_subjects(db))


@app.get("/subjects/{subject_id}", response_model=schemas.SubjectOut)
def read_subject(
    subject_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_subject(db, subject_id))


@app.put("/subjects/{subject_id}", response_model=schemas.SubjectOut)
def update_subject(
    subject_id: int,
    subject: schemas.SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.update_subject(db, subject_id, subject)
    clear_cache()
    return result


@app.delete("/subjects/{subject_id}")
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.delete_subject(db, subject_id)
    clear_cache()
    return result


# =========================
# STUDENTS
# =========================

@app.post("/students", response_model=schemas.StudentOut)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.create_student(db, student)
    clear_cache()
    return result


@app.get("/students", response_model=list[schemas.StudentOut])
def read_students(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_students(db))


@app.get("/students/{student_id}", response_model=schemas.StudentOut)
def read_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_student(db, student_id))


@app.put("/students/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    student: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.update_student(db, student_id, student)
    clear_cache()
    return result


@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.delete_student(db, student_id)
    clear_cache()
    return result


# =========================
# STUDENT SUBJECTS
# =========================

@app.post("/student-subjects", response_model=schemas.StudentSubjectOut)
def create_student_subject(
    ss: schemas.StudentSubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.create_student_subject(db, ss)
    clear_cache()
    return result


@app.get("/student-subjects", response_model=list[schemas.StudentSubjectOut])
def read_student_subjects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_student_subjects(db))


@app.get("/student-subjects/{ss_id}", response_model=schemas.StudentSubjectOut)
def read_student_subject(
    ss_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_student_subject(db, ss_id))


@app.put("/student-subjects/{ss_id}", response_model=schemas.StudentSubjectOut)
def update_student_subject(
    ss_id: int,
    ss: schemas.StudentSubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.update_student_subject(db, ss_id, ss)
    clear_cache()
    return result


@app.delete("/student-subjects/{ss_id}")
def delete_student_subject(
    ss_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    result = crud.delete_student_subject(db, ss_id)
    clear_cache()
    return result


# =========================
# IMPORT / REPORTS / EXPORT
# =========================

@app.post("/import-csv-background", response_model=schemas.BackgroundTaskResponse)
def import_csv_background(
    payload: schemas.CsvImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_write_access),
):
    background_tasks.add_task(import_csv_background_task, payload.csv_path)
    return {"message": f"Фоновая задача импорта запущена для файла: {payload.csv_path}"}

@app.post("/students/delete-background", response_model=schemas.BackgroundTaskResponse)
def delete_students_background(
    payload: schemas.DeleteStudentsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_write_access),
):
    background_tasks.add_task(delete_students_background_task, payload.student_ids)
    return {"message": "Фоновая задача удаления студентов запущена"}


@app.get("/reports/students/by-faculty/{faculty_name}", response_model=list[schemas.StudentOut])
def students_by_faculty(
    faculty_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_students_by_faculty_name(db, faculty_name))


@app.get("/reports/subjects/unique", response_model=list[schemas.SubjectOut])
def unique_subjects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_unique_subjects(db))


@app.get("/reports/students/by-subject-low-grade/{subject_name}", response_model=list[schemas.StudentOut])
def students_by_subject_low_grade(
    subject_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(
        request,
        lambda: crud.get_students_by_subject_with_low_grade(db, subject_name, 30)
    )


@app.get("/reports/faculty-average/{faculty_name}", response_model=schemas.FacultyAverageOut)
def faculty_average(
    faculty_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_set_cache(request, lambda: crud.get_faculty_average_grade(db, faculty_name))


@app.get("/export-csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    csv_content = crud.export_all_data_to_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"},
    )