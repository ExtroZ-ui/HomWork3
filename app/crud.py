import csv
import io

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Faculty, Student, Subject, StudentSubject
from app import schemas


def create_faculty(db: Session, faculty_in: schemas.FacultyCreate) -> Faculty:
    existing = db.query(Faculty).filter(Faculty.name == faculty_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Faculty already exists")

    faculty = Faculty(name=faculty_in.name)
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def get_faculties(db: Session):
    return db.query(Faculty).all()


def get_faculty(db: Session, faculty_id: int) -> Faculty:
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty


def update_faculty(db: Session, faculty_id: int, faculty_in: schemas.FacultyUpdate) -> Faculty:
    faculty = get_faculty(db, faculty_id)

    if faculty_in.name is not None:
        faculty.name = faculty_in.name

    db.commit()
    db.refresh(faculty)
    return faculty


def delete_faculty(db: Session, faculty_id: int):
    faculty = get_faculty(db, faculty_id)
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted"}



def create_subject(db: Session, subject_in: schemas.SubjectCreate) -> Subject:
    existing = db.query(Subject).filter(Subject.name == subject_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject already exists")

    subject = Subject(name=subject_in.name)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def get_subjects(db: Session):
    return db.query(Subject).all()


def get_subject(db: Session, subject_id: int) -> Subject:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


def update_subject(db: Session, subject_id: int, subject_in: schemas.SubjectUpdate) -> Subject:
    subject = get_subject(db, subject_id)

    if subject_in.name is not None:
        subject.name = subject_in.name

    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: int):
    subject = get_subject(db, subject_id)
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted"}



def create_student(db: Session, student_in: schemas.StudentCreate) -> Student:
    faculty = db.query(Faculty).filter(Faculty.id == student_in.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    existing = (
        db.query(Student)
        .filter(
            Student.last_name == student_in.last_name,
            Student.first_name == student_in.first_name,
            Student.faculty_id == student_in.faculty_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists in this faculty")

    student = Student(**student_in.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_students(db: Session):
    return db.query(Student).all()


def get_student(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def update_student(db: Session, student_id: int, student_in: schemas.StudentUpdate) -> Student:
    student = get_student(db, student_id)

    if student_in.faculty_id is not None:
        faculty = db.query(Faculty).filter(Faculty.id == student_in.faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")

    for field, value in student_in.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int):
    student = get_student(db, student_id)
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}



def create_student_subject(db: Session, ss_in: schemas.StudentSubjectCreate) -> StudentSubject:
    student = db.query(Student).filter(Student.id == ss_in.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    subject = db.query(Subject).filter(Subject.id == ss_in.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = (
        db.query(StudentSubject)
        .filter(
            StudentSubject.student_id == ss_in.student_id,
            StudentSubject.subject_id == ss_in.subject_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Student already linked to this subject")

    ss = StudentSubject(**ss_in.model_dump())
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss


def get_student_subjects(db: Session):
    return db.query(StudentSubject).all()


def get_student_subject(db: Session, ss_id: int) -> StudentSubject:
    ss = db.query(StudentSubject).filter(StudentSubject.id == ss_id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="StudentSubject not found")
    return ss


def update_student_subject(db: Session, ss_id: int, ss_in: schemas.StudentSubjectUpdate) -> StudentSubject:
    ss = get_student_subject(db, ss_id)

    data = ss_in.model_dump(exclude_unset=True)

    if "student_id" in data:
        student = db.query(Student).filter(Student.id == data["student_id"]).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

    if "subject_id" in data:
        subject = db.query(Subject).filter(Subject.id == data["subject_id"]).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

    for field, value in data.items():
        setattr(ss, field, value)

    db.commit()
    db.refresh(ss)
    return ss


def delete_student_subject(db: Session, ss_id: int):
    ss = get_student_subject(db, ss_id)
    db.delete(ss)
    db.commit()
    return {"message": "StudentSubject deleted"}



def import_students_from_csv(db: Session, file_path: str = "students.csv"):
    faculties_cache = {}
    subjects_cache = {}
    students_cache = {}
    student_subject_cache = set()

    imported_rows = 0

    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                last_name = row["Фамилия"]
                first_name = row["Имя"]
                faculty_name = row["Факультет"]
                subject_name = row["Курс"]
                grade = int(row["Оценка"])

                # Faculty
                if faculty_name not in faculties_cache:
                    faculty = db.query(Faculty).filter_by(name=faculty_name).first()
                    if not faculty:
                        faculty = Faculty(name=faculty_name)
                        db.add(faculty)
                        db.flush()
                    faculties_cache[faculty_name] = faculty
                faculty = faculties_cache[faculty_name]

                # Student
                student_key = (last_name, first_name, faculty_name)
                if student_key not in students_cache:
                    student = (
                        db.query(Student)
                        .filter_by(
                            last_name=last_name,
                            first_name=first_name,
                            faculty_id=faculty.id,
                        )
                        .first()
                    )
                    if not student:
                        student = Student(
                            last_name=last_name,
                            first_name=first_name,
                            faculty_id=faculty.id,
                        )
                        db.add(student)
                        db.flush()
                    students_cache[student_key] = student
                student = students_cache[student_key]

                # Subject
                if subject_name not in subjects_cache:
                    subject = db.query(Subject).filter_by(name=subject_name).first()
                    if not subject:
                        subject = Subject(name=subject_name)
                        db.add(subject)
                        db.flush()
                    subjects_cache[subject_name] = subject
                subject = subjects_cache[subject_name]

                # StudentSubject
                ss_key = (student.id, subject.id)
                if ss_key in student_subject_cache:
                    continue

                existing_ss = (
                    db.query(StudentSubject)
                    .filter_by(student_id=student.id, subject_id=subject.id)
                    .first()
                )
                if existing_ss:
                    student_subject_cache.add(ss_key)
                    continue

                ss = StudentSubject(
                    student_id=student.id,
                    subject_id=subject.id,
                    grade=grade,
                )
                db.add(ss)
                student_subject_cache.add(ss_key)
                imported_rows += 1

        db.commit()
        return {"message": "Данные успешно загружены", "imported_relations": imported_rows}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при импорте: {str(e)}")



def get_students_by_faculty_name(db: Session, faculty_name: str):
    faculty = db.query(Faculty).filter(Faculty.name == faculty_name).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")

    return db.query(Student).filter(Student.faculty_id == faculty.id).all()


def get_unique_subjects(db: Session):
    subjects = db.query(Subject).order_by(Subject.name.asc()).all()
    return subjects


def get_students_by_subject_with_low_grade(db: Session, subject_name: str, max_grade: int = 30):
    result = (
        db.query(Student)
        .join(StudentSubject, Student.id == StudentSubject.student_id)
        .join(Subject, Subject.id == StudentSubject.subject_id)
        .filter(Subject.name == subject_name, StudentSubject.grade < max_grade)
        .all()
    )
    return result


def get_faculty_average_grade(db: Session, faculty_name: str):
    result = (
        db.query(
            Faculty.name.label("faculty_name"),
            func.avg(StudentSubject.grade).label("average_grade"),
        )
        .join(Student, Student.faculty_id == Faculty.id)
        .join(StudentSubject, StudentSubject.student_id == Student.id)
        .filter(Faculty.name == faculty_name)
        .group_by(Faculty.name)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Faculty not found or no grades")

    return {
        "faculty_name": result.faculty_name,
        "average_grade": round(float(result.average_grade), 2),
    }



def export_all_data_to_csv(db: Session) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Фамилия", "Имя", "Факультет", "Курс", "Оценка"])

    rows = (
        db.query(
            Student.last_name,
            Student.first_name,
            Faculty.name,
            Subject.name,
            StudentSubject.grade,
        )
        .join(Faculty, Student.faculty_id == Faculty.id)
        .join(StudentSubject, StudentSubject.student_id == Student.id)
        .join(Subject, StudentSubject.subject_id == Subject.id)
        .order_by(Faculty.name, Student.last_name, Student.first_name, Subject.name)
        .all()
    )

    for row in rows:
        writer.writerow(row)

    return output.getvalue()