# RAG.py: Retrieval và Generation (offline)

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
import re

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Load embedding model từ local
embedding_model_path = "../models/multilingual_e5_large"  # Path tương đối từ src/
embedding_model = SentenceTransformer(embedding_model_path)

# Load FAISS và chunks (local)
faiss_index_path = "../results/all_faiss.index"
faiss_index = faiss.read_index(faiss_index_path)
with open("../results/all_embeddings.pkl", "rb") as f:
    data = pickle.load(f)
chunks = [chunk for item in data for chunk in item["chunks"]]

# Load LLM từ local
model_path = "../models/vinallama-2.7b-chat"
tokenizer = AutoTokenizer.from_pretrained(model_path)
tokenizer.pad_token = tokenizer.eos_token
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto"
)
model.eval()

def sanitize_query(query):
    query = re.sub(r'[<>\'";]', '', query)
    sensitive_keywords = ["hack", "exploit", "phá hoại", "tấn công thực tế"]
    if any(kw in query.lower() for kw in sensitive_keywords):
        return None, "Câu hỏi liên quan đến hoạt động bất hợp pháp. Hãy tuân thủ pháp luật và tập trung vào bảo vệ."
    return query, None

def get_relevant_chunks(query, top_k=3, max_tokens_per_chunk=512):
    query = query.strip()
    query_vector = embedding_model.encode([query])
    D, I = faiss_index.search(np.array(query_vector).astype("float32"), top_k)
    context_chunks = []
    for i in I[0]:
        chunk = chunks[i]
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
    Bạn là một trợ lý AI an toàn thông tin. Chỉ trả lời dựa trên thông tin được cung cấp. Nếu không biết, hãy trả lời: "Tôi không có thông tin về câu hỏi này." Không được bịa. Trả lời bằng tiếng Việt.
    <|im_end|>
    <|im_start|>user
    Thông tin:
    {context}

    Câu hỏi: {question}
    <|im_end|>
    <|im_start|>assistant
    """.strip()

def generate_answer(prompt):
    encoding = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        input_ids=encoding.input_ids,
        attention_mask=encoding.attention_mask,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id
    )
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return full_response.split("<|im_start|>assistant")[-1].strip()

def rag_answer(query):
    sanitized_query, error = sanitize_query(query)
    if error:
        return error
    context_chunks = get_relevant_chunks(sanitized_query)
    if not context_chunks:
        return "Tôi không có thông tin về câu hỏi này."
    prompt = build_prompt(context_chunks, sanitized_query)
    return generate_answer(prompt)