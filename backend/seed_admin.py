# file: seed_admin.py
import os
from passlib.context import CryptContext
from backend.db.database import SessionLocal
from backend.db.models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme"  # đổi ngay sau khi tạo

db = SessionLocal()
try:
    existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
    if existing:
        print("Admin đã tồn tại.")
    else:
        user = User(username=ADMIN_USERNAME, password_hash=pwd.hash(ADMIN_PASSWORD), role="admin")
        db.add(user)
        db.commit()
        print("Tạo admin thành công.")
finally:
    db.close()