from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
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
    is_embedded_by_pdf_name,
    normalize_filename,
)
from ..core.rag import rag_answer, rag_answer_stream, reload_embeddings  # Từ core
import uuid
import os
from .auth import get_current_user

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Xác định tài liệu (nếu có) để lọc ngữ cảnh
    pdf_name = None
    if request.doc_id is not None:
        doc = db.query(Document).filter(Document.id == request.doc_id).first()
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        pdf_name = doc.pdf_name
    elif request.pdf_name:
        pdf_name = request.pdf_name

    # Generate response
    response = rag_answer(request.query, pdf_name=pdf_name)
    
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

    # Chuyển đổi tên file từ tiếng Việt có dấu sang không dấu
    normalized_filename = normalize_filename(file.filename)
    pdf_name = os.path.splitext(os.path.basename(normalized_filename))[0]

    # Nếu đã tồn tại trong DB thì bỏ qua để tránh embed trùng
    existing = db.query(Document).filter(Document.pdf_name == pdf_name).first()
    if existing:
        return {"message": "PDF already embedded", "doc_id": existing.id, "pdf_name": pdf_name}

    # Lưu file tạm vào backend/data/uploads để xử lý OCR/Embedding
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uploads_dir = os.path.join(backend_dir, "data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    saved_pdf_path = os.path.join(uploads_dir, normalized_filename)
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

    # Lưu metadata vào DB (lưu cả tên gốc và tên đã chuyển đổi)
    doc = Document(pdf_name=pdf_name, path=saved_pdf_path, original_filename=file.filename)
    db.add(doc)
    db.commit()

    # Reload embeddings để cập nhật RAG system
    reload_embeddings()

    return {"message": "PDF embedded successfully", "doc_id": doc.id, "pdf_name": pdf_name, "original_filename": file.filename}


@router.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")

    session_id = request.session_id or str(uuid.uuid4())

    def event_generator():
        # Stream từng chunk text ra client theo SSE
        pdf_name = None
        if request.doc_id is not None:
            doc = db.query(Document).filter(Document.id == request.doc_id).first()
            if doc is None:
                # Nếu tài liệu không tồn tại, dừng stream với thông báo lỗi
                yield f"data: Tài liệu không tồn tại.\n\n"
                return
            pdf_name = doc.pdf_name
        elif request.pdf_name:
            pdf_name = request.pdf_name
        for chunk in rag_answer_stream(request.query, pdf_name=pdf_name):
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


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        # Hiển thị tên file gốc nếu có, nếu không thì dùng tên đã chuyển đổi
        display_name = d.original_filename if d.original_filename else d.pdf_name
        results.append({
            "id": d.id,
            "pdf_name": d.pdf_name,  # Tên file đã chuyển đổi để xử lý
            "display_name": display_name,  # Tên file hiển thị cho người dùng
            "path": d.path,
            "embedded": is_embedded_by_pdf_name(d.pdf_name, OUTPUT_DIR),
            "category": "Uploads",
        })
    # Liệt kê tài liệu ban đầu trong initial_docs của cả results và data (không nằm DB)
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    initial_dirs = [
        os.path.join(OUTPUT_DIR, "initial_docs"),
        os.path.join(backend_dir, "data", "initial_docs"),
    ]
    seen = set((item["pdf_name"], item["category"]) for item in results)
    for initial_dir in initial_dirs:
        if os.path.exists(initial_dir):
            for root, _, files in os.walk(initial_dir):
                for fname in files:
                    if not fname.lower().endswith('.pdf'):
                        continue
                    name = os.path.splitext(fname)[0]
                    rel = os.path.relpath(root, initial_dir)
                    category = rel if rel != "." else "Initial"
                    key = (name, category)
                    if key in seen:
                        continue
                    results.append({
                        "id": None,
                        "pdf_name": name,
                        "path": os.path.join(root, fname),
                        "embedded": is_embedded_by_pdf_name(name, OUTPUT_DIR),
                        "category": category,
                    })
                    seen.add(key)
    # Thêm các file upload trong backend/data/uploads (chưa qua DB)
    uploads_dir = os.path.join(backend_dir, "data", "uploads")
    if os.path.exists(uploads_dir):
        for fname in os.listdir(uploads_dir):
            if not fname.lower().endswith('.pdf'):
                continue
            name = os.path.splitext(fname)[0]
            if not any(r["pdf_name"] == name and r["category"] == "Uploads" for r in results):
                results.append({
                    "id": None,
                    "pdf_name": name,
                    "path": os.path.join(uploads_dir, fname),
                    "embedded": is_embedded_by_pdf_name(name, OUTPUT_DIR),
                    "category": "Uploads",
                })
    return {"items": results}


@router.post("/documents/refresh")
def refresh_documents(db: Session = Depends(get_db)):
    """
    Refresh danh sách tài liệu và reload embeddings.
    Được gọi khi có thay đổi trong file system.
    """
    try:
        # Reload embeddings để cập nhật RAG system
        reload_embeddings()
        
        # Trả về danh sách tài liệu mới
        return list_documents(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh documents: {str(e)}")


@router.get("/documents/{pdf_name}")
def view_document(pdf_name: str, category: str | None = None):
    # Ưu tiên trong uploads (cả results và data), sau đó initial_docs (cả results và data)
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uploads_dirs = [
        os.path.join(OUTPUT_DIR, "uploads"),
        os.path.join(backend_dir, "data", "uploads"),
    ]
    initial_dirs = [
        os.path.join(OUTPUT_DIR, "initial_docs"),
        os.path.join(backend_dir, "data", "initial_docs"),
    ]
    # Tìm trong uploads (phẳng)
    for up_dir in uploads_dirs:
        fpath = os.path.join(up_dir, f"{pdf_name}.pdf")
        if os.path.exists(fpath):
            return FileResponse(fpath, media_type='application/pdf', filename=f"{pdf_name}.pdf")
    # Tìm theo category nếu cung cấp
    if category:
        for base in initial_dirs:
            cat_dir = os.path.join(base, category)
            if os.path.isdir(cat_dir):
                for root, _, files in os.walk(cat_dir):
                    for fname in files:
                        if fname.lower() == f"{pdf_name.lower()}.pdf":
                            return FileResponse(os.path.join(root, fname), media_type='application/pdf', filename=f"{pdf_name}.pdf")
    # Fallback: tìm đệ quy trong initial_docs
    for base in initial_dirs:
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for fname in files:
                    if fname.lower() == f"{pdf_name.lower()}.pdf":
                        return FileResponse(os.path.join(root, fname), media_type='application/pdf', filename=f"{pdf_name}.pdf")
    raise HTTPException(status_code=404, detail="Document file not found")


@router.post("/documents/{pdf_name}/embed")
def embed_existing_document(pdf_name: str, category: str | None = None):
    # Tìm file trong uploads hoặc initial_docs (cả results và data)
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uploads_dirs = [
        os.path.join(OUTPUT_DIR, "uploads"),
        os.path.join(backend_dir, "data", "uploads"),
    ]
    initial_dirs = [
        os.path.join(OUTPUT_DIR, "initial_docs"),
        os.path.join(backend_dir, "data", "initial_docs"),
    ]
    pdf_path = None
    # Tìm trong uploads (phẳng)
    for up_dir in uploads_dirs:
        f_up = os.path.join(up_dir, f"{pdf_name}.pdf")
        if os.path.exists(f_up):
            pdf_path = f_up
            break
    # Tìm theo category (nếu có)
    if pdf_path is None and category:
        for base in initial_dirs:
            cat_dir = os.path.join(base, category)
            if os.path.isdir(cat_dir):
                for root, _, files in os.walk(cat_dir):
                    for fname in files:
                        if fname.lower() == f"{pdf_name.lower()}.pdf":
                            pdf_path = os.path.join(root, fname)
                            break
                    if pdf_path:
                        break
            if pdf_path:
                break
    # Fallback: tìm đệ quy trong initial_docs
    if pdf_path is None:
        for base in initial_dirs:
            if os.path.isdir(base):
                for root, _, files in os.walk(base):
                    for fname in files:
                        if fname.lower() == f"{pdf_name.lower()}.pdf":
                            pdf_path = os.path.join(root, fname)
                            break
                    if pdf_path:
                        break
            if pdf_path:
                break
    if pdf_path is None:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Nếu đã nhúng thì trả về luôn
    if is_embedded_by_pdf_name(pdf_name, OUTPUT_DIR):
        return {"message": "Already embedded", "pdf_name": pdf_name}

    # Thực hiện OCR/clean/chunk/embed
    raw_text = ocr_pdf_to_text(pdf_path, OUTPUT_DIR)
    if not raw_text:
        raise HTTPException(status_code=500, detail="OCR failed")
    cleaned_text = clean_text(raw_text, pdf_path, OUTPUT_DIR)
    chunks_local = split_text_to_chunks_vi_tokenized_with_section(cleaned_text)
    embeddings = create_embeddings(chunks_local)
    save_embeddings(chunks_local, embeddings, pdf_path, OUTPUT_DIR)
    
    # Reload embeddings để cập nhật RAG system
    reload_embeddings()
    
    return {"message": "Embedded successfully", "pdf_name": pdf_name}


@router.delete("/documents/{pdf_name}")
def delete_document(pdf_name: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Xóa tài liệu chỉ áp dụng với tài liệu upload từ người dùng.
    Không cho phép xóa các file trong initial_docs.
    """
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uploads_dirs = [
        os.path.join(OUTPUT_DIR, "uploads"),
        os.path.join(backend_dir, "data", "uploads"),
    ]
    
    # Chỉ tìm trong thư mục uploads
    pdf_path = None
    for up_dir in uploads_dirs:
        f_up = os.path.join(up_dir, f"{pdf_name}.pdf")
        if os.path.exists(f_up):
            pdf_path = f_up
            break
    
    if pdf_path is None:
        raise HTTPException(status_code=404, detail="Document not found in uploads")
    
    try:
        # Xóa file PDF
        os.remove(pdf_path)
        
        # Xóa embeddings và FAISS index nếu có
        from ..core.embeding import remove_embeddings_by_pdf_name
        remove_embeddings_by_pdf_name(pdf_name, OUTPUT_DIR)
        
        # Xóa record trong database nếu có
        doc = db.query(Document).filter(Document.pdf_name == pdf_name).first()
        if doc:
            db.delete(doc)
            db.commit()
        
        # Reload embeddings để cập nhật RAG system
        reload_embeddings()
        
        return {"message": f"Document {pdf_name} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")