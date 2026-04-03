from pydantic import BaseModel, Field


class FacultyBase(BaseModel):
    name: str = Field(..., max_length=100)


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)


class FacultyOut(FacultyBase):
    id: int

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str = Field(..., max_length=150)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)


class SubjectOut(SubjectBase):
    id: int

    class Config:
        from_attributes = True



class StudentBase(BaseModel):
    last_name: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    faculty_id: int


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    last_name: str | None = Field(default=None, max_length=100)
    first_name: str | None = Field(default=None, max_length=100)
    faculty_id: int | None = None


class StudentOut(StudentBase):
    id: int

    class Config:
        from_attributes = True



class StudentSubjectBase(BaseModel):
    student_id: int
    subject_id: int
    grade: int = Field(..., ge=0, le=100)


class StudentSubjectCreate(StudentSubjectBase):
    pass


class StudentSubjectUpdate(BaseModel):
    student_id: int | None = None
    subject_id: int | None = None
    grade: int | None = Field(default=None, ge=0, le=100)


class StudentSubjectOut(StudentSubjectBase):
    id: int

    class Config:
        from_attributes = True



class StudentShortOut(BaseModel):
    id: int
    last_name: str
    first_name: str
    faculty_id: int

    class Config:
        from_attributes = True


class FacultyAverageOut(BaseModel):
    faculty_name: str
    average_grade: float