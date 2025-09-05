from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import DS_Nguoi_dung, SessionToken
from schemas import TokenData

SESSION_EXPIRE_MINUTES = 60 * 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Vẫn tái sử dụng OAuth2PasswordBearer để lấy token từ header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


def create_session_token(db: Session, user_id: int) -> str:
	# Tạo token ngẫu nhiên an toàn
	token = secrets.token_urlsafe(48)
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=SESSION_EXPIRE_MINUTES)
	sess = SessionToken(token=token, user_id=user_id, expires_at=expires_at)
	db.add(sess)
	db.commit()
	db.refresh(sess)
	return token


def get_session(db: Session, token: str) -> Optional[SessionToken]:
	return db.query(SessionToken).filter(SessionToken.token == token).first()


def ensure_session_valid(sess: SessionToken) -> None:
	if sess.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")


def decode_token(token: str) -> TokenData:
	# Với session token, chỉ giữ cấu trúc trả về phù hợp
	return TokenData(username=None, role=None)


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DS_Nguoi_dung:
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	if not token:
		raise credentials_exception
	sess = get_session(db, token)
	if sess is None:
		raise credentials_exception
	ensure_session_valid(sess)
	user: Optional[DS_Nguoi_dung] = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.UID == sess.user_id).first()
	if user is None:
		raise credentials_exception
	return user


async def get_current_admin(current_user: DS_Nguoi_dung = Depends(get_current_user)) -> DS_Nguoi_dung:
	if not current_user.isAdmin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
	return current_user
