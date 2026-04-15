from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.dependencies import get_db
from app.models import User, UserSession
from app.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut)
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


@router.post("/login", response_model=schemas.AuthResponse)
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


@router.post("/logout")
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