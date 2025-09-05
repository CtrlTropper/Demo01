# schemas.py: Schemas cho request/response

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
	username: str
	password: str
	is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
	password: Optional[str] = None
	is_admin: Optional[bool] = None

class UserOut(BaseModel):
	UID: int
	Username: str
	isAdmin: bool

	model_config = {"from_attributes": True}

class FileCreate(BaseModel):
	Ten_file: str
	CreateBy: int
	isEmbeding: Optional[bool] = False

class FileOut(BaseModel):
	UID: int
	Ten_file: str
	CreateBy: int
	CreateAt: datetime
	isEmbeding: bool

	model_config = {"from_attributes": True}

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: Optional[str] = None
	role: Optional[str] = None