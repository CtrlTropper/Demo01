# embedding.py: Script để embed PDF vào vector store cho RAG

import os
import torch
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import re
from underthesea import sent_tokenize
from transformers import AutoTokenizer
import faiss
from dotenv import load_dotenv

load_dotenv()

# Paths từ .env (hoặc mặc định về thư mục `backend/data` trong dự án)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data")

EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "D:/Vian/Step2_Embeding_and_VectorDB/models/multilingual_e5_large")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", os.path.join(DEFAULT_DATA_DIR, "all_faiss.index"))
EMBEDDINGS_PICKLE_PATH = os.getenv("EMBEDDINGS_PICKLE_PATH", os.path.join(DEFAULT_DATA_DIR, "all_embeddings.pkl"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", DEFAULT_DATA_DIR)

# Load models
model = SentenceTransformer(EMBEDDING_MODEL_PATH)
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_PATH)

def is_pdf_embedded(pdf_path):
    if not os.path.exists(EMBEDDINGS_PICKLE_PATH):
        return False
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    with open(EMBEDDINGS_PICKLE_PATH, 'rb') as f:
        all_data = pickle.load(f)
    existing_pdf_names = {entry['pdf_name'] for entry in all_data}
    return pdf_name in existing_pdf_names

def preprocess_image(img):
    if img.mode != 'L':
        img = img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    return img.filter(ImageFilter.SHARPEN)

def ocr_pdf_to_text(pdf_path, output_dir):
    print(f"📖 Đang OCR file: {pdf_path}")
    doc = fitz.open(pdf_path)
    full_text = ""
    ocr_config = r'--oem 3 --psm 6 -l vie'
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img = preprocess_image(img)
        page_text = pytesseract.image_to_string(img, config=ocr_config)
        full_text += page_text.strip()
    doc.close()
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(output_dir, pdf_name, f"{pdf_name}_ocr.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    return full_text

def clean_text(text, pdf_path, output_dir):
    text = re.sub(r'[^\w\s.,;:()\[\]?!\"\'\-–—…°%‰≥≤→←≠=+/*<>\n\r]', '', text)
    text = re.sub(r'-\n', '', text)
    text = re.sub(r'\n(?=\w)', ' ', text)
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    clean_text_val = text.strip()
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(output_dir, pdf_name, f"{pdf_name}_clean.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_text_val)
    return clean_text_val

def split_sections(text):
    return [s.strip() for s in re.split(r'\n(?=(?:[IVXLCDM]+\.)|(?:\d+\.)|(?:[a-z]\)))', text) if s.strip()]

def split_text_to_chunks_vi_tokenized_with_section(text, chunk_size=512, overlap=50):
    sections = split_sections(text)
    all_chunks = []
    for section in sections:
        sentences = sent_tokenize(section)
        current_chunk = []
        current_tokens = 0
        for sentence in sentences:
            num_tokens = len(tokenizer.tokenize(sentence))
            if current_tokens + num_tokens > chunk_size:
                chunk_text = '\n'.join(current_chunk).strip()
                all_chunks.append(chunk_text)
                overlap_chunk = []
                total = 0
                for s in reversed(current_chunk):
                    toks = len(tokenizer.tokenize(s))
                    if total + toks > overlap:
                        break
                    overlap_chunk.insert(0, s)
                    total += toks
                current_chunk = overlap_chunk + [sentence]
                current_tokens = total + num_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += num_tokens
        if current_chunk:
            all_chunks.append(' '.join(current_chunk).strip())
    return all_chunks

def create_embeddings(chunks):
    return model.encode(chunks, show_progress_bar=True)

def save_embeddings(chunks, embeddings, pdf_path, output_dir):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(os.path.join(output_dir, pdf_name), exist_ok=True)
    data = {
        'pdf_name': pdf_name,
        'chunks': chunks,
        'embeddings': embeddings,
        'created_at': datetime.now().isoformat()
    }
    pickle_path = os.path.join(output_dir, pdf_name, f"{pdf_name}_embeddings.pkl")
    with open(pickle_path, 'wb') as f:
        pickle.dump(data, f)
    # ... (tiếp tục phần lưu chunks.txt, embedding_info.txt như trước)
    # Lưu FAISS
    index_path = os.path.join(output_dir, pdf_name, f"{pdf_name}_faiss.index")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype(np.float32))
    faiss.write_index(index, index_path)
    # Cập nhật all_faiss và all_pickle
    all_faiss = faiss.IndexFlatL2(dim) if not os.path.exists(FAISS_INDEX_PATH) else faiss.read_index(FAISS_INDEX_PATH)
    all_faiss.add(embeddings.astype(np.float32))
    faiss.write_index(all_faiss, FAISS_INDEX_PATH)
    all_data = [] if not os.path.exists(EMBEDDINGS_PICKLE_PATH) else pickle.load(open(EMBEDDINGS_PICKLE_PATH, 'rb'))
    all_data.append(data)
    with open(EMBEDDINGS_PICKLE_PATH, 'wb') as f:
        pickle.dump(all_data, f)
    return pickle_path, index_path


def is_embedded_by_pdf_name(pdf_name: str, output_dir: str = OUTPUT_DIR) -> bool:
    """Kiểm tra đã có embedding cho một tài liệu theo tên PDF (không đuôi)."""
    per_doc_pkl = os.path.join(output_dir, pdf_name, f"{pdf_name}_embeddings.pkl")
    per_doc_index = os.path.join(output_dir, pdf_name, f"{pdf_name}_faiss.index")
    return os.path.exists(per_doc_pkl) and os.path.exists(per_doc_index)

# Test độc lập (comment nếu tích hợp)
if __name__ == "__main__":
    pdf_path = "D:/Vian/Step1_Data_Prepare/documents/pdf/qd-ban-hanh-va-phuong-an-kich-ban-ung-cu-su-co-he-thong-thong-tin-2023.signed638415142917550402.pdf"  # Thay bằng path thực
    if not is_pdf_embedded(pdf_path):
        raw_text = ocr_pdf_to_text(pdf_path, OUTPUT_DIR)
        cleaned_text = clean_text(raw_text, pdf_path, OUTPUT_DIR)
        chunks = split_text_to_chunks_vi_tokenized_with_section(cleaned_text)
        embeddings = create_embeddings(chunks)
        save_embeddings(chunks, embeddings, pdf_path, OUTPUT_DIR)
    print("Embedding hoàn thành!")