from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import yaml

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import DS_Nguoi_dung
from schemas import TokenData

# Đọc SECRET_KEY từ config hoặc ENV
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
SECRET_KEY = os.environ.get("JWT_SECRET")
if not SECRET_KEY:
	try:
		if os.path.exists(CONFIG_PATH):
			with open(CONFIG_PATH, "r", encoding="utf-8") as f:
				cfg = yaml.safe_load(f) or {}
				SECRET_KEY = cfg.get("security", {}).get("jwt_secret")
	except Exception:
		SECRET_KEY = None
if not SECRET_KEY:
	SECRET_KEY = "CHANGE_ME_SECRET_KEY"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
	to_encode = data.copy()
	expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
	to_encode.update({"exp": expire})
	token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return token


def decode_token(token: str) -> TokenData:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username: str = payload.get("sub")
		is_admin: Optional[bool] = payload.get("is_admin")
		if username is None:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
		return TokenData(username=username, role=("admin" if is_admin else "user"))
	except PyJWTError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DS_Nguoi_dung:
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	token_data = decode_token(token)
	user: Optional[DS_Nguoi_dung] = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.Username == token_data.username).first()
	if user is None:
		raise credentials_exception
	return user


async def get_current_admin(current_user: DS_Nguoi_dung = Depends(get_current_user)) -> DS_Nguoi_dung:
	if not current_user.isAdmin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
	return current_user
