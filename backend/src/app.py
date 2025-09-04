# app.py: Backend FastAPI với auth và user management

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import yaml
from RAG import rag_answer  # Từ RAG.py
from database import get_db, engine, Base
from models import User
from schemas import UserCreate, UserUpdate, UserOut, Token
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_admin
)

app = FastAPI(title="Cybersecurity Assistant Backend")

# Tạo DB tables nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

class QueryRequest(BaseModel):
    query: str

# Endpoint Đăng nhập
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint Chat (Yêu cầu auth, cho cả User và Admin)
@app.post("/chat")
def chat(query_request: QueryRequest, current_user: User = Depends(get_current_user)):
    response = rag_answer(query_request.query)
    return {"response": response}

# Endpoints Quản lý Người Dùng (Chỉ Admin)
@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=list[UserOut])
def read_users(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    users = db.query(User).all()
    return users

@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    if user_update.role:
        db_user.role = user_update.role
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}

# Tạo admin mặc định nếu chưa có (chạy lần đầu)
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        hashed_password = get_password_hash("admin_password")  # Thay bằng password mạnh
        new_admin = User(username="admin", hashed_password=hashed_password, role="admin")
        db.add(new_admin)
        db.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)