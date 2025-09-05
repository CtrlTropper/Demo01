# app.py: Backend FastAPI với auth và user management

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import yaml
from RAG import rag_answer  # Từ RAG.py
from database import get_db, engine, Base
from models import DS_Nguoi_dung, DS_File
from schemas import UserCreate, UserUpdate, UserOut, Token, FileCreate, FileOut
from auth import (
	verify_password, get_password_hash,
	get_current_user, get_current_admin, create_session_token
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cybersecurity Assistant Backend")

# CORS cho frontend Vite
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Tạo DB tables nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

class QueryRequest(BaseModel):
	query: str

# Endpoint Đăng nhập
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
	user = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.Username == form_data.username).first()
	if not user or not verify_password(form_data.password, user.passwork):
		raise HTTPException(status_code=400, detail="Incorrect username or password")
	# Tạo session token thay vì JWT
	token = create_session_token(db, user.UID)
	return {"access_token": token, "token_type": "bearer"}

# Endpoint lấy thông tin người dùng hiện tại
@app.get("/me")
def me(current_user: DS_Nguoi_dung = Depends(get_current_user)):
	return {"username": current_user.Username, "is_admin": current_user.isAdmin}

# Endpoint Chat (Yêu cầu auth, cho cả User và Admin)
@app.post("/chat")
def chat(query_request: QueryRequest, current_user: DS_Nguoi_dung = Depends(get_current_user)):
	response = rag_answer(query_request.query)
	return {"response": response}

# Endpoints Quản lý Người Dùng (Chỉ Admin)
@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_admin: DS_Nguoi_dung = Depends(get_current_admin)):
	db_user = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.Username == user.username).first()
	if db_user:
		raise HTTPException(status_code=400, detail="Username already registered")
	hashed_password = get_password_hash(user.password)
	new_user = DS_Nguoi_dung(Username=user.username, passwork=hashed_password, isAdmin=bool(user.is_admin))
	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	return new_user

@app.get("/users", response_model=list[UserOut])
def read_users(db: Session = Depends(get_db), current_admin: DS_Nguoi_dung = Depends(get_current_admin)):
	users = db.query(DS_Nguoi_dung).all()
	return users

@app.put("/users/{uid}", response_model=UserOut)
def update_user(uid: int, user_update: UserUpdate, db: Session = Depends(get_db), current_admin: DS_Nguoi_dung = Depends(get_current_admin)):
	db_user = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.UID == uid).first()
	if not db_user:
		raise HTTPException(status_code=404, detail="User not found")
	if user_update.password:
		db_user.passwork = get_password_hash(user_update.password)
	if user_update.is_admin is not None:
		db_user.isAdmin = bool(user_update.is_admin)
	db.commit()
	db.refresh(db_user)
	return db_user

@app.delete("/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), current_admin: DS_Nguoi_dung = Depends(get_current_admin)):
	db_user = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.UID == uid).first()
	if not db_user:
		raise HTTPException(status_code=404, detail="User not found")
	db.delete(db_user)
	db.commit()
	return {"detail": "User deleted"}

# Endpoints quản lý file (tham khảo)
@app.post("/files", response_model=FileOut)
def create_file(file: FileCreate, db: Session = Depends(get_db), current_user: DS_Nguoi_dung = Depends(get_current_user)):
	# Chỉ cho phép tạo file cho chính mình hoặc admin tạo thay
	if (not current_user.isAdmin) and (current_user.UID != file.CreateBy):
		raise HTTPException(status_code=403, detail="Not allowed")
	new_file = DS_File(Ten_file=file.Ten_file, CreateBy=file.CreateBy, isEmbeding=bool(file.isEmbeding))
	db.add(new_file)
	db.commit()
	db.refresh(new_file)
	return new_file

@app.get("/files", response_model=list[FileOut])
def list_files(db: Session = Depends(get_db), current_user: DS_Nguoi_dung = Depends(get_current_user)):
	# Admin thấy tất cả, user chỉ thấy file của mình
	query = db.query(DS_File)
	if not current_user.isAdmin:
		query = query.filter(DS_File.CreateBy == current_user.UID)
	return query.all()

@app.delete("/files/{uid}")
def delete_file(uid: int, db: Session = Depends(get_db), current_user: DS_Nguoi_dung = Depends(get_current_user)):
	f = db.query(DS_File).filter(DS_File.UID == uid).first()
	if not f:
		raise HTTPException(status_code=404, detail="File not found")
	if (not current_user.isAdmin) and (current_user.UID != f.CreateBy):
		raise HTTPException(status_code=403, detail="Not allowed")
	db.delete(f)
	db.commit()
	return {"detail": "File deleted"}

# Tạo admin mặc định nếu chưa có (chạy lần đầu)
@app.on_event("startup")
def startup_event():
	db = next(get_db())
	admin = db.query(DS_Nguoi_dung).filter(DS_Nguoi_dung.Username == "Admin").first()
	if not admin:
		hashed_password = get_password_hash("123456789")
		new_admin = DS_Nguoi_dung(Username="Admin", passwork=hashed_password, isAdmin=True)
		db.add(new_admin)
		db.commit()

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)