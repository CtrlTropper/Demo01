from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..db.database import get_db
from ..db.models import User
from .auth import get_current_user


router = APIRouter(prefix="/admin", tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def require_admin(user: User | None):
    if user is None or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")


@router.post("/users")
def create_user(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_admin(user)

    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role", "user")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="invalid role")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user_obj = User(
        username=username,
        password_hash=pwd_context.hash(password),
        role=role,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)

    return {"id": user_obj.id, "username": user_obj.username, "role": user_obj.role}


