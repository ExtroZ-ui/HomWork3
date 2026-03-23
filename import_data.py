import csv
from app.db import SessionLocal
from app.models import Faculty, Student, Subject, StudentSubject

db = SessionLocal()

faculties_cache = {}
subjects_cache = {}
students_cache = {}
student_subject_cache = set()

try:
    with open("students.csv", encoding="utf-8") as f:
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

    db.commit()
    print("Данные успешно загружены")

except Exception as e:
    db.rollback()
    print(f"Ошибка при импорте: {e}")

finally:
    db.close()