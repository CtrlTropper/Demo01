from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Để duy trì lịch sử nếu cần
    doc_id: Optional[int] = None  # Tùy chọn: giới hạn truy vấn theo tài liệu đã upload
    pdf_name: Optional[str] = None  # Tùy chọn: cho tài liệu khởi tạo (không có doc_id)

class ChatResponse(BaseModel):
    response: str
    session_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class ConversationItem(BaseModel):
    id: int
    title: str
    created_at: str


class MessageItem(BaseModel):
    id: int
    sender: str
    text: str
    created_at: str