from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


# DATABASE_URL ví dụ: sqlite:///./app.db hoặc postgresql+psycopg2://user:pass@host:port/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")


# Với SQLite cần check_same_thread=False để dùng qua nhiều threads trong FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


