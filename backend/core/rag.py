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
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "D:/Vian/Demo/backend/results/all_faiss.index")
EMBEDDINGS_PICKLE_PATH = os.getenv("EMBEDDINGS_PICKLE_PATH", "D:/Vian/Demo/backend/results/all_embeddings.pkl")

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

def remove_repetitive_content(response: str, original_query: str) -> str:
    """
    Loại bỏ nội dung lặp lại trong response.
    """
    # Tách response thành các câu
    sentences = response.split('. ')
    
    # Loại bỏ các câu trùng lặp
    unique_sentences = []
    seen_sentences = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Chuẩn hóa câu để so sánh (loại bỏ dấu câu, chuyển thành chữ thường)
        normalized = re.sub(r'[^\w\s]', '', sentence.lower())
        
        # Bỏ qua câu trùng lặp hoặc câu chỉ chứa câu hỏi gốc
        if (normalized not in seen_sentences and 
            len(normalized) > 10 and  # Bỏ qua câu quá ngắn
            not any(word in normalized for word in ['câu hỏi:', 'hỏi:', '?'])):
            unique_sentences.append(sentence)
            seen_sentences.add(normalized)
    
    # Ghép lại thành response hoàn chỉnh
    cleaned_response = '. '.join(unique_sentences)
    
    # Đảm bảo response kết thúc bằng dấu chấm
    if cleaned_response and not cleaned_response.endswith('.'):
        cleaned_response += '.'
    
    return cleaned_response

def is_context_relevant(query: str, context_chunks: list) -> bool:
    """
    Kiểm tra xem context có liên quan đến câu hỏi không.
    """
    if not context_chunks:
        return False
    
    # Lấy các từ khóa chính từ câu hỏi
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    
    # Kiểm tra xem có ít nhất 2 từ khóa xuất hiện trong context không
    relevant_count = 0
    for chunk in context_chunks:
        chunk_words = set(re.findall(r'\b\w+\b', chunk.lower()))
        common_words = query_words.intersection(chunk_words)
        if len(common_words) >= 2:  # Ít nhất 2 từ khóa chung
            relevant_count += 1
    
    # Nếu ít nhất 1 chunk có liên quan thì coi là relevant
    return relevant_count > 0

def is_response_hallucinated(response: str, context_chunks: list) -> bool:
    """
    Kiểm tra xem response có vẻ như bịa đặt không.
    """
    if not response or len(response.strip()) < 20:
        return False
    
    # Kiểm tra các dấu hiệu bịa đặt
    hallucination_indicators = [
        "tôi không có thông tin",
        "không có thông tin",
        "không biết",
        "không rõ",
        "có thể",
        "có lẽ",
        "có khả năng",
        "theo tôi",
        "tôi nghĩ",
        "tôi cho rằng"
    ]
    
    response_lower = response.lower()
    
    # Nếu response chứa các từ chỉ sự không chắc chắn
    if any(indicator in response_lower for indicator in hallucination_indicators):
        return True
    
    # Kiểm tra xem response có chứa thông tin không có trong context không
    response_words = set(re.findall(r'\b\w+\b', response_lower))
    context_text = ' '.join(context_chunks).lower()
    context_words = set(re.findall(r'\b\w+\b', context_text))
    
    # Nếu response có quá nhiều từ không xuất hiện trong context
    unique_words = response_words - context_words
    if len(unique_words) > len(response_words) * 0.3:  # Hơn 30% từ không có trong context
        return True
    
    return False

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
    
    # Kiểm tra nếu không có context hoặc context quá ngắn
    if not context_chunks or len(context.strip()) < 50:
        return f"""
        <|im_start|>system
        Bạn là một trợ lý AI chuyên về an toàn thông tin. 
        
        QUY TẮC NGHIÊM NGẶT:
        - CHỈ trả lời dựa trên thông tin được cung cấp trong phần "Thông tin tham khảo"
        - TUYỆT ĐỐI KHÔNG được bịa đặt, suy đoán hoặc tạo ra thông tin không có trong tài liệu
        - Nếu thông tin tham khảo không đủ hoặc không liên quan, PHẢI trả lời: "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
        - KHÔNG được sử dụng kiến thức bên ngoài hoặc kinh nghiệm cá nhân
        <|im_end|>
        <|im_start|>user
        Thông tin tham khảo: {context}

        Câu hỏi: {question}
        <|im_end|>
        <|im_start|>assistant
        """.strip()
    
    return f"""
    <|im_start|>system
    Bạn là một trợ lý AI chuyên về an toàn thông tin. 
    
    QUY TẮC NGHIÊM NGẶT:
    - CHỈ trả lời dựa trên thông tin được cung cấp trong phần "Thông tin tham khảo"
    - TUYỆT ĐỐI KHÔNG được bịa đặt, suy đoán hoặc tạo ra thông tin không có trong tài liệu
    - Nếu thông tin tham khảo không đủ hoặc không liên quan, PHẢI trả lời: "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
    - KHÔNG được sử dụng kiến thức bên ngoài hoặc kinh nghiệm cá nhân
    - Trả lời ngắn gọn, súc tích và có cấu trúc rõ ràng
    - KHÔNG lặp lại câu hỏi trong câu trả lời
    <|im_end|>
    <|im_start|>user
    Thông tin tham khảo:
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
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
        repetition_penalty=1.2,  # Giảm lặp lại
        no_repeat_ngram_size=3,  # Tránh lặp lại cụm từ 3 từ
        early_stopping=True,     # Dừng sớm khi gặp end token
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def rag_answer(query, top_k=3, pdf_name=None):
    ensure_initialized()
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    
    # Kiểm tra nếu không có context hoặc context không liên quan
    if not context_chunks or len(context_chunks) == 0:
        return "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
    
    # Kiểm tra độ liên quan của context với câu hỏi
    if not is_context_relevant(query, context_chunks):
        return "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
    
    prompt = build_prompt(context_chunks, query)
    answer = generate_answer(prompt)
    
    # Xử lý response tốt hơn để tránh lặp lại
    if "<|im_start|>assistant" in answer:
        # Lấy phần response sau assistant token
        response = answer.split("<|im_start|>assistant")[-1].strip()
    else:
        # Nếu không có assistant token, lấy phần cuối của response
        response = answer.strip()
    
    # Loại bỏ các token đặc biệt còn sót lại
    response = response.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()
    
    # Kiểm tra và loại bỏ nội dung lặp lại
    response = remove_repetitive_content(response, query)
    
    # Kiểm tra lại nếu response có vẻ như bịa đặt
    if is_response_hallucinated(response, context_chunks):
        return "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
    
    return response


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
        repetition_penalty=1.2,  # Giảm lặp lại
        no_repeat_ngram_size=3,  # Tránh lặp lại cụm từ 3 từ
        early_stopping=True,     # Dừng sớm khi gặp end token
        pad_token_id=tokenizer.eos_token_id,
        streamer=streamer,
    )

    thread = Thread(target=model.generate, kwargs=generate_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text


def rag_answer_stream(query, top_k=3, pdf_name=None):
    context_chunks = get_relevant_chunks(query, top_k, pdf_name=pdf_name)
    
    # Kiểm tra nếu không có context hoặc context không liên quan
    if not context_chunks or len(context_chunks) == 0:
        def no_info_generator():
            yield "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
        return no_info_generator()
    
    # Kiểm tra độ liên quan của context với câu hỏi
    if not is_context_relevant(query, context_chunks):
        def no_info_generator():
            yield "Tôi không có thông tin về vấn đề này trong các tài liệu hiện có."
        return no_info_generator()
    
    prompt = build_prompt(context_chunks, query)
    return generate_answer_stream(prompt)

# Test độc lập (comment nếu tích hợp)
if __name__ == "__main__":
    query = "An toàn thông tin là gì?"
    response = rag_answer(query)
    print(response)