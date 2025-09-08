from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env

from .core.rag_core import init_models  # Khởi tạo models
from .routers.chat import router as chat_router
from .db.database import engine
from .db.models import Base
from fastapi.middleware.cors import CORSMiddleware

# Tạo DB tables nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG-Chatbot Cybersecurity Assistant")

# CORS cho frontend Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers
app.include_router(chat_router, prefix="/api")

# Khởi tạo models (embedding, LLM, FAISS)
init_models()

@app.get("/")
def root():
    return {"message": "Welcome to RAG-Chatbot API"}