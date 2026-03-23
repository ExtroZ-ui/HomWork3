from app.db import SessionLocal
from app.models import Student, Faculty, Subject, StudentSubject

db = SessionLocal()

print("=== Students ===")
for s in db.query(Student).all():
    print(s)

print("\n=== Faculties ===")
for f in db.query(Faculty).all():
    print(f)

print("\n=== Subjects ===")
for sub in db.query(Subject).all():
    print(sub)