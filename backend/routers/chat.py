from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..schemas.chat import ChatRequest, ChatResponse
from ..db.database import get_db
from ..db.models import Chat, Document
from ..core.embeding import (
    ocr_pdf_to_text,
    clean_text,
    split_text_to_chunks_vi_tokenized_with_section,
    create_embeddings,
    save_embeddings,
    OUTPUT_DIR,
)
from ..core.rag import rag_answer, rag_answer_stream  # Từ core
import uuid
import os
from .auth import get_current_user

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Generate response
    response = rag_answer(request.query)
    
    # Lưu lịch sử (chỉ khi có user đăng nhập)
    session_id = request.session_id or str(uuid.uuid4())
    if user is not None:
        chat = Chat(session_id=session_id, user_query=request.query, ai_response=response, user_id=user.id)
        db.add(chat)
        db.commit()
    
    return ChatResponse(response=response, session_id=session_id)

@router.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    pdf_name = os.path.splitext(os.path.basename(file.filename))[0]

    # Nếu đã tồn tại trong DB thì bỏ qua để tránh embed trùng
    existing = db.query(Document).filter(Document.pdf_name == pdf_name).first()
    if existing:
        return {"message": "PDF already embedded"}

    # Lưu file tạm vào OUTPUT_DIR/uploads để xử lý OCR/Embedding
    uploads_dir = os.path.join(OUTPUT_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    saved_pdf_path = os.path.join(uploads_dir, f"{pdf_name}.pdf")
    with open(saved_pdf_path, "wb") as f:
        f.write(file.file.read())

    # OCR và xử lý văn bản
    raw_text = ocr_pdf_to_text(saved_pdf_path, OUTPUT_DIR)
    if not raw_text:
        raise HTTPException(status_code=500, detail="OCR failed")

    cleaned_text = clean_text(raw_text, saved_pdf_path, OUTPUT_DIR)
    chunks_local = split_text_to_chunks_vi_tokenized_with_section(cleaned_text)
    embeddings = create_embeddings(chunks_local)
    save_embeddings(chunks_local, embeddings, saved_pdf_path, OUTPUT_DIR)

    # Lưu metadata vào DB
    doc = Document(pdf_name=pdf_name, path=saved_pdf_path)
    db.add(doc)
    db.commit()

    return {"message": "PDF embedded successfully"}


@router.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    session_id = request.session_id or str(uuid.uuid4())

    def event_generator():
        # Stream từng chunk text ra client theo SSE
        for chunk in rag_answer_stream(request.query):
            if not chunk:
                continue
            # SSE chuẩn: mỗi dòng dữ liệu đều bắt đầu bằng 'data:'
            # và một sự kiện kết thúc bằng dòng trống.
            for line in str(chunk).splitlines():
                yield f"data: {line}\n"
            # Kết thúc một sự kiện
            yield "\n"
        # Kết thúc stream
        yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    response = StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
    return response