from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, UserSession


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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