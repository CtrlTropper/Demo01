from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Để duy trì lịch sử nếu cần

class ChatResponse(BaseModel):
    response: str
    session_id: str