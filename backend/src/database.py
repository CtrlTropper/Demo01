from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import yaml

# Đọc cấu hình DB từ YAML nếu có, fallback sang SQLite file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
DB_URL_DEFAULT = "sqlite:///../results/app.db"

DATABASE_URL = None
try:
	if os.path.exists(CONFIG_PATH):
		with open(CONFIG_PATH, "r", encoding="utf-8") as f:
			cfg = yaml.safe_load(f) or {}
			DATABASE_URL = cfg.get("database", {}).get("url")
except Exception:
	# Giữ None để dùng default
	pass

if not DATABASE_URL:
	DATABASE_URL = DB_URL_DEFAULT

# SQLite needs check_same_thread=False if used with FastAPI sessions
engine = create_engine(
	DATABASE_URL,
	connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency sử dụng trong FastAPI

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
