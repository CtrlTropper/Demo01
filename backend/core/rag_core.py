from dotenv import load_dotenv
import os

# Chỉ export API công khai để nơi khác import từ đây
from .embeding import (
    ocr_pdf_to_text,
    clean_text,
    split_text_to_chunks_vi_tokenized_with_section,
    create_embeddings,
    save_embeddings,
)
from .rag import ensure_initialized


load_dotenv()


def init_models() -> None:
    """Khởi tạo lười các tài nguyên nặng (LLM/FAISS) trước khi phục vụ request.

    - Đảm bảo các biến môi trường đã được load
    - Kiểm tra hoặc tạo các tài nguyên bắt buộc (FAISS index, embeddings pickle)
    - Khởi tạo model LLM/embedding khi cần
    """
    # Chuyển phần khởi tạo thật sự sang core.rag.ensure_initialized để tránh import nặng ở startup
    ensure_initialized()
