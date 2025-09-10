import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
from dotenv import load_dotenv
import re  # Cho sanitize
from threading import Thread

load_dotenv()

# Paths từ .env
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "D:/Vian/Step2_Embeding_and_VectorDB/models/multilingual_e5_large")
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "D:/Vian/Step3_RAG_and_LLM/models/vinallama-2.7b-chat")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "D:/Vian/Step2_Embeding_and_VectorDB/results/all_faiss.index")
EMBEDDINGS_PICKLE_PATH = os.getenv("EMBEDDINGS_PICKLE_PATH", "D:/Vian/Step2_Embeding_and_VectorDB/results/all_embeddings.pkl")

# Biến toàn cục để khởi tạo lười
embedding_model = None
tokenizer = None
model = None
faiss_index = None
chunks = []
chunk_metadata = []  # Lưu metadata cho mỗi chunk (pdf_name, index)
_initialized = False


def ensure_initialized() -> None:
    global embedding_model, tokenizer, model, faiss_index, chunks, chunk_metadata, _initialized
    if _initialized:
        return

    # Load embedding model
    if embedding_model is None:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_PATH)

    # Load tokenizer và LLM 4-bit
    if tokenizer is None or model is None:
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_PATH)
        tokenizer.pad_token = tokenizer.eos_token
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL_PATH,
            quantization_config=bnb_config,
            device_map={"": 0},
        )
        model.eval()

    # Load FAISS index và chunks nếu tồn tại; nếu không, dùng cấu hình rỗng an toàn
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(EMBEDDINGS_PICKLE_PATH):
        faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(EMBEDDINGS_PICKLE_PATH, "rb") as f:
            data = pickle.load(f)
        chunks = []
        chunk_metadata = []
        for item in data:
            pdf_name = item.get("pdf_name", "unknown")
            item_chunks = item.get("chunks", [])
            chunks.extend(item_chunks)
            # Lưu metadata cho mỗi chunk
            for i in range(len(item_chunks)):
                chunk_metadata.append({
                    "pdf_name": pdf_name,
                    "chunk_index": i
                })
    else:
        faiss_index = None
        chunks = []
        chunk_metadata = []

    _initialized = True

def sanitize_input(text: str) -> str:
    text = re.sub(r'[^\w\s.,;:()\[\]?!\"\'\-–—…°%‰≥≤→←≠=+/*<>\n\r]', '', text)
    return text.strip()

def get_relevant_chunks(query, top_k=3, max_tokens_per_chunk=512, pdf_name=None):
    query = sanitize_input(query)
    if faiss_index is None or len(chunks) == 0:
        return []
    query_vector = embedding_model.encode([query])
    D, I = faiss_index.search(np.array(query_vector).astype("float32"), top_k)
    context_chunks = []
    for i in I[0]:
        if i < len(chunks):
            chunk = chunks[i]
            # Nếu có pdf_name, chỉ lấy chunks từ tài liệu đó
            if pdf_name is not None and i < len(chunk_metadata):
                chunk_pdf_name = chunk_metadata[i].get("pdf_name", "")
                if chunk_pdf_name != pdf_name:
                    continue  # Bỏ qua chunk không thuộc PDF được chỉ định
            tokens = tokenizer.tokenize(chunk)
            if len(tokens) > max_tokens_per_chunk:
                tokens = tokens[:max_tokens_per_chunk]
                chunk = tokenizer.convert_tokens_to_string(tokens)
            context_chunks.append(chunk.strip())
    return context_chunks

def build_prompt(context_chunks, question):
    context = "\n---\n".join(context_chunks)
    return f"""
    <|im_start|>system
    Bạn là một trợ lý AI an toàn thông tin. Chỉ trả lời người dùng dựa trên thông tin được cung cấp dưới đây. Nếu không biết, hãy trả lời: "Tôi không có thông tin về câu hỏi này." Không được bịa.
    <|im_end|>
    <|im_start|>user
    Thông tin:
    {context}

    Câu hỏi: {question}
    <|im_end|>
    <|im_start|>assistant
    """.strip()

def generate_answer(prompt):
    encoding = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        input_ids=encoding.input_ids,
        attention_mask=encoding.attention_mask,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def rag_answer(query, top_k=3, pdf_name=None):
    ensure_initialized()
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    prompt = build_prompt(context_chunks, query)
    answer = generate_answer(prompt)
    return answer.split("<|im_start|>assistant")[-1].strip()


def generate_answer_stream(prompt):
    """Trả về iterator text stream theo thời gian thực."""
    ensure_initialized()
    streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, skip_prompt=True)
    encoding = tokenizer(prompt, return_tensors="pt").to(model.device)

    generate_kwargs = dict(
        input_ids=encoding.input_ids,
        attention_mask=encoding.attention_mask,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True,
        streamer=streamer,
    )

    thread = Thread(target=model.generate, kwargs=generate_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text


def rag_answer_stream(query, top_k=3, pdf_name=None):
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    prompt = build_prompt(context_chunks, query)
    return generate_answer_stream(prompt)

# Test độc lập (comment nếu tích hợp)
if __name__ == "__main__":
    query = "An toàn thông tin là gì?"
    response = rag_answer(query)
    print(response)