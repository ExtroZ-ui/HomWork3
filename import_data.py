from app.db import SessionLocal
from app.crud import import_students_from_csv

def run():
    with SessionLocal() as db:
        result = import_students_from_csv(db, "students.csv")
        print(result)

if __name__ == "__main__":
    run()