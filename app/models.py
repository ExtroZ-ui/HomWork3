from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    students = relationship("Student", back_populates="faculty", cascade="all, delete")

    def __repr__(self):
        return f"Faculty(id={self.id}, name='{self.name}')"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    first_name = Column(String(100), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=False)

    faculty = relationship("Faculty", back_populates="students")
    student_subjects = relationship("StudentSubject", back_populates="student", cascade="all, delete")

    __table_args__ = (
        UniqueConstraint("last_name", "first_name", "faculty_id", name="uq_student_fullname_faculty"),
    )

    def __repr__(self):
        return (
            f"Student(id={self.id}, last_name='{self.last_name}', "
            f"first_name='{self.first_name}', faculty_id={self.faculty_id})"
        )


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False, index=True)

    student_subjects = relationship("StudentSubject", back_populates="subject", cascade="all, delete")

    def __repr__(self):
        return f"Subject(id={self.id}, name='{self.name}')"


class StudentSubject(Base):
    __tablename__ = "student_subjects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    grade = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="student_subjects")
    subject = relationship("Subject", back_populates="student_subjects")

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),
    )

    def __repr__(self):
        return (
            f"StudentSubject(id={self.id}, student_id={self.student_id}, "
            f"subject_id={self.subject_id}, grade={self.grade})"
        )