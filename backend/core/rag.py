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

# Paths từ .env (mặc định về thư mục `backend/data`)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "results")

EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "D:/Vian/Step2_Embeding_and_VectorDB/models/multilingual_e5_large")
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "D:/Vian/Step3_RAG_and_LLM/models/vinallama-2.7b-chat")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", os.path.join(DEFAULT_DATA_DIR, "all_faiss.index"))
EMBEDDINGS_PICKLE_PATH = os.getenv("EMBEDDINGS_PICKLE_PATH", os.path.join(DEFAULT_DATA_DIR, "all_embeddings.pkl"))
# Đồng bộ với embedding.py: cho phép chỉ định OUTPUT_DIR
OUTPUT_DIR = os.getenv("OUTPUT_DIR", DEFAULT_DATA_DIR)

# Cấu hình sinh
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))

# Biến toàn cục để khởi tạo lười
embedding_model = None
tokenizer = None
model = None
faiss_index = None
chunks = []
_initialized = False


def ensure_initialized() -> None:
    global embedding_model, tokenizer, model, faiss_index, chunks, _initialized
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
        for item in data:
            chunks.extend(item.get("chunks", []))
    else:
        faiss_index = None
        chunks = []

    _initialized = True

def sanitize_input(text: str) -> str:
    text = re.sub(r'[^\w\s.,;:()\[\]?!\"\'\-–—…°%‰≥≤→←≠=+/*<>\n\r]', '', text)
    return text.strip()

def _trim_chunk_tokens(chunk: str, max_tokens_per_chunk: int) -> str:
    tokens = tokenizer.tokenize(chunk)
    if len(tokens) > max_tokens_per_chunk:
        tokens = tokens[:max_tokens_per_chunk]
        return tokenizer.convert_tokens_to_string(tokens)
    return chunk


def get_relevant_chunks(query, top_k=3, max_tokens_per_chunk=512, pdf_name: str | None = None):
    query = sanitize_input(query)
    # Cải thiện cho e5: thêm tiền tố 'query: '
    query_for_embedding = f"query: {query}" if "e5" in EMBEDDING_MODEL_PATH.lower() else query
    # Nếu chỉ định tài liệu, ưu tiên dùng index và chunks theo tài liệu đó
    if pdf_name:
        doc_dir = os.path.join(OUTPUT_DIR, pdf_name)
        index_path = os.path.join(doc_dir, f"{pdf_name}_faiss.index")
        pickle_path = os.path.join(doc_dir, f"{pdf_name}_embeddings.pkl")
        if os.path.exists(index_path) and os.path.exists(pickle_path):
            local_index = faiss.read_index(index_path)
            with open(pickle_path, "rb") as f:
                local_data = pickle.load(f)
            local_chunks = local_data.get("chunks", [])
            if len(local_chunks) == 0:
                return []
            query_vector = embedding_model.encode([query_for_embedding])
            D, I = local_index.search(np.array(query_vector).astype("float32"), top_k)
            context_chunks = []
            for i in I[0]:
                if i < len(local_chunks):
                    chunk = _trim_chunk_tokens(local_chunks[i], max_tokens_per_chunk)
                    context_chunks.append(chunk.strip())
            return context_chunks

    # Ngược lại, dùng index toàn cục
    if faiss_index is None or len(chunks) == 0:
        return []
    query_vector = embedding_model.encode([query_for_embedding])
    D, I = faiss_index.search(np.array(query_vector).astype("float32"), top_k)
    context_chunks = []
    for i in I[0]:
        if i < len(chunks):
            chunk = _trim_chunk_tokens(chunks[i], max_tokens_per_chunk)
            context_chunks.append(chunk.strip())
    return context_chunks

def build_prompt(context_chunks, question):
    context = "\n---\n".join(context_chunks)
    return f"""
<|im_start|>system
Bạn là trợ lý AI lĩnh vực an toàn thông tin, trả lời NGẮN GỌN, rõ ràng, bằng tiếng Việt. CHỈ dùng thông tin trong phần 'Thông tin'. Nếu không có thông tin liên quan, trả lời đúng một câu: "Tôi không có thông tin về câu hỏi này." Không lặp lại câu hỏi. Không nhắc lại 'Thông tin'.
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
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=0.2,
        do_sample=False,
        repetition_penalty=1.15,
        no_repeat_ngram_size=4,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Chỉ lấy phần sau thẻ assistant để tránh echo prompt
    if "<|im_start|>assistant" in full_text:
        return full_text.split("<|im_start|>assistant", 1)[1].strip()
    # Fallback: cắt bỏ phần prompt đầu vào
    prompt_len = len(tokenizer.decode(encoding.input_ids[0], skip_special_tokens=True))
    return full_text[prompt_len:].strip()

def rag_answer(query, top_k=3, pdf_name: str | None = None):
    ensure_initialized()
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    # Nếu không có ngữ cảnh, trả lời chuẩn
    if not context_chunks:
        return "Tôi không có thông tin về câu hỏi này."
    prompt = build_prompt(context_chunks, query)
    answer = generate_answer(prompt)
    return answer.strip()


def generate_answer_stream(prompt):
    """Trả về iterator text stream theo thời gian thực."""
    ensure_initialized()
    streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, skip_prompt=True)
    encoding = tokenizer(prompt, return_tensors="pt").to(model.device)

    generate_kwargs = dict(
        input_ids=encoding.input_ids,
        attention_mask=encoding.attention_mask,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=0.2,
        do_sample=False,
        repetition_penalty=1.15,
        no_repeat_ngram_size=4,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        streamer=streamer,
    )

    thread = Thread(target=model.generate, kwargs=generate_kwargs)
    thread.start()

    # Bỏ phần prompt nếu model vẫn stream lại đầu vào
    yielded_any = False
    for new_text in streamer:
        if not yielded_any:
            # Cắt tiền tố nếu nó khớp với một phần của prompt
            if new_text.strip().startswith("<|im_start|>assistant"):
                new_text = new_text.split("<|im_start|>assistant", 1)[1]
            yielded_any = True if new_text else yielded_any
        if new_text:
            yield new_text


def rag_answer_stream(query, top_k=3, pdf_name: str | None = None):
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    if not context_chunks:
        # Stream câu trả lời mặc định ngắn
        def _gen():
            yield "Tôi không có thông tin về câu hỏi này."
        return _gen()
    prompt = build_prompt(context_chunks, query)
    return generate_answer_stream(prompt)

# Test độc lập (comment nếu tích hợp)
if __name__ == "__main__":
    query = "An toàn thông tin là gì?"
    response = rag_answer(query)
    print(response)